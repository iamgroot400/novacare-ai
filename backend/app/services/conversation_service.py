"""CRUD helpers for conversations, messages and events."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentEvent, Conversation, Message


def new_conversation_id() -> str:
    return f"conv_{uuid.uuid4().hex[:16]}"


def create_conversation(db: Session, channel: str = "chat", customer_id: str | None = None,
                        context: dict | None = None) -> Conversation:
    conv = Conversation(
        id=new_conversation_id(), channel=channel, customer_id=customer_id,
        status="active", created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    conv.context = context or {}
    db.add(conv)
    db.flush()
    return conv


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    return db.get(Conversation, conversation_id)


def add_message(db: Session, conversation_id: str, role: str, content: str,
                channel: str = "chat") -> Message:
    m = Message(conversation_id=conversation_id, role=role, content=content, channel=channel,
                created_at=datetime.now(timezone.utc))
    db.add(m)
    conv = db.get(Conversation, conversation_id)
    if conv:
        conv.updated_at = datetime.now(timezone.utc)
    db.flush()
    return m


def list_events(db: Session, conversation_id: str, after_id: int = 0) -> list[AgentEvent]:
    stmt = select(AgentEvent).where(AgentEvent.conversation_id == conversation_id)
    if after_id:
        stmt = stmt.where(AgentEvent.id > after_id)
    return list(db.scalars(stmt.order_by(AgentEvent.id)).all())
