"""Series A funding negotiation scenario configuration."""
from __future__ import annotations

AGENTS = [
    {
        "config_key": "startup_ceo",
        "name": "Startup CEO",
        "description": "Lead negotiator AI agent for NovaTech (startup) in Series A negotiations.",
        "team": "startup",
    },
    {
        "config_key": "startup_lawyer",
        "name": "Startup Lawyer",
        "description": "Legal counsel AI agent for NovaTech, advises on term sheet provisions and governance.",
        "team": "startup",
    },
    {
        "config_key": "vc_partner",
        "name": "VC Partner",
        "description": "Lead negotiator AI agent for Apex Ventures (VC) in Series A negotiations.",
        "team": "vc",
    },
    {
        "config_key": "vc_counsel",
        "name": "VC Lawyer",
        "description": "Legal counsel AI agent for Apex Ventures, advises on deal structure and investor protections.",
        "team": "vc",
    },
]

# Team strategy seeded as organization-scoped long-term memories.
# Both the lead negotiator and counsel on each team can query these.
TEAM_MEMORIES = {
    "startup": [
        "Target pre-money valuation: $22M or higher. Walk-away floor: $18M.",
        "Target founder equity: above 60% post-money after the round.",
        "Preferred board: 2 investor seats + 2 founder seats + 1 independent.",
        "Concessions: may accept $20M pre-money if other terms favorable. "
        "May accept a 3rd investor-affiliated board observer (non-voting).",
    ],
    "vc": [
        "Target pre-money valuation: $15-18M. Ceiling: $20M.",
        "Target equity: 25-30% for a $5M investment.",
        "Preferred board: 2 VC seats + 1 founder seat + 1 independent (VC-weighted).",
        "Concessions: may accept up to $20M pre-money if governance terms strong. "
        "May accept 2 VC + 2 founder + 1 independent board (balanced).",
    ],
}

AGENT_MODULES = [
    "scenarios.series_a.startup_ceo",
    "scenarios.series_a.startup_lawyer",
    "scenarios.series_a.vc_partner",
    "scenarios.series_a.vc_lawyer",
]


def get_kickoff_config(agent_ids: dict, agent_names: dict) -> dict:
    """Return room topology, briefings, and kickoff message."""
    return {
        "rooms": [
            {
                "name": "negotiation",
                "owner": "startup_ceo",
                "participants": ["vc_partner"],
                "message": (
                    "Thank you for taking this meeting. NovaTech is raising "
                    "a $5M Series A. We're an AI-powered drug-discovery platform with "
                    "$1.2M ARR growing 3x year-over-year.\n\n"
                    "Introductions: I'm the CEO of NovaTech, negotiating directly with "
                    "@VC Partner from Apex Ventures. We'll each bring in our legal counsel "
                    "as specific terms require.\n\n"
                    "Two terms to agree on:\n"
                    "1. Valuation and investment amount\n"
                    "2. Board composition and governance rights\n\n"
                    "Let's work through them in order."
                ),
                "mentions": ["vc_partner"],
            },
        ]
    }
