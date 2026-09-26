"""Thin HTTP client to the NovaCare backend agent — keeps ONE agent for chat + voice."""
from __future__ import annotations

import re

import httpx

from config import config


class AgentClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or config.backend_url).rstrip("/")

    async def ensure_conversation(self, conversation_id: str | None) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            if conversation_id:
                r = await client.get(f"{self.base_url}/api/conversations/{conversation_id}")
                if r.status_code == 200:
                    return conversation_id
            r = await client.post(
                f"{self.base_url}/api/conversations", json={"channel": "voice"}
            )
            r.raise_for_status()
            return r.json()["id"]

    async def send_message(self, conversation_id: str, text: str) -> dict:
        async with httpx.AsyncClient(timeout=config_timeout()) as client:
            r = await client.post(
                f"{self.base_url}/api/conversations/{conversation_id}/message",
                json={"content": text, "channel": "voice"},
            )
            r.raise_for_status()
            return r.json()


def config_timeout() -> float:
    return 180.0


agent_client = AgentClient()


_YES = re.compile(
    r"\b(yes|yeah|yep|yup|sure|ok|okay|confirm|confirmed|go ahead|do it|please do|correct|proceed"
    r"|ho|huncha|hunchha|garnus)\b"
    r"|हो(?!इन)|हुन्छ|ठीक छ|ठिक छ|(?<!न)गर्नुस्|(?<!न)गरिदिनुस्|अगाडि बढ|पक्का",
    re.I,
)
_NO = re.compile(
    r"\b(no|nope|nah|cancel|don'?t|do not|stop|never ?mind|decline|reject|hoina|chaina|nagarnus)\b"
    r"|होइन|छैन|नगर्नुस्|नगर|रद्द|हुँदैन|हुदैन",
    re.I,
)
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")

# Fixed phrases for the confirmation flow, in the language the customer just spoke.
_T = {
    "ne": {
        "ask": "माफ गर्नुहोला, मैले राम्ररी बुझिनँ। म यो गरिदिऊँ कि नगरूँ?",
        "confirm": " म यो गरिदिऊँ? हुन्छ भने 'हुन्छ' भन्नुहोला, नत्र 'हुँदैन' भन्नुहोला।",
        "rejected": "हुन्छ, म यो गर्दिनँ। अरू केही सहयोग चाहियो भने भन्नुहोला।",
        "done": "भयो! तपाईंको अनुरोध दर्ता भयो, नम्बर {id} हो।",
        "failed": "माफ गर्नुहोला, अहिले यो काम पूरा गर्न सकिएन।",
    },
    "en": {
        "ask": "Sorry, I need a clear yes or no. Shall I go ahead?",
        "confirm": " Shall I go ahead? Say yes to confirm, or no to cancel.",
    },
}


def speakable(text: str) -> str:
    """Strip markdown and list markers so TTS doesn't read "*", "#" or a lone "१." aloud."""
    text = re.sub(r"(?m)^\s*(?:[-•*]|[0-9०-९]+[.)])\s+", "", text)
    return re.sub(r"[*_`#>]+", "", text).strip()


async def voice_turn(conversation_id: str, text: str) -> dict:
    """One spoken turn. If an action awaits approval, 'yes'/'no' resolves it; else it goes to the agent.

    Returns {"reply": display text, "spoken": text for TTS, "pending_action": dict | None}.
    """
    c = agent_client
    ne = bool(_DEVANAGARI.search(text))
    async with httpx.AsyncClient(timeout=config_timeout()) as client:
        base = f"{c.base_url}/api/conversations/{conversation_id}"
        conv = (await client.get(base)).json()
        if conv.get("pending_action"):
            yes, no = bool(_YES.search(text)), bool(_NO.search(text))
            if yes != no:  # exactly one matched
                r = await client.post(f"{base}/{'approve' if yes else 'reject'}", json={})
                r.raise_for_status()
                body = r.json()
                reply = body.get("reply", "")
                if ne:  # backend confirmation text is English; say it in Nepali
                    res = body.get("result") or {}
                    obj = res.get("ticket") or res.get("return") or {}
                    reply = (_T["ne"]["rejected"] if not yes else
                             _T["ne"]["done"].format(id=obj.get("id", "")) if body.get("ok") else _T["ne"]["failed"])
                return {"reply": reply, "spoken": speakable(reply), "pending_action": None}
            ask = _T["ne" if ne else "en"]["ask"]
            return {"reply": ask, "spoken": ask, "pending_action": conv["pending_action"]}

    data = await c.send_message(conversation_id, text)
    reply, pending = data.get("reply", ""), data.get("pending_action")
    spoken = speakable(reply)
    if pending:  # follow the language of the agent's own reply
        spoken += _T["ne" if _DEVANAGARI.search(reply) or ne else "en"]["confirm"]
    return {"reply": reply, "spoken": spoken, "pending_action": pending}
