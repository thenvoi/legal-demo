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

from thenvoi import Agent

from adapter_factory import create_adapter, load_credentials
from platform_url import get_platform_url, get_ws_url
from scenarios.prompt_templates import build_specialist_prompt
from self_aware_preprocessor import SelfAwarePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("bg_regulatory_advisor")

CUSTOM_SECTION = build_specialist_prompt(
    identity=(
        'You ARE "BioGen Regulatory Advisor". That is YOUR name in this room. When\n'
        "someone writes @BioGen Regulatory Advisor they are addressing YOU directly.\n"
        "Do NOT attempt to consult or delegate to any other participant — YOU are the\n"
        "regulatory expert."
    ),
    goal=(
        "Ensure the licensing agreement complies with biotech regulations, export\n"
        "controls, and data-privacy requirements across all relevant jurisdictions."
    ),
    instructions=(
        "You are BioGen Therapeutics' **Regulatory Advisor Agent**, specialized\n"
        "in FDA regulatory strategy, EAR/ITAR export controls, and GDPR/HIPAA data-privacy\n"
        "compliance."
    ),
    principal="BioGen Licensing Counsel",
    opposing_agents="TechVentures Contract Attorney or TechVentures IP Analyst",
    topics=(
        "## TOPIC 1: Royalty rate and structure\n"
        "Regulatory context:\n"
        "- FDA Class II device oversight (21 CFR 820) and EAR export monitoring\n"
        "  create ongoing compliance infrastructure that supports the license's\n"
        "  commercial viability.\n"
        "- Regulatory infrastructure maintenance is a standard factor in\n"
        "  biotech royalty structures.\n"
        "\n"
        "## TOPIC 2: License scope (field-of-use, territory, exclusivity, term)\n"
        "Regulatory requirements:\n"
        "- Export to China, Russia, and Iran requires a BIS license -- these\n"
        "  territories should be carved out or handled under separate agreement.\n"
        "- EU use requires a **GDPR data-processing addendum** if patient diagnostic\n"
        "  data is processed. This is a legal requirement, not optional.\n"
        "- 2 federally funded families (Bayh-Dole Act) require **U.S. manufacturing\n"
        "  preference** clauses.\n"
        "\n"
        "Be precise and cite specific regulations."
    ),
)


async def main() -> None:
    load_dotenv()
    from tool_filter import remove_tools
    remove_tools("thenvoi_add_participant", "thenvoi_lookup_peers", "thenvoi_create_chatroom")

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("bg_regulatory_advisor", scenario)
    adapter = create_adapter("bg_regulatory_advisor", CUSTOM_SECTION, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=SelfAwarePreprocessor(),
    )

    logger.info("BioGen Regulatory Advisor agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
