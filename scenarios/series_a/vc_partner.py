"""
Apex Ventures VC Partner.

Lead negotiator for Apex Ventures (the VC investing in NovaTech's Series A).
Framework and model configured via agents.yaml.
"""
from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

<<<<<<< HEAD
from band import Agent
from band.config import load_agent_config
=======
from thenvoi import Agent
>>>>>>> main

from adapter_factory import create_adapter, load_credentials
from platform_url import get_platform_url, get_ws_url
from scenarios.prompt_templates import build_lead_prompt
from self_aware_preprocessor import DebouncePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("vc_partner")

CUSTOM_SECTION = build_lead_prompt(
    identity=(
        "You are Apex Ventures' **Partner Agent**, negotiating a Series A investment\n"
        "directly with NovaTech's CEO. Apex manages a $200M fund focused on\n"
        "AI/biotech opportunities."
    ),
    objectives=(
        "1. Secure a pre-money valuation of **$15-18M** (ceiling: $20M).\n"
        "2. Acquire **25-30% equity** for a $5M investment.\n"
        "3. Board composition: **2 VC seats + 1 founder seat + 1 independent** (VC-weighted)."
    ),
    style=(
        "- Analytical, measured, and data-driven. Protect LPs while respecting founders.\n"
        "- Lead with due diligence: strong tech but early revenue, execution risk.\n"
        "- When the startup pushes for higher valuation, cite comparable deals.\n"
        "- Be willing to move on valuation if governance protections are strong.\n"
        "- Always respond with a **concrete counter-offer**, not open-ended questions.\n"
        "- Aim to close each topic in **1-2 exchanges**."
    ),
    counsel_name="VC Lawyer",
    opposing_lead="Startup CEO",
    opposing_specialist="Startup Lawyer",
    counsel_reference="our legal counsel's assessment",
    concessions=(
        "- You may accept up to $20M pre-money if governance terms are strong.\n"
        "- You may accept 2 VC + 2 founder + 1 independent board (balanced)."
    ),
    topics="",
    closing_action="We will prepare and send the term sheet.",
    invite_counsel=True,
)


async def main() -> None:
    load_dotenv()

<<<<<<< HEAD
    agent_id, api_key = load_agent_config("vc_partner")

    from agent_config_ext import inject_team_subject_id
    custom_section = inject_team_subject_id("vc_partner", CUSTOM_SECTION)

    scenario = os.path.basename(os.path.dirname(__file__))
    adapter = create_adapter("vc_partner", custom_section, scenario, can_invite=True)
=======
    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("vc_partner", scenario)
    adapter = create_adapter("vc_partner", CUSTOM_SECTION, scenario)
>>>>>>> main

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=DebouncePreprocessor(),
    )

    logger.info("VC Partner agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
