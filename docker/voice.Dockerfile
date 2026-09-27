FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models_cache \
    CT2_VERBOSE=0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ffmpeg libsndfile1 git && rm -rf /var/lib/apt/lists/*

COPY voice/requirements.txt voice/requirements-pipecat.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Full-duplex stack is best-effort; the push-to-talk fallback works regardless.
RUN pip install --no-cache-dir -r requirements-pipecat.txt \
    || echo "WARN: pipecat/aiortc not installed — voice service will run in push-to-talk-only mode"

# Piper fallback voice (~20 MB), baked into the image
RUN python -m piper.download_voices en_US-lessac-low ne_NP-chitwan-medium --data-dir /models_cache/piper \
    || echo "WARN: piper voice not downloaded - TTS fallback unavailable"

COPY voice/ ./

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
  CMD curl -fsS http://localhost:8080/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
