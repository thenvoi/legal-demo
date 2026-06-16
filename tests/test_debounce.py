"""Regression spec for DebouncePreprocessor.

The debounce skips a message when a *newer* message from the same sender is
already queued. It must NOT skip when the only same-sender event queued is a
DUPLICATE of the message currently being processed: during backlog sync the
runtime puts the sync-point message in the WS queue and drains it only AFTER
processing (band.runtime.execution._sync_via_next / _drain_duplicate_from_queue),
so debouncing on that duplicate drops the sole copy and stalls the agent.
"""
from __future__ import annotations

import pytest

from self_aware_preprocessor import DebouncePreprocessor


class _Payload:
    def __init__(self, sender_id: str, msg_id: str) -> None:
        self.sender_id = sender_id
        self.id = msg_id


class _Event:
    def __init__(self, sender_id: str, msg_id: str) -> None:
        self.payload = _Payload(sender_id, msg_id)


class _Queue:
    def __init__(self, events: list[_Event]) -> None:
        self._queue = list(events)

    def qsize(self) -> int:
        return len(self._queue)


class _Result:
    # Mirrors AgentInput just enough: the principal-filter block is skipped when
    # participants_msg is None, so process() returns this result unchanged.
    participants_msg = None


class _Ctx:
    def __init__(self, events: list[_Event]) -> None:
        self.queue = _Queue(events)
        self.participants: list[dict] = []


class _Inner:
    """Stand-in for SelfAwarePreprocessor so we can detect 'not debounced'."""

    def __init__(self) -> None:
        self.called = False

    async def process(self, ctx, event, agent_id):
        self.called = True
        return _Result()


SENDER = "sender-1"
AGENT = "agent-1"


@pytest.mark.asyncio
async def test_does_not_debounce_duplicate_of_current_message():
    # The queued event is the SAME message (same id) as the one being processed —
    # the sync-point duplicate. It must be processed, not skipped.
    inner = _Inner()
    deb = DebouncePreprocessor(inner=inner)
    event = _Event(SENDER, "msg-A")
    ctx = _Ctx([_Event(SENDER, "msg-A")])
    result = await deb.process(ctx, event, AGENT)
    assert result is not None, "duplicate of current message was wrongly debounced"
    assert inner.called


@pytest.mark.asyncio
async def test_debounces_genuinely_newer_message_from_same_sender():
    # A different, newer message from the same sender is queued — debounce it.
    inner = _Inner()
    deb = DebouncePreprocessor(inner=inner)
    event = _Event(SENDER, "msg-A")
    ctx = _Ctx([_Event(SENDER, "msg-B")])
    result = await deb.process(ctx, event, AGENT)
    assert result is None, "should debounce when a newer same-sender message is queued"
    assert not inner.called


@pytest.mark.asyncio
async def test_does_not_debounce_when_queue_has_other_sender():
    inner = _Inner()
    deb = DebouncePreprocessor(inner=inner)
    event = _Event(SENDER, "msg-A")
    ctx = _Ctx([_Event("sender-2", "msg-B")])
    result = await deb.process(ctx, event, AGENT)
    assert result is not None
    assert inner.called
