"""Idempotent seeding. Running repeatedly never duplicates demo rows."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.seed_data import CUSTOMERS, ORDERS, PRODUCTS, RETURNS, TICKETS
from app.database.session import init_db, session_scope
from app.models import Customer, Order, Product, Return, Ticket


def _dt(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _upsert(db: Session, model, pk: str, data: dict) -> None:
    obj = db.get(model, pk)
    if obj is None:
        obj = model(id=pk)
        db.add(obj)
    for key, val in data.items():
        setattr(obj, key, val)


def seed_all(verbose: bool = True) -> dict[str, int]:
    init_db()
    with session_scope() as db:
        for p in PRODUCTS:
            data = dict(p)
            pid = data.pop("id")
            features = data.pop("features", [])
            obj = db.get(Product, pid) or Product(id=pid)
            for k, v in data.items():
                setattr(obj, k, v)
            obj.features = features
            if obj not in db:
                db.add(obj)

        for c in CUSTOMERS:
            data = dict(c)
            _upsert(db, Customer, data.pop("id"), data)

        db.flush()

        for o in ORDERS:
            data = dict(o)
            oid = data.pop("id")
            data.setdefault("is_demo", 0)
            _upsert(db, Order, oid, data)

        db.flush()

        for t in TICKETS:
            data = dict(t)
            data["created_at"] = _dt(data.get("created_at"))
            _upsert(db, Ticket, data.pop("id"), data)

        for r in RETURNS:
            data = dict(r)
            data["created_at"] = _dt(data.get("created_at"))
            _upsert(db, Return, data.pop("id"), data)

    with session_scope() as db:
        from sqlalchemy import func

        summary = {
            "products": db.scalar(select(func.count()).select_from(Product)),
            "customers": db.scalar(select(func.count()).select_from(Customer)),
            "orders": db.scalar(select(func.count()).select_from(Order)),
            "tickets": db.scalar(select(func.count()).select_from(Ticket)),
            "returns": db.scalar(select(func.count()).select_from(Return)),
        }
    if verbose:
        print("Seed complete:", summary)
    return summary


if __name__ == "__main__":  # pragma: no cover
    seed_all()
