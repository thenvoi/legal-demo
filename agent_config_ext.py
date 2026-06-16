"""Extended agent config loader that injects team_subject_id into prompts."""
from __future__ import annotations

import yaml

from adapter_factory import credentials_path

PLACEHOLDER = "__TEAM_SUBJECT_ID__"


def inject_team_subject_id(agent_key: str, custom_section: str, scenario: str) -> str:
    """Replace the ``__TEAM_SUBJECT_ID__`` placeholder with the agent's team id.

    Reads the same per-scenario credentials file that ``setup_agents.py`` writes
    and ``load_credentials`` reads (``agent_config.<scenario>.yaml``), so the
    lookup can never drift from where the id was actually stored.
    """
    with open(credentials_path(scenario)) as f:
        config = yaml.safe_load(f) or {}

    subject_id = config.get(agent_key, {}).get("team_subject_id", "")
    return custom_section.replace(PLACEHOLDER, subject_id)
