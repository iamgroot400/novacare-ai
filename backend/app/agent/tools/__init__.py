"""LangGraph / LangChain tools for NovaCare.

Every tool:
  * validates its arguments with a Pydantic schema (schemas/tools.py),
  * emits observable agent-activity events,
  * touches the database only through app.services.store_service.

READ tools run automatically. WRITE tools (create_return_request,
create_support_ticket) DO NOT write — they register a pending action that the
customer must approve through POST /api/conversations/{id}/approve.
"""
from __future__ import annotations

import json

from langchain_core.tools import StructuredTool

from app.agent.context import current
from app.database.session import session_scope
from app.rag import get_rag
from app.schemas.tools import (
    CheckReturnEligibilityArgs,
    CreateReturnRequestArgs,
    CreateSupportTicketArgs,
    EscalateArgs,
    GetCustomerArgs,
    GetOrderArgs,
    GetProductArgs,
    GetTicketArgs,
    SearchKnowledgeBaseArgs,
    SearchProductsArgs,
)
from app.services import store_service as svc


def _dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


# ─── READ tools ────────────────────────────────────────────────────────
def _search_knowledge_base(query: str, top_k: int = 4) -> str:
    ctx = current()
    ctx.emitter.tool_started("search_knowledge_base", f"Searching the knowledge base for “{query}”")
    rag = get_rag()
    product_id = None
    if ctx.order_context:
        with session_scope() as db:
            o = svc.get_order(db, ctx.order_context)
            product_id = o["product_id"] if o else None
    chunks = rag.search(query, top_k=top_k)
    if not chunks and product_id:
        chunks = rag.search(query, top_k=top_k, product_id=product_id)
    ctx.emitter.tool_finished(
        "search_knowledge_base",
        f"Found {len(chunks)} knowledge passage(s)"
        + (f" (top: {chunks[0].source})" if chunks else ""),
        meta={"sources": [c.source for c in chunks]},
    )
    return _dump({
        "query": query,
        "results": [
            {"source": c.source, "section": c.section, "document_type": c.document_type,
             "score": c.score, "text": c.text}
            for c in chunks
        ],
    })


def _search_products(query: str = "", category: str | None = None, max_price: int | None = None,
                     min_price: int | None = None, required_features: list[str] | None = None) -> str:
    ctx = current()
    desc = "Searching the product catalogue"
    if query:
        desc += f" for “{query}”"
    if max_price:
        desc += f" under NPR {max_price:,}"
    ctx.emitter.tool_started("search_products", desc)
    with session_scope() as db:
        results = svc.search_products(
            db, query=query or "", category=category, max_price=max_price,
            min_price=min_price, required_features=required_features or [],
        )
    ctx.emitter.tool_finished(
        "search_products", f"Found {len(results)} matching product(s)",
        meta={"product_ids": [r["id"] for r in results]},
    )
    return _dump({"count": len(results), "products": results})


def _get_product(product_id: str) -> str:
    ctx = current()
    ctx.emitter.tool_started("get_product", f"Looking up product {product_id}")
    with session_scope() as db:
        p = svc.get_product(db, product_id)
    if not p:
        ctx.emitter.tool_error("get_product", f"Product {product_id} not found")
        return _dump({"found": False, "product_id": product_id})
    ctx.emitter.tool_finished("get_product", f"Product identified: {p['name']}")
    return _dump({"found": True, "product": p})


def _get_order(order_id: str) -> str:
    ctx = current()
    ctx.emitter.tool_started("get_order", f"Searching for order {order_id}")
    with session_scope() as db:
        o = svc.get_order(db, order_id)
    if not o:
        ctx.emitter.tool_error("get_order", f"Order {order_id} not found in the demo system")
        return _dump({"found": False, "order_id": order_id})
    ctx.order_context = o["id"]
    line = f"Order {o['id']} found — {o['product_name']} — status {o['status']}"
    ctx.emitter.tool_finished("get_order", line, meta={"order_id": o["id"], "status": o["status"]})
    return _dump({"found": True, "order": o})


def _get_customer(customer_id: str) -> str:
    ctx = current()
    ctx.emitter.tool_started("get_customer", f"Looking up customer {customer_id}")
    with session_scope() as db:
        c = svc.get_customer(db, customer_id)
    if not c:
        ctx.emitter.tool_error("get_customer", f"Customer {customer_id} not found")
        return _dump({"found": False, "customer_id": customer_id})
    ctx.customer_id = c["id"]
    ctx.emitter.tool_finished("get_customer", f"Customer identified: {c['name']}")
    return _dump({"found": True, "customer": c})


