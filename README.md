# NovaCare AI

An **agentic** AI customer-support platform for **NovaStore**, a fictional Nepal-based
electronics e-commerce company. NovaCare shows that an AI support agent can do far more
than generate text — it looks up real orders, searches policy documents, checks return
eligibility, creates tickets and returns (with your confirmation), troubleshoots devices,
escalates to humans, and does all of it over **chat or an in-browser voice call** with a
shared conversation.

> NovaStore is fictional. No real products, customers, orders or payments exist. Refund
> lifecycles are simulated and never touch a real payment system.

---

## Architecture

```
                    Customer (phone / tablet / desktop, over the Internet)
                          │                                   │
                     Text chat                          Voice call
                          │                                   │
                          │                    Browser mic ─ WebRTC / push-to-talk
                          │                                   │
                          │                     Faster-Whisper STT (Pipecat, local)
                          │                                   │
                          └───────────────► text message ◄────┘
                                              │
                                   ┌──────────▼───────────┐
                                   │   LangGraph agent    │   (ONE agent, two interfaces)
                                   │  (backend, FastAPI)  │
                                   └─────┬──────┬─────────┘
                          ┌──────────────┘      └───────────────┐
                          ▼                                     ▼
                 Ollama  qwen3:4b                    Tools (Pydantic-validated)
                                                     ├─ RAG: ChromaDB + local embeddings
                                                     └─ DB:  SQLite (orders / products /
                                                             customers / tickets / returns /
                                                             conversations / messages / events)
                                              │
                                     Agent response text
                                              │
                                     Kokoro TTS (Pipecat, local)  ──►  audio ──► browser
```

Observable **agent activity** (tool calls, KB searches, DB reads/writes, confirmation
requests) is streamed to the UI as structured backend events — **never** chain-of-thought
or model scratchpad.

## Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS · mobile-first |
| Backend | Python · FastAPI · SQLAlchemy · SQLite |
| Agent | LangGraph (ReAct) · `langchain-ollama` |
| LLM | Ollama · `qwen3:4b` (override with `OLLAMA_MODEL`) |
| RAG | ChromaDB · `sentence-transformers/all-MiniLM-L6-v2` (local, no paid embeddings) |
| Voice | Pipecat · SmallWebRTC · WhisperSTTService (Faster-Whisper) · KokoroTTSService |
| Deploy | Docker Compose (frontend, backend, voice, ollama, chroma, optional coturn) |

No OpenAI / Anthropic / ElevenLabs / Deepgram / Cartesia. The whole pipeline runs locally
once model assets are downloaded.

## Screenshots

_Add screenshots of `/`, `/products`, `/support` (with the Agent Activity panel), the
voice call modal, and `/dashboard` here._

## Features

- Chat + in-browser voice, **same conversation** and memory across both
- Real LangGraph tools: `search_knowledge_base`, `search_products`, `get_product`,
  `get_order`, `get_customer`, `check_return_eligibility`, `create_return_request`,
  `create_support_ticket`, `get_ticket`, `escalate_to_human`
- Read actions run automatically; **write actions require an approval card** before anything
  is written
- Return eligibility against a fixed demo date (`2026-09-03`) and a 14-day rule
- RAG-grounded troubleshooting from 14 Markdown knowledge docs
- Live "Agent Activity" stream over WebSocket (observable events only)
- Product catalogue (22 Nova products), order tracking, admin **Demo Analytics** dashboard
- CPU-friendly defaults; configurable Whisper model size
- Graceful voice fallback: if full-duplex WebRTC can't start, push-to-talk still works

## Requirements

- Docker + Docker Compose v2
- ~6 GB free disk for models (`qwen3:4b` ≈ 2.6 GB, Whisper `base` ≈ 150 MB, Kokoro ≈ 350 MB,
  embeddings ≈ 90 MB)
- 8 GB RAM recommended (CPU-only works; a GPU makes voice snappier)
- For local (non-Docker) dev: Python 3.11 and Node 20

---

## Quick start (Docker)

```bash
git clone <repo> novacare-ai && cd novacare-ai
cp .env.example .env                 # review values
docker compose up -d --build         # starts frontend, backend, voice, ollama, chroma
bash scripts/init_models.sh          # pulls qwen3:4b, builds RAG index, warms voice models
```

Then open **http://localhost:3000**.

The `ollama-init` service also pulls the model automatically on first `up`; `init_models.sh`
is the explicit/repeatable path and also warms the RAG and voice caches.

### Exact commands

| Purpose | Command |
| --- | --- |
| Start the stack | `docker compose up -d --build` |
| Pull the LLM | `docker compose exec ollama ollama pull qwen3:4b` |
| Seed / re-seed DB | `docker compose exec backend python /app/scripts/seed.py` |
| Build RAG index | `docker compose exec backend python -c "from app.rag import get_rag; print(get_rag().reindex(force=True))"` |
| Run tests | `docker compose exec backend python -m pytest -q` |
| End-to-end smoke | `python scripts/smoke_test.py` |
| Logs | `docker compose logs -f` |
| Stop | `docker compose down` |
| Wipe everything | `docker compose down -v` |

