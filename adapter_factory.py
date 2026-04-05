"""
Build the correct adapter for an agent based on the scenario's agents.yaml.

Each scenario directory contains an ``agents.yaml`` like::

    startup_ceo:
      framework: anthropic
      model: claude-sonnet-4-6-20250514

    vc_partner:
      framework: langgraph
      model: claude-sonnet-4-6-20250514

Supported frameworks: ``anthropic``, ``pydantic_ai``, ``langgraph``.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml


SCENARIOS_DIR = Path(__file__).parent / "scenarios"


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
        from thenvoi.adapters import AnthropicAdapter

        return AnthropicAdapter(
            model=model,
            custom_section=custom_section,
        )

    if framework == "pydantic_ai":
        from thenvoi.adapters import PydanticAIAdapter

        return PydanticAIAdapter(
            model=f"{provider}:{model}",
            custom_section=custom_section,
        )

    if framework == "langgraph":
        from langgraph.checkpoint.memory import InMemorySaver
        from thenvoi.adapters import LangGraphAdapter

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
        )

    raise ValueError(f"Unknown framework: {framework}")
