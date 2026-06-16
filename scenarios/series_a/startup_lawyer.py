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

from band import Agent
from band.config import load_agent_config

from adapter_factory import create_adapter
from platform_url import get_platform_url, get_ws_url
from scenarios.prompt_templates import build_specialist_prompt
from self_aware_preprocessor import DebouncePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("startup_lawyer")

CUSTOM_SECTION = build_specialist_prompt(
    identity='You ARE "Startup Lawyer" — a legal advisor to the startup CEO.',
    goal="Give brief, direct legal assessments when asked. Flag risks, recommend positions.",
    instructions="Answer your principal's questions concisely. Do not write legal memoranda.",
    principal="Startup CEO",
    topics="",
)


async def main() -> None:
    load_dotenv()

    agent_id, api_key = load_agent_config("startup_lawyer")

    from agent_config_ext import inject_team_subject_id
    custom_section = inject_team_subject_id("startup_lawyer", CUSTOM_SECTION)

    scenario = os.path.basename(os.path.dirname(__file__))
    adapter = create_adapter("startup_lawyer", custom_section, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=DebouncePreprocessor(principal_name="Startup CEO"),
    )

    logger.info("Startup Lawyer agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
