"""Tests for watchlist management and data-source sync."""

import pytest

from app.db import DEFAULT_TICKERS
from app.services.portfolio import execute_trade
from app.services.validation import ValidationError
from app.services.watchlist import (
    NotWatchedError,
    add_ticker,
    get_watchlist,
    remove_ticker,
    watchlist_tickers,
)

pytestmark = pytest.mark.usefixtures("temp_db")


def test_seeded_watchlist_with_and_without_prices(cache):
    cache.update("AAPL", 190.0)
    entries = get_watchlist(cache)

    assert len(entries) == len(DEFAULT_TICKERS)
    by_ticker = {entry["ticker"]: entry for entry in entries}
    assert by_ticker["AAPL"]["price"]["price"] == 190.0
    assert by_ticker["MSFT"]["price"] is None


async def test_add_ticker(cache, source):
    result = await add_ticker(source, "pypl")

    assert result == {"ticker": "PYPL", "added": True}
    assert "PYPL" in watchlist_tickers()
    assert source.added == ["PYPL"]


async def test_add_duplicate_is_noop_success(cache, source):
    result = await add_ticker(source, "AAPL")

    assert result == {"ticker": "AAPL", "added": False}
    assert watchlist_tickers().count("AAPL") == 1


async def test_add_invalid_ticker_rejected(source):
    with pytest.raises(ValidationError):
        await add_ticker(source, "123456")


async def test_remove_ticker(cache, source):
    await remove_ticker(source, "AAPL")

    assert "AAPL" not in watchlist_tickers()
    assert source.removed == ["AAPL"]


async def test_remove_keeps_stream_for_held_position(cache, source):
    cache.update("AAPL", 100.0)
    await execute_trade(cache, source, "AAPL", 1, "buy")
    await remove_ticker(source, "AAPL")

    assert "AAPL" not in watchlist_tickers()
    assert source.removed == []


async def test_remove_unwatched_raises(source):
    with pytest.raises(NotWatchedError):
        await remove_ticker(source, "PYPL")
