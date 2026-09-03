"""End-to-end agent smoke test. Skipped unless Ollama + the AI stack are available.

Run explicitly with:  RUN_AGENT_SMOKE=1 pytest tests/test_agent_smoke.py
"""
from __future__ import annotations

import os

import pytest

if not os.getenv("RUN_AGENT_SMOKE"):
    pytest.skip("set RUN_AGENT_SMOKE=1 to run the live agent smoke test", allow_module_level=True)

pytest.importorskip("langgraph")


@pytest.mark.asyncio
async def test_agent_order_lookup_flow():
    from app.database import session_scope
    from app.services import conversation_service as convo
    from app.agent import get_runner

    with session_scope() as db:
        conv = convo.create_conversation(db, channel="chat")
        cid = conv.id
        convo.add_message(db, cid, "user", "Where is order NS-1077?")

    result = await get_runner().run_turn(cid, "Where is order NS-1077?")
    assert "NS-1077" in result["reply"] or "transit" in result["reply"].lower()

    with session_scope() as db:
        events = convo.list_events(db, cid)
        assert any(e.tool == "get_order" for e in events)


@pytest.mark.asyncio
async def test_agent_ticket_requires_confirmation():
    from app.database import session_scope
    from app.services import conversation_service as convo
    from app.agent import get_runner

    with session_scope() as db:
        conv = convo.create_conversation(db, channel="chat")
        cid = conv.id

    await get_runner().run_turn(cid, "My NovaPods Pro from order NS-1042 keep disconnecting. I tried every reset. Please open a support ticket.")
    with session_scope() as db:
        c = convo.get_conversation(db, cid)
        # a ticket must NOT exist yet; a pending action should be recorded
        assert c.context.get("pending_action", {}).get("tool") == "create_support_ticket"
