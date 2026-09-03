"""Kokoro text-to-speech (local, no paid API). Produces 24 kHz mono WAV bytes."""
from __future__ import annotations

import io
import logging
import threading

import numpy as np

from config import config

log = logging.getLogger("novacare.voice.tts")
_pipeline = None
_lock = threading.Lock()


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        with _lock:
            if _pipeline is None:
                from kokoro import KPipeline

                log.info("Loading Kokoro pipeline lang=%s", config.kokoro_lang)
                _pipeline = KPipeline(lang_code=config.kokoro_lang)
    return _pipeline


def synthesize(text: str) -> np.ndarray:
    """Return float32 mono audio at 24 kHz."""
    text = (text or "").strip()
    if not text:
        return np.zeros(0, dtype="float32")
    pipeline = get_pipeline()
    chunks: list[np.ndarray] = []
    for _gs, _ps, audio in pipeline(text, voice=config.kokoro_voice):
        arr = np.asarray(audio, dtype="float32")
        chunks.append(arr)
    if not chunks:
        return np.zeros(0, dtype="float32")
    return np.concatenate(chunks)


def synthesize_wav(text: str) -> bytes:
    import soundfile as sf

    audio = synthesize(text)
    buf = io.BytesIO()
    sf.write(buf, audio, config.sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()
