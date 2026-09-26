"""Business logic over the store database.

Tools call these functions — never raw SQL from the model. All functions take an
explicit Session so they are easy to test and transaction-safe.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Customer, Order, Product, Return, Ticket

RETURNABLE_WINDOW_DAYS = 14
NON_RETURNABLE_STATUSES = {"processing", "shipped", "in_transit", "delayed", "cancelled"}


# ─── serialisers ────────────────────────────────────────────────────────
def product_to_dict(p: Product) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "category": p.category,
        "price_npr": p.price_npr,
        "price_display": f"NPR {p.price_npr:,}",
        "stock": p.stock,
        "in_stock": p.in_stock,
        "warranty_months": p.warranty_months,
        "rating": p.rating,
        "features": p.features,
        "description": p.description,
        "warranty_note": p.warranty_note,
    }


def order_to_dict(o: Order) -> dict[str, Any]:
    return {
        "id": o.id,
        "customer_id": o.customer_id,
        "product_id": o.product_id,
        "product_name": o.product.name if o.product else None,
        "quantity": o.quantity,
        "total_npr": o.total_npr,
        "total_display": f"NPR {o.total_npr:,}",
        "status": o.status,
        "ordered_at": o.ordered_at,
        "shipped_at": o.shipped_at,
        "delivered_at": o.delivered_at,
        "estimated_delivery": o.estimated_delivery,
        "current_location": o.current_location,
        "delay_reason": o.delay_reason,
        "payment_method": o.payment_method,
        "is_demo": bool(o.is_demo),
    }


def ticket_to_dict(t: Ticket) -> dict[str, Any]:
    return {
        "id": t.id,
        "customer_id": t.customer_id,
        "order_id": t.order_id,
        "subject": t.subject,
        "description": t.description,
        "priority": t.priority,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "resolution": t.resolution,
    }


def return_to_dict(r: Return) -> dict[str, Any]:
    return {
        "id": r.id,
        "order_id": r.order_id,
        "customer_id": r.customer_id,
        "reason": r.reason,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ─── reads ─────────────────────────────────────────────────────────────
def get_product(db: Session, product_id: str) -> dict | None:
    p = db.get(Product, product_id.upper())
    return product_to_dict(p) if p else None


def get_order(db: Session, order_id: str) -> dict | None:
    o = db.get(Order, order_id.upper())
    return order_to_dict(o) if o else None


def get_customer(db: Session, customer_id: str) -> dict | None:
    c = db.get(Customer, customer_id.upper())
    if not c:
        return None
    orders = db.scalars(select(Order).where(Order.customer_id == c.id)).all()
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "city": c.city,
        "order_ids": [o.id for o in orders],
    }


def get_ticket(db: Session, ticket_id: str) -> dict | None:
    t = db.get(Ticket, ticket_id.upper())
    return ticket_to_dict(t) if t else None


# How customers phrase a feature -> the label the catalogue uses. Without this, a
# required feature of "noise cancelling" demotes every ANC product out of the results.
_FEATURE_ALIASES = {"anc": ("noise cancel", "noise-cancel", "active noise")}


def _canon_feature(f: str) -> str:
    return next((canon for canon, aliases in _FEATURE_ALIASES.items() if any(a in f for a in aliases)), f)


def search_products(
    db: Session,
    query: str = "",
    category: str | None = None,
    max_price: int | None = None,
    min_price: int | None = None,
    required_features: list[str] | None = None,
    limit: int = 6,
) -> list[dict]:
    stmt = select(Product)
    # The model guesses categories ("headphones") that aren't catalogue categories ("Audio");
    # an exact filter on those silently returns nothing, so treat unknown ones as search words.
    known = {c.lower() for c in db.scalars(select(Product.category).distinct())}
    if category and category.strip().lower() not in known:
        query, category = f"{query} {category}".strip(), None
    if category:
        stmt = stmt.where(func.lower(Product.category) == category.strip().lower())
    if max_price is not None:
        stmt = stmt.where(Product.price_npr <= max_price)
    if min_price is not None:
        stmt = stmt.where(Product.price_npr >= min_price)

    rows = list(db.scalars(stmt).all())
    q = (query or "").strip().lower()
    feats = [_canon_feature(f.strip().lower()) for f in (required_features or []) if f.strip()]

    synonyms = {
        "headphones": ["earbuds", "pods", "audio", "anc", "headphone"],
        "earphones": ["earbuds", "pods"],
        "earbuds": ["pods", "buds"],
        "watch": ["watch", "wearable", "band"],
        "smartwatch": ["watch", "wearable"],
        "keyboard": ["keys", "keyboard", "mechanical"],
        "mouse": ["mouse"],
        "charger": ["charge", "charging", "power", "gan"],
        "speaker": ["sound", "speaker", "soundbar"],
        "webcam": ["cam", "camera", "webcam"],
        "gaming": ["mechanical", "keys", "low-latency", "rgb", "hot-swappable"],
        "mic": ["mic", "microphone"],
        "powerbank": ["power", "20k", "mah"],
    }

    def score(p: Product) -> float:
        hay = " ".join(
            [p.name.lower(), p.category.lower(), p.description.lower(), " ".join(p.features).lower()]
        )
        s = 0.0
        if not q:
            s += 0.5
        else:
            for token in q.split():
                if token in hay:
                    s += 2.0
                for base, syns in synonyms.items():
                    if token == base or token in syns:
                        if base in hay or any(x in hay for x in syns):
                            s += 1.5
        pf = " ".join(p.features).lower()
        for f in feats:
            if re.search(rf"\b{re.escape(f)}\b", pf):
                s += 3.0
            else:
                s -= 5.0  # required feature missing -> strongly demote
        s += p.rating / 10.0
        return s

    scored = sorted(((score(p), p) for p in rows), key=lambda t: t[0], reverse=True)
    result = [product_to_dict(p) for sc, p in scored if sc > -1.0][:limit]
    return result


# ─── return eligibility ────────────────────────────────────────────────
def _parse_iso(d: str | None) -> date | None:
    if not d:
        return None
    try:
        return date.fromisoformat(d)
    except ValueError:
        return None


def check_return_eligibility(db: Session, order_id: str) -> dict[str, Any]:
    o = db.get(Order, order_id.upper())
    if not o:
        return {"order_id": order_id.upper(), "found": False, "eligible": False,
                "reason": "Order not found in the demo system."}

    today = settings.demo_date_obj
    base = {
        "order_id": o.id,
        "found": True,
        "status": o.status,
        "product_id": o.product_id,
        "product_name": o.product.name if o.product else None,
        "delivered_at": o.delivered_at,
        "demo_date": today.isoformat(),
        "window_days": RETURNABLE_WINDOW_DAYS,
    }

    if o.status in NON_RETURNABLE_STATUSES:
        return {**base, "eligible": False,
                "reason": f"Order status is '{o.status}'. Only delivered orders can be returned."}

    if o.status == "return_requested":
        return {**base, "eligible": False,
                "reason": "A return has already been requested for this order."}

    delivered = _parse_iso(o.delivered_at)
    if o.status != "delivered" or delivered is None:
        return {**base, "eligible": False,
                "reason": "This order has not been delivered yet, so it cannot be returned."}

    days_since = (today - delivered).days
    base["days_since_delivery"] = days_since
    if days_since <= RETURNABLE_WINDOW_DAYS:
        return {**base, "eligible": True,
                "reason": f"Delivered {days_since} day(s) ago, within the {RETURNABLE_WINDOW_DAYS}-day window."}

    warranty_months = o.product.warranty_months if o.product else 12
    return {
        **base,
        "eligible": False,
        "reason": (
            f"Delivered {days_since} day(s) ago, which is outside the "
            f"{RETURNABLE_WINDOW_DAYS}-day return window."
        ),
        "warranty_available": True,
        "warranty_months": warranty_months,
        "warranty_hint": "Outside the return window, but a warranty support ticket may still be possible.",
    }


# ─── id generation ─────────────────────────────────────────────────────
def _next_id(db: Session, model, prefix: str, start: int) -> str:
    rows = db.scalars(select(model.id)).all()
    nums = []
    for rid in rows:
        try:
            nums.append(int(str(rid).split("-")[-1]))
        except ValueError:
            continue
    nxt = (max(nums) + 1) if nums else start
    return f"{prefix}-{nxt}"


# ─── writes ────────────────────────────────────────────────────────────
def create_return_request(
    db: Session, order_id: str, reason: str, conversation_id: str | None = None
) -> dict[str, Any]:
    order_id = order_id.upper()
    elig = check_return_eligibility(db, order_id)
    if not elig["found"]:
        return {"ok": False, "error": "Order not found."}
    if not elig["eligible"]:
        return {"ok": False, "error": elig["reason"], "eligibility": elig}

    o = db.get(Order, order_id)
    existing = db.scalar(select(Return).where(Return.order_id == order_id))
    if existing:
        return {"ok": False, "error": f"Return {existing.id} already exists for this order.",
                "return": return_to_dict(existing)}

    ret_id = _next_id(db, Return, "RET", 4100)
    r = Return(
        id=ret_id, order_id=order_id, customer_id=o.customer_id,
        reason=reason.strip(), status="REQUESTED", conversation_id=conversation_id,
        created_at=datetime.now(timezone.utc),
    )
    o.status = "return_requested"
    db.add(r)
    db.flush()
    return {"ok": True, "return": return_to_dict(r),
            "message": f"Return {ret_id} created with status REQUESTED. No money has been moved."}


def create_demo_order(db: Session, product_id: str, customer_id: str = "C001",
                       quantity: int = 1) -> dict[str, Any]:
    product_id = product_id.upper()
    p = db.get(Product, product_id)
    if not p:
        return {"ok": False, "error": f"Product {product_id} not found."}
    if not db.get(Customer, customer_id.upper()):
        customer_id = "C001"
    quantity = max(1, min(quantity, 5))
    order_id = _next_id(db, Order, "NS", 2000)
    today = settings.demo_date_obj.isoformat()
    o = Order(
        id=order_id, customer_id=customer_id.upper(), product_id=product_id,
        quantity=quantity, total_npr=p.price_npr * quantity, status="processing",
        ordered_at=today, estimated_delivery=today, payment_method="Demo (no charge)",
        is_demo=1,
    )
    db.add(o)
    db.flush()
    return {"ok": True, "order": order_to_dict(o),
            "message": f"Demo order {order_id} created (synthetic, no payment)."}


def create_support_ticket(
    db: Session,
    subject: str,
    description: str,
    customer_id: str | None = None,
    order_id: str | None = None,
    priority: str = "NORMAL",
    conversation_id: str | None = None,
) -> dict[str, Any]:
    if customer_id:
        customer_id = customer_id.upper()
        if not db.get(Customer, customer_id):
            return {"ok": False, "error": f"Customer {customer_id} not found."}
    if order_id:
        order_id = order_id.upper()
        if not db.get(Order, order_id):
            return {"ok": False, "error": f"Order {order_id} not found."}

    tid = _next_id(db, Ticket, "SUP", 8400)
    t = Ticket(
        id=tid, customer_id=customer_id, order_id=order_id,
        subject=subject.strip()[:200], description=description.strip()[:2000],
        priority=priority.upper(), status="OPEN", conversation_id=conversation_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(t)
    db.flush()
    return {"ok": True, "ticket": ticket_to_dict(t),
            "message": f"Support ticket {tid} created with status OPEN."}


# ─── dashboard analytics ───────────────────────────────────────────────
def dashboard_metrics(db: Session) -> dict[str, Any]:
    from app.models import AgentEvent, Conversation, Message

    total_conv = db.scalar(select(func.count()).select_from(Conversation)) or 0
    voice_conv = db.scalar(
        select(func.count()).select_from(Conversation).where(Conversation.channel == "voice")
    ) or 0
    escalations = db.scalar(
        select(func.count()).select_from(AgentEvent).where(AgentEvent.type == "escalation")
    ) or 0
    tickets_created = db.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.conversation_id.is_not(None))
    ) or 0
    returns_created = db.scalar(
        select(func.count()).select_from(Return).where(Return.conversation_id.is_not(None))
    ) or 0
    resolved = db.scalar(
        select(func.count()).select_from(Conversation).where(Conversation.status == "resolved")
    ) or 0

    # crude avg response time from message pair timestamps
    msgs = db.scalars(select(Message).order_by(Message.conversation_id, Message.created_at)).all()
    deltas: list[float] = []
    last_user: dict[str, datetime] = {}
    for m in msgs:
        if m.role == "user":
            last_user[m.conversation_id] = m.created_at
        elif m.role == "assistant" and m.conversation_id in last_user:
            dt = (m.created_at - last_user.pop(m.conversation_id)).total_seconds()
            if 0 < dt < 300:
                deltas.append(dt)
    avg_response = round(sum(deltas) / len(deltas), 1) if deltas else None

    recent = db.scalars(
        select(Conversation).order_by(Conversation.updated_at.desc()).limit(8)
    ).all()
    recent_activity = []
    for c in recent:
        ev_types = {e.type for e in c.events}
        outcome = "Resolved" if c.status == "resolved" else c.status.capitalize()
        if "db_write" in ev_types or any(e.tool == "create_support_ticket" for e in c.events):
            outcome = "Ticket / return created"
        if "escalation" in ev_types:
            outcome = "Escalated to human"
        ctx = c.context
        recent_activity.append({
            "conversation_id": c.id,
            "order_id": ctx.get("order_id"),
            "channel": c.channel,
            "summary": (c.messages[0].content[:60] + "…") if c.messages else "New conversation",
            "outcome": outcome,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    by_status = dict(
        db.execute(select(Ticket.status, func.count()).group_by(Ticket.status)).all()
    )
    returns_by_status = dict(
        db.execute(select(Return.status, func.count()).group_by(Return.status)).all()
    )
    orders_by_status = dict(
        db.execute(select(Order.status, func.count()).group_by(Order.status)).all()
    )

    return {
        "label": "Demo Analytics",
        "disclaimer": "NovaStore is fictional. These numbers are derived from the demo database only.",
        "totals": {
            "conversations": total_conv,
            "ai_resolved": resolved,
            "escalations": escalations,
            "tickets_created_by_ai": tickets_created,
            "returns_created_by_ai": returns_created,
            "voice_sessions": voice_conv,
            "avg_response_seconds": avg_response,
        },
        "tickets_by_status": by_status,
        "returns_by_status": returns_by_status,
        "orders_by_status": orders_by_status,
        "recent_activity": recent_activity,
    }