The database auto-seeds on first boot if empty, so `seed.py` is only needed to reset it.

### Windows

`make` isn't required. Use `./scripts/tasks.ps1 <task>` (`env`, `setup`, `up`, `models`,
`seed`, `test`, `smoke`, `turn`, `down`, `clean`) or the raw `docker compose` commands above.

---

## Local development (no Docker for app code)

You still need Ollama + Chroma. Easiest: run just those in Docker.

```bash
docker compose up -d ollama chroma
docker compose exec ollama ollama pull qwen3:4b

# backend
cd backend
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export OLLAMA_BASE_URL=http://localhost:11434 CHROMA_HOST=localhost CHROMA_PORT=8001
export DATABASE_URL="sqlite:///./data/novacare.db"
python ../scripts/seed.py
uvicorn app.main:app --reload --port 8000

# voice (new terminal)
cd voice
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export BACKEND_URL=http://localhost:8000 WHISPER_MODEL=base
uvicorn server:app --reload --port 8080

# frontend (new terminal)
cd frontend
cp .env.local.example .env.local
npm install && npm run dev
```

### Test commands

```bash
# core logic (no Ollama needed)
cd backend && python -m pytest -q tests/test_store_service.py tests/test_api.py

# RAG retrieval (needs sentence-transformers + chromadb)
python -m pytest -q tests/test_rag.py

# full agent smoke (needs Ollama + model)
RUN_AGENT_SMOKE=1 python -m pytest -q tests/test_agent_smoke.py

# whole-stack smoke against a running deployment
python scripts/smoke_test.py
```

---

## Voice setup

- **Full-duplex**: Pipecat `SmallWebRTCTransport` + `WhisperSTTService` + `KokoroTTSService`.
  Signaling endpoint: `POST {VOICE_URL}/api/voice/offer`.
- **Push-to-talk fallback** (always available): `POST {VOICE_URL}/api/voice/ptt` takes one
  audio clip, returns `{ transcript, reply, audio_base64 }`. The browser uses this
  automatically if full-duplex can't initialise.
- Whisper size via `WHISPER_MODEL` = `tiny` | `base` | `small`. `tiny`/`base` are fine on
  CPU; `small` needs more RAM/CPU. Kokoro voice via `KOKORO_VOICE` (default `af_heart`).
- Slow inference shows "Processing voice…" — it never crashes the app.

### STUN / TURN

Set in `.env`:

```
WEBRTC_STUN_URL=stun:stun.l.google.com:19302
WEBRTC_TURN_URL=turn:your-host:3478
WEBRTC_TURN_USERNAME=novacare
WEBRTC_TURN_PASSWORD=...
```

These are served to the browser via `GET /api/config` and `GET /api/voice/config`.

Self-hosted TURN is bundled as an optional profile:

```bash
docker compose --profile turn up -d          # starts coturn (host networking)
# open UDP 3478 and 49152–49200 on the host firewall; set COTURN_EXTERNAL_IP in .env
```

TURN is **not** needed for local testing.

---

## Deployment

### Mode A — instant demo (Cloudflare Quick Tunnel)

Good for showing the demo from a laptop. Not for production.

```bash
docker compose up -d --build && bash scripts/init_models.sh
# expose the frontend
cloudflared tunnel --url http://localhost:3000
```

Cloudflare prints a `https://<random>.trycloudflare.com` URL. Because the frontend calls the
backend/voice from the **browser**, also tunnel those and rebuild the frontend with the
public URLs, or (simpler) put all three behind one hostname with a reverse proxy and set:

```
NEXT_PUBLIC_API_URL=https://<tunnel-host>/api-backend
NEXT_PUBLIC_VOICE_URL=https://<tunnel-host>/api-voice
```

The quickest single-URL option is Mode B's Caddy/nginx reverse proxy pointed at a tunnel.

### Mode B — stable deployment (VPS)

1. **Server**: a VPS with Docker + Compose, 2 vCPU / 8 GB RAM / 40 GB disk minimum.
2. **DNS**: `A` record `support.example.com → <VPS IP>` (or a named Cloudflare Tunnel).
3. **HTTPS**: put a reverse proxy (Caddy, nginx, Traefik, or `cloudflared`) in front:
   - `/` and `/_next` → `frontend:3000`
   - `/api` and `/health` and WebSocket `/api/conversations/*/ws` → `backend:8000`
   - `/voice` → `voice:8080` (strip prefix)
   Enable WebSocket upgrades on the proxy.
