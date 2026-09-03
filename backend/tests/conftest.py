"""Shared fixtures. Uses a fresh file-based SQLite DB per test session."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp(prefix="novacare_test_")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ.setdefault("DEMO_DATE", "2026-09-03")
os.environ.setdefault("CHROMA_HOST", "local")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")

from app.database import session_scope  # noqa: E402
from app.database.seed import seed_all  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seeded_db():
    seed_all(verbose=False)
    yield


@pytest.fixture
def db():
    with session_scope() as session:
        yield session
