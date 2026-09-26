# NovaCare AI

An **agentic, voice-first** AI customer-support agent for **NovaStore**, a fictional
Nepal-based electronics store. NovaCare doesn't just generate text: it looks up real
orders, searches policy documents, checks return eligibility, creates tickets and returns
(after you say yes), troubleshoots devices and escalates to a human. It speaks **natural
Nepali and English**, over a **full-duplex browser call** or a **real phone call**.

> NovaStore is fictional. No real products, customers, orders or payments exist. Refund
> lifecycles are simulated and never touch a real payment system.

It runs on **Groq's free tier**: the LLM, speech-to-text and (English) text-to-speech are
hosted, so the server only runs FastAPI, Pipecat, SQLite and a small ONNX embedding
model. The three containers use about 430 MB of RAM at idle, so a 1 GB cloud VM with swap
is enough for a demo (not load-tested).

---

## Architecture

```
      Caller (browser mic over a WebSocket, or phone via Twilio)
                            │
            Silero VAD (turn detection + barge-in, Pipecat)
                            │
     Groq Whisper large-v3 STT  (Nepali-primed; Hindi mislabels retried as Nepali)
                            │
                  ┌─────────▼──────────┐
                  │  LangGraph agent   │   ONE agent for chat, browser voice and phone
                  │ (backend, FastAPI) │
                  └───┬────────────┬───┘
                      ▼            ▼
      Groq openai/gpt-oss-120b     Tools (Pydantic-validated)
                                   ├─ RAG: ChromaDB (embedded) + ONNX MiniLM embeddings
                                   └─ DB:  SQLite (orders / products / customers /
                                           tickets / returns / conversations / events)
                            │
          reply text, spoken sentence by sentence (filler if a turn is slow)
                            │
     TTS per sentence:  English  Groq → Edge neural → Piper
                        Nepali   Edge neural (ne-NP) → Piper (ne_NP)
                            │
                  audio ──► browser / phone
```

Observable **agent activity** (tool calls, KB searches, DB reads/writes, confirmation
requests) is streamed to the UI as structured backend events, **never** chain-of-thought.

## Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS · mobile-first |
| Backend | Python · FastAPI · SQLAlchemy · SQLite |
| Agent | LangGraph (ReAct) · `langchain-groq` |
| LLM | Groq `openai/gpt-oss-120b` (override with `GROQ_MODEL`) |
| RAG | ChromaDB (embedded) · ONNX `all-MiniLM-L6-v2` baked into the image |
| Speech-to-text | Groq `whisper-large-v3` |
| Text-to-speech | Groq (English), Microsoft Edge neural voices, Piper (offline fallback) |
| Voice transport | Pipecat 0.0.62 · WebSocket PCM (browser) · Twilio Media Streams (phone) |
| Deploy | Docker Compose (frontend, backend, voice; optional cloudflared) |

## Features

- **Voice-only support page** (`/support`): a real call, like a phone. It listens all the
  time, answers when you stop talking, and stops talking the moment you speak over it.
  Live captions; push-to-talk is only a fallback if the call can't connect.
- **Nepali and English**, detected per turn. Devanagari or romanized Nepali
  ("mero order kaha cha") gets a reply in spoken-style Nepali, never Hindi.
- **Spoken confirmations.** Write actions ask "म यो गरिदिऊँ?" / "Shall I go ahead?" and
  accept हुन्छ / हो / yes or हुँदैन / होइन / no. Unclear answers are asked again.
- **Phone calls.** The agent rings a mobile number and greets the caller in both languages.
- **No dead air.** If a turn takes more than 1.2 s (tools running), the caller hears
  "एकछिन पर्खनुहोला, म हेर्दैछु।". Fixed phrases are synthesized once at startup.
- Real tools: `search_knowledge_base`, `search_products`, `get_product`, `get_order`,
  `get_customer`, `check_return_eligibility`, `create_return_request`,
  `create_support_ticket`, `get_ticket`, `escalate_to_human`.
- Read actions run automatically; **write actions need the customer's confirmation**.
- Return eligibility against a fixed demo date (`2026-09-03`) and a 14-day rule.
- RAG-grounded troubleshooting from 14 Markdown knowledge docs.
- Product catalogue (22 Nova products), order tracking, admin **Demo Analytics** dashboard.

## Requirements

