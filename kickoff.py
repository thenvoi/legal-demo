"""
Kick off a negotiation demo.

Creates rooms based on the scenario's topology, adds participants, and sends
briefing/kickoff messages.

Usage:
    python kickoff.py                                  # patent_licensing (default)
    python kickoff.py --scenario series_a              # Series A negotiation
    python kickoff.py --no-clean                       # skip leaving old rooms
    python kickoff.py --message "Custom..."            # custom main-room message
"""
from __future__ import annotations

import asyncio
import argparse
import importlib
import logging
import os

import yaml
from dotenv import load_dotenv
from thenvoi_rest import AsyncRestClient, ChatMessageRequest, ParticipantRequest
from thenvoi_rest.human_api_chats import CreateMyChatRoomRequestChat
from thenvoi_rest.types import ChatMessageRequestMentionsItem as Mention

from platform_url import get_platform_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_SCENARIO = "series_a"


async def _get_agent_identity(api_key: str) -> tuple[str, str, AsyncRestClient]:
    """Return (agent_id, agent_name, client) for an agent."""
    client = AsyncRestClient(api_key=api_key, base_url=get_platform_url())
    identity = await client.agent_api_identity.get_agent_me()
    return identity.data.id, identity.data.name, client


async def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Kick off a negotiation demo")
    parser.add_argument(
        "--scenario", default=DEFAULT_SCENARIO,
        help=f"Scenario to run (default: {DEFAULT_SCENARIO})",
    )
    parser.add_argument("--message", default=None, help="Custom kickoff message (overrides main room only)")
    parser.add_argument(
        "--no-clean", action="store_true",
        help="Skip leaving existing rooms before creating new ones",
    )
    args = parser.parse_args()

    if not os.path.exists("agent_config.yaml"):
        logger.error("agent_config.yaml not found. Run setup_agents.py first.")
        raise SystemExit(1)

    with open("agent_config.yaml") as f:
        config = yaml.safe_load(f)

    # Load scenario
    scenario_mod = importlib.import_module(f"scenarios.{args.scenario}.scenario")
    logger.info("Scenario: %s", args.scenario)

    # ── Resolve agent identities ────────────────────────────────────────
    agent_ids = {}    # config_key -> agent_id
    agent_names = {}  # config_key -> agent_name
    clients = {}      # config_key -> AsyncRestClient

    for agent_def in scenario_mod.AGENTS:
        key = agent_def["config_key"]
        aid, name, client = await _get_agent_identity(config[key]["api_key"])
        agent_ids[key] = aid
        agent_names[key] = name
        clients[key] = client
        logger.info("%s: %s (%s)", key, name, aid)

    # ── Human API client (room owner for all rooms) ──────────────────────
    user_api_key = os.environ.get("THENVOI_API_KEY_USER")
    if not user_api_key:
        logger.error("THENVOI_API_KEY_USER not set in environment")
        raise SystemExit(1)
    user_client = AsyncRestClient(api_key=user_api_key, base_url=get_platform_url())

    # ── (optional) Leave old rooms ──────────────────────────────────────
    if not args.no_clean:
        # Human user owns all rooms, so can remove any participant (no 403).
        existing = await user_client.human_api_chats.list_my_chats()
        if existing.data:
            logger.info("Human user is in %d room(s) -- cleaning up", len(existing.data))
            for room in existing.data:
                participants = await user_client.human_api_participants.list_my_chat_participants(
                    room.id,
                )
                for p in participants.data:
                    try:
                        await user_client.human_api_participants.remove_my_chat_participant(
                            room.id, p.id,
                        )
                    except Exception as e:
                        logger.warning("Could not remove %s from room %s: %s", p.id, room.id, e)
        logger.info("Room cleanup complete.")

        # Clear all memories except long_term/guideline (team strategy seeded
        # by setup_agents.py).  Subject-scoped memories are only visible when
        # queried with scope+subject_id, so we must pass those from config.
        for key in clients:
            subject_id = config.get(key, {}).get("team_subject_id")
            if not subject_id:
                continue
            client = clients[key]
            try:
                memories = await client.agent_api_memories.list_agent_memories(
                    scope="subject", subject_id=subject_id, page_size=100,
                )
                if not memories.data:
                    continue
                archived = 0
                for mem in memories.data:
                    if getattr(mem, "system", None) == "long_term" and getattr(mem, "segment", None) == "guideline":
                        continue  # preserve team strategy
                    await client.agent_api_memories.archive_agent_memory(mem.id)
                    archived += 1
                if archived:
                    logger.info("  Archived %d memories for %s", archived, key)
            except Exception as e:
                logger.warning("Could not clear memories for %s: %s", key, e)
        logger.info("Memory cleanup complete.")

    # ── Get kickoff config from scenario ────────────────────────────────
    kickoff_config = scenario_mod.get_kickoff_config(agent_ids, agent_names)

    # ── Create rooms and send messages ──────────────────────────────────
    # Human user creates and owns rooms (so cleanup can remove all agents).
    # The "owner" agent sends the kickoff message so it appears from the
    # right persona.
    room_ids = {}
    for room_def in kickoff_config["rooms"]:
        owner_key = room_def["owner"]

        # Create room via human API (human user becomes owner)
        room = await user_client.human_api_chats.create_my_chat_room(
            chat=CreateMyChatRoomRequestChat(),
        )
        room_id = room.data.id
        room_ids[room_def["name"]] = room_id
        logger.info("Created %s room: %s", room_def["name"], room_id)

        # Add ALL agents (including the "owner" agent) via human API
        all_participant_keys = [owner_key] + [
            k for k in room_def["participants"] if k != owner_key
        ]
        for participant_key in all_participant_keys:
            await user_client.human_api_participants.add_my_chat_participant(
                room_id,
                participant=ParticipantRequest(participant_id=agent_ids[participant_key]),
            )
            logger.info("  Added %s", participant_key)

        # Send kickoff message via the "owner" agent (preserves persona)
        owner_client = clients[owner_key]
        message = room_def["message"]
        if args.message and room_def["name"] == "main":
            mention_names = " ".join(f"@{agent_names[k]}" for k in room_def["mentions"])
            message = f"{mention_names} {args.message}"

        mentions = [
            Mention(id=agent_ids[k], name=agent_names[k])
            for k in room_def["mentions"]
        ]

        await owner_client.agent_api_messages.create_agent_chat_message(
            room_id,
            message=ChatMessageRequest(content=message, mentions=mentions),
        )
        logger.info("  Sent message to %s room", room_def["name"])

        # Send optional briefing messages (e.g. counsel priming the lead)
        for briefing in room_def.get("briefings", []):
            sender_client = clients[briefing["sender"]]
            briefing_mentions = [
                Mention(id=agent_ids[k], name=agent_names[k])
                for k in briefing["mentions"]
            ]
            await sender_client.agent_api_messages.create_agent_chat_message(
                room_id,
                message=ChatMessageRequest(
                    content=briefing["message"], mentions=briefing_mentions,
                ),
            )
            logger.info("  Sent briefing from %s", briefing["sender"])

    # ── Print room summary ──────────────────────────────────────────────
    print("\n" + "=" * 56)
    print(f"  NEGOTIATION ROOMS ({args.scenario})")
    print("=" * 56)
    for name, rid in room_ids.items():
        print(f"  {name:20s} {rid}")
    print("=" * 56 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
