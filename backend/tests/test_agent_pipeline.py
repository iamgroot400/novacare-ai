"""Exercise the full turn pipeline (runner -> tools -> events -> pending -> approve)
with a FAKE agent, so it runs without Ollama.

Proves the 'no fake AI actions' contract: activity events correspond to real tool
calls and DB rows.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("langgraph")

from langchain_core.messages import AIMessage  # noqa: E402


class FakeAgent:
    """Minimal stand-in for a LangGraph react agent.

    Runs the real tools (they read contextvars) then returns a final AIMessage.
    """

    def __init__(self, script):
        self._script = script

    def invoke(self, state, config=None):
        from app.agent.tools import build_tools

        tools = {t.name: t for t in build_tools()}
        last = ""
        for name, args in self._script:
            last = tools[name].invoke(args)
        return {"messages": [AIMessage(content=f"[done] {last[:120]}")]}


@pytest.mark.asyncio
async def test_order_lookup_pipeline(monkeypatch):
    from app.agent import graph, runner
    from app.database import session_scope
    from app.services import conversation_service as convo

    monkeypatch.setattr(graph, "get_agent", lambda: FakeAgent([("get_order", {"order_id": "NS-1077"})]))
    monkeypatch.setattr(runner, "get_agent", graph.get_agent)

    with session_scope() as s:
        cid = convo.create_conversation(s, channel="chat").id

    result = await runner.AgentRunner().run_turn(cid, "Where is NS-1077?")
    assert "NS-1077" in result["reply"]

    with session_scope() as s:
        events = convo.list_events(s, cid)
        tools_used = [e.tool for e in events if e.tool]
        assert "get_order" in tools_used
        assert any(e.type == "tool_finished" and "NS-1077" in e.display for e in events)


@pytest.mark.asyncio
async def test_ticket_confirmation_pipeline(monkeypatch):
    from app.agent import graph, runner
    from app.database import session_scope
    from app.models import Ticket
    from app.services import conversation_service as convo

    script = [
        ("get_order", {"order_id": "NS-1042"}),
        ("check_return_eligibility", {"order_id": "NS-1042"}),
        ("create_support_ticket", {
            "subject": "NovaPods Pro disconnecting",
            "description": "Customer tried all resets; still drops connection.",
            "customer_id": "C001", "order_id": "NS-1042", "priority": "HIGH",
        }),
    ]
    monkeypatch.setattr(graph, "get_agent", lambda: FakeAgent(script))
    monkeypatch.setattr(runner, "get_agent", graph.get_agent)

    with session_scope() as s:
        cid = convo.create_conversation(s, channel="chat").id
        tickets_before = s.query(Ticket).count()

    await runner.AgentRunner().run_turn(cid, "My NovaPods keep disconnecting, order NS-1042, open a ticket")

    # No ticket yet — confirmation required
    with session_scope() as s:
        assert s.query(Ticket).count() == tickets_before
        c = convo.get_conversation(s, cid)
        pending = c.context.get("pending_action")
        assert pending and pending["tool"] == "create_support_ticket"

    # Approve -> real row
    from app.agent.tools import execute_pending_action
    from app.events import AgentActivityEmitter

    res = execute_pending_action(pending, AgentActivityEmitter(cid))
    assert res["ok"] is True
    ticket_id = res["ticket"]["id"]
    with session_scope() as s:
        assert s.get(Ticket, ticket_id) is not None
        s.query(Ticket).filter(Ticket.id == ticket_id).delete()
