"""Pydantic argument schemas for every agent tool.

The LLM only ever passes structured arguments that are validated here — it has
no raw SQL or shell access.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ORDER_RE = re.compile(r"^NS-\d{3,6}$")
PRODUCT_RE = re.compile(r"^P\d{3,5}$")
CUSTOMER_RE = re.compile(r"^C\d{3,5}$")
TICKET_RE = re.compile(r"^SUP-\d{3,6}$")

Priority = Literal["LOW", "NORMAL", "HIGH", "URGENT"]


def _norm(value: str) -> str:
    return value.strip().upper()


def _normalise_order_id(v: str) -> str:
    v = _norm(v)
    if v.isdigit():
        v = f"NS-{v}"
    if not ORDER_RE.match(v):
        raise ValueError("order_id must look like NS-1077")
    return v


class SearchKnowledgeBaseArgs(BaseModel):
    query: str = Field(..., min_length=2, max_length=400)
    top_k: int = Field(4, ge=1, le=8)


class SearchProductsArgs(BaseModel):
    query: str = Field("", max_length=200)
    category: str | None = Field(None, max_length=40)
    max_price: int | None = Field(None, ge=0, le=10_000_000)
    min_price: int | None = Field(None, ge=0, le=10_000_000)
    required_features: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("required_features")
    @classmethod
    def _strip_features(cls, v: list[str]) -> list[str]:
        return [f.strip() for f in v if f and f.strip()][:10]


class GetProductArgs(BaseModel):
    product_id: str

    @field_validator("product_id")
    @classmethod
    def _check(cls, v: str) -> str:
        v = _norm(v)
        if not PRODUCT_RE.match(v):
            raise ValueError("product_id must look like P001")
        return v


class GetOrderArgs(BaseModel):
    order_id: str

    @field_validator("order_id")
    @classmethod
    def _check(cls, v: str) -> str:
        return _normalise_order_id(v)


class GetCustomerArgs(BaseModel):
    customer_id: str

    @field_validator("customer_id")
    @classmethod
    def _check(cls, v: str) -> str:
        v = _norm(v)
        if not CUSTOMER_RE.match(v):
            raise ValueError("customer_id must look like C001")
        return v


class CheckReturnEligibilityArgs(BaseModel):
    order_id: str

    @field_validator("order_id")
    @classmethod
    def _check(cls, v: str) -> str:
        return _normalise_order_id(v)


class CreateReturnRequestArgs(BaseModel):
    order_id: str
    reason: str = Field(..., min_length=3, max_length=500)

    @field_validator("order_id")
    @classmethod
    def _check(cls, v: str) -> str:
        return _normalise_order_id(v)


class CreateSupportTicketArgs(BaseModel):
    customer_id: str | None = None
    order_id: str | None = None
    subject: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=3, max_length=2000)
    priority: Priority = "NORMAL"

    @field_validator("customer_id")
    @classmethod
    def _cust(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        v = _norm(v)
        if not CUSTOMER_RE.match(v):
            raise ValueError("customer_id must look like C001")
        return v

    @field_validator("order_id")
    @classmethod
    def _order(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return None
        return _normalise_order_id(v)


class GetTicketArgs(BaseModel):
    ticket_id: str

    @field_validator("ticket_id")
    @classmethod
    def _check(cls, v: str) -> str:
        v = _norm(v)
        if v.isdigit():
            v = f"SUP-{v}"
        if not TICKET_RE.match(v):
            raise ValueError("ticket_id must look like SUP-8392")
        return v


class EscalateArgs(BaseModel):
    # No conversation_id: the tool reads it from the run context. Asking the model for it made
    # it invent ids like "3", which Groq rejects (400 tool_use_failed) and the turn failed.
    reason: str = Field(..., min_length=3, max_length=500)
