"""Bilingual (Nepali + English) text-to-speech. Output is 24 kHz mono float32 / PCM16.

Each sentence is routed by script (Devanagari -> Nepali, else English) and tried down a
provider chain, so a rate limit or outage degrades voice quality instead of ending the call:
  English: Groq -> Edge neural -> Piper
  Nepali:  Edge neural -> Piper
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import re
import subprocess
import sys
import tempfile
import wave

import httpx
import numpy as np

from config import config

log = logging.getLogger("novacare.voice.tts")
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_SENTENCES = re.compile(r"(?<=[.!?।])\s+")


def is_nepali(text: str) -> bool:
    return bool(_DEVANAGARI.search(text))


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCES.split((text or "").strip()) if s.strip()]


def resample(audio: np.ndarray, sr: int, target: int | None = None) -> np.ndarray:
    # ponytail: linear interpolation, no anti-alias filter; fine for speech, use soxr if 8 kHz phone audio sounds harsh
    target = target or config.sample_rate
    if sr == target or len(audio) == 0:
        return audio
    n = int(len(audio) * target / sr)
    return np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio).astype("float32")


def _read_wav(data: bytes) -> np.ndarray:
    with wave.open(io.BytesIO(data)) as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype("float32") / 32768
        if w.getnchannels() > 1:
            pcm = pcm.reshape(-1, w.getnchannels()).mean(axis=1)
        return resample(pcm, w.getframerate())


def _groq(text: str) -> np.ndarray:
    r = httpx.post(
        "https://api.groq.com/openai/v1/audio/speech",
        headers={"Authorization": f"Bearer {config.groq_api_key}"},
        json={"model": config.groq_tts_model, "voice": config.groq_tts_voice,
              "input": text, "response_format": "wav"},
        timeout=20,
    )
    r.raise_for_status()
    return _read_wav(r.content)


def _edge_voice(text: str) -> str:
    return config.edge_voice_ne if is_nepali(text) else config.edge_voice_en


def _edge(text: str) -> np.ndarray:
    """Microsoft neural voices via the free edge-tts endpoint (unofficial; hence the fallbacks)."""
    import edge_tts

    async def fetch() -> bytes:
        out = b""
        async for c in edge_tts.Communicate(text, _edge_voice(text)).stream():
            if c["type"] == "audio":
                out += c["data"]
        return out

    mp3 = asyncio.run(asyncio.wait_for(fetch(), 15))
    if not mp3:
        raise RuntimeError("edge-tts returned no audio")
    pcm = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-f", "s16le", "-ar", str(config.sample_rate),
         "-ac", "1", "pipe:1"],
        input=mp3, check=True, capture_output=True, timeout=15,
    ).stdout
    return np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768


def _piper(text: str) -> np.ndarray:
    voice = config.piper_voice_ne if is_nepali(text) else config.piper_voice
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(
            [sys.executable, "-m", "piper", "-m", voice, "--data-dir", config.piper_dir, "-f", path],
            input=text.encode(), check=True, timeout=30, capture_output=True,
        )
        with open(path, "rb") as fh:
            return _read_wav(fh.read())
    finally:
        os.unlink(path)


# Fixed phrases (greeting, fillers, confirm prompts) are said on every call: synthesize once at
# startup via warm(), then they play instantly. Only warmed phrases are cached.
_cache: dict[str, np.ndarray] = {}


def warm(phrases: list[str]) -> None:
    for p in phrases:
        audio = _speak(p)
        if len(audio):
            _cache[p] = audio


def _chain(text: str):
    return (_edge, _piper) if is_nepali(text) else (_groq, _edge, _piper)


def _speak(text: str) -> np.ndarray:
    for provider in _chain(text):
        try:
            return provider(text)
        except Exception as exc:  # noqa: BLE001
            log.warning("TTS %s failed (%s); trying next", provider.__name__, exc)
    return np.zeros(0, dtype="float32")


def synthesize(text: str) -> np.ndarray:
    """float32 mono at config.sample_rate. Mixed Nepali/English text is voiced sentence by sentence."""
    parts = sentences(text)
    if not parts:
        return np.zeros(0, dtype="float32")
    gap = np.zeros(int(config.sample_rate * 0.12), dtype="float32")  # short natural pause
    out: list[np.ndarray] = []
    for s in parts:
        out += [_cache[s] if s in _cache else _speak(s), gap]
    return np.concatenate(out)


def synthesize_wav(text: str) -> bytes:
    pcm = (np.clip(synthesize(text), -1, 1) * 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(config.sample_rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()
