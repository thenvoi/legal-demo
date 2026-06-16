"""Extended agent config loader that injects team_subject_id into prompts."""
from __future__ import annotations

import yaml

CONFIG_FILE = "agent_config.yaml"
PLACEHOLDER = "__TEAM_SUBJECT_ID__"


def inject_team_subject_id(agent_key: str, custom_section: str) -> str:
    """Replace __TEAM_SUBJECT_ID__ placeholder with the actual ID from config."""
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)

    subject_id = config.get(agent_key, {}).get("team_subject_id", "")
    return custom_section.replace(PLACEHOLDER, subject_id)
