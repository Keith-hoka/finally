"""Tests for trade execution, valuation, and snapshots."""

import pytest

from app.db import DEFAULT_CASH, get_connection
from app.services.portfolio import (
    execute_trade,
    get_history,
    get_portfolio,
    position_tickers,
    record_snapshot,
    resolve_price,
)
from app.services.validation import ValidationError

pytestmark = pytest.mark.usefixtures("temp_db")


async def test_buy_creates_position_and_deducts_cash(cache, source):
    cache.update("AAPL", 100.0)
    result = await execute_trade(cache, source, "AAPL", 10, "buy")

    assert result["cash_balance"] == DEFAULT_CASH - 1000.0
    portfolio = get_portfolio(cache)
    assert portfolio["positions"][0]["ticker"] == "AAPL"
    assert portfolio["positions"][0]["quantity"] == 10
    assert portfolio["positions"][0]["avg_cost"] == 100.0


async def test_repeat_buy_recalculates_avg_cost(cache, source):
    cache.update("AAPL", 100.0)
    await execute_trade(cache, source, "AAPL", 10, "buy")
    cache.update("AAPL", 200.0)
    await execute_trade(cache, source, "AAPL", 10, "buy")

    position = get_portfolio(cache)["positions"][0]
    assert position["quantity"] == 20
    assert position["avg_cost"] == 150.0


async def test_partial_sell(cache, source):
    cache.update("AAPL", 100.0)
    await execute_trade(cache, source, "AAPL", 10, "buy")
    result = await execute_trade(cache, source, "AAPL", 4, "sell")

    assert result["cash_balance"] == DEFAULT_CASH - 1000.0 + 400.0
    position = get_portfolio(cache)["positions"][0]
    assert position["quantity"] == 6
    assert position["avg_cost"] == 100.0


async def test_full_sell_deletes_position(cache, source):
    cache.update("AAPL", 100.0)
    await execute_trade(cache, source, "AAPL", 10, "buy")
    await execute_trade(cache, source, "AAPL", 10, "sell")

    assert get_portfolio(cache)["positions"] == []
    assert position_tickers() == []


async def test_sell_at_a_loss(cache, source):
    cache.update("AAPL", 100.0)
    await execute_trade(cache, source, "AAPL", 10, "buy")
    cache.update("AAPL", 50.0)
    result = await execute_trade(cache, source, "AAPL", 10, "sell")

    assert result["cash_balance"] == DEFAULT_CASH - 1000.0 + 500.0


async def test_insufficient_cash_rejected(cache, source):
    cache.update("AAPL", 100.0)
    with pytest.raises(ValidationError, match="Insufficient cash"):
        await execute_trade(cache, source, "AAPL", 1000, "buy")


async def test_insufficient_shares_rejected(cache, source):
    cache.update("AAPL", 100.0)
    await execute_trade(cache, source, "AAPL", 5, "buy")
    with pytest.raises(ValidationError, match="Insufficient shares"):
        await execute_trade(cache, source, "AAPL", 6, "sell")


async def test_invalid_inputs_rejected(cache, source):
    cache.update("AAPL", 100.0)
    with pytest.raises(ValidationError, match="Quantity"):
        await execute_trade(cache, source, "AAPL", 0, "buy")
    with pytest.raises(ValidationError, match="Quantity"):
        await execute_trade(cache, source, "AAPL", -5, "buy")
    with pytest.raises(ValidationError, match="Invalid ticker"):
        await execute_trade(cache, source, "TOOLONG", 1, "buy")
    with pytest.raises(ValidationError, match="Invalid side"):
        await execute_trade(cache, source, "AAPL", 1, "hold")


async def test_fractional_buy(cache, source):
    cache.update("AAPL", 100.0)
    result = await execute_trade(cache, source, "AAPL", 2.5, "buy")

    assert result["total"] == 250.0
    assert get_portfolio(cache)["positions"][0]["quantity"] == 2.5


async def test_buy_unknown_ticker_registers_with_source(cache, source):
    result = await execute_trade(cache, source, "pypl", 1, "buy")

    assert source.added == ["PYPL"]
    assert result["price"] == 60.0


async def test_resolve_price_times_out_without_price(cache, source):
    with pytest.raises(ValidationError, match="No price available"):
        await resolve_price(cache, source, "FAKE", timeout=0.3)


async def test_trade_records_trade_and_snapshot(cache, source, temp_db):
    cache.update("AAPL", 100.0)
    await execute_trade(cache, source, "AAPL", 10, "buy")

    with get_connection() as conn:
        trades = conn.execute("SELECT * FROM trades").fetchall()
        snapshots = conn.execute("SELECT * FROM portfolio_snapshots").fetchall()
    assert len(trades) == 1
    assert trades[0]["side"] == "buy"
    assert trades[0]["price"] == 100.0
    assert len(snapshots) == 1
    assert snapshots[0]["total_value"] == DEFAULT_CASH


async def test_portfolio_valuation_and_pnl(cache, source):
    cache.update("AAPL", 100.0)
    await execute_trade(cache, source, "AAPL", 10, "buy")
    cache.update("AAPL", 110.0)

    portfolio = get_portfolio(cache)
    position = portfolio["positions"][0]
    assert position["unrealized_pnl"] == 100.0
    assert position["pnl_percent"] == 10.0
    assert portfolio["total_value"] == DEFAULT_CASH + 100.0


def test_snapshot_and_history(cache):
    record_snapshot(cache)
    record_snapshot(cache)

    history = get_history()
    assert len(history) == 2
    assert all(entry["total_value"] == DEFAULT_CASH for entry in history)
    assert history[0]["recorded_at"] <= history[1]["recorded_at"]
    assert len(get_history(limit=1)) == 1
