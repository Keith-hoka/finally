"""Tests for chat orchestration in mock mode and the unavailable path."""

import pytest

from app.db import DEFAULT_CASH
from app.services.chat import get_history, handle_message
from app.services.llm import ChatUnavailableError, get_reply
from app.services.portfolio import get_portfolio
from app.services.watchlist import watchlist_tickers

pytestmark = pytest.mark.usefixtures("temp_db")


@pytest.fixture
def mock_llm(monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")


async def test_buy_message_executes_trade(mock_llm, cache, source):
    cache.update("AAPL", 100.0)
    result = await handle_message(cache, source, "Please buy some AAPL")

    assert result["actions"]["trades"][0]["ticker"] == "AAPL"
    assert result["actions"]["trades"][0]["side"] == "buy"
    assert result["actions"]["errors"] == []
    portfolio = get_portfolio(cache)
    assert portfolio["positions"][0]["quantity"] == 1
    assert portfolio["cash_balance"] == DEFAULT_CASH - 100.0


async def test_failed_trade_reported_as_error(mock_llm, cache, source):
    cache.update("AAPL", 100.0)
    result = await handle_message(cache, source, "sell my AAPL shares")

    assert result["actions"]["trades"] == []
    assert "Insufficient shares" in result["actions"]["errors"][0]


async def test_watch_message_updates_watchlist(mock_llm, cache, source):
    result = await handle_message(cache, source, "watch paypal for me")

    assert result["actions"]["watchlist_changes"] == [
        {"ticker": "PYPL", "action": "add"}
    ]
    assert "PYPL" in watchlist_tickers()


async def test_turns_are_persisted_in_order(mock_llm, cache, source):
    await handle_message(cache, source, "hello there")
    await handle_message(cache, source, "how is my portfolio")

    history = get_history()
    assert [entry["role"] for entry in history] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert history[0]["content"] == "hello there"
    assert history[2]["content"] == "how is my portfolio"


async def test_history_limit(mock_llm, cache, source):
    for i in range(5):
        await handle_message(cache, source, f"message {i}")

    assert len(get_history(limit=4)) == 4


async def test_no_key_and_no_mock_is_unavailable(monkeypatch):
    monkeypatch.delenv("LLM_MOCK", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ChatUnavailableError):
        await get_reply([{"role": "user", "content": "hi"}])
