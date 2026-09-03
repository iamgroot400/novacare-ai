"""In-process event bus for observable agent activity.

Events are:
  * broadcast to any live WebSocket subscribers for a conversation, and
  * persisted to the agent_events table.

These are SAFE, OBSERVABLE events only — never chain-of-thought, never raw model
output. Each event has a stable machine `type`, an optional `tool`, and a
human-readable `display` string.
"""
from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timezone
from typing import Any

from app.database.session import session_scope
from app.models import AgentEvent

VALID_TYPES = {
    "intent_detected",
    "tool_started",
    "tool_finished",
    "tool_error",
    "kb_search",
    "db_read",
    "db_write",
    "confirmation_requested",
    "confirmation_resolved",
    "escalation",
    "message",
    "status",
}


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, conversation_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers.setdefault(conversation_id, set()).add(q)
        return q

    async def unsubscribe(self, conversation_id: str, q: asyncio.Queue) -> None:
        async with self._lock:
            subs = self._subscribers.get(conversation_id)
            if subs and q in subs:
                subs.discard(q)
                if not subs:
                    self._subscribers.pop(conversation_id, None)

    async def publish(self, conversation_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            subs = list(self._subscribers.get(conversation_id, set()))
        for q in subs:
            with contextlib.suppress(asyncio.QueueFull):
                q.put_nowait(payload)


event_bus = EventBus()


def _persist_event(
    conversation_id: str,
    type_: str,
    display: str,
    tool: str | None,
    status: str,
    meta: dict[str, Any] | None,
) -> dict[str, Any]:
    with session_scope() as db:
        ev = AgentEvent(
            conversation_id=conversation_id,
            type=type_,
            tool=tool,
            display=display[:300],
            status=status,
        )
        ev.meta = meta or {}
        db.add(ev)
        db.flush()
        return {
            "id": ev.id,
            "type": ev.type,
            "tool": ev.tool,
            "display": ev.display,
            "status": ev.status,
            "meta": ev.meta,
            "created_at": (ev.created_at or datetime.now(timezone.utc)).isoformat(),
        }


class AgentActivityEmitter:
    """Bound to a single conversation. Passed into tools and the agent graph."""

    def __init__(self, conversation_id: str, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self.conversation_id = conversation_id
        self._loop = loop

    def _dispatch(self, payload: dict[str, Any]) -> None:
        payload = {"kind": "event", **payload}
        try:
            loop = self._loop or asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(
                event_bus.publish(self.conversation_id, payload), loop
            )
        # else: no live subscribers reachable; DB persistence already happened.

    def emit(
        self,
        type_: str,
        display: str,
        *,
        tool: str | None = None,
        status: str = "info",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if type_ not in VALID_TYPES:
            type_ = "status"
        record = _persist_event(self.conversation_id, type_, display, tool, status, meta)
        self._dispatch(record)
        return record

    # convenience helpers ------------------------------------------------
    def intent(self, display: str, meta: dict | None = None) -> None:
        self.emit("intent_detected", display, status="info", meta=meta)

    def tool_started(self, tool: str, display: str, meta: dict | None = None) -> None:
        self.emit("tool_started", display, tool=tool, status="running", meta=meta)

    def tool_finished(self, tool: str, display: str, meta: dict | None = None) -> None:
        self.emit("tool_finished", display, tool=tool, status="success", meta=meta)

    def tool_error(self, tool: str, display: str, meta: dict | None = None) -> None:
        self.emit("tool_error", display, tool=tool, status="error", meta=meta)

    def confirmation_requested(self, display: str, meta: dict | None = None) -> None:
        self.emit("confirmation_requested", display, status="waiting", meta=meta)

    def confirmation_resolved(self, display: str, approved: bool) -> None:
        self.emit(
            "confirmation_resolved",
            display,
            status="success" if approved else "cancelled",
            meta={"approved": approved},
        )

    def escalation(self, display: str, meta: dict | None = None) -> None:
        self.emit("escalation", display, status="warning", meta=meta)

    def status(self, display: str, meta: dict | None = None) -> None:
        self.emit("status", display, status="info", meta=meta)
