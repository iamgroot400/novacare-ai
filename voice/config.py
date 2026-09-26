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
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    # large-v3 (not -turbo): noticeably better on Nepali
    groq_stt_model: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3")
    stt_language: str = os.getenv("STT_LANGUAGE", "")  # "" = auto-detect; "ne" or "en" pins it
    # Groq's TTS model names have changed over time; check console.groq.com/docs/text-to-speech
    groq_tts_model: str = os.getenv("GROQ_TTS_MODEL", "canopylabs/orpheus-v1-english")
    groq_tts_voice: str = os.getenv("GROQ_TTS_VOICE", "autumn")
    piper_voice: str = os.getenv("PIPER_VOICE", "en_US-lessac-low")
    piper_voice_ne: str = os.getenv("PIPER_VOICE_NE", "ne_NP-google-medium")
    edge_voice_ne: str = os.getenv("EDGE_VOICE_NE", "ne-NP-HemkalaNeural")
    edge_voice_en: str = os.getenv("EDGE_VOICE_EN", "en-US-AriaNeural")
    edge_rate: str = os.getenv("EDGE_RATE", "+0%")  # e.g. "-10%" speaks a little slower
    vad_stop_secs: float = float(os.getenv("VAD_STOP_SECS", "0.6"))
    # If the agent hasn't answered after this long (a tool is running), say a short filler.
    filler_after_secs: float = float(os.getenv("FILLER_AFTER_SECS", "1.2"))
    # ElevenLabs: most human-sounding (eleven_v3 speaks Nepali). Needs both key and voice id.
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "")
    elevenlabs_model: str = os.getenv("ELEVENLABS_MODEL", "eleven_v3")
    piper_dir: str = os.getenv("PIPER_DIR", "/models_cache/piper")
    sample_rate: int = 24000
    # Phone calls (Twilio). PUBLIC_VOICE_URL empty = auto-discover the cloudflared quick tunnel.
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_from_number: str = os.getenv("TWILIO_FROM_NUMBER", "")
    call_api_token: str = os.getenv("CALL_API_TOKEN", "")
    public_voice_url: str = os.getenv("PUBLIC_VOICE_URL", "")
    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ]
    )
    ice_servers: list[dict] = field(default_factory=_ice_servers)
    max_utterance_seconds: int = int(os.getenv("VOICE_MAX_UTTERANCE_SECONDS", "30"))


config = VoiceConfig()
