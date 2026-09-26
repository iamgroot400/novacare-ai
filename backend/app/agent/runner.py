"""Drives one agent turn for a conversation."""
from __future__ import annotations

import asyncio
import time
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.context import RunContext, run_context
from app.agent.graph import get_agent, strip_reasoning
from app.database.session import session_scope
from app.events import AgentActivityEmitter
from app.models import Conversation, Message

MAX_HISTORY_MESSAGES = 10  # resent on every LLM call; tools still see the last order via conv.context

_INTENT_HINTS = [
    (("where", "track", "status", "arriv", "deliver", "delay", "transit"), "Detected an order-tracking request"),
    (("return", "refund", "money back", "send back"), "Detected a return / refund request"),
    (("recommend", "suggest", "looking for", "which", "below rs", "under rs", "budget"),
     "Detected a product recommendation request"),
    (("disconnect", "not working", "broken", "issue", "problem", "won't", "cant", "can't", "fix", "trouble"),
     "Detected a troubleshooting request"),
    (("human", "agent", "person", "representative", "escalat"), "Detected a request to speak with a human"),
    (("warranty", "guarantee", "covered"), "Detected a warranty question"),
]


def _guess_intent(text: str) -> str | None:
    low = text.lower()
    for keys, label in _INTENT_HINTS:
        if any(k in low for k in keys):
            return label
    return None


class AgentRunner:
    async def run_turn(self, conversation_id: str, user_text: str) -> dict:
        loop = asyncio.get_running_loop()
        emitter = AgentActivityEmitter(conversation_id, loop=loop)

        with session_scope() as db:
            conv = db.get(Conversation, conversation_id)
            if conv is None:
                raise ValueError("conversation not found")
            history = list(conv.messages)[-MAX_HISTORY_MESSAGES:]
            ctx_data = conv.context
            customer_id = conv.customer_id
            lc_messages: list = []
            for m in history:
                if m.role == "user":
                    lc_messages.append(HumanMessage(content=m.content))
                elif m.role == "assistant":
                    lc_messages.append(AIMessage(content=m.content))
            lc_messages.append(HumanMessage(content=user_text))

        intent = _guess_intent(user_text)
        if intent:
            emitter.intent(intent)

        rc = RunContext(
            conversation_id=conversation_id,
            emitter=emitter,
            customer_id=customer_id,
            order_context=ctx_data.get("order_id"),
        )

        started = time.perf_counter()
        agent = get_agent()

        def _invoke() -> dict:
            with run_context(rc):
                return agent.invoke(
                    {"messages": lc_messages},
                    config={"recursion_limit": 12},
                )

        try:
            result = await asyncio.to_thread(_invoke)
        except Exception as exc:  # noqa: BLE001
            emitter.tool_error("agent", f"Agent error: {type(exc).__name__}")
            reply = (
                "Sorry — I ran into a problem processing that. Please try again, or ask "
                "for a human specialist and I'll escalate."
            )
            self._persist_assistant(conversation_id, reply)
            return {"reply": reply, "pending_action": None, "error": str(exc)}

        elapsed = round(time.perf_counter() - started, 2)
        messages = result.get("messages", [])
        reply = ""
        for m in reversed(messages):
            if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
                reply = strip_reasoning(_as_text(m.content))
                if reply:
                    break
        if not reply:
            reply = "I'm here to help — could you rephrase that?"

        emitter.status(f"Response ready ({elapsed}s)", meta={"elapsed_seconds": elapsed})

        self._persist_assistant(conversation_id, reply, rc)
        return {
            "reply": reply,
            "pending_action": rc.pending_action,
            "elapsed_seconds": elapsed,
        }

    def _persist_assistant(self, conversation_id: str, reply: str, rc: RunContext | None = None) -> None:
        with session_scope() as db:
            conv = db.get(Conversation, conversation_id)
            if conv is None:
                return
            db.add(Message(conversation_id=conversation_id, role="assistant",
                           content=reply, channel=conv.channel))
            c = conv.context
            if rc:
                if rc.order_context:
                    c["order_id"] = rc.order_context
                if rc.customer_id:
                    conv.customer_id = rc.customer_id
                    c["customer_id"] = rc.customer_id
                if rc.pending_action:
                    c["pending_action"] = rc.pending_action
                else:
                    c.pop("pending_action", None)
            conv.context = c


def _as_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


@lru_cache
def get_runner() -> AgentRunner:
    return AgentRunner()