- Docker + Docker Compose v2
- A free Groq API key from [console.groq.com/keys](https://console.groq.com/keys)
- About 5 GB disk for the images (voice 3.2 GB, backend 1.6 GB, frontend 0.3 GB).
- For local (non-Docker) dev: Python 3.11, Node 20 and ffmpeg

---

## Quick start (Docker)

```bash
git clone https://github.com/iamgroot400/novacare-ai && cd novacare-ai
cp .env.example .env          # then set GROQ_API_KEY
docker compose up -d --build
```

Open **http://localhost:3000/support** and allow the microphone. Browsers only allow the
mic on `localhost` or HTTPS.

The database seeds itself on first boot and the RAG index builds on the first knowledge
search.

### Exact commands

| Purpose | Command |
| --- | --- |
| Start the stack | `docker compose up -d --build` |
| Seed / re-seed DB | `docker compose exec backend python /app/scripts/seed.py` |
| Rebuild RAG index | `bash scripts/init_models.sh` |
| Backend tests | `docker compose exec backend sh -c "pip install -q pytest pytest-asyncio && python -m pytest -q"` |
| Voice tests | `docker compose exec voice sh -c "pip install -q pytest && python -m pytest -q"` |
| Nepali fluency check | `pip install httpx && python scripts/nepali_check.py` (on the host, stack running) |
| End-to-end smoke | `python scripts/smoke_test.py` |
| Logs | `docker compose logs -f` |
| Stop | `docker compose down` |
| Wipe everything | `docker compose down -v` |

### Windows

`make` isn't required. Use `./scripts/tasks.ps1 <task>` (`env`, `setup`, `up`, `models`,
`seed`, `test`, `smoke`, `down`, `clean`) or the `docker compose` commands above.

---

## Configuration

All settings live in `.env` (copy `.env.example`). Only `GROQ_API_KEY` is required.

| Variable | Default | What it does |
| --- | --- | --- |
| `GROQ_API_KEY` | (none) | Required. Used for the LLM, speech-to-text and English TTS. |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Chat model. It had the most natural Nepali of the Groq models tested. |
| `GROQ_FALLBACK_MODEL` | `openai/gpt-oss-20b` | Used automatically when `GROQ_MODEL` hits a rate limit (each model has its own daily quota). |
| `GROQ_REASONING_EFFORT` | `low` | `low`/`medium`/`high` for gpt-oss; `none`/`default` for qwen; empty = not sent. |
| `GROQ_STT_MODEL` | `whisper-large-v3` | Better on Nepali than `-turbo`. |
| `STT_LANGUAGE` | empty | Empty auto-detects; `ne` or `en` pins the language. |
| `GROQ_TTS_MODEL` / `GROQ_TTS_VOICE` | `canopylabs/orpheus-v1-english` / `autumn` | English voice. Groq requires accepting this model's terms in its console first; until then Edge is used. |
| `EDGE_VOICE_NE` | `ne-NP-HemkalaNeural` | Nepali voice (female). `ne-NP-SagarNeural` is male. |
| `EDGE_VOICE_EN` | `en-US-AriaNeural` | English fallback voice. |
| `VAD_STOP_SECS` | `0.6` | Silence before the agent replies. Lower is snappier; higher cuts people off less. |
| `FILLER_AFTER_SECS` | `1.2` | How long before a slow turn gets a filler phrase. |

## Nepali

- **Understanding.** Whisper is given a Nepali and store-vocabulary prompt. Whisper often
  labels Nepali as Hindi (same script), so those clips are transcribed again as Nepali.
- **Speaking.** The prompt asks for spoken call-centre Nepali ("हजुर", "भन्नुहोला",
  "रिटर्न गर्ने समय सकियो"), bans Hindi forms, keeps common loanwords (अर्डर, डेलिभरी,
  रिटर्न, वारेन्टी) and says dates as "४ सेप्टेम्बर".
- **Voices.** Each sentence is routed by script, so mixed replies switch voices mid-reply.
- **Checking it.** `scripts/nepali_check.py` runs 10 Nepali and romanized-Nepali turns
  against a running backend. It flags non-Devanagari replies, Hindi words, lists or
  markdown, the "फिर्टा" misspelling, mentions of on-screen buttons, and replies too long
  to say on a call. Read the output too: it catches common failures, not awkward phrasing.

## Phone calls (Twilio)

The agent can ring a real phone and talk as support.

1. **Twilio account.** A trial account works. Buy a number, verify the mobile you'll call,
   and enable the destination country (e.g. Nepal +977) under Voice → Geo permissions.
   Trial accounts only call verified numbers and play a short trial notice first.
2. **`.env`.** Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, and
   `CALL_API_TOKEN` (any long random string).
3. **Public URL.** Twilio must reach the voice service. On a laptop, start the bundled
   Cloudflare quick tunnel; the voice service discovers its URL automatically:
   ```bash
   docker compose --profile phone up -d
   ```
   On a server, set `PUBLIC_VOICE_URL=https://your-domain/voice` instead.
