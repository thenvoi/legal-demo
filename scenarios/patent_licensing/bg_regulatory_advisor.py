"""
BioGen Regulatory Advisor.

Specialist in biotech regulatory compliance, export controls, and data-privacy
requirements. Called upon when regulatory clauses or cross-border issues arise.
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
logger = logging.getLogger("bg_regulatory_advisor")

CUSTOM_SECTION = build_specialist_prompt(
    identity='You ARE "BioGen Regulatory Advisor" — a regulatory advisor to BioGen\'s Licensing Counsel.',
    goal="Give brief, direct regulatory assessments when asked. Flag compliance requirements.",
    instructions="Answer your principal's questions concisely. Do not write regulatory reports.",
    principal="BioGen Licensing Counsel",
    topics="",
)


async def main() -> None:
    load_dotenv()

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("bg_regulatory_advisor", scenario)

    from agent_config_ext import inject_team_subject_id
    custom_section = inject_team_subject_id("bg_regulatory_advisor", CUSTOM_SECTION)

    adapter = create_adapter("bg_regulatory_advisor", custom_section, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=DebouncePreprocessor(principal_name="BioGen Licensing Counsel"),
    )

    logger.info("BioGen Regulatory Advisor agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
