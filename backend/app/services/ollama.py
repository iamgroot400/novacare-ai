"""LLM health check (Groq). Module name kept so main.py / services imports stay unchanged."""
from __future__ import annotations

from app.config import settings


async def check_health() -> dict:
    ok = bool(settings.groq_api_key)
    return {
        "model": settings.groq_model,
        "reachable": ok,
        "model_available": ok,
        "message": "Groq key configured." if ok else "GROQ_API_KEY is not set.",
    }
