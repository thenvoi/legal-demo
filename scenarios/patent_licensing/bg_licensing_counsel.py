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

from band import Agent
from band.config import load_agent_config

from adapter_factory import create_adapter
from platform_url import get_platform_url, get_ws_url
from scenarios.prompt_templates import build_lead_prompt
from self_aware_preprocessor import DebouncePreprocessor

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
    closing_action="We will prepare and send the draft license agreement.",
    invite_counsel=True,
)


async def main() -> None:
    load_dotenv()

    agent_id, api_key = load_agent_config("bg_licensing_counsel")

    from agent_config_ext import inject_team_subject_id
    custom_section = inject_team_subject_id("bg_licensing_counsel", CUSTOM_SECTION)

    scenario = os.path.basename(os.path.dirname(__file__))
    adapter = create_adapter("bg_licensing_counsel", custom_section, scenario, can_invite=True)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=DebouncePreprocessor(),
    )

    logger.info("BioGen Licensing Counsel agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
