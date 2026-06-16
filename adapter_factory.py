"""
Build the correct adapter for an agent based on the scenario's agents.yaml.

Each scenario directory contains an ``agents.yaml`` like::

    startup_ceo:
      framework: anthropic
      model: claude-sonnet-4-6-20250514

    vc_partner:
      framework: langgraph
      model: claude-sonnet-4-6-20250514

Supported frameworks: ``anthropic``, ``pydantic_ai``, ``langgraph``, ``crewai``,
``letta``, ``parlant`` (parlant must be wired up directly in the agent module).
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from band import AdapterFeatures, Capability


SCENARIOS_DIR = Path(__file__).parent / "scenarios"

# Shared adapter features:
# - capabilities: enable the memory tools (band_list_memories, band_store_memory, ...)
#   that the negotiation prompts rely on for team strategy and deal-state tracking.
# - exclude_tools: drop room/peer-management tools the agents must never use. This is
#   honored by the LangGraph adapter; pydantic_ai/anthropic ignore it (the prompt is
#   the backstop there — see scenarios/prompt_templates.py).
_FEATURES = AdapterFeatures(
    capabilities={Capability.MEMORY},
    exclude_tools=("band_add_participant", "band_lookup_peers", "band_create_chatroom"),
)


def _model_provider(model: str) -> str:
    """Infer provider from model id."""
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("gpt") or model.startswith("o"):
        return "openai"
    raise ValueError(f"Cannot infer provider for model: {model}")


def create_adapter(agent_key: str, custom_section: str, scenario: str):
    """Return an adapter instance configured via ``scenarios/<scenario>/agents.yaml``."""
    config_path = SCENARIOS_DIR / scenario / "agents.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    agent_cfg = config[agent_key]
    framework = agent_cfg["framework"]
    model = agent_cfg["model"]
    provider = _model_provider(model)

    if framework == "anthropic":
        from band.adapters import AnthropicAdapter

        return AnthropicAdapter(
            model=model,
            prompt=custom_section,
            features=_FEATURES,
        )

    if framework == "pydantic_ai":
        from band.adapters import PydanticAIAdapter

        return PydanticAIAdapter(
            model=f"{provider}:{model}",
            custom_section=custom_section,
            features=_FEATURES,
        )

    if framework == "langgraph":
        from langgraph.checkpoint.memory import InMemorySaver
        from band.adapters import LangGraphAdapter

        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model=model)
        else:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=model)

        return LangGraphAdapter(
            llm=llm,
            checkpointer=InMemorySaver(),
            custom_section=custom_section,
            features=_FEATURES,
        )

    if framework == "crewai":
        from band.adapters import CrewAIAdapter

        return CrewAIAdapter(
            model=model,
            custom_section=custom_section,
            features=_FEATURES,
        )

    if framework == "letta":
        from band.adapters import LettaAdapter
        from band.adapters.letta import LettaAdapterConfig

        letta_model = f"{provider}/{model}"
        config = LettaAdapterConfig(
            model=letta_model,
            custom_section=custom_section,
            enable_memory_tools=True,
            api_key=agent_cfg.get("letta_api_key") or os.environ.get("LETTA_API_KEY"),
            base_url=agent_cfg.get("letta_base_url", "https://api.letta.com"),
        )
        return LettaAdapter(config=config)

    if framework == "parlant":
        raise ValueError(
            "Parlant requires async setup (Server is an async context manager). "
            "Create the adapter directly in the agent module:\n"
            "  import parlant.sdk as p\n"
            "  async with p.Server() as server:\n"
            "      agent = await server.create_agent(name=..., description=...)\n"
            "      adapter = ParlantAdapter(server=server, parlant_agent=agent, "
            "custom_section=...)"
        )

    raise ValueError(f"Unknown framework: {framework}")