def _check_return_eligibility(order_id: str) -> str:
    ctx = current()
    ctx.emitter.tool_started("check_return_eligibility", f"Checking return eligibility for {order_id}")
    with session_scope() as db:
        result = svc.check_return_eligibility(db, order_id)
    verdict = "eligible" if result.get("eligible") else "not eligible"
    ctx.emitter.tool_finished(
        "check_return_eligibility",
        f"{order_id} is {verdict} for a standard return",
        meta={"eligible": result.get("eligible")},
    )
    return _dump(result)


def _get_ticket(ticket_id: str) -> str:
    ctx = current()
    ctx.emitter.tool_started("get_ticket", f"Looking up ticket {ticket_id}")
    with session_scope() as db:
        t = svc.get_ticket(db, ticket_id)
    if not t:
        ctx.emitter.tool_error("get_ticket", f"Ticket {ticket_id} not found")
        return _dump({"found": False, "ticket_id": ticket_id})
    ctx.emitter.tool_finished("get_ticket", f"Ticket {ticket_id} found — status {t['status']}")
    return _dump({"found": True, "ticket": t})


# ─── WRITE tools (register pending action, do not write) ────────────────
def _create_return_request(order_id: str, reason: str) -> str:
    ctx = current()
    with session_scope() as db:
        elig = svc.check_return_eligibility(db, order_id)
    if not elig["found"]:
        ctx.emitter.tool_error("create_return_request", f"Order {order_id} not found")
        return _dump({"ok": False, "error": "Order not found."})
    if not elig["eligible"]:
        ctx.emitter.tool_finished(
            "create_return_request",
            f"Return for {order_id} cannot proceed: {elig['reason']}",
        )
        return _dump({"ok": False, "blocked": True, "reason": elig["reason"], "eligibility": elig})

    summary = f"Create a return request for {order_id.upper()}. Reason: {reason.strip()}"
    ctx.pending_action = {
        "tool": "create_return_request",
        "display": summary,
        "summary": summary,
        "args": {"order_id": order_id.upper(), "reason": reason.strip(),
                 "conversation_id": ctx.conversation_id},
    }
    ctx.emitter.confirmation_requested(
        f"Requesting customer confirmation to create a return for {order_id.upper()}",
        meta=ctx.pending_action,
    )
    return _dump({
        "ok": False, "awaiting_confirmation": True,
        "message": (
            f"A return request for {order_id.upper()} is ready. Ask the customer to confirm "
            "using the approval card. Do not claim it is created yet."
        ),
    })


def _create_support_ticket(subject: str, description: str, customer_id: str | None = None,
                           order_id: str | None = None, priority: str = "NORMAL") -> str:
    ctx = current()
    customer_id = customer_id or ctx.customer_id
    order_id = order_id or ctx.order_context
    summary = f"Create a {priority.upper()} support ticket: “{subject.strip()}”"
    if order_id:
        summary += f" (order {order_id})"
    ctx.pending_action = {
        "tool": "create_support_ticket",
        "display": summary,
        "summary": summary,
        "args": {
            "subject": subject.strip(), "description": description.strip(),
            "customer_id": customer_id, "order_id": order_id,
            "priority": priority.upper(), "conversation_id": ctx.conversation_id,
        },
    }
    ctx.emitter.confirmation_requested(
        f"Requesting customer confirmation to create a support ticket: {subject.strip()}",
        meta=ctx.pending_action,
    )
    return _dump({
        "ok": False, "awaiting_confirmation": True,
        "message": (
            "A support ticket is ready. Ask the customer to confirm using the approval card. "
            "Do not invent a ticket number — it does not exist until the customer confirms."
        ),
    })


def _escalate_to_human(conversation_id: str, reason: str) -> str:
    ctx = current()
    ctx.emitter.escalation(f"Escalating to a human specialist: {reason}", meta={"reason": reason})
    with session_scope() as db:
        from app.models import Conversation

        conv = db.get(Conversation, ctx.conversation_id)
        if conv:
            conv.status = "escalated"
            c = conv.context
            c["escalation_reason"] = reason
            conv.context = c
    return _dump({
        "ok": True,
        "message": (
            "This conversation has been flagged for a human specialist. A NovaCare team "
            "member will follow up. Reference: " + ctx.conversation_id
        ),
    })


