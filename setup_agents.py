"""
Create demo agents on the Thenvoi platform and write agent_config.yaml.

Requires a User API key (not an agent key). Get one from platform.thenvoi.com
under your account settings.

Usage:
    python setup_agents.py                             # patent_licensing (default)
    python setup_agents.py --scenario series_a         # Series A agents

To tear down:
    python setup_agents.py --delete
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import os
import sys

import yaml
from dotenv import load_dotenv

from platform_url import get_platform_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_SCENARIO = "series_a"
AGENT_IDS_FILE = ".agent_ids.txt"
CONFIG_FILE = "agent_config.yaml"


async def create_agents(agents: list[dict]) -> None:
    from thenvoi_rest import AsyncRestClient
    from thenvoi_rest.types import AgentRegisterRequest

    api_key = os.environ.get("THENVOI_API_KEY_USER")
    if not api_key:
        raise ValueError(
            "THENVOI_API_KEY_USER environment variable is required. "
            "Get a User API key from platform.thenvoi.com account settings."
        )

    client = AsyncRestClient(api_key=api_key, base_url=get_platform_url())

    config = {}
    agent_ids = []

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

    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info("Credentials written to %s", CONFIG_FILE)

    with open(AGENT_IDS_FILE, "w") as f:
        for aid in agent_ids:
            f.write(f"{aid}\n")
    logger.info("Agent IDs saved to %s for cleanup", AGENT_IDS_FILE)


async def delete_agents() -> None:
    from thenvoi_rest import AsyncRestClient

    api_key = os.environ.get("THENVOI_API_KEY_USER")
    if not api_key:
        raise ValueError("THENVOI_API_KEY_USER environment variable is required.")

    if not os.path.exists(AGENT_IDS_FILE):
        logger.error("No %s file found. Nothing to delete.", AGENT_IDS_FILE)
        sys.exit(1)

    client = AsyncRestClient(api_key=api_key, base_url=get_platform_url())

    with open(AGENT_IDS_FILE) as f:
        agent_ids = [line.strip() for line in f if line.strip()]

    for agent_id in agent_ids:
        try:
            await client.human_api_agents.delete_my_agent(id=agent_id, force=True)
            logger.info("Deleted agent: %s", agent_id)
        except Exception as e:
            logger.warning("Failed to delete %s: %s", agent_id, e)

    os.remove(AGENT_IDS_FILE)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    logger.info("Cleanup complete.")


async def main() -> None:
    load_dotenv()

    if "--delete" in sys.argv:
        await delete_agents()
        return

    # Parse scenario
    scenario = DEFAULT_SCENARIO
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--scenario" and i < len(sys.argv) - 1:
            scenario = sys.argv[i + 1]

    if os.path.exists(CONFIG_FILE):
        logger.error(
            "%s already exists. Delete it first or run with --delete to tear down.",
            CONFIG_FILE,
        )
        sys.exit(1)

    scenario_mod = importlib.import_module(f"scenarios.{scenario}.scenario")
    logger.info("Setting up agents for scenario: %s", scenario)
    await create_agents(scenario_mod.AGENTS)


if __name__ == "__main__":
    asyncio.run(main())
