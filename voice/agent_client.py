"""Thin HTTP client to the NovaCare backend agent — keeps ONE agent for chat + voice."""
from __future__ import annotations

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
