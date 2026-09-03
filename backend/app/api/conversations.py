"""Conversation lifecycle: create, fetch, message, approve/reject, live events."""
from __future__ import annotations

import asyncio
import contextlib

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.events import AgentActivityEmitter, event_bus
from app.schemas.api import (
    ApproveRequest,
    ConversationCreate,
    ConversationOut,
    EventOut,
    MessageIn,
    MessageOut,
    PendingActionOut,
    RejectRequest,
)
from app.services import conversation_service as convo

router = APIRouter()


def _serialize(conv) -> ConversationOut:
    ctx = conv.context
    pending = ctx.get("pending_action")
    return ConversationOut(
        id=conv.id,
        channel=conv.channel,
        status=conv.status,
        customer_id=conv.customer_id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        context=ctx,
        messages=[MessageOut.model_validate(m) for m in conv.messages],
        events=[EventOut(id=e.id, type=e.type, tool=e.tool, display=e.display,
                         status=e.status, meta=e.meta, created_at=e.created_at)
                for e in conv.events],
        pending_action=PendingActionOut(**pending) if pending else None,
    )


@router.post("", response_model=ConversationOut)
@router.post("/", response_model=ConversationOut)
def create_conversation(body: ConversationCreate, db: Session = Depends(get_db)):
    conv = convo.create_conversation(db, channel=body.channel, customer_id=body.customer_id,
                                     context=body.context)
    db.commit()
    db.refresh(conv)
    return _serialize(conv)


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = convo.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return _serialize(conv)


@router.get("/{conversation_id}/events", response_model=list[EventOut])
def get_events(conversation_id: str, after_id: int = 0, db: Session = Depends(get_db)):
    if not convo.get_conversation(db, conversation_id):
        raise HTTPException(404, "Conversation not found")
    return [
        EventOut(id=e.id, type=e.type, tool=e.tool, display=e.display, status=e.status,
                 meta=e.meta, created_at=e.created_at)
        for e in convo.list_events(db, conversation_id, after_id=after_id)
    ]


async def _run_turn(conversation_id: str, content: str, channel: str) -> dict:
    with next(get_db()) as db:  # type: ignore
        conv = convo.get_conversation(db, conversation_id)
        if not conv:
            raise HTTPException(404, "Conversation not found")
        if conv.status in {"escalated", "resolved"}:
            conv.status = "active"
        convo.add_message(db, conversation_id, "user", content, channel=channel)
        db.commit()

    from app.agent import get_runner

    result = await get_runner().run_turn(conversation_id, content)

    with next(get_db()) as db:  # type: ignore
        conv = convo.get_conversation(db, conversation_id)
        return {
            "reply": result["reply"],
            "pending_action": result.get("pending_action"),
            "conversation": _serialize(conv).model_dump(mode="json"),
        }


@router.post("/{conversation_id}/message")
async def post_message(conversation_id: str, body: MessageIn):
    content = body.content.strip()
    if not content:
        raise HTTPException(400, "Empty message")
    if len(content) > settings.max_message_chars:
        raise HTTPException(413, "Message too long")
    return await _run_turn(conversation_id, content, body.channel)


@router.post("/{conversation_id}/approve")
async def approve_action(conversation_id: str, body: ApproveRequest, db: Session = Depends(get_db)):
    conv = convo.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    ctx = conv.context
    pending = ctx.get("pending_action")
    if not pending:
        raise HTTPException(409, "No pending action to approve")

    loop = asyncio.get_running_loop()
    emitter = AgentActivityEmitter(conversation_id, loop=loop)
    emitter.confirmation_resolved(f"Customer approved: {pending['summary']}", approved=True)

    from app.agent.tools import execute_pending_action

    result = await asyncio.to_thread(execute_pending_action, pending, emitter)

    if result.get("ok"):
        if "ticket" in result:
            obj = result["ticket"]
            msg = f"Done — I've created support ticket **{obj['id']}** (status {obj['status']}). A specialist will review it."
        elif "return" in result:
            obj = result["return"]
            msg = (f"Done — return **{obj['id']}** has been created with status {obj['status']}. "
                   "No money has moved; this is a demo RMA record. You'll get updates as it progresses.")
        else:
            msg = "Done — the action was completed."
    else:
        msg = f"I couldn't complete that: {result.get('error', 'unknown error')}."

    with next(get_db()) as db2:  # type: ignore
        convo.add_message(db2, conversation_id, "assistant", msg, channel=conv.channel)
        c2 = convo.get_conversation(db2, conversation_id)
        cc = c2.context
        cc.pop("pending_action", None)
        if result.get("ok"):
            c2.status = "resolved"
        c2.context = cc
        db2.commit()
        final = _serialize(convo.get_conversation(db2, conversation_id))

    await event_bus.publish(conversation_id, {"kind": "assistant", "content": msg})
    return {"ok": result.get("ok", False), "result": result, "reply": msg,
            "conversation": final.model_dump(mode="json")}


@router.post("/{conversation_id}/reject")
async def reject_action(conversation_id: str, body: RejectRequest, db: Session = Depends(get_db)):
    conv = convo.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    ctx = conv.context
    pending = ctx.get("pending_action")
    if not pending:
        raise HTTPException(409, "No pending action to reject")

    emitter = AgentActivityEmitter(conversation_id, loop=asyncio.get_running_loop())
    emitter.confirmation_resolved(f"Customer declined: {pending['summary']}", approved=False)

    msg = "No problem — I won't do that. Let me know if there's anything else I can help with."
    ctx.pop("pending_action", None)
    conv.context = ctx
    convo.add_message(db, conversation_id, "assistant", msg, channel=conv.channel)
    db.commit()
    await event_bus.publish(conversation_id, {"kind": "assistant", "content": msg})
    final = _serialize(convo.get_conversation(db, conversation_id))
    return {"ok": True, "reply": msg, "conversation": final.model_dump(mode="json")}


@router.websocket("/{conversation_id}/ws")
async def conversation_ws(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    with next(get_db()) as db:  # type: ignore
        if not convo.get_conversation(db, conversation_id):
            await websocket.send_json({"kind": "error", "message": "Conversation not found"})
            await websocket.close()
            return

    queue = await event_bus.subscribe(conversation_id)
    stop = asyncio.Event()

    async def pump_events() -> None:
        try:
            while not stop.is_set():
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                await websocket.send_json(payload)
        except Exception:
            stop.set()

    pump = asyncio.create_task(pump_events())
    try:
        while True:
            data = await websocket.receive_json()
            kind = data.get("kind") or data.get("type")
            if kind in {"message", "user_message"}:
                content = (data.get("content") or "").strip()[: settings.max_message_chars]
                if not content:
                    continue
                channel = data.get("channel", "chat")
                await websocket.send_json({"kind": "ack", "content": content})
                try:
                    result = await _run_turn(conversation_id, content, channel)
                    await websocket.send_json({
                        "kind": "assistant",
                        "content": result["reply"],
                        "pending_action": result.get("pending_action"),
                    })
                except Exception as exc:  # noqa: BLE001
                    await websocket.send_json({"kind": "error", "message": str(exc)})
            elif kind == "ping":
                await websocket.send_json({"kind": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        stop.set()
        pump.cancel()
        with contextlib.suppress(Exception):
            await pump
        await event_bus.unsubscribe(conversation_id, queue)
