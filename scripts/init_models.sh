#!/usr/bin/env bash
# Pull the LLM into the Ollama volume and warm the RAG + voice model caches.
# Run once after `docker compose up -d` (or any time you change OLLAMA_MODEL).
set -euo pipefail

MODEL="${OLLAMA_MODEL:-qwen3:4b}"

echo "==> Pulling Ollama model: ${MODEL}"
if docker compose ps --services 2>/dev/null | grep -q '^ollama$'; then
  docker compose exec -T ollama ollama pull "${MODEL}"
else
  echo "ollama service not running; starting it..."
  docker compose up -d ollama
  sleep 5
  docker compose exec -T ollama ollama pull "${MODEL}"
fi

echo "==> Building the RAG index (knowledge/ -> Chroma)"
docker compose exec -T backend python -c "from app.rag import get_rag; print(get_rag().reindex(force=True))"

echo "==> Warming voice models (Whisper + Kokoro) — first run downloads weights"
docker compose exec -T voice python -c "import stt, tts; stt.get_model(); tts.get_pipeline(); print('voice models ready')" || \
  echo "voice warmup skipped (service may still be starting)"

echo "==> Done. Open http://localhost:3000"
