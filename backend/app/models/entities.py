"""ORM entities for NovaCare AI.

All monetary values are integer NPR (paisa-free, matching the seed spec).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JSONList(Text):
    """Store a python list as a JSON string in a TEXT column."""


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    price_npr: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    _features: Mapped[str] = mapped_column("features", Text, nullable=False, default="[]")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    warranty_note: Mapped[str] = mapped_column(Text, nullable=False, default="")

    orders: Mapped[list["Order"]] = relationship(back_populates="product")

    @property
    def features(self) -> list[str]:
        try:
            return json.loads(self._features)
        except (ValueError, TypeError):
            return []

    @features.setter
    def features(self, value: list[str]) -> None:
        self._features = json.dumps(list(value))

    @property
    def in_stock(self) -> bool:
        return self.stock > 0


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(60), nullable=False, default="")

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_npr: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    ordered_at: Mapped[str | None] = mapped_column(String(10), nullable=True)
    delivered_at: Mapped[str | None] = mapped_column(String(10), nullable=True)
    shipped_at: Mapped[str | None] = mapped_column(String(10), nullable=True)
    estimated_delivery: Mapped[str | None] = mapped_column(String(10), nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    delay_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    is_demo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    product: Mapped["Product"] = relationship(back_populates="orders")
    returns: Mapped[list["Return"]] = relationship(back_populates="order")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), index=True, nullable=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id"), index=True, nullable=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(12), nullable=False, default="NORMAL")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="OPEN", index=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    resolution: Mapped[str] = mapped_column(Text, nullable=False, default="")
    conversation_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    customer: Mapped["Customer"] = relationship(back_populates="tickets")


class Return(Base):
    __tablename__ = "returns"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="REQUESTED", index=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    conversation_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    order: Mapped["Order"] = relationship(back_populates="returns")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(12), nullable=False, default="chat")  # chat | voice
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)
    context_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan"
    )
    events: Mapped[list["AgentEvent"]] = relationship(
        back_populates="conversation", order_by="AgentEvent.created_at", cascade="all, delete-orphan"
    )

    @property
    def context(self) -> dict:
        try:
            return json.loads(self.context_json)
        except (ValueError, TypeError):
            return {}

    @context.setter
    def context(self, value: dict) -> None:
        self.context_json = json.dumps(value)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(12), nullable=False)  # user | assistant | system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(12), nullable=False, default="chat")
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    tool: Mapped[str | None] = mapped_column(String(48), nullable=True)
    display: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    meta_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="events")

    @property
    def meta(self) -> dict:
        try:
            return json.loads(self.meta_json)
        except (ValueError, TypeError):
            return {}

    @meta.setter
    def meta(self, value: dict) -> None:
        self.meta_json = json.dumps(value, default=str)


Index("ix_orders_customer_status", Order.customer_id, Order.status)
Index("ix_messages_conv_created", Message.conversation_id, Message.created_at)
Index("ix_events_conv_created", AgentEvent.conversation_id, AgentEvent.created_at)
