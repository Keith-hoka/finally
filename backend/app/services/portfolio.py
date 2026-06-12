"""Trade execution, portfolio valuation, and snapshots."""

from __future__ import annotations

import asyncio
import sqlite3
import uuid

from app.db import DEFAULT_USER_ID, get_connection
from app.db.seed import utc_now_iso
from app.market import MarketDataSource, PriceCache

from .validation import ValidationError, normalize_quantity, normalize_ticker

PRICE_WAIT_SECONDS = 2.0
EPSILON = 1e-9


async def resolve_price(
    cache: PriceCache,
    source: MarketDataSource,
    ticker: str,
    timeout: float = PRICE_WAIT_SECONDS,
) -> float:
    """Get the current price, registering the ticker with the source if needed.

    Waits up to `timeout` seconds for a first price to arrive.
    """
    price = cache.get_price(ticker)
    if price is not None:
        return price

    await source.add_ticker(ticker)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        await asyncio.sleep(0.1)
        price = cache.get_price(ticker)
        if price is not None:
            return price
    raise ValidationError(f"No price available for {ticker}")


async def execute_trade(
    cache: PriceCache,
    source: MarketDataSource,
    ticker: str,
    quantity: float,
    side: str,
) -> dict:
    """Execute a market order at the current cached price.

    Validates inputs and sufficiency, updates cash and position atomically,
    appends to the trade log, and records a portfolio snapshot.
    """
    if side not in ("buy", "sell"):
        raise ValidationError(f"Invalid side '{side}': must be 'buy' or 'sell'")
    ticker = normalize_ticker(ticker)
    quantity = normalize_quantity(quantity)
    price = await resolve_price(cache, source, ticker)

    with get_connection() as conn:
        cash = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
        ).fetchone()["cash_balance"]
        pos = conn.execute(
            "SELECT quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
            (DEFAULT_USER_ID, ticker),
        ).fetchone()
        held = pos["quantity"] if pos else 0.0
        now = utc_now_iso()

        if side == "buy":
            cost = quantity * price
            if cost > cash + EPSILON:
                raise ValidationError(
                    f"Insufficient cash: need ${cost:.2f}, have ${cash:.2f}"
                )
            new_cash = cash - cost
            exact_qty = held + quantity
            new_qty = round(exact_qty, 4)
            old_avg = pos["avg_cost"] if pos else 0.0
            new_avg = (held * old_avg + cost) / exact_qty
            conn.execute(
                """INSERT INTO positions (user_id, ticker, quantity, avg_cost, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT (user_id, ticker)
                   DO UPDATE SET quantity = excluded.quantity,
                                 avg_cost = excluded.avg_cost,
                                 updated_at = excluded.updated_at""",
                (DEFAULT_USER_ID, ticker, new_qty, new_avg, now),
            )
        else:
            if quantity > held + EPSILON:
                raise ValidationError(
                    f"Insufficient shares: selling {quantity} {ticker}, holding {held}"
                )
            new_cash = cash + quantity * price
            new_qty = round(held - quantity, 4)
            if new_qty <= 0:
                conn.execute(
                    "DELETE FROM positions WHERE user_id = ? AND ticker = ?",
                    (DEFAULT_USER_ID, ticker),
                )
            else:
                conn.execute(
                    """UPDATE positions SET quantity = ?, updated_at = ?
                       WHERE user_id = ? AND ticker = ?""",
                    (new_qty, now, DEFAULT_USER_ID, ticker),
                )

        conn.execute(
            "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
            (new_cash, DEFAULT_USER_ID),
        )
        conn.execute(
            """INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), DEFAULT_USER_ID, ticker, side, quantity, price, now),
        )
        _insert_snapshot(conn, cache)

    return {
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price": price,
        "total": round(quantity * price, 2),
        "cash_balance": round(new_cash, 2),
        "position_quantity": new_qty if new_qty > 0 else 0.0,
        "executed_at": now,
    }


def get_portfolio(cache: PriceCache) -> dict:
    """Current cash, positions with live valuation, and total portfolio value."""
    with get_connection() as conn:
        cash = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
        ).fetchone()["cash_balance"]
        rows = conn.execute(
            """SELECT ticker, quantity, avg_cost FROM positions
               WHERE user_id = ? ORDER BY ticker""",
            (DEFAULT_USER_ID,),
        ).fetchall()

    positions = []
    total_value = cash
    for row in rows:
        price = cache.get_price(row["ticker"]) or row["avg_cost"]
        market_value = row["quantity"] * price
        cost_basis = row["quantity"] * row["avg_cost"]
        pnl = market_value - cost_basis
        positions.append(
            {
                "ticker": row["ticker"],
                "quantity": row["quantity"],
                "avg_cost": round(row["avg_cost"], 4),
                "current_price": price,
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(pnl, 2),
                "pnl_percent": round(pnl / cost_basis * 100, 4) if cost_basis else 0.0,
            }
        )
        total_value += market_value

    return {
        "cash_balance": round(cash, 2),
        "total_value": round(total_value, 2),
        "positions": positions,
    }


def record_snapshot(cache: PriceCache) -> float:
    """Record the current total portfolio value. Returns the value recorded."""
    with get_connection() as conn:
        return _insert_snapshot(conn, cache)


def get_history(limit: int = 1000) -> list[dict]:
    """Most recent snapshots in chronological order, capped at `limit`."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT total_value, recorded_at FROM portfolio_snapshots
               WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?""",
            (DEFAULT_USER_ID, limit),
        ).fetchall()
    return [
        {"total_value": row["total_value"], "recorded_at": row["recorded_at"]}
        for row in reversed(rows)
    ]


def position_tickers() -> list[str]:
    """Tickers currently held as positions."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT ticker FROM positions WHERE user_id = ?", (DEFAULT_USER_ID,)
        ).fetchall()
    return [row["ticker"] for row in rows]


def _insert_snapshot(conn: sqlite3.Connection, cache: PriceCache) -> float:
    """Compute total value from this connection's state and insert a snapshot row."""
    cash = conn.execute(
        "SELECT cash_balance FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
    ).fetchone()["cash_balance"]
    rows = conn.execute(
        "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ?",
        (DEFAULT_USER_ID,),
    ).fetchall()

    total = cash
    for row in rows:
        price = cache.get_price(row["ticker"]) or row["avg_cost"]
        total += row["quantity"] * price
    total = round(total, 2)

    conn.execute(
        """INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at)
           VALUES (?, ?, ?, ?)""",
        (str(uuid.uuid4()), DEFAULT_USER_ID, total, utc_now_iso()),
    )
    return total