4. **Env**: in `.env` set
   ```
   ENVIRONMENT=production
   PUBLIC_APP_URL=https://support.example.com
   NEXT_PUBLIC_API_URL=https://support.example.com
   NEXT_PUBLIC_VOICE_URL=https://support.example.com/voice
   CORS_ALLOW_ORIGINS=https://support.example.com
   ```
   Rebuild the frontend image so the `NEXT_PUBLIC_*` values are baked in:
   `docker compose build frontend && docker compose up -d`.
5. **Persistent storage**: named volumes `sqlite_data`, `chroma_data`, `ollama_models`,
   `models_cache` persist across restarts. Back up `sqlite_data`.
6. **Firewall**: expose only 80/443. If self-hosting TURN, also open UDP 3478 and the relay
   range (49152–49200) and set `COTURN_EXTERNAL_IP`.
7. **WebRTC**: browsers require HTTPS for microphone access — terminate TLS at the proxy.
   Behind strict NATs, configure TURN (above).

Secrets live only in `.env` (git-ignored). Never commit real credentials.

---

## Return & warranty policy (demo)

- Fixed reference date `DEMO_DATE=2026-09-03`.
- Standard return window: **14 days after delivery**; order must be `delivered`.
  - `NS-1042` delivered 2026-08-26 → **eligible** (8 days).
  - `NS-1033` delivered 2026-08-10 → **not eligible** (24 days); warranty may still apply.
- Warranty: 12 months standard, 6 months for NovaCharge. Warranty claims create a
  **support ticket**, not an automatic replacement.
- A return only ever creates a `RET-XXXX` record. Refund lifecycle:
  `REQUESTED → APPROVED → ITEM_RECEIVED → REFUND_PROCESSING → REFUNDED`. No real money moves.

## Demo scenarios / recommended prompts

1. `Where is order NS-1077?`
2. `Why is NS-1089 delayed?`
3. `Can I return NS-1042?`  → then approve the return → a real `RET-XXXX` is created
4. `Can I return NS-1033?`  → correctly denied, warranty offered
5. `My NovaPods Pro keep disconnecting.` → `NS-1042` → RAG troubleshooting → `I already tried all of that` → offer + create a ticket
6. `Recommend headphones under Rs 7,000 with ANC.` → NovaPods Lite
7. `Recommend a keyboard under Rs 8,000.` → NovaKeys Mechanical
8. `I want to speak to a human.` → immediate escalation (no confirmation)

The same flows work from the **Call AI Support** voice interface.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `/health` shows `model_available: false` | `docker compose exec ollama ollama pull qwen3:4b` |
| Agent replies "trouble reaching the support system" | Ollama not up / wrong `OLLAMA_BASE_URL` |
| Empty product list on the site | backend not reachable at `NEXT_PUBLIC_API_URL`; check CORS |
| Voice says "full-duplex unavailable" | expected on some networks — push-to-talk still works; configure TURN for full-duplex |
| Mic permission blocked | browser site settings → allow microphone; HTTPS required off-localhost |
| Chroma errors on boot | wait for `chroma` healthcheck; index builds lazily on first KB search |
| RAG returns nothing | `docker compose exec backend python -c "from app.rag import get_rag; print(get_rag().reindex(force=True))"` |
| Slow first voice turn | Whisper/Kokoro weights download on first use; subsequent turns are fast |

## Known limitations

- Chat replies stream at the message level (agent **activity** streams live during the turn);
  token-by-token streaming is not wired through LangGraph here.
- Full-duplex voice depends on Pipecat/aiortc versions and network NAT; push-to-talk is the
  guaranteed path and is what the acceptance flow uses.
- Human-in-the-loop is enforced at the tool boundary (write tools register a pending action
  the API must approve) rather than via LangGraph checkpoint interrupts.
- `qwen3:4b` is small; occasionally it needs a nudge to pick the right tool. Larger models
  via `OLLAMA_MODEL` improve reliability.
- Single-node SQLite + in-process event bus — fine for a demo, not for horizontal scaling.
- No auth: the dashboard and all APIs are open (clearly labelled demo data).

## Project layout

```
novacare-ai/
├─ frontend/        Next.js app (pages, chat, voice, dashboard, agent-activity, lib, hooks)
├─ backend/
│  └─ app/
│     ├─ api/       REST + WebSocket routes
│     ├─ agent/     LangGraph graph, prompts, context, tools/
│     ├─ models/    SQLAlchemy entities
│     ├─ database/  session, seed, seed_data
│     ├─ rag/       Chroma + local embeddings store
│     ├─ services/  store_service (business logic), ollama, conversation_service
│     ├─ schemas/   Pydantic (API + tool argument validation)
│     └─ events/    observable agent-activity event bus
├─ voice/           Pipecat bot + FastAPI signaling + push-to-talk (STT/TTS)
├─ knowledge/       14 Markdown docs for RAG
├─ scripts/         seed.py, init_models.sh, smoke_test.py, tasks.ps1
├─ docker/          Dockerfiles + coturn config
├─ docker-compose.yml
├─ .env.example
└─ Makefile
```
