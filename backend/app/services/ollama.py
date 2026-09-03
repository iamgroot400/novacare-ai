"""Ollama health + model availability checks. Never falls back to a paid API."""
from __future__ import annotations

import httpx

from app.config import settings


async def check_health() -> dict:
    base = settings.ollama_base_url.rstrip("/")
    result = {
        "base_url": base,
        "model": settings.ollama_model,
        "reachable": False,
        "model_available": False,
        "models": [],
        "message": "",
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{base}/api/tags")
            r.raise_for_status()
            data = r.json()
            names = [m.get("name", "") for m in data.get("models", [])]
            result["reachable"] = True
            result["models"] = names
            want = settings.ollama_model
            result["model_available"] = any(
                n == want or n.split(":")[0] == want.split(":")[0] for n in names
            )
            if not result["model_available"]:
                result["message"] = (
                    f"Ollama is running but model '{want}' is not pulled. "
                    f"Run:  ollama pull {want}"
                )
            else:
                result["message"] = "Ollama healthy."
    except Exception as exc:  # noqa: BLE001
        result["message"] = (
            f"Cannot reach Ollama at {base}: {exc}. "
            "Start Ollama (docker compose up ollama) — NovaCare does not use any paid AI API."
        )
    return result