4. **Ring a phone.**
   ```bash
   curl -X POST localhost:8080/api/voice/call \
     -H "Content-Type: application/json" -H "X-Call-Token: $CALL_API_TOKEN" \
     -d '{"to":"+9779812345678"}'
   ```

Security: placing a call needs `CALL_API_TOKEN`. Twilio's webhook is verified with Twilio's
request signature, and the audio websocket only accepts streams carrying a per-process
secret, so visitors to the tunnel can't open a stream and use up your Groq quota.

Phone audio is 8 kHz, so recognition (especially Nepali) is a bit weaker than in the browser.
Twilio bills calls per minute; check its pricing for your destination.

## Free-tier limits

Groq's free tier allows **8,000 tokens per minute**, **200,000 tokens per day** and
**1,000 requests per day** per model. When the main model runs out, turns fall back to
`GROQ_FALLBACK_MODEL`, which has its own quota.
A reply without tools uses about 1,300 tokens and one with a tool call about 3,000, so a
busy call can hit the per-minute limit. The client then waits and retries, and the caller hears the
filler phrase. The prompt, history (10 messages) and knowledge-base results (3 passages)
are kept small for this reason. Groq's paid Dev tier removes the wait.

## Local development (without Docker)

```bash
# backend
cd backend
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export GROQ_API_KEY=... DATABASE_URL="sqlite:///./data/novacare.db"
python ../scripts/seed.py
uvicorn app.main:app --reload --port 8000

# voice (new terminal; needs ffmpeg on PATH)
cd voice
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-pipecat.txt
python -m piper.download_voices en_US-lessac-low ne_NP-google-medium --data-dir ./piper
export GROQ_API_KEY=... BACKEND_URL=http://localhost:8000 PIPER_DIR=./piper
uvicorn server:app --reload --port 8080

# frontend (new terminal)
cd frontend
cp .env.local.example .env.local
npm install && npm run dev
```

---

## Voice setup

- **Full duplex:** `WS {VOICE_URL}/api/voice/ws`. The browser streams 16 kHz PCM from the
  mic continuously (an AudioWorklet in `frontend/components/voice/duplex.ts`); Silero VAD on
  the server decides when you've finished (`VAD_STOP_SECS`) and sends `0x02` to stop playback
  the moment you talk over the bot. Bot audio comes back as `0x01` + 24 kHz PCM. It's plain
  HTTPS/WSS, so it works on any network with no UDP ports, STUN or TURN.
- **Push-to-talk fallback:** `POST {VOICE_URL}/api/voice/ptt` takes one audio clip and
  returns `{ transcript, reply, audio_base64 }`. Used only if the call can't connect.
