"""NovaCare AI — FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import func, select

from app.api import api_router
from app.config import settings
from app.database import init_db, session_scope
from app.models import Product
from app.services import ollama

logging.basicConfig(level=settings.log_level.upper())
log = logging.getLogger("novacare")

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with session_scope() as db:
        count = db.scalar(select(func.count()).select_from(Product)) or 0
    if count == 0:
        log.info("Empty database — running seed()")
        from app.database.seed import seed_all

        seed_all(verbose=True)
    try:
        from app.rag import get_rag

        stats = get_rag().reindex(force=False)
        log.info("RAG index ready: %s", stats)
    except Exception as exc:  # noqa: BLE001
        log.warning("RAG index not ready yet: %s", exc)
    yield


app = FastAPI(title="NovaCare AI", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests, slow down."})


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s", request.url.path)
    detail = "Internal server error" if settings.is_production else f"{type(exc).__name__}: {exc}"
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/health")
async def health():
    with session_scope() as db:
        products = db.scalar(select(func.count()).select_from(Product)) or 0
    oll = await ollama.check_health()
    ok = products > 0 and oll["reachable"]
    return {
        "status": "ok" if ok else "degraded",
        "demo_date": settings.demo_date,
        "database": {"products": products, "seeded": products > 0},
        "ollama": oll,
    }


@app.get("/")
async def root():
    return {"service": "NovaCare AI", "docs": "/docs", "health": "/health"}


app.include_router(api_router, prefix="/api")
