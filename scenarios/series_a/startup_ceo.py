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

from thenvoi import Agent
from thenvoi.config import load_agent_config

from adapter_factory import create_adapter
from platform_url import get_platform_url, get_ws_url
from scenarios.prompt_templates import build_lead_prompt
from self_aware_preprocessor import SelfAwarePreprocessor

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
        "2. Keep founder equity above **60% post-money** after the round.\n"
        "3. Limit board to **2 investor seats + 2 founder seats + 1 independent**."
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
    opposing_specialist="VC Legal Counsel",
    counsel_reference="our legal counsel's assessment",
    concessions=(
        "- You may accept $20M pre-money if other terms are favorable.\n"
        "- You may accept a 3rd investor-affiliated board observer (non-voting)."
    ),
    topics="",
)


async def main() -> None:
    load_dotenv()
    # Room topology is fixed by kickoff.py — prevent the LLM from inviting
    # agents into rooms or creating new ones (the SDK's base prompt otherwise
    # encourages this, overriding our custom instructions).
    from tool_filter import remove_tools
    remove_tools("thenvoi_add_participant", "thenvoi_lookup_peers", "thenvoi_create_chatroom")

    agent_id, api_key = load_agent_config("startup_ceo")

    scenario = os.path.basename(os.path.dirname(__file__))
    adapter = create_adapter("startup_ceo", CUSTOM_SECTION, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=SelfAwarePreprocessor(),
    )

    logger.info("Startup CEO agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