# ─── tool registry ─────────────────────────────────────────────────────
def build_tools() -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            _search_knowledge_base, name="search_knowledge_base",
            description="Search NovaStore policy and troubleshooting documentation "
                        "(shipping, returns, refunds, warranty, and per-product guides). "
                        "Use for any 'how do I', policy, or troubleshooting question.",
            args_schema=SearchKnowledgeBaseArgs,
        ),
        StructuredTool.from_function(
            _search_products, name="search_products",
            description="Search the NovaStore product catalogue. Filter by category, "
                        "max_price (NPR), min_price, and required_features (e.g. ['ANC']). "
                        "Use for recommendations and 'do you have ...' questions.",
            args_schema=SearchProductsArgs,
        ),
        StructuredTool.from_function(
            _get_product, name="get_product",
            description="Get full details for one product by id (e.g. P001).",
            args_schema=GetProductArgs,
        ),
        StructuredTool.from_function(
            _get_order, name="get_order",
            description="Look up one order by id (e.g. NS-1077). Returns status, item, "
                        "location, ETA, payment method. Accepts bare numbers like 1077.",
            args_schema=GetOrderArgs,
        ),
        StructuredTool.from_function(
            _get_customer, name="get_customer",
            description="Look up a customer by id (e.g. C001) and list their order ids.",
            args_schema=GetCustomerArgs,
        ),
        StructuredTool.from_function(
            _check_return_eligibility, name="check_return_eligibility",
            description="Check whether an order can be returned under the 14-day policy. "
                        "Always call this before offering or creating a return.",
            args_schema=CheckReturnEligibilityArgs,
        ),
        StructuredTool.from_function(
            _get_ticket, name="get_ticket",
            description="Look up an existing support ticket by id (e.g. SUP-8001).",
            args_schema=GetTicketArgs,
        ),
        StructuredTool.from_function(
            _create_return_request, name="create_return_request",
            description="Begin creating a return request for an order. This requires "
                        "explicit customer confirmation and will NOT complete on its own.",
            args_schema=CreateReturnRequestArgs,
        ),
        StructuredTool.from_function(
            _create_support_ticket, name="create_support_ticket",
            description="Begin creating a support ticket (including warranty claims). "
                        "Requires explicit customer confirmation; will NOT complete on its own.",
            args_schema=CreateSupportTicketArgs,
        ),
        StructuredTool.from_function(
            _escalate_to_human, name="escalate_to_human",
            description="Hand the conversation to a human specialist. Use when the customer "
                        "asks for a human, or when you cannot safely resolve the issue.",
            args_schema=EscalateArgs,
        ),
    ]


READ_TOOLS = {
    "search_knowledge_base", "search_products", "get_product", "get_order",
    "get_customer", "check_return_eligibility", "get_ticket",
}
WRITE_TOOLS = {"create_return_request", "create_support_ticket"}


def execute_pending_action(action: dict, emitter) -> dict:
    """Run an approved write action for real. Called by the /approve endpoint."""
    tool = action["tool"]
    args = dict(action["args"])
    if tool not in ("create_return_request", "create_support_ticket"):
        return {"ok": False, "error": f"Unknown action {tool}"}

    emitter.tool_started(tool, f"Creating {tool.replace('_', ' ')}")

    # Do the DB write in its own committed transaction FIRST, then emit events
    # (emitting opens another session — never nest it inside this write).
    with session_scope() as db:
        if tool == "create_return_request":
            result = svc.create_return_request(
                db, order_id=args["order_id"], reason=args["reason"],
                conversation_id=args.get("conversation_id"),
            )
        else:
            result = svc.create_support_ticket(
                db, subject=args["subject"], description=args["description"],
                customer_id=args.get("customer_id"), order_id=args.get("order_id"),
                priority=args.get("priority", "NORMAL"),
                conversation_id=args.get("conversation_id"),
            )

    if not result.get("ok"):
        emitter.tool_error(tool, result.get("error", "Action failed"))
        return result

    if tool == "create_return_request":
        emitter.emit("db_write", f"Return {result['return']['id']} created",
                     tool=tool, status="success", meta={"return_id": result["return"]["id"]})
    else:
        emitter.emit("db_write", f"Support ticket {result['ticket']['id']} created",
                     tool=tool, status="success", meta={"ticket_id": result["ticket"]["id"]})
    return result