- **Phone:** `POST /api/voice/call`, `POST /api/voice/twilio/twiml`,
  `WS /api/voice/twilio/ws` (see [Phone calls](#phone-calls-twilio)).
- **Echo:** the browser's echo cancellation keeps the bot from hearing itself on speakers;
  headphones make barge-in the most reliable.

---

## Deployment

### Small cloud VM (e.g. AWS EC2 free tier)

Because all models are hosted, the stack is sized for a 1 vCPU / 1 GB VM:

1. Install Docker + Compose and add swap (2 GB recommended):
   `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
2. Put a reverse proxy with HTTPS in front (Caddy, nginx or `cloudflared`). Browsers need
   HTTPS for the microphone.
   - `/` and `/_next` → `frontend:3000`
   - `/api`, `/health` and WebSocket `/api/conversations/*/ws` → `backend:8000`
   - `/voice` → `voice:8080` (strip prefix; enable WebSocket upgrades)
3. In `.env` set:
   ```
   ENVIRONMENT=production
   PUBLIC_APP_URL=https://support.example.com
   NEXT_PUBLIC_API_URL=https://support.example.com
   NEXT_PUBLIC_VOICE_URL=https://support.example.com/voice
   PUBLIC_VOICE_URL=https://support.example.com/voice
   CORS_ALLOW_ORIGINS=https://support.example.com
   ```
   Rebuild the frontend so `NEXT_PUBLIC_*` values are baked in:
   `docker compose build frontend && docker compose up -d`.
4. Security group / firewall: expose 80/443 only. Calls are websockets over 443.
5. Named volumes `sqlite_data` and `models_cache` persist across restarts. Back up `sqlite_data`.

Secrets live only in `.env` (git-ignored). Never commit real credentials.

### Instant demo from a laptop

```bash
docker compose up -d --build
cloudflared tunnel --url http://localhost:3000
```

The frontend calls the backend and voice services from the browser, so either tunnel
those too or put all three behind one hostname with a reverse proxy (as above).

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

## Demo scenarios

English:

1. `Where is order NS-1077?`
2. `Why is NS-1089 delayed?`
3. `Can I return NS-1042?`, then say "yes" → a real `RET-XXXX` is created
4. `Can I return NS-1033?` → correctly denied, warranty offered
5. `My NovaPods Pro keep disconnecting.` → `NS-1042` → RAG troubleshooting → `I already tried all of that` → a ticket is offered
6. `Recommend headphones under Rs 7,000 with noise cancelling.` → NovaPods Lite
7. `Recommend a keyboard under Rs 8,000.` → NovaKeys Mechanical
8. `I want to speak to a human.` → immediate escalation (no confirmation)

Nepali:

1. `मेरो अर्डर NS-1077 कहाँ पुग्यो?`
2. `mero order NS-1042 return garna milcha?`, then `हुन्छ` to confirm or `हुँदैन` to cancel
3. `NS-1033 रिटर्न गर्न मिल्छ?`
4. `मेरो NovaPods Pro बारम्बार डिस्कनेक्ट हुन्छ`
5. `सात हजार भित्रको noise cancelling हेडफोन सुझाव दिनुहोस्`
6. `मलाई मान्छेसँग कुरा गर्नु छ`

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `docker compose` says `GROQ_API_KEY` is missing | Set it in `.env` |
| Every reply is "Sorry, I ran into a problem" | Check `docker compose logs backend`: a 401 means a bad key, a 404 means `GROQ_MODEL` isn't available to your key |
| Replies take 10–30 s | Free-tier rate limit (see [Free-tier limits](#free-tier-limits)) |
| English voice sounds robotic, logs show `Groq TTS failed ... 400` | Accept the `GROQ_TTS_MODEL` terms in the Groq console; Edge/Piper are used meanwhile |
| Call shows push-to-talk instead of a live call | The `/voice/api/voice/ws` websocket didn't connect: check `docker compose logs voice` and that your proxy passes websockets |
| The bot cuts itself off or answers itself | It's hearing its own voice from the speakers: use headphones, or raise `VAD_STOP_SECS` |
| Mic permission blocked | Browser site settings → allow microphone; HTTPS required off-localhost |
| Phone call never connects | Check the tunnel is up (`docker compose --profile phone ps`), the number is verified, and geo permissions allow the country |
| RAG returns nothing | `bash scripts/init_models.sh` |
| Empty product list on the site | Backend not reachable at `NEXT_PUBLIC_API_URL`; check CORS |

## Known limitations

- Free-tier Groq rate limits make multi-tool turns slow under load (the filler phrase covers the gap).
- The phone path is implemented and unit-tested (Twilio signature check, pipeline setup)
  but has not yet been tried end to end with a live Twilio call.
- Edge neural voices come from an unofficial Microsoft endpoint and could stop working;
  Piper is the offline fallback.
- Nepali is good but not perfect: occasional written-style phrasing, and troubleshooting
  sometimes packs more than two steps into one reply.
- Human-in-the-loop is enforced at the tool boundary (write tools register a pending action
  the API must approve) rather than via LangGraph checkpoint interrupts.
- Single-node SQLite + in-process event bus: fine for a demo, not for horizontal scaling.
- No auth: the dashboard and all APIs are open (clearly labelled demo data). Only placing
  phone calls is token-protected.

## Project layout

```
novacare-ai/
├─ frontend/        Next.js app (/support voice call page, chat, dashboard, agent activity)
├─ backend/
│  └─ app/
│     ├─ api/       REST + WebSocket routes
│     ├─ agent/     LangGraph graph, prompts, context, tools/
│     ├─ models/    SQLAlchemy entities
│     ├─ database/  session, seed, seed_data
│     ├─ rag/       Chroma + ONNX embeddings store
│     ├─ services/  store_service (business logic), LLM health, conversation_service
│     ├─ schemas/   Pydantic (API + tool argument validation)
│     └─ events/    observable agent-activity event bus
├─ voice/
│  ├─ bot.py        Pipecat pipelines (browser websocket + phone), fillers, greeting
│  ├─ stt.py        Groq Whisper with Nepali handling
│  ├─ tts.py        per-sentence Nepali/English TTS with fallbacks + phrase cache
│  ├─ agent_client.py  backend client + spoken yes/no confirmations
│  ├─ phone.py      Twilio outbound calls, TwiML, media-stream websocket
│  └─ server.py     FastAPI: call websocket, push-to-talk, phone routes
├─ knowledge/       14 Markdown docs for RAG
├─ scripts/         seed.py, init_models.sh, smoke_test.py, nepali_check.py, tasks.ps1
├─ docker/          Dockerfiles
├─ docker-compose.yml
├─ .env.example
└─ Makefile
```
