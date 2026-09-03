"""Central configuration, loaded from environment variables."""
from __future__ import annotations

from datetime import date
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Demo determinism
    demo_date: str = "2026-09-03"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"

    # Chroma
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Database
    database_url: str = "sqlite:///./data/novacare.db"

    # URLs
    public_app_url: str = "http://localhost:3000"

    # Voice / webrtc (exposed to frontend through /api/config)
    webrtc_stun_url: str = "stun:stun.l.google.com:19302"
    webrtc_turn_url: str = ""
    webrtc_turn_username: str = ""
    webrtc_turn_password: str = ""
    voice_url: str = "http://localhost:8080"

    # Security
    cors_allow_origins: str = "http://localhost:3000"
    max_message_chars: int = 2000
    rate_limit_per_minute: int = 30
    request_timeout_seconds: int = 120
    log_level: str = "INFO"
    environment: str = "development"

    @property
    def demo_date_obj(self) -> date:
        return date.fromisoformat(self.demo_date)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
