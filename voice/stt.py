"""Groq hosted Whisper speech-to-text for Nepali + English. No local model, ~0 RAM.

Whisper's language auto-detect is unreliable on short Nepali: it reports Hindi, Urdu (then
writes Urdu script) or even Indonesian ("मेरो अर्डर कहाँ पुग्यो?" -> "Miro order ke H2O.").
So anything not detected as English or Nepali is transcribed again pinned to Nepali. Groq
reports full names ("Nepali (macrolanguage)", "English"), not ISO codes.
"""
from __future__ import annotations

import re

import httpx

from config import config

# Style/vocabulary primer: Devanagari Nepali + English brand terms customers actually say.
_PROMPT = (
    "नमस्ते, म NovaStore को अर्डर NS-1042 बारे सोध्न चाहन्छु। NovaPods Pro, NovaKeys, "
    "NovaCharge, return, refund, warranty, ticket। मेरो अर्डर कहाँ पुग्यो?"
)
_LETTERS = re.compile(r"[^\W\d_]", re.UNICODE)


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


def needs_nepali_retry(language: str | None) -> bool:
    return not (language or "").strip().lower().startswith(("english", "nepali", "en", "ne"))


def transcribe_file(data: bytes, filename: str = "audio.wav") -> str:
    """Transcribe wav/webm/ogg/mp3 bytes. STT_LANGUAGE pins a language; empty = auto (en/ne).

    Returns "" for noise: Whisper turns silence into a lone "।" or ".", which isn't speech.
    """
    res = _request(data, filename, config.stt_language or None)
    if not config.stt_language and needs_nepali_retry(res.get("language")):
        res = _request(data, filename, "ne")
    text = (res.get("text") or "").strip()
    return text if _LETTERS.search(text) else ""
