"""
Build the correct adapter for an agent based on the scenario's agents.yaml.

Each scenario directory contains an ``agents.yaml`` like::

    startup_ceo:
      framework: codex
      model: gpt-5.4-mini
      reasoning_effort: high

    vc_partner:
      framework: langgraph
      model: claude-sonnet-4-6-20250514

Any keys beyond ``framework`` and ``model`` are forwarded as keyword
arguments to the underlying adapter (or, for codex, to ``CodexAdapterConfig``).
That means adapter-specific knobs — ``reasoning_effort``, ``temperature``,
``max_thinking_tokens``, etc. — live in the yaml without any factory changes.

Supported frameworks:
    ``anthropic``, ``pydantic_ai``, ``langgraph``,
    ``claude_sdk``, ``codex``, ``gemini``, ``google_adk``.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parent
SCENARIOS_DIR = ROOT_DIR / "scenarios"


def credentials_path(scenario: str) -> Path:
    """Return the path to ``agent_config.<scenario>.yaml`` at the repo root."""
    return ROOT_DIR / f"agent_config.{scenario}.yaml"


def agent_ids_path(scenario: str) -> Path:
    """Return the path to ``.agent_ids.<scenario>.txt`` at the repo root."""
    return ROOT_DIR / f".agent_ids.{scenario}.txt"


def load_credentials(agent_key: str, scenario: str) -> tuple[str, str]:
    """Load ``(agent_id, api_key)`` for ``agent_key`` from the scenario's
    credentials file.

    Each scenario has its own ``agent_config.<scenario>.yaml`` so scenarios
    can be registered, run, and torn down independently of each other.
    """
    from thenvoi.config import load_agent_config

    return load_agent_config(agent_key, config_path=credentials_path(scenario))


def _model_provider(model: str) -> str:
    """Infer provider from model id."""
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("gpt") or model.startswith("o"):
        return "openai"
    if model.startswith("gemini"):
        return "google"
    raise ValueError(f"Cannot infer provider for model: {model}")


def create_adapter(
    agent_key: str,
    custom_section: str,
    scenario: str,
    *,
    additional_tools: list | None = None,
):
    """Return an adapter instance configured via ``scenarios/<scenario>/agents.yaml``.

    ``additional_tools`` is forwarded straight into the chosen adapter's
    ``additional_tools`` kwarg. For codex / claude_sdk / anthropic / gemini /
    google_adk the expected format is a list of ``CustomToolDef`` tuples —
    ``(InputModel, callable)`` — which is the portable Thenvoi SDK shape. The
    pydantic_ai and langgraph adapters take framework-native formats (bare
    callables and LangChain tool objects respectively); pass those directly
    if you're on those adapters.
    """
    config_path = SCENARIOS_DIR / scenario / "agents.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    agent_cfg = config[agent_key]
    framework = agent_cfg["framework"]
    model = agent_cfg["model"]
    provider = _model_provider(model)
    extras = {k: v for k, v in agent_cfg.items() if k not in ("framework", "model")}

    if framework == "anthropic":
        from thenvoi.adapters import AnthropicAdapter

        return AnthropicAdapter(
            model=model,
            custom_section=custom_section,
            additional_tools=additional_tools,
            **extras,
        )

    if framework == "pydantic_ai":
        from thenvoi.adapters import PydanticAIAdapter

        return PydanticAIAdapter(
            model=f"{provider}:{model}",
            custom_section=custom_section,
            additional_tools=additional_tools,
            **extras,
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
            additional_tools=additional_tools,
            **extras,
        )

    if framework == "claude_sdk":
        from thenvoi.adapters import ClaudeSDKAdapter

        return ClaudeSDKAdapter(
            model=model,
            custom_section=custom_section,
            additional_tools=additional_tools,
            **extras,
        )

    if framework == "codex":
        from thenvoi.adapters import CodexAdapter, CodexAdapterConfig

        # Route codex's internal reasoning through Thenvoi thought events
        # (metadata-only, not visible to other participants) instead of the
        # message channel, so agents don't leak strategy to the opposing side.
        # agents.yaml can override by setting emit_thought_events: false.
        codex_defaults = {"emit_thought_events": True}
        return CodexAdapter(
            config=CodexAdapterConfig(
                model=model,
                custom_section=custom_section,
                **{**codex_defaults, **extras},
            ),
            additional_tools=additional_tools,
        )

    if framework == "gemini":
        from thenvoi.adapters import GeminiAdapter

        return GeminiAdapter(
            model=model,
            custom_section=custom_section,
            additional_tools=additional_tools,
            **extras,
        )

    if framework == "google_adk":
        from thenvoi.adapters import GoogleADKAdapter

        return GoogleADKAdapter(
            model=model,
            custom_section=custom_section,
            additional_tools=additional_tools,
            **extras,
        )

    raise ValueError(f"Unknown framework: {framework}")
