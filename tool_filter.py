"""Per-process tool filtering for Thenvoi agents.

The Thenvoi SDK does not yet support an `excluded_tools` parameter on
adapters or Agent.create().  As a workaround we monkey-patch the
adapter-level tool-list builders so excluded tools never reach the LLM.

This is safe because each agent is launched in its own
multiprocessing.Process (via run_all.py), so mutations here are
fully isolated — they never affect other agents or other scenarios.
"""
from __future__ import annotations

_EXCLUDED: set[str] = set()


def remove_tools(*tool_names: str) -> None:
    """Remove named tools from all adapter tool lists for this process."""
    _EXCLUDED.update(tool_names)
    _patch_once()


_patched = False


def _patch_once() -> None:
    global _patched
    if _patched:
        return
    _patched = True

    # --- Patch LangGraph adapter ---
    from thenvoi.integrations.langgraph.langchain_tools import (
        agent_tools_to_langchain as _orig_lg,
    )
    import thenvoi.integrations.langgraph.langchain_tools as _lg_mod
    import thenvoi.adapters.langgraph as _lg_adapter_mod

    def _filtered_lg(*args, **kwargs):
        tools = _orig_lg(*args, **kwargs)
        return [t for t in tools if t.name not in _EXCLUDED]

    _lg_mod.agent_tools_to_langchain = _filtered_lg
    # The adapter imports it at call time, so patch the module it reads from
    _lg_adapter_mod.agent_tools_to_langchain = _filtered_lg  # type: ignore[attr-error]

    # --- Patch CrewAI adapter ---
    from thenvoi.adapters.crewai import CrewAIAdapter

    _orig_crewai = CrewAIAdapter._create_crewai_tools

    def _filtered_crewai(self):
        tools = _orig_crewai(self)
        return [t for t in tools if t.name not in _EXCLUDED]

    CrewAIAdapter._create_crewai_tools = _filtered_crewai  # type: ignore[assignment]

    # --- Patch CrewAI empty-response crash ---
    # CrewAI hard-rejects empty LLM responses (raises ValueError).  When an
    # agent is instructed to stay silent (not @mentioned), the model sometimes
    # returns nothing instead of calling a tool.  Substitute a no-op string so
    # the executor treats it as a harmless final answer.
    from crewai.utilities import agent_utils as _agent_utils_mod

    _orig_validate = _agent_utils_mod._validate_and_finalize_llm_response

    def _safe_validate(answer, executor_context, printer, verbose=True):
        if not answer:
            answer = "[no response]"
        return _orig_validate(answer, executor_context, printer, verbose=verbose)

    _agent_utils_mod._validate_and_finalize_llm_response = _safe_validate

    # --- Also patch the runtime TOOL_DEFINITIONS for the Anthropic adapter ---
    from thenvoi.runtime.tools import TOOL_DEFINITIONS

    for name in _EXCLUDED:
        TOOL_DEFINITIONS.pop(name, None)
