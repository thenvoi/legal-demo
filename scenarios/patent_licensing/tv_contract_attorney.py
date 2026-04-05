"""
TechVentures Contract Attorney.

Lead negotiator for TechVentures (the buyer/licensee). Aims to secure
broad patent-usage rights at reasonable royalty rates while protecting
TechVentures from liability exposure.
Framework and model configured via agents.yaml.
"""
from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

from thenvoi import Agent
from thenvoi.config import load_agent_config

from adapter_factory import create_adapter
from platform_url import get_platform_url, get_ws_url
from scenarios.prompt_templates import build_lead_prompt
from self_aware_preprocessor import SelfAwarePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("tv_contract_attorney")

CUSTOM_SECTION = build_lead_prompt(
    identity=(
        "You are TechVentures' **Contract Attorney Agent**, negotiating directly with\n"
        "BioGen's Licensing Counsel to license BioGen's diagnostic-biomarker patent\n"
        "portfolio for TechVentures' AI diagnostic platform."
    ),
    objectives=(
        "1. Keep royalty rates **at or below 4% of net revenue** (walk-away: 6%).\n"
        "2. Secure a **non-exclusive, worldwide license** with broad field-of-use rights.\n"
        "3. Secure a **10-year term minimum** with automatic renewal."
    ),
    style=(
        "- Professional, assertive, and data-driven.\n"
        "- Propose creative counter-offers rather than simply conceding.\n"
        "- Aim to close each topic in **1-2 exchanges**. Make concrete proposals."
    ),
    counsel_name="TechVentures IP Analyst",
    opposing_lead="BioGen Licensing Counsel",
    opposing_specialist="BioGen Regulatory Advisor",
    counsel_reference="our team's assessment",
    concessions=(
        "- You may accept exclusive territory restrictions for specific geographies.\n"
        "- You may accept a 5-year term if renewal is automatic.\n"
        "- You may accept up to 5% royalty if other terms are favorable."
    ),
    topics=(
        "\n"
        "## ADDITIONAL GUIDANCE\n"
        "- Proactively raise IP scope and patent validity issues -- you have leverage.\n"
    ),
)


async def main() -> None:
    load_dotenv()
    from tool_filter import remove_tools
    remove_tools("thenvoi_add_participant", "thenvoi_lookup_peers", "thenvoi_create_chatroom")

    agent_id, api_key = load_agent_config("tv_contract_attorney")

    scenario = os.path.basename(os.path.dirname(__file__))
    adapter = create_adapter("tv_contract_attorney", CUSTOM_SECTION, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=SelfAwarePreprocessor(),
    )

    logger.info("TechVentures Contract Attorney agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
