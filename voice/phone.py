"""Phone calls via Twilio: outbound dialling, TwiML, and the media-stream websocket.

Twilio needs public HTTPS/WSS URLs. On a laptop the `cloudflared` compose service (profile
"phone") gives a random trycloudflare.com URL, discovered automatically from its metrics port.

Security: placing a call costs money, so POST /call requires CALL_API_TOKEN. The TwiML webhook
checks Twilio's request signature, and hands the websocket a per-process secret, so random
visitors to the tunnel can't open a (quota-burning) audio stream.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import re
import secrets
from xml.sax.saxutils import quoteattr

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, WebSocket
from fastapi.responses import Response

from agent_client import AgentClient
from config import config

log = logging.getLogger("novacare.voice.phone")
router = APIRouter(prefix="/api/voice")
_STREAM_SECRET = secrets.token_urlsafe(24)


async def public_url() -> str:
    if config.public_voice_url:
        return config.public_voice_url.rstrip("/")
    async with httpx.AsyncClient(timeout=5) as c:  # cloudflared quick tunnel
        host = (await c.get("http://cloudflared:2000/quicktunnel")).json().get("hostname")
    if not host:
        raise HTTPException(503, "No public URL: set PUBLIC_VOICE_URL or start the 'phone' profile")
    return f"https://{host}"


def twilio_signature_ok(url: str, params: dict, signature: str) -> bool:
    """Twilio request signing: base64(HMAC-SHA1(auth_token, url + sorted key+value pairs))."""
    payload = url + "".join(k + params[k] for k in sorted(params))
    digest = hmac.new(config.twilio_auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode(), signature)


@router.post("/call")
async def place_call(payload: dict, x_call_token: str = Header("")):
    """Ring a phone: {"to": "+97798XXXXXXXX"}. The agent greets when answered."""
    if not config.call_api_token or not hmac.compare_digest(x_call_token, config.call_api_token):
        raise HTTPException(403, "Bad or missing X-Call-Token")
    to = str(payload.get("to", "")).replace(" ", "")
    if not re.fullmatch(r"\+\d{8,15}", to):
        raise HTTPException(400, "'to' must be E.164, e.g. +9779812345678")
    sid = config.twilio_account_sid
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json",
            auth=(sid, config.twilio_auth_token),
            data={"To": to, "From": config.twilio_from_number,
                  "Url": f"{await public_url()}/api/voice/twilio/twiml"},
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.json().get("message", r.text))
    return {"call_sid": r.json()["sid"], "to": to, "status": r.json().get("status")}


@router.post("/twilio/twiml")
async def twiml(request: Request):
    """Called by Twilio for outbound calls (and inbound, if the number's webhook points here)."""
    form = {k: str(v) for k, v in (await request.form()).items()}
    base = await public_url()
    if not twilio_signature_ok(f"{base}/api/voice/twilio/twiml", form,
                               request.headers.get("x-twilio-signature", "")):
        raise HTTPException(403, "Invalid Twilio signature")
    ws_url = base.replace("https://", "wss://", 1) + "/api/voice/twilio/ws"
    xml = (f'<?xml version="1.0" encoding="UTF-8"?><Response><Connect><Stream url={quoteattr(ws_url)}>'
           f'<Parameter name="secret" value={quoteattr(_STREAM_SECRET)}/></Stream></Connect></Response>')
    return Response(xml, media_type="application/xml")


@router.websocket("/twilio/ws")
async def media_stream(ws: WebSocket):
    import bot

    await ws.accept()
    start = None
    for _ in range(5):  # Twilio sends "connected", then "start" (streamSid + our secret) before audio
        msg = await ws.receive_json()
        if msg.get("event") == "start":
            start = msg["start"]
            break
    secret = (start or {}).get("customParameters", {}).get("secret", "")
    if not start or not hmac.compare_digest(secret, _STREAM_SECRET):
        await ws.close(code=1008)
        return
    conversation_id = await AgentClient().ensure_conversation(None)
    log.info("phone call %s -> conversation %s", start.get("callSid"), conversation_id)
    await bot.run_phone_bot(ws, start["streamSid"], conversation_id)
