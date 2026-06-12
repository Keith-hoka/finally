"""LLM client: Cerebras inference via LiteLLM and OpenRouter, with mock mode."""

from __future__ import annotations

import asyncio
import os
from typing import Literal

from litellm import completion
from pydantic import BaseModel, Field

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}


class ChatUnavailableError(RuntimeError):
    """Chat cannot run: no API key and mock mode is off."""


class TradeAction(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float


class WatchlistAction(BaseModel):
    ticker: str
    action: Literal["add", "remove"]


class AssistantReply(BaseModel):
    """Structured output the LLM must produce for every chat turn."""

    message: str
    trades: list[TradeAction] = Field(default_factory=list)
    watchlist_changes: list[WatchlistAction] = Field(default_factory=list)


def mock_enabled() -> bool:
    return os.environ.get("LLM_MOCK", "").strip().lower() == "true"


async def get_reply(messages: list[dict]) -> AssistantReply:
    """Get a structured assistant reply, from the mock or the real LLM."""
    if mock_enabled():
        return _mock_reply(messages[-1]["content"])

    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        raise ChatUnavailableError(
            "Chat is unavailable: OPENROUTER_API_KEY is not set"
        )

    response = await asyncio.to_thread(
        completion,
        model=MODEL,
        messages=messages,
        response_format=AssistantReply,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
    )
    return AssistantReply.model_validate_json(response.choices[0].message.content)


def _mock_reply(user_message: str) -> AssistantReply:
    """Deterministic responses for E2E tests and key-less development.

    Contract: 'buy' triggers a 1-share AAPL buy, 'sell' a 1-share AAPL sell,
    'watch' adds PYPL to the watchlist. Anything else echoes the message.
    """
    text = user_message.lower()
    if "buy" in text:
        return AssistantReply(
            message="Mock: buying 1 share of AAPL.",
            trades=[TradeAction(ticker="AAPL", side="buy", quantity=1)],
        )
    if "sell" in text:
        return AssistantReply(
            message="Mock: selling 1 share of AAPL.",
            trades=[TradeAction(ticker="AAPL", side="sell", quantity=1)],
        )
    if "watch" in text:
        return AssistantReply(
            message="Mock: adding PYPL to the watchlist.",
            watchlist_changes=[WatchlistAction(ticker="PYPL", action="add")],
        )
    return AssistantReply(message=f"Mock response to: {user_message}")
