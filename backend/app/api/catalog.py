"""Product / order / ticket read endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, Product, Return, Ticket
from app.schemas.api import OrderOut, ProductOut, ReturnOut, TicketOut
from app.schemas.tools import ORDER_RE, PRODUCT_RE, TICKET_RE
from app.services import store_service as svc

router = APIRouter()


@router.get("/products", response_model=list[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    category: str | None = Query(None),
    q: str | None = Query(None),
    max_price: int | None = Query(None, ge=0),
):
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category.ilike(category))
    products = list(db.scalars(stmt.order_by(Product.category, Product.name)).all())
    if q or max_price:
        wanted = {p["id"] for p in svc.search_products(db, query=q or "", max_price=max_price, limit=50)}
        products = [p for p in products if p.id in wanted]
    return [ProductOut(**svc.product_to_dict(p)) for p in products]


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product_id = product_id.strip().upper()
    if not PRODUCT_RE.match(product_id):
        raise HTTPException(400, "Invalid product id")
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return ProductOut(**svc.product_to_dict(p))


class DemoOrderIn(BaseModel):
    product_id: str
    customer_id: str = "C001"
    quantity: int = Field(1, ge=1, le=5)


@router.post("/orders/demo", response_model=OrderOut)
def create_demo_order(body: DemoOrderIn, db: Session = Depends(get_db)):
    pid = body.product_id.strip().upper()
    if not PRODUCT_RE.match(pid):
        raise HTTPException(400, "Invalid product id")
    res = svc.create_demo_order(db, pid, body.customer_id, body.quantity)
    if not res["ok"]:
        raise HTTPException(400, res["error"])
    db.commit()
    return OrderOut(**res["order"])


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order_id = order_id.strip().upper()
    if order_id.isdigit():
        order_id = f"NS-{order_id}"
    if not ORDER_RE.match(order_id):
        raise HTTPException(400, "Invalid order id")
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    return OrderOut(**svc.order_to_dict(o))


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket_id = ticket_id.strip().upper()
    if ticket_id.isdigit():
        ticket_id = f"SUP-{ticket_id}"
    if not TICKET_RE.match(ticket_id):
        raise HTTPException(400, "Invalid ticket id")
    t = db.get(Ticket, ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    return TicketOut.model_validate(t)


@router.get("/returns/{return_id}", response_model=ReturnOut)
def get_return(return_id: str, db: Session = Depends(get_db)):
    r = db.get(Return, return_id.strip().upper())
    if not r:
        raise HTTPException(404, "Return not found")
    return ReturnOut.model_validate(r)
