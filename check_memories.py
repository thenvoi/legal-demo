"""Quick diagnostic: list memories visible to each agent, verify team isolation."""
from __future__ import annotations

import argparse
import asyncio

import yaml
from dotenv import load_dotenv
from thenvoi_rest import AsyncRestClient

from adapter_factory import credentials_path
from platform_url import get_platform_url


async def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="List memories per agent for a scenario")
    parser.add_argument(
        "--scenario", default="series_a",
        help="Scenario whose agent_config to inspect (default: series_a)",
    )
    args = parser.parse_args()

    with open(credentials_path(args.scenario)) as f:
        config = yaml.safe_load(f)

    platform_url = get_platform_url()

    for name, creds in config.items():
        client = AsyncRestClient(api_key=creds["api_key"], base_url=platform_url)

        identity = await client.agent_api_identity.get_agent_me()
        subject_id = creds.get("team_subject_id", "N/A")
        print(f"\n{'='*60}")
        print(f"Agent: {identity.data.name} ({name})")
        print(f"  ID: {identity.data.id}")
        print(f"  team_subject_id: {subject_id}")

        if subject_id and subject_id != "N/A":
            memories = await client.agent_api_memories.list_agent_memories(
                scope="subject",
                subject_id=subject_id,
            )
            items = memories.data or []
            print(f"  Subject-scoped memories ({len(items)}):")
            for mem in items:
                print(f"    - [{mem.system}/{mem.type}/{mem.segment}] {mem.content[:80]}")
        else:
            print("  No team_subject_id configured")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
