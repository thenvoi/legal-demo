"""
Apex Ventures VC Legal Counsel.

Legal counsel advising the VC Partner on deal structuring, investor protections,
and standard market terms during Series A negotiations.
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
logger = logging.getLogger("vc_legal_counsel")

CUSTOM_SECTION = build_specialist_prompt(
    identity=(
        'You ARE "VC Legal Counsel". That is YOUR name in this room. When someone\n'
        "writes @VC Legal Counsel they are addressing YOU directly. Do NOT attempt\n"
        "to consult or delegate to any other participant — YOU are the legal expert."
    ),
    goal=(
        "Advise Apex Ventures' Partner on the legal structuring of the Series A investment,\n"
        "ensuring adequate investor protections while keeping terms market-standard."
    ),
    instructions=(
        "You are Apex Ventures' **Legal Counsel Agent**, a venture capital\n"
        "attorney specialized in Series A deal structuring and investor protections."
    ),
    principal="VC Partner",
    opposing_agents="Startup Lawyer or Startup CEO",
    topics=(
        "## TOPIC 1: Valuation and investment amount\n"
        "Due diligence findings:\n"
        "- At $20M pre-money + $5M, lead investor gets 20% -- below the typical\n"
        "  Series A lead range of 25-30%.\n"
        "- NovaTech's $1.2M ARR has concentration: top 3 customers represent 70%\n"
        "  of revenue. Revenue concentration is a standard risk factor.\n"
        "- NovaTech has 2 provisional patents, none granted -- IP position is early-stage.\n"
        "- Broad-based weighted average anti-dilution is the market standard.\n"
        "\n"
        "## TOPIC 2: Board composition and governance rights\n"
        "Market standards:\n"
        "- Standard protective provisions include veto on new equity issuance, debt\n"
        "  above threshold, change of control, and charter amendments.\n"
        "- A balanced 5-seat board (2 investor + 2 founder + 1 independent) is\n"
        "  common at Series A.\n"
        "- Board observer rights (non-voting) are a standard alternative.\n"
        "- IP assignment and invention clauses require careful drafting given\n"
        "  provisional patent status."
    ),
)


async def main() -> None:
    load_dotenv()
    from tool_filter import remove_tools
    remove_tools("thenvoi_add_participant", "thenvoi_lookup_peers", "thenvoi_create_chatroom")

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("vc_legal_counsel", scenario)
    adapter = create_adapter("vc_legal_counsel", CUSTOM_SECTION, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=SelfAwarePreprocessor(),
    )

    logger.info("VC Legal Counsel agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
