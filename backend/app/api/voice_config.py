"""Runtime config the frontend needs (ICE servers, demo date, model)."""
from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.schemas.api import ConfigOut

router = APIRouter()


def ice_servers() -> list[dict]:
    servers: list[dict] = []
    if settings.webrtc_stun_url:
        servers.append({"urls": settings.webrtc_stun_url})
    if settings.webrtc_turn_url:
        entry = {"urls": settings.webrtc_turn_url}
        if settings.webrtc_turn_username:
            entry["username"] = settings.webrtc_turn_username
            entry["credential"] = settings.webrtc_turn_password
        servers.append(entry)
    if not servers:
        servers.append({"urls": "stun:stun.l.google.com:19302"})
    return servers


@router.get("/config", response_model=ConfigOut)
def get_config():
    return ConfigOut(
        demo_date=settings.demo_date,
        ice_servers=ice_servers(),
        voice_url=settings.voice_url,
        model=settings.ollama_model,
    )
