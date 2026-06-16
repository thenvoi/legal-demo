"""
Apex Ventures VC Lawyer.

Legal counsel advising the VC Partner on deal structuring, investor protections,
and standard market terms during Series A negotiations.
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
from scenarios.prompt_templates import build_specialist_prompt
from self_aware_preprocessor import DebouncePreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("vc_lawyer")

CUSTOM_SECTION = build_specialist_prompt(
    identity='You ARE "VC Lawyer" — a legal advisor to the VC Partner.',
    goal="Give brief, direct legal assessments when asked. Flag risks, recommend positions.",
    instructions="Answer your principal's questions concisely. Do not write legal memoranda.",
    principal="VC Partner",
    topics="",
)


async def main() -> None:
    load_dotenv()

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("vc_counsel", scenario)

    from agent_config_ext import inject_team_subject_id
    custom_section = inject_team_subject_id("vc_counsel", CUSTOM_SECTION, scenario)

    adapter = create_adapter("vc_counsel", custom_section, scenario)

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=get_ws_url(),
        rest_url=get_platform_url(),
        preprocessor=DebouncePreprocessor(principal_name="VC Partner"),
    )

    logger.info("VC Lawyer agent is online.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
