"""Groq hosted Whisper speech-to-text for Nepali + English. No local model, ~0 RAM.

Whisper often mislabels Nepali as Hindi (same script). We send a bilingual prompt to bias it
toward Nepali vocabulary and store terms, and if it still reports Hindi we redo the request
pinned to Nepali.
"""
from __future__ import annotations

import httpx

from config import config

# Style/vocabulary primer: Devanagari Nepali + English brand terms customers actually say.
_PROMPT = (
    "नमस्ते, म NovaStore को अर्डर NS-1042 बारे सोध्न चाहन्छु। NovaPods Pro, NovaKeys, "
    "NovaCharge, return, refund, warranty, ticket। मेरो अर्डर कहाँ पुग्यो?"
)


def _request(data: bytes, filename: str, language: str | None) -> dict:
    form = {"model": config.groq_stt_model, "response_format": "verbose_json",
            "temperature": "0", "prompt": _PROMPT}
    if language:
        form["language"] = language
    r = httpx.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {config.groq_api_key}"},
        files={"file": (filename, data)},
        data=form,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def transcribe_file(data: bytes, filename: str = "audio.wav") -> str:
    """Transcribe wav/webm/ogg/mp3 bytes. STT_LANGUAGE pins a language; empty = auto-detect."""
    res = _request(data, filename, config.stt_language or None)
    if not config.stt_language and res.get("language") in ("hindi", "hi", "urdu", "ur", "marathi", "mr"):
        res = _request(data, filename, "ne")
    return (res.get("text") or "").strip()
