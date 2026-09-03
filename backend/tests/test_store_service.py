from __future__ import annotations

from app.services import store_service as svc


def test_get_order_ns1077(db):
    o = svc.get_order(db, "NS-1077")
    assert o is not None
    assert o["status"] == "in_transit"
    assert o["product_name"] == "NovaWatch S2"
    assert o["current_location"] == "Kathmandu Distribution Hub"
    assert o["estimated_delivery"] == "2026-09-04"


def test_get_order_bare_number_via_schema():
    from app.schemas.tools import GetOrderArgs

    assert GetOrderArgs(order_id="1077").order_id == "NS-1077"


def test_invalid_order_id_rejected():
    from pydantic import ValidationError
    from app.schemas.tools import GetOrderArgs
    import pytest

    with pytest.raises(ValidationError):
        GetOrderArgs(order_id="hello world")


def test_return_eligibility_ns1042_true(db):
    r = svc.check_return_eligibility(db, "NS-1042")
    assert r["found"] is True
    assert r["eligible"] is True
    assert r["days_since_delivery"] == 8


def test_return_eligibility_ns1033_false(db):
    r = svc.check_return_eligibility(db, "NS-1033")
    assert r["found"] is True
    assert r["eligible"] is False
    assert r["days_since_delivery"] == 24
    assert r["warranty_available"] is True


def test_return_eligibility_unknown_order(db):
    r = svc.check_return_eligibility(db, "NS-9999")
    assert r["found"] is False
    assert r["eligible"] is False


def test_return_eligibility_in_transit_not_returnable(db):
    r = svc.check_return_eligibility(db, "NS-1077")
    assert r["eligible"] is False


def test_product_search_headphones_anc_under_7000(db):
    results = svc.search_products(
        db, query="headphones", max_price=7000, required_features=["ANC"]
    )
    ids = [r["id"] for r in results]
    assert "P002" in ids  # NovaPods Lite
    assert "P001" not in ids  # NovaPods Pro is 8499, over budget
    assert results[0]["id"] == "P002"


def test_product_search_keyboard_under_8000(db):
    results = svc.search_products(db, query="keyboard", max_price=8000)
    ids = [r["id"] for r in results]
    assert "P006" in ids  # NovaKeys Mechanical 7499
    assert results[0]["category"] == "Computing"


def test_create_return_requires_eligibility(db):
    # NS-1033 is not eligible -> must fail
    res = svc.create_return_request(db, "NS-1033", "changed my mind")
    assert res["ok"] is False


def test_create_return_and_ticket_flow(db):
    res = svc.create_return_request(db, "NS-1042", "Bluetooth keeps dropping", conversation_id="conv_test1")
    assert res["ok"] is True
    assert res["return"]["id"].startswith("RET-")
    rid = res["return"]["id"]

    # order now marked return_requested, second attempt blocked
    again = svc.create_return_request(db, "NS-1042", "again")
    assert again["ok"] is False

    fetched = svc.get_order(db, "NS-1042")
    assert fetched["status"] == "return_requested"

    t = svc.create_support_ticket(
        db, subject="NovaPods Pro disconnecting", description="Tried all resets",
        customer_id="C001", order_id="NS-1042", priority="HIGH", conversation_id="conv_test1",
    )
    assert t["ok"] is True
    assert t["ticket"]["id"].startswith("SUP-")
    assert svc.get_ticket(db, t["ticket"]["id"])["priority"] == "HIGH"

    # restore state so a re-run / reseed stays clean
    from app.models import Order, Return, Ticket
    db.get(Order, "NS-1042").status = "delivered"
    db.query(Return).filter(Return.id == rid).delete()
    db.query(Ticket).filter(Ticket.id == t["ticket"]["id"]).delete()


def test_dashboard_metrics_shape(db):
    m = svc.dashboard_metrics(db)
    assert m["label"] == "Demo Analytics"
    assert "totals" in m and "orders_by_status" in m
    assert m["totals"]["conversations"] >= 0
