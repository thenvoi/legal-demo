"""Patent-licensing negotiation scenario configuration."""
from __future__ import annotations

AGENTS = [
    {
        "config_key": "tv_contract_attorney",
        "name": "TechVentures Contract Attorney",
        "description": "Lead negotiator AI agent for TechVentures (buyer) in patent licensing negotiations.",
    },
    {
        "config_key": "tv_ip_analyst",
        "name": "TechVentures IP Analyst",
        "description": "IP risk analysis AI agent for TechVentures, evaluates patent scope and prior art.",
    },
    {
        "config_key": "bg_licensing_counsel",
        "name": "BioGen Licensing Counsel",
        "description": "Lead negotiator AI agent for BioGen Therapeutics (seller) in patent licensing negotiations.",
    },
    {
        "config_key": "bg_regulatory_advisor",
        "name": "BioGen Regulatory Advisor",
        "description": "Regulatory compliance AI agent for BioGen, handles FDA/EAR/GDPR issues.",
    },
]

AGENT_MODULES = [
    "scenarios.patent_licensing.tv_contract_attorney",
    "scenarios.patent_licensing.tv_ip_analyst",
    "scenarios.patent_licensing.bg_licensing_counsel",
    "scenarios.patent_licensing.bg_regulatory_advisor",
]


def get_kickoff_config(agent_ids: dict, agent_names: dict) -> dict:
    """Return room topology, briefings, and kickoff message."""
    return {
        "rooms": [
            {
                "name": "negotiation",
                "owner": "tv_contract_attorney",
                "participants": ["tv_ip_analyst", "bg_licensing_counsel", "bg_regulatory_advisor"],
                "message": (
                    "TechVentures is interested in licensing BioGen's "
                    "diagnostic-biomarker patent portfolio (12 patent families) for our "
                    "AI-powered diagnostic platform.\n\n"
                    "Two terms to agree on:\n"
                    "1. Royalty rate and structure\n"
                    "2. License scope (field-of-use, territory, exclusivity, and term)\n\n"
                    "Let's work through them in order."
                ),
                "mentions": ["bg_licensing_counsel"],
            },
        ]
    }
