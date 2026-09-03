"""Voice service configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _ice_servers() -> list[dict]:
    servers: list[dict] = []
    stun = os.getenv("WEBRTC_STUN_URL", "stun:stun.l.google.com:19302")
    if stun:
        servers.append({"urls": stun})
    turn = os.getenv("WEBRTC_TURN_URL", "")
    if turn:
        entry = {"urls": turn}
        if os.getenv("WEBRTC_TURN_USERNAME"):
            entry["username"] = os.getenv("WEBRTC_TURN_USERNAME")
            entry["credential"] = os.getenv("WEBRTC_TURN_PASSWORD", "")
        servers.append(entry)
    return servers or [{"urls": "stun:stun.l.google.com:19302"}]


@dataclass
class VoiceConfig:
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    kokoro_voice: str = os.getenv("KOKORO_VOICE", "af_heart")
    kokoro_lang: str = os.getenv("KOKORO_LANG", "a")
    sample_rate: int = 24000
    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ]
    )
    ice_servers: list[dict] = field(default_factory=_ice_servers)
    max_utterance_seconds: int = int(os.getenv("VOICE_MAX_UTTERANCE_SECONDS", "30"))


config = VoiceConfig()
