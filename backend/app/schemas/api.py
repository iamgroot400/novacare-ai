"""Request/response models for the public REST + WS API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.config import settings


class ProductOut(BaseModel):
    id: str
    name: str
    category: str
    price_npr: int
    stock: int
    in_stock: bool
    warranty_months: int
    rating: float
    features: list[str]
    description: str
    warranty_note: str = ""

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    customer_id: str
    product_id: str
    product_name: str | None = None
    quantity: int
    total_npr: int
    status: str
    ordered_at: str | None = None
    delivered_at: str | None = None
    shipped_at: str | None = None
    estimated_delivery: str | None = None
    current_location: str | None = None
    delay_reason: str | None = None
    payment_method: str
    is_demo: bool = False

    model_config = {"from_attributes": True}


class TicketOut(BaseModel):
    id: str
    customer_id: str | None = None
    order_id: str | None = None
    subject: str
    description: str
    priority: str
    status: str
    created_at: datetime
    resolution: str = ""

    model_config = {"from_attributes": True}


class ReturnOut(BaseModel):
    id: str
    order_id: str
    customer_id: str
    reason: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    channel: Literal["chat", "voice"] = "chat"
    customer_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    channel: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: int
    type: str
    tool: str | None = None
    display: str
    status: str
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class PendingActionOut(BaseModel):
    tool: str
    display: str
    args: dict[str, Any]
    summary: str


class ConversationOut(BaseModel):
    id: str
    channel: str
    status: str
    customer_id: str | None = None
    created_at: datetime
    updated_at: datetime
    context: dict[str, Any] = Field(default_factory=dict)
    messages: list[MessageOut] = Field(default_factory=list)
    events: list[EventOut] = Field(default_factory=list)
    pending_action: PendingActionOut | None = None


class MessageIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=settings.max_message_chars)
    channel: Literal["chat", "voice"] = "chat"


class ApproveRequest(BaseModel):
    note: str | None = Field(None, max_length=500)


class RejectRequest(BaseModel):
    note: str | None = Field(None, max_length=500)


class ConfigOut(BaseModel):
    demo_date: str
    ice_servers: list[dict[str, Any]]
    voice_url: str
    model: str
