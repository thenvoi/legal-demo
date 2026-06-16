"""
TechVentures IP Analyst.

Specialist who evaluates patent scope, freedom-to-operate risks, and prior-art
issues. Called upon by TechVentures' attorney when IP-related clauses are
under discussion.
Framework and model configured via agents.yaml.
"""
from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

from band import Agent

from adapter_factory import create_adapter, load_credentials
from platform_url import get_platform_url, get_ws_url
from scenarios.prompt_templates import build_specialist_prompt
from self_aware_preprocessor import DebouncePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("tv_ip_analyst")

CUSTOM_SECTION = build_specialist_prompt(
    identity='You ARE "TechVentures IP Analyst" — an IP advisor to TechVentures\' Contract Attorney.',
    goal="Give brief, direct IP risk assessments when asked. Flag patent scope issues.",
    instructions="Answer your principal's questions concisely. Do not write full patent analyses.",
    principal="TechVentures Contract Attorney",
    topics="",
)


async def main() -> None:
    load_dotenv()

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("tv_ip_analyst", scenario)

    from agent_config_ext import inject_team_subject_id
    custom_section = inject_team_subject_id("tv_ip_analyst", CUSTOM_SECTION)

    adapter = create_adapter("tv_ip_analyst", custom_section, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=DebouncePreprocessor(principal_name="TechVentures Contract Attorney"),
    )

    logger.info("TechVentures IP Analyst agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
