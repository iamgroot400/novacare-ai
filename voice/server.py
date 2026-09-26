"""NovaCare voice service.

Endpoints:
  GET  /health
  GET  /api/voice/config           -> ICE servers, capabilities
  POST /api/voice/offer            -> SmallWebRTC signaling (full-duplex, if available)
  POST /api/voice/ptt              -> push-to-talk fallback (always works):
                                      multipart audio -> STT -> agent -> TTS wav
  POST /api/voice/call             -> ring a phone via Twilio (see phone.py)
"""
from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from agent_client import AgentClient, voice_turn
from config import config
from phone import router as phone_router

logging.basicConfig(level="INFO")
log = logging.getLogger("novacare.voice")

app = FastAPI(title="NovaCare Voice", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(phone_router)

agent_client = AgentClient()
_pcs: dict[str, object] = {}

try:
    import bot as bot_module

    PIPECAT = bot_module.PIPECAT_AVAILABLE
except Exception as exc:  # noqa: BLE001
    log.warning("bot module import failed: %s", exc)
    bot_module = None
    PIPECAT = False


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "full_duplex": PIPECAT,
        "stt_model": config.groq_stt_model,
        "tts_model": config.groq_tts_model,
        "backend_url": config.backend_url,
    }


@app.get("/api/voice/config")
async def voice_config():
    return {
        "ice_servers": config.ice_servers,
        "full_duplex": PIPECAT,
        "ptt_fallback": True,
        "max_utterance_seconds": config.max_utterance_seconds,
    }


@app.post("/api/voice/offer")
async def offer(payload: dict):
    """SmallWebRTC offer/answer. Body: {sdp, type, conversation_id, pc_id?}."""
    if not PIPECAT:
        raise HTTPException(503, "Full-duplex voice is unavailable in this deployment; use push-to-talk.")

    from pipecat.transports.network.small_webrtc import SmallWebRTCConnection

    sdp = payload.get("sdp")
    sdp_type = payload.get("type", "offer")
    conversation_id = payload.get("conversation_id")
    pc_id = payload.get("pc_id")
    if not sdp:
        raise HTTPException(400, "Missing sdp")

    conversation_id = await agent_client.ensure_conversation(conversation_id)

    if pc_id and pc_id in _pcs:
        conn = _pcs[pc_id]
        await conn.renegotiate(sdp=sdp, type=sdp_type)
    else:
        conn = SmallWebRTCConnection(ice_servers=config.ice_servers)
        await conn.initialize(sdp=sdp, type=sdp_type)
        pc_id = str(uuid.uuid4())
        _pcs[pc_id] = conn

        @conn.event_handler("closed")
        async def _closed(_c):  # noqa: ANN001
            _pcs.pop(pc_id, None)

        async def _on_event(evt: dict) -> None:
            log.info("voice event: %s", evt)

        asyncio.create_task(bot_module.run_bot(conn, conversation_id, on_event=_on_event))

    answer = conn.get_answer()
    return JSONResponse({**answer, "pc_id": pc_id, "conversation_id": conversation_id})


@app.post("/api/voice/ptt")
async def push_to_talk(
    audio: UploadFile = File(...),
    conversation_id: str = Form(""),
):
    """Reliable fallback: one audio clip in, transcript + spoken reply out."""
    import stt as stt_module
    import tts as tts_module

    data = await audio.read()
    if not data:
        raise HTTPException(400, "Empty audio")
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, "Audio too large")

    conversation_id = await agent_client.ensure_conversation(conversation_id or None)

    try:
        transcript = await asyncio.to_thread(stt_module.transcribe_file, data)
    except Exception as exc:  # noqa: BLE001
        log.exception("STT failed")
        raise HTTPException(500, f"Speech recognition failed: {exc}")

    if not transcript.strip():
        return JSONResponse({
            "conversation_id": conversation_id,
            "transcript": "",
            "reply": "I didn't catch that — could you say it again?",
            "audio_base64": None,
            "pending_action": None,
        })

    turn = await voice_turn(conversation_id, transcript)
    reply, pending, spoken = turn["reply"], turn["pending_action"], turn["spoken"]

    try:
        wav = await asyncio.to_thread(tts_module.synthesize_wav, spoken)
        import base64

        audio_b64 = base64.b64encode(wav).decode("ascii")
    except Exception as exc:  # noqa: BLE001
        log.exception("TTS failed")
        audio_b64 = None

    return JSONResponse({
        "conversation_id": conversation_id,
        "transcript": transcript,
        "reply": reply,
        "pending_action": pending,
        "audio_base64": audio_b64,
        "audio_mime": "audio/wav",
    })


@app.on_event("startup")
async def _warm_tts():
    if bot_module:  # background: ~10-20s of TTS calls, must not delay startup
        asyncio.create_task(asyncio.to_thread(bot_module.warm_tts))


@app.on_event("shutdown")
async def _shutdown():
    for conn in list(_pcs.values()):
        try:
            await conn.close()
        except Exception:  # noqa: BLE001
            pass
