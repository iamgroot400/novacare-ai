"""Per-run context shared with tools via contextvars.

A single agent turn runs inside `run_context(...)`. Tools read the current
emitter / conversation id / identified customer, and register a pending write
action instead of performing it directly.
"""
from __future__ import annotations

import contextlib
import contextvars
from dataclasses import dataclass, field
from typing import Any

from app.events import AgentActivityEmitter


@dataclass
class RunContext:
    conversation_id: str
    emitter: AgentActivityEmitter
    customer_id: str | None = None
    order_context: str | None = None
    pending_action: dict[str, Any] | None = None
    tool_calls: list[str] = field(default_factory=list)


_current: contextvars.ContextVar[RunContext | None] = contextvars.ContextVar(
    "novacare_run_context", default=None
)


def current() -> RunContext:
    ctx = _current.get()
    if ctx is None:
        raise RuntimeError("No active agent run context")
    return ctx


@contextlib.contextmanager
def run_context(ctx: RunContext):
    token = _current.set(ctx)
    try:
        yield ctx
    finally:
        _current.reset(token)
