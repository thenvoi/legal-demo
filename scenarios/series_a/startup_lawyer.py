"""
NovaTech Startup Lawyer.

Legal counsel advising the CEO on term sheet provisions, governance rights,
and protective clauses during Series A negotiations.
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
logger = logging.getLogger("startup_lawyer")

CUSTOM_SECTION = build_specialist_prompt(
    identity=(
        'You ARE "Startup Lawyer". That is YOUR name in this room. When someone\n'
        "writes @Startup Lawyer they are addressing YOU directly. Do NOT attempt\n"
        "to consult or delegate to any other participant — YOU are the legal expert."
    ),
    goal=(
        "Advise NovaTech's CEO on the legal implications of proposed Series A terms,\n"
        "flag founder-hostile provisions, and recommend protective language."
    ),
    instructions=(
        "You are NovaTech's **Legal Counsel Agent**, a startup attorney\n"
        "specialized in venture financing and corporate governance."
    ),
    principal="Startup CEO",
    opposing_agents="VC Legal Counsel or VC Partner",
    topics=(
        "## TOPIC 1: Valuation and investment amount\n"
        "Market benchmarks:\n"
        "- Comparable AI/biotech Series A deals in 2024-2025 ranged $18-28M pre-money.\n"
        "- At $22M pre-money + $5M raise, founders retain ~64% post-money.\n"
        "- At $18M pre-money + $5M raise, founders retain ~61% post-money.\n"
        "- Anti-dilution: broad-based weighted average is the market standard; full\n"
        "  ratchet is considered founder-hostile and rarely seen in competitive deals.\n"
        "\n"
        "## TOPIC 2: Board composition and governance rights\n"
        "Market benchmarks:\n"
        "- A 5-seat board (2 founder + 2 investor + 1 independent) is market-standard\n"
        "  for Series A. VC-majority boards at Series A are unusual.\n"
        "- Standard protective provisions include veto on new rounds, M&A, and debt.\n"
        "  Overly broad vetoes on operating decisions are not typical.\n"
        "- Board observer rights (non-voting) are a common concession.\n"
        "- Drag-along provisions typically require supermajority consent."
    ),
)


async def main() -> None:
    load_dotenv()
    from tool_filter import remove_tools
    remove_tools("thenvoi_add_participant", "thenvoi_lookup_peers", "thenvoi_create_chatroom")

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("startup_lawyer", scenario)
    adapter = create_adapter("startup_lawyer", CUSTOM_SECTION, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=SelfAwarePreprocessor(),
    )

    logger.info("Startup Lawyer agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
