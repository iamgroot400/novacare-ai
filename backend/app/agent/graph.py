"""LangGraph agent construction (Ollama + tools, ReAct style)."""
from __future__ import annotations

import re
from functools import lru_cache

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import build_tools
from app.config import settings

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_reasoning(text: str) -> str:
    """Remove any model 'thinking' spans so they are never shown to a customer."""
    if not text:
        return ""
    text = _THINK_RE.sub("", text)
    text = re.sub(r"</?think>", "", text, flags=re.IGNORECASE)
    return text.strip()


def _build_llm() -> ChatOllama:
    common = dict(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.2,
        num_ctx=8192,
    )
    # `reasoning=` disables qwen3's thinking trace on newer langchain-ollama.
    try:
        return ChatOllama(**common, reasoning=False)
    except TypeError:
        return ChatOllama(**common)


@lru_cache
def get_agent():
    llm = _build_llm()
    tools = build_tools()
    try:
        return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    except TypeError:
        # older langgraph used `state_modifier`
        return create_react_agent(llm, tools, state_modifier=SYSTEM_PROMPT)
