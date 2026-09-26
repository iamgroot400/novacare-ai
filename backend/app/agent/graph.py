"""LangGraph agent construction (Groq + tools, ReAct style)."""
from __future__ import annotations

import re
from functools import lru_cache

from langchain_groq import ChatGroq
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


def _groq(model: str) -> ChatGroq:
    extra = {"reasoning_effort": settings.groq_reasoning_effort} if settings.groq_reasoning_effort else {}
    return ChatGroq(model=model, api_key=settings.groq_api_key or None, temperature=0.2,
                    max_tokens=settings.groq_max_tokens, max_retries=1, **extra)


def _build_llm():
    # Groq's free tier caps each model at 200k tokens/day; once the main model is out, every
    # turn failed instantly. Each model has its own quota, so retry the turn on the fallback.
    llm = _groq(settings.groq_model)
    if settings.groq_fallback_model:
        from groq import RateLimitError

        llm = llm.with_fallbacks([_groq(settings.groq_fallback_model)],
                                 exceptions_to_handle=(RateLimitError,))
    return llm


@lru_cache
def get_agent():
    llm = _build_llm()
    tools = build_tools()
    try:
        return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    except TypeError:
        # older langgraph used `state_modifier`
        return create_react_agent(llm, tools, state_modifier=SYSTEM_PROMPT)
