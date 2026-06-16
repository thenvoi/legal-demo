"""
NovaTech Startup CEO.

Lead negotiator for NovaTech (the startup seeking Series A funding).
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
from scenarios.prompt_templates import build_lead_prompt
from self_aware_preprocessor import DebouncePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("startup_ceo")

CUSTOM_SECTION = build_lead_prompt(
    identity=(
        "You are NovaTech's **CEO Agent**, negotiating Series A funding directly with\n"
        "Apex Ventures' Partner. NovaTech is an AI-powered drug-discovery platform\n"
        "with $1.2M ARR and 3x year-over-year growth."
    ),
    objectives=(
        "1. Secure a pre-money valuation of **$22M or higher** (walk-away: $18M).\n"
        "2. Limit board to **2 investor seats + 2 founder seats + 1 independent**."
    ),
    style=(
        "- Passionate but professional. Lead with traction and TAM.\n"
        "- When the VC pushes for lower valuation, emphasize competitive interest and\n"
        "  the $50B drug discovery market.\n"
        "- Be willing to concede on governance if valuation holds.\n"
        "- Aim to close each topic in **1-2 exchanges**. Make concrete proposals, not\n"
        "  open-ended questions."
    ),
    counsel_name="Startup Lawyer",
    opposing_lead="VC Partner",
    opposing_specialist="VC Lawyer",
    counsel_reference="our legal counsel's assessment",
    concessions=(
        "- You may accept $20M pre-money if other terms are favorable.\n"
        "- You may accept a 3rd investor-affiliated board observer (non-voting)."
    ),
    topics="",
    closing_action="We look forward to receiving the term sheet from your side.",
    invite_counsel=True,
)


async def main() -> None:
    load_dotenv()
    # Room topology is fixed by kickoff.py — prevent the LLM from inviting
    # agents into rooms or creating new ones (the SDK's base prompt otherwise
    # encourages this, overriding our custom instructions).

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("startup_ceo", scenario)

    from agent_config_ext import inject_team_subject_id
    custom_section = inject_team_subject_id("startup_ceo", CUSTOM_SECTION, scenario)

    adapter = create_adapter("startup_ceo", custom_section, scenario, can_invite=True)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=DebouncePreprocessor(),
    )

    logger.info("Startup CEO agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
