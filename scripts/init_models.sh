#!/usr/bin/env bash
# Build the RAG index. The LLM, STT and TTS are hosted on Groq, so there is nothing to pull.
set -euo pipefail

echo "==> Building the RAG index (knowledge/ -> Chroma)"
docker compose exec -T backend python -c "from app.rag import get_rag; print(get_rag().reindex(force=True))"

echo "==> Done. Open http://localhost:3000"
