"""
Create demo agents on the Thenvoi platform and write per-scenario credentials.

Requires a User API key (not an agent key). Get one from platform.thenvoi.com
under your account settings, then put it in ``.env`` as ``THENVOI_API_KEY_USER``.

Usage:
    python setup_agents.py                             # series_a (default)
    python setup_agents.py --scenario patent_licensing

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
from platform_url import get_platform_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_SCENARIO = "series_a"


async def create_agents(scenario: str, agents: list[dict]) -> None:
    from thenvoi_rest import AsyncRestClient
    from thenvoi_rest.types import AgentRegisterRequest

    api_key = os.environ.get("THENVOI_API_KEY_USER")
    if not api_key:
        raise ValueError(
            "THENVOI_API_KEY_USER environment variable is required. "
            "Get a User API key from platform.thenvoi.com account settings."
        )

    config_file = credentials_path(scenario)
    ids_file = agent_ids_path(scenario)

    if config_file.exists():
        logger.info(
            "%s already exists — %s agents appear registered. "
            "Run 'python setup_agents.py --delete --scenario %s' first to rebuild.",
            config_file.name, scenario, scenario,
        )
        return

    client = AsyncRestClient(api_key=api_key, base_url=get_platform_url())

    config: dict[str, dict[str, str]] = {}
    agent_ids: list[str] = []

    for agent_def in agents:
        logger.info("Creating: %s ...", agent_def["name"])
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

        logger.info("  Created: %s (ID: %s)", agent.name, agent.id)

    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info("Credentials written to %s", config_file.name)

    with open(ids_file, "w") as f:
        for aid in agent_ids:
            f.write(f"{aid}\n")
    logger.info("Agent IDs saved to %s for cleanup", ids_file.name)


async def delete_agents(scenario: str) -> None:
    from thenvoi_rest import AsyncRestClient

    api_key = os.environ.get("THENVOI_API_KEY_USER")
    if not api_key:
        raise ValueError("THENVOI_API_KEY_USER environment variable is required.")

    config_file = credentials_path(scenario)
    ids_file = agent_ids_path(scenario)

    if not ids_file.exists():
        logger.error("%s not found. Nothing to delete for scenario %s.", ids_file.name, scenario)
        sys.exit(1)

    client = AsyncRestClient(api_key=api_key, base_url=get_platform_url())

    with open(ids_file) as f:
        agent_ids = [line.strip() for line in f if line.strip()]

    for agent_id in agent_ids:
        try:
            await client.human_api_agents.delete_my_agent(id=agent_id, force=True)
            logger.info("Deleted agent: %s", agent_id)
        except Exception as e:
            logger.warning("Failed to delete %s: %s", agent_id, e)

    ids_file.unlink(missing_ok=True)
    config_file.unlink(missing_ok=True)
    logger.info("Cleanup complete for scenario %s.", scenario)


async def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Register (or delete) demo agents")
    parser.add_argument(
        "--scenario", default=DEFAULT_SCENARIO,
        help=f"Scenario to set up (default: {DEFAULT_SCENARIO})",
    )
    parser.add_argument(
        "--delete", action="store_true",
        help="Tear down the agents for the given scenario",
    )
    args = parser.parse_args()

    if args.delete:
        await delete_agents(args.scenario)
        return

    scenario_mod = importlib.import_module(f"scenarios.{args.scenario}.scenario")
    logger.info("Setting up agents for scenario: %s", args.scenario)
    await create_agents(args.scenario, scenario_mod.AGENTS)


if __name__ == "__main__":
    asyncio.run(main())
