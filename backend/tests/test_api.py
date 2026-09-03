from __future__ import annotations

from fastapi.testclient import TestClient


def _client():
    from app.main import app

    return TestClient(app)


def test_health():
    c = _client()
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["demo_date"] == "2026-09-03"
    assert body["database"]["seeded"] is True


def test_list_products():
    c = _client()
    r = c.get("/api/products")
    assert r.status_code == 200
    products = r.json()
    assert len(products) >= 20
    assert any(p["id"] == "P001" for p in products)


def test_get_product_and_order_and_ticket():
    c = _client()
    assert c.get("/api/products/P003").json()["name"] == "NovaWatch S2"
    assert c.get("/api/orders/NS-1089").json()["status"] == "delayed"
    assert c.get("/api/orders/1089").json()["id"] == "NS-1089"
    assert c.get("/api/tickets/SUP-8001").json()["status"] == "RESOLVED"
    assert c.get("/api/orders/NS-0000").status_code == 404


def test_conversation_persistence():
    c = _client()
    conv = c.post("/api/conversations", json={"channel": "chat"}).json()
    cid = conv["id"]
    assert cid.startswith("conv_")

    # add messages directly through the service layer to avoid needing Ollama
    from app.database import session_scope
    from app.services import conversation_service as convo

    with session_scope() as db:
        convo.add_message(db, cid, "user", "My NovaPods keep disconnecting")
        convo.add_message(db, cid, "assistant", "Can you share your order number?")
        convo.add_message(db, cid, "user", "NS-1042")

    got = c.get(f"/api/conversations/{cid}").json()
    assert [m["content"] for m in got["messages"]][-1] == "NS-1042"
    assert len(got["messages"]) == 3


def test_config_endpoint():
    c = _client()
    cfg = c.get("/api/config").json()
    assert cfg["demo_date"] == "2026-09-03"
    assert isinstance(cfg["ice_servers"], list) and cfg["ice_servers"]


def test_dashboard_endpoint():
    c = _client()
    d = c.get("/api/dashboard").json()
    assert d["label"] == "Demo Analytics"
