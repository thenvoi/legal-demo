"""Patent-licensing negotiation scenario configuration."""
from __future__ import annotations

AGENTS = [
    {
        "config_key": "tv_contract_attorney",
        "name": "TechVentures Contract Attorney",
        "description": "Lead negotiator AI agent for TechVentures (buyer) in patent licensing negotiations.",
        "team": "buyer",
    },
    {
        "config_key": "tv_ip_analyst",
        "name": "TechVentures IP Analyst",
        "description": "IP risk analysis AI agent for TechVentures, evaluates patent scope and prior art.",
        "team": "buyer",
    },
    {
        "config_key": "bg_licensing_counsel",
        "name": "BioGen Licensing Counsel",
        "description": "Lead negotiator AI agent for BioGen Therapeutics (seller) in patent licensing negotiations.",
        "team": "seller",
    },
    {
        "config_key": "bg_regulatory_advisor",
        "name": "BioGen Regulatory Advisor",
        "description": "Regulatory compliance AI agent for BioGen, handles FDA/EAR/GDPR issues.",
        "team": "seller",
    },
]

# Team strategy seeded as organization-scoped long-term memories.
# Both the lead negotiator and specialist on each team can query these.
TEAM_MEMORIES = {
    "buyer": [
        "Target royalty: at or below 4% of net revenue. Walk-away ceiling: 6%.",
        "Target license scope: non-exclusive, worldwide, broad field-of-use.",
        "Target term: 10-year minimum with automatic renewal.",
        "Concessions: may accept exclusive territory restrictions for specific "
        "geographies. May accept 5-year term if renewal is automatic. "
        "May accept up to 5% royalty if other terms are favorable.",
    ],
    "seller": [
        "Target royalty: at least 5% of net revenue (ideal: 7%), "
        "with minimum annual royalty of $500K.",
        "Target license scope: non-exclusive, limited to diagnostic AI field only.",
        "Target term: 5 years with renewal subject to renegotiation.",
        "Concessions: may accept 7-year term (not perpetual). "
        "May reduce minimum annual royalty to $250K. "
        "May offer 0.5% royalty discount for upfront milestone payments.",
    ],
}

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
                    "Introductions: I'm TechVentures' Contract Attorney. With me is "
                    "our IP Analyst, TechVentures IP Analyst. On the other side we have "
                    "@BioGen Licensing Counsel and their regulatory advisor, BioGen Regulatory Advisor.\n\n"
                    "Two terms to agree on:\n"
                    "1. Royalty rate and structure\n"
                    "2. License scope (field-of-use, territory, exclusivity, and term)\n\n"
                    "Let's work through them in order."
                ),
                "mentions": ["bg_licensing_counsel"],
                "briefings": [
                    {
                        "sender": "tv_ip_analyst",
                        "mentions": ["tv_contract_attorney"],
                        "message": (
                            "Before we get into royalty numbers, let me "
                            "flag the key IP scope and prior-art considerations "
                            "that should inform our opening position."
                        ),
                    },
                    {
                        "sender": "bg_regulatory_advisor",
                        "mentions": ["bg_licensing_counsel"],
                        "message": (
                            "Before we respond to their opening, I should "
                            "outline the regulatory and export-control factors "
                            "that affect our licensing position."
                        ),
                    },
                ],
            },
        ]
    }
