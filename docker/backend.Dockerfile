FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models_cache \
    SENTENCE_TRANSFORMERS_HOME=/models_cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements-core.txt backend/requirements-ai.txt backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements-core.txt -r requirements-ai.txt
# Bake Chroma's ONNX MiniLM (~80 MB) into the image. Otherwise the first knowledge-base search
# downloads it mid-conversation, and a stalled download hangs that turn indefinitely.
RUN python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction as E; E()(['warm'])"

COPY backend/ ./backend/
COPY knowledge/ ./knowledge/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app/backend \
    KNOWLEDGE_DIR=/app/knowledge \
    DATABASE_URL=sqlite:////data/novacare.db

WORKDIR /app/backend
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
