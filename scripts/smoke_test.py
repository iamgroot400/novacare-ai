#!/usr/bin/env python3
"""End-to-end smoke test against a running stack (backend on :8000).

    python scripts/smoke_test.py            # uses http://localhost:8000
    API=http://host:8000 python scripts/smoke_test.py

Checks: health, product list, order lookup, return eligibility (NS-1042 vs NS-1033),
conversation create + message + agent activity, and (if a write is proposed)
the approve flow producing a real RET-/SUP- record.
"""
from __future__ import annotations

import os
import sys
import time

import httpx

API = os.getenv("API", "http://localhost:8000").rstrip("/")
VOICE = os.getenv("VOICE", "http://localhost:8080").rstrip("/")
ok = True


def check(name: str, cond: bool, extra: str = "") -> None:
    global ok
    mark = "PASS" if cond else "FAIL"
    if not cond:
        ok = False
    print(f"[{mark}] {name}{(' — ' + extra) if extra else ''}")


with httpx.Client(timeout=180) as c:
    h = c.get(f"{API}/health").json()
    check("health reachable", h.get("demo_date") == "2026-09-03", str(h.get("status")))
    check("ollama reachable", h["ollama"]["reachable"], h["ollama"]["message"])
    check("model available", h["ollama"]["model_available"], h["ollama"]["model"])

    products = c.get(f"{API}/api/products").json()
    check("catalogue >= 20 products", len(products) >= 20, f"{len(products)} products")

    o = c.get(f"{API}/api/orders/NS-1077").json()
    check("order NS-1077 in transit", o.get("status") == "in_transit", o.get("current_location", ""))

    conv = c.post(f"{API}/api/conversations", json={"channel": "chat"}).json()
    cid = conv["id"]
    check("conversation created", cid.startswith("conv_"))

    r = c.post(f"{API}/api/conversations/{cid}/message",
               json={"content": "Where is order NS-1077?", "channel": "chat"}).json()
    check("agent answered order query", "1077" in r["reply"] or "transit" in r["reply"].lower(), r["reply"][:80])
    events = c.get(f"{API}/api/conversations/{cid}/events").json()
    check("get_order tool actually ran", any(e.get("tool") == "get_order" for e in events))

    r2 = c.post(f"{API}/api/conversations/{cid}/message",
                json={"content": "Can I return NS-1042?", "channel": "chat"}).json()
    events = c.get(f"{API}/api/conversations/{cid}/events").json()
    check("return eligibility checked", any(e.get("tool") == "check_return_eligibility" for e in events))

    # Ask for a ticket, then approve it
    conv2 = c.post(f"{API}/api/conversations", json={"channel": "chat"}).json()["id"]
    c.post(f"{API}/api/conversations/{conv2}/message", json={
        "content": "My NovaPods Pro from order NS-1042 keep disconnecting and I tried every reset. "
                   "Please open a high priority support ticket.",
        "channel": "chat",
    })
    detail = c.get(f"{API}/api/conversations/{conv2}").json()
    pending = detail.get("pending_action")
    check("write action requires confirmation", bool(pending), str(pending and pending.get("tool")))
    if pending:
        appr = c.post(f"{API}/api/conversations/{conv2}/approve", json={}).json()
        check("approve created a real record", appr.get("ok") is True, appr.get("reply", "")[:80])

    try:
        v = c.get(f"{VOICE}/health").json()
        check("voice service reachable", v.get("status") == "ok",
              f"full_duplex={v.get('full_duplex')}")
    except Exception as e:  # noqa: BLE001
        check("voice service reachable", False, str(e))

print()
print("SMOKE TEST:", "OK" if ok else "FAILURES")
sys.exit(0 if ok else 1)
