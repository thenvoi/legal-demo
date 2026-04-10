"""Series A funding negotiation scenario configuration."""
from __future__ import annotations

AGENTS = [
    {
        "config_key": "startup_ceo",
        "name": "Startup CEO",
        "description": "Lead negotiator AI agent for NovaTech (startup) in Series A negotiations.",
    },
    {
        "config_key": "startup_lawyer",
        "name": "Startup Lawyer",
        "description": "Legal counsel AI agent for NovaTech, advises on term sheet provisions and governance.",
    },
    {
        "config_key": "vc_partner",
        "name": "VC Partner",
        "description": "Lead negotiator AI agent for Apex Ventures (VC) in Series A negotiations.",
    },
    {
        "config_key": "vc_legal_counsel",
        "name": "VC Legal Counsel",
        "description": "Legal counsel AI agent for Apex Ventures, advises on deal structure and investor protections.",
    },
]

AGENT_MODULES = [
    "scenarios.series_a.startup_ceo",
    "scenarios.series_a.startup_lawyer",
    "scenarios.series_a.vc_partner",
    "scenarios.series_a.vc_legal_counsel",
]


def get_kickoff_config(agent_ids: dict, agent_names: dict) -> dict:
    """Return room topology, briefings, and kickoff message."""
    return {
        "rooms": [
            {
                "name": "negotiation",
                "owner": "startup_ceo",
                "participants": ["startup_lawyer", "vc_partner", "vc_legal_counsel"],
                "message": (
                    "Thank you for taking this meeting. NovaTech is raising "
                    "a $5M Series A. We're an AI-powered drug-discovery platform with "
                    "$1.2M ARR growing 3x year-over-year.\n\n"
                    "Two terms to agree on:\n"
                    "1. Valuation and investment amount\n"
                    "2. Board composition and governance rights\n\n"
                    "Let's work through them in order."
                ),
                "mentions": ["vc_partner"],
            },
        ]
    }
