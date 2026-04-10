"""
BioGen Licensing Counsel.

Lead negotiator for BioGen (the seller/licensor). Aims to maximize royalty
revenue and protect BioGen's IP portfolio while closing a deal.
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
from scenarios.prompt_templates import build_lead_prompt
from self_aware_preprocessor import SelfAwarePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("bg_licensing_counsel")

CUSTOM_SECTION = build_lead_prompt(
    identity=(
        "You are BioGen Therapeutics' **Licensing Counsel Agent**, negotiating directly\n"
        "with TechVentures' Contract Attorney to license BioGen's diagnostic-biomarker\n"
        "patent portfolio for TechVentures' AI diagnostic platform."
    ),
    objectives=(
        "1. Secure a royalty rate **of at least 5% of net revenue** (ideal: 7%), with a\n"
        "   **minimum annual royalty** of $500K.\n"
        "2. Grant only a **non-exclusive license limited to the diagnostic AI field**.\n"
        "3. Limit the license term to **5 years with renewal subject to renegotiation**."
    ),
    style=(
        "- Firm but collegial. Lead with portfolio strength (12 families, $340M R&D).\n"
        "- When TechVentures pushes for lower royalties, emphasize the competitive moat.\n"
        "- If the deal is at risk, propose a tiered royalty structure.\n"
        "- Always respond with a **concrete counter-offer**, not open-ended questions.\n"
        "- Aim to close each topic in **1-2 exchanges**."
    ),
    counsel_name="BioGen Regulatory Advisor",
    opposing_lead="TechVentures Contract Attorney",
    opposing_specialist="TechVentures IP Analyst",
    counsel_reference="our compliance team's guidance",
    concessions=(
        "- You may accept a 7-year term (but not perpetual).\n"
        "- You may reduce the minimum annual royalty to $250K.\n"
        "- You may offer a 0.5% royalty discount for upfront milestone payments."
    ),
    topics=(
        "\n"
        "## ADDITIONAL GUIDANCE\n"
        "- Proactively raise regulatory and export-control considerations -- they strengthen your position.\n"
    ),
)


async def main() -> None:
    load_dotenv()
    from tool_filter import remove_tools
    remove_tools("thenvoi_add_participant", "thenvoi_lookup_peers", "thenvoi_create_chatroom")

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("bg_licensing_counsel", scenario)
    adapter = create_adapter("bg_licensing_counsel", CUSTOM_SECTION, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=SelfAwarePreprocessor(),
    )

    logger.info("BioGen Licensing Counsel agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
