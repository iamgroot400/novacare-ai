from fastapi import APIRouter

from app.api import catalog, conversations, dashboard, voice_config

api_router = APIRouter()
api_router.include_router(catalog.router, tags=["catalog"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(voice_config.router, tags=["voice"])

__all__ = ["api_router"]
