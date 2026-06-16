"""
Create demo agents on the Thenvoi platform and write per-scenario credentials.

Requires a User API key (not an agent key). Get one from platform.thenvoi.com
under your account settings, then put it in ``.env`` as ``THENVOI_API_KEY_USER``.

Usage:
    python setup_agents.py                             # series_a (default)
    python setup_agents.py --scenario series_a         # Series A agents

To tear down a scenario:
    python setup_agents.py --delete                    # series_a
    python setup_agents.py --delete --scenario patent_licensing

Scenarios are isolated: each writes to ``agent_config.<scenario>.yaml`` and
``.agent_ids.<scenario>.txt``, so registering one scenario never disturbs
another.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
import os
import sys

import yaml
from dotenv import load_dotenv

from adapter_factory import agent_ids_path, credentials_path
from memory_config import memory_enabled
from platform_url import get_platform_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_SCENARIO = "series_a"

# Maps team names to env var names for per-team User API keys.
TEAM_KEY_ENV_VARS = {
    "startup": "BAND_API_KEY_USER_STARTUP",
    "vc": "BAND_API_KEY_USER_VC",
}


def _get_api_key_for_team(team: str | None) -> str:
    """Return the User API key for a team, falling back to the default."""
    if team and team in TEAM_KEY_ENV_VARS:
        key = os.environ.get(TEAM_KEY_ENV_VARS[team])
        if key:
            return key
    key = os.environ.get("BAND_API_KEY_USER")
    if not key:
        raise ValueError(
            "BAND_API_KEY_USER environment variable is required. "
            "Get a User API key from platform.thenvoi.com account settings."
        )
    return key


def _all_api_keys() -> set[str]:
    """Collect all unique user API keys from environment."""
    keys = set()
    for env_var in ["BAND_API_KEY_USER", *TEAM_KEY_ENV_VARS.values()]:
        key = os.environ.get(env_var)
        if key:
            keys.add(key)
    return keys


async def create_agents(
    scenario: str, agents: list[dict], team_memories: dict | None = None
) -> None:
    from thenvoi_rest import AsyncRestClient
    from thenvoi_rest.types import AgentRegisterRequest

    platform_url = get_platform_url()
    config_file = credentials_path(scenario)
    ids_file = agent_ids_path(scenario)
    config = {}
    agent_ids = []

    # team -> {agent_api_key, lead_agent_id}
    teams_seen: dict[str, dict] = {}

    for agent_def in agents:
        team = agent_def.get("team")
        api_key = _get_api_key_for_team(team)
        client = AsyncRestClient(api_key=api_key, base_url=platform_url)

        logger.info("Creating: %s (team=%s) ...", agent_def["name"], team or "default")
        response = await client.human_api_agents.register_my_agent(
            agent=AgentRegisterRequest(
                name=agent_def["name"],
                description=agent_def["description"],
            )
        )

        agent = response.data.agent
        credentials = response.data.credentials

        config[agent_def["config_key"]] = {
            "agent_id": agent.id,
            "api_key": credentials.api_key,
        }
        agent_ids.append(agent.id)

        # Track lead (first) agent per team — used as subject_id for memory scoping
        if team and team not in teams_seen:
            teams_seen[team] = {
                "agent_api_key": credentials.api_key,
                "lead_agent_id": agent.id,
            }

        logger.info("  Created: %s (ID: %s)", agent.name, agent.id)

    # Write team_subject_id into config for each agent
    for agent_def in agents:
        team = agent_def.get("team")
        if team and team in teams_seen:
            config[agent_def["config_key"]]["team_subject_id"] = teams_seen[team]["lead_agent_id"]

    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info("Credentials written to %s", config_file.name)

    with open(ids_file, "w") as f:
        for aid in agent_ids:
            f.write(f"{aid}\n")
    logger.info("Agent IDs saved to %s for cleanup", ids_file.name)

    # Seed team memories (subject-scoped to lead agent for team isolation)
    if team_memories:
        await _seed_team_memories(teams_seen, team_memories, platform_url)


async def _seed_team_memories(
    teams_seen: dict[str, dict],
    team_memories: dict[str, list[str]],
    platform_url: str,
) -> None:
    """Store team strategy as subject-scoped memories keyed to the lead agent."""
    from thenvoi_rest import AsyncRestClient, MemoryCreateRequest

    for team, memories in team_memories.items():
        if team not in teams_seen:
            logger.warning("No agents registered for team '%s', skipping memory seeding", team)
            continue

        agent_api_key = teams_seen[team]["agent_api_key"]
        subject_id = teams_seen[team]["lead_agent_id"]
        client = AsyncRestClient(api_key=agent_api_key, base_url=platform_url)

        logger.info("Seeding %d memories for team '%s' (subject=%s)...", len(memories), team, subject_id)
        for content in memories:
            await client.agent_api_memories.create_agent_memory(
                memory=MemoryCreateRequest(
                    content=content,
                    system="long_term",
                    type="semantic",
                    segment="guideline",
                    scope="subject",
                    subject_id=subject_id,
                    thought="Team negotiation strategy seeded at setup.",
                ),
            )
        logger.info("  Seeded %d memories for team '%s'", len(memories), team)


async def delete_agents(scenario: str, agent_names: set[str] | None = None) -> None:
    """Delete agents by name. If agent_names is None, delete ALL agents."""
    from thenvoi_rest import AsyncRestClient

    platform_url = get_platform_url()
    api_keys = _all_api_keys()

    if not api_keys:
        logger.warning("No User API keys found — skipping platform cleanup.")
    else:
        for api_key in api_keys:
            client = AsyncRestClient(api_key=api_key, base_url=platform_url)
            try:
                response = await client.human_api_agents.list_my_agents()
                agents = response.data or []
            except Exception as e:
                logger.warning("Could not list agents for a key: %s", e)
                continue

            for agent in agents:
                if agent_names is not None and agent.name not in agent_names:
                    continue
                try:
                    await client.human_api_agents.delete_my_agent(id=agent.id, force=True)
                    logger.info("Deleted agent: %s (%s)", agent.name, agent.id)
                except Exception as e:
                    logger.warning("Could not delete %s: %s", agent.id, e)

    # Always clean up local files
    for path in [agent_ids_path(scenario), credentials_path(scenario)]:
        if path.exists():
            path.unlink()
    logger.info("Cleanup complete.")


async def main() -> None:
    load_dotenv()

    # Parse scenario
    scenario = DEFAULT_SCENARIO
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--scenario" and i < len(sys.argv) - 1:
            scenario = sys.argv[i + 1]

    if "--delete" in sys.argv:
        scenario_mod = importlib.import_module(f"scenarios.{scenario}.scenario")
        names = {a["name"] for a in scenario_mod.AGENTS}
        await delete_agents(scenario, agent_names=names)
        return

    # Load scenario to know which agent names to clean up
    scenario_mod = importlib.import_module(f"scenarios.{scenario}.scenario")
    agent_names = {a["name"] for a in scenario_mod.AGENTS}

    # Clean up only THIS scenario's agents before creating new ones
    logger.info("Cleaning up existing agents for scenario: %s", scenario)
    await delete_agents(scenario, agent_names=agent_names)

    logger.info("Setting up agents for scenario: %s", scenario)
    # Memory seeding uses the Enterprise-only Memory API; skip it unless enabled.
    team_memories = getattr(scenario_mod, "TEAM_MEMORIES", None) if memory_enabled() else None
    if team_memories is None:
        logger.info("Memory disabled (set BAND_ENABLE_MEMORY=1 to seed team strategy).")
    await create_agents(scenario, scenario_mod.AGENTS, team_memories)


if __name__ == "__main__":
    asyncio.run(main())
