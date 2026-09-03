"""Faster-Whisper speech-to-text (local, no paid API)."""
from __future__ import annotations

import io
import logging
import threading

import numpy as np

from config import config

log = logging.getLogger("novacare.voice.stt")
_model = None
_lock = threading.Lock()


def get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from faster_whisper import WhisperModel

                log.info("Loading faster-whisper model=%s device=%s", config.whisper_model, config.whisper_device)
                _model = WhisperModel(
                    config.whisper_model,
                    device=config.whisper_device,
                    compute_type=config.whisper_compute_type,
                )
    return _model


def transcribe_pcm(pcm: np.ndarray, sample_rate: int = 16000) -> str:
    """pcm: float32 mono in [-1, 1]."""
    model = get_model()
    segments, _info = model.transcribe(pcm, language="en", vad_filter=True, beam_size=1)
    return " ".join(s.text.strip() for s in segments).strip()


def transcribe_file(data: bytes) -> str:
    """Transcribe an uploaded audio file (wav/webm/ogg/mp3). Requires ffmpeg/soundfile."""
    import soundfile as sf

    try:
        audio, sr = sf.read(io.BytesIO(data), dtype="float32", always_2d=False)
    except Exception:
        # fall back to letting faster-whisper/ffmpeg decode from a temp file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as fh:
            fh.write(data)
            path = fh.name
        model = get_model()
        segments, _ = model.transcribe(path, language="en", vad_filter=True, beam_size=1)
        return " ".join(s.text.strip() for s in segments).strip()

    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        # simple linear resample
        import math

        target_len = int(math.floor(len(audio) * 16000 / sr))
        idx = np.linspace(0, len(audio) - 1, target_len).astype(np.int64)
        audio = audio[idx]
    return transcribe_pcm(audio.astype("float32"), 16000)
