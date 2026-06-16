"""Custom preprocessors for identity-awareness and message debouncing.

``SelfAwarePreprocessor`` marks the agent's own entry in the participant list
so the LLM doesn't try to @mention itself.

``DebouncePreprocessor`` wraps ``SelfAwarePreprocessor`` and skips processing
when newer messages are already queued, preventing agents from responding to
stale state in rapid-fire conversations.

Usage::

    from self_aware_preprocessor import DebouncePreprocessor

    agent = Agent.create(
        ...,
        preprocessor=DebouncePreprocessor(),
    )
"""
from __future__ import annotations

import dataclasses
import logging
import re

from thenvoi.core.types import AgentInput
from thenvoi.preprocessing.default import DefaultPreprocessor

logger = logging.getLogger(__name__)


_YOU_MARKER = " (You)"
_SELF_MENTION_WARNING = " NEVER mention yourself (the entry marked '(You)')."


class SelfAwarePreprocessor:
    """Wraps DefaultPreprocessor; marks self with '(You)' and hides non-Agent participants."""

    def __init__(self) -> None:
        self._default = DefaultPreprocessor()

    async def process(self, ctx, event, agent_id: str) -> AgentInput | None:
        result = await self._default.process(ctx, event, agent_id)
        if result is None or result.participants_msg is None:
            return result

        agent_handle = _resolve_handle(agent_id, ctx.participants)
        non_agent_handles = _non_agent_handles(ctx.participants)
        new_msg = result.participants_msg
        if agent_handle:
            new_msg = _mark_self(new_msg, agent_handle)
        if non_agent_handles:
            new_msg = _strip_participants(new_msg, non_agent_handles)
        if new_msg != result.participants_msg:
            result = dataclasses.replace(result, participants_msg=new_msg)
        return result


def _non_agent_handles(participants: list[dict]) -> set[str]:
    """Return handles of non-Agent participants (humans, etc.)."""
    return {
        p["handle"]
        for p in participants
        if p.get("type") != "Agent" and p.get("handle")
    }


def _strip_participants(msg: str, handles: set[str]) -> str:
    """Remove participant lines for the given handles."""
    lines = msg.split("\n")
    filtered = [
        line for line in lines
        if not any(f"@{h} " in line for h in handles)
    ]
    return "\n".join(filtered)


def _resolve_handle(agent_id: str, participants: list[dict]) -> str | None:
    for p in participants:
        if p.get("id") == agent_id:
            return p.get("handle")
    return None


def _resolve_handle_by_name(name: str, participants: list[dict]) -> str | None:
    for p in participants:
        if p.get("name") == name:
            return p.get("handle")
    return None


class DebouncePreprocessor:
    """Wraps SelfAwarePreprocessor; skips stale messages when a newer one from
    the **same sender** is already queued.

    When an agent is slow to respond and multiple messages from the same
    participant pile up, this preprocessor returns ``None`` for all but the
    latest message from that sender.  Messages from *different* senders are
    never skipped, so cross-party messages (e.g. opposing negotiator while
    consulting counsel) are always processed.

    Returning ``None`` causes the SDK to skip LLM invocation while still
    marking the message as processed on the server.

    Args:
        principal_name: If set, only the participant with this display name
            (plus self) is shown in the participant list.  Use this for
            specialist agents so they only see their principal.
    """

    def __init__(
        self,
        inner: SelfAwarePreprocessor | None = None,
        principal_name: str | None = None,
    ) -> None:
        self._inner = inner or SelfAwarePreprocessor()
        self._principal_name = principal_name

    async def process(self, ctx, event, agent_id: str) -> AgentInput | None:
        sender_id = getattr(getattr(event, "payload", None), "sender_id", None)
        if sender_id and ctx.queue.qsize() > 0:
            # Peek at queued events to see if a newer message from the same
            # sender is waiting.  Uses the internal deque (same pattern the
            # SDK itself uses in _drain_duplicate_from_queue).
            # Verified against thenvoi-sdk 0.2.4.
            for queued in ctx.queue._queue:  # noqa: SLF001
                queued_sender = getattr(
                    getattr(queued, "payload", None), "sender_id", None
                )
                if queued_sender == sender_id:
                    logger.info(
                        "Debounce: skipping message from %s "
                        "(%d more queued, newer from same sender exists)",
                        sender_id,
                        ctx.queue.qsize(),
                    )
                    return None
        result = await self._inner.process(ctx, event, agent_id)

        # Strip participants not visible to this specialist (if configured).
        if result and result.participants_msg and self._principal_name:
            agent_handle = _resolve_handle(agent_id, ctx.participants)
            principal_handle = _resolve_handle_by_name(
                self._principal_name, ctx.participants
            )
            allowed = set()
            if agent_handle:
                allowed.add(agent_handle)
            if principal_handle:
                allowed.add(principal_handle)
            all_handles = {
                p["handle"] for p in ctx.participants if p.get("handle")
            }
            to_hide = all_handles - allowed
            if to_hide:
                new_msg = _strip_participants(result.participants_msg, to_hide)
                result = dataclasses.replace(result, participants_msg=new_msg)

        return result


def _mark_self(msg: str, agent_handle: str) -> str:
    # Add "(You)" after the agent's own line in the participant list
    pattern = re.compile(
        rf"(- @{re.escape(agent_handle)} .+?)(\n|$)"
    )
    msg = pattern.sub(rf"\g<1>{_YOU_MARKER}\2", msg, count=1)

    # Append self-mention warning to the IMPORTANT instruction line
    if "NEVER mention yourself" not in msg:
        msg = msg.replace(
            "Handles are lowercase with no spaces.",
            "Handles are lowercase with no spaces." + _SELF_MENTION_WARNING,
        )
    return msg
