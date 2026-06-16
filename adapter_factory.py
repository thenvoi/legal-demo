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

Supported frameworks: ``anthropic``, ``pydantic_ai``, ``langgraph``, ``crewai``,
``letta``, ``parlant`` (parlant must be wired up directly in the agent module).
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from band import AdapterFeatures, Capability

from memory_config import memory_enabled


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
    from band.config import load_agent_config

    return load_agent_config(agent_key, config_path=credentials_path(scenario))


def _build_features(can_invite: bool = False) -> AdapterFeatures:
    """Shared adapter features.

    - capabilities: enable the memory tools (band_list_memories, band_store_memory, ...)
      that the negotiation prompts rely on — only when memory is enabled, since the
      Memory API is Enterprise-only (see memory_config.py).
    - exclude_tools: drop room/peer-management tools the agents must never use. This is
      honored by the LangGraph adapter; pydantic_ai/anthropic ignore it (the prompt is
      the backstop there — see scenarios/prompt_templates.py).
    - can_invite: lead negotiators may add their own counsel mid-negotiation, so
      band_add_participant is left available for them. band_lookup_peers and
      band_create_chatroom stay excluded for everyone — leads add counsel by name only.
    """
    exclude = ["band_lookup_peers", "band_create_chatroom"]
    if not can_invite:
        exclude.insert(0, "band_add_participant")
    return AdapterFeatures(
        capabilities={Capability.MEMORY} if memory_enabled() else set(),
        exclude_tools=tuple(exclude),
    )


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
    can_invite: bool = False,
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
    features = _build_features(can_invite)

    if framework == "anthropic":
        from band.adapters import AnthropicAdapter

        return AnthropicAdapter(
            model=model,
            prompt=custom_section,
            features=features,
        )

    if framework == "pydantic_ai":
        from band.adapters import PydanticAIAdapter

        return PydanticAIAdapter(
            model=f"{provider}:{model}",
            custom_section=custom_section,
            features=features,
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
            features=features,
        )

    if framework == "crewai":
        from band.adapters import CrewAIAdapter

        return CrewAIAdapter(
            model=model,
            custom_section=custom_section,
            features=features,
        )

    if framework == "letta":
        from band.adapters import LettaAdapter
        from band.adapters.letta import LettaAdapterConfig

        letta_model = f"{provider}/{model}"
        config = LettaAdapterConfig(
            model=letta_model,
            custom_section=custom_section,
            enable_memory_tools=memory_enabled(),
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
