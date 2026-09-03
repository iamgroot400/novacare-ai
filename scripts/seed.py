#!/usr/bin/env python3
"""Seed the NovaCare demo database. Safe to run repeatedly (idempotent).

Usage:
    python scripts/seed.py
    DATABASE_URL=sqlite:////data/novacare.db python scripts/seed.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("KNOWLEDGE_DIR", str(ROOT / "knowledge"))

from app.database.seed import seed_all  # noqa: E402


def main() -> int:
    summary = seed_all(verbose=True)
    required = ["NS-1042", "NS-1077", "NS-1089", "NS-1033", "NS-1091"]
    from app.database import session_scope
    from app.models import Order

    with session_scope() as db:
        missing = [oid for oid in required if db.get(Order, oid) is None]
    if missing:
        print("ERROR: required demo orders missing:", missing)
        return 1
    print("All required demo orders present. Seed OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
