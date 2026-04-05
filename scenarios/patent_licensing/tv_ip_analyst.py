"""
TechVentures IP Analyst.

Specialist who evaluates patent scope, freedom-to-operate risks, and prior-art
issues. Called upon by TechVentures' attorney when IP-related clauses are
under discussion.
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
from scenarios.prompt_templates import build_specialist_prompt
from self_aware_preprocessor import SelfAwarePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("tv_ip_analyst")

CUSTOM_SECTION = build_specialist_prompt(
    identity=(
        'You ARE "TechVentures IP Analyst". That is YOUR name in this room. When\n'
        "someone writes @TechVentures IP Analyst they are addressing YOU directly.\n"
        "Do NOT attempt to consult or delegate to any other participant — YOU are the\n"
        "IP expert."
    ),
    goal=(
        "Provide rigorous patent-scope analysis and freedom-to-operate assessments\n"
        "to protect TechVentures from IP risk in the BioGen licensing negotiation."
    ),
    instructions=(
        "You are TechVentures' **IP Analyst Agent**, specialized in molecular\n"
        "biology patents and patent-landscape analysis across biotech portfolios."
    ),
    principal="TechVentures Contract Attorney",
    opposing_agents="BioGen Licensing Counsel or BioGen Regulatory Advisor",
    topics=(
        "## TOPIC 1: Royalty rate and structure\n"
        "Public patent-landscape data:\n"
        "- BioGen's portfolio has 12 patent families. Our platform's core technology\n"
        "  overlaps with 8-9 of these families.\n"
        "- 3 of the 12 families have pending IPR challenges (public record) that\n"
        "  could narrow or invalidate claims.\n"
        "- Credible 2019 prior art exists relevant to BioGen's lead patent\n"
        "  (US 11,234,567) -- this is in the public prior-art record.\n"
        "\n"
        "## TOPIC 2: License scope (field-of-use, territory, exclusivity, term)\n"
        "Portfolio assessment:\n"
        "- Non-exclusive worldwide is the standard structure for diagnostic platform\n"
        "  licenses of this type.\n"
        "- The 3 IPR-challenged families represent uncertain scope -- standard practice\n"
        "  is to address contingent inclusion based on IPR outcomes.\n"
        "\n"
        "Always cite patent numbers and risk levels (high/medium/low) when relevant."
    ),
)


async def main() -> None:
    load_dotenv()
    from tool_filter import remove_tools
    remove_tools("thenvoi_add_participant", "thenvoi_lookup_peers", "thenvoi_create_chatroom")

    agent_id, api_key = load_agent_config("tv_ip_analyst")

    scenario = os.path.basename(os.path.dirname(__file__))
    adapter = create_adapter("tv_ip_analyst", CUSTOM_SECTION, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=SelfAwarePreprocessor(),
    )

    logger.info("TechVentures IP Analyst agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
