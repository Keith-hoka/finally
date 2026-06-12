"""Watchlist management, kept in sync with the market data source."""

from __future__ import annotations

from app.db import DEFAULT_USER_ID, get_connection
from app.db.seed import utc_now_iso
from app.market import MarketDataSource, PriceCache

from .validation import normalize_ticker


class NotWatchedError(ValueError):
    """The ticker is not on the watchlist."""


def get_watchlist(cache: PriceCache) -> list[dict]:
    """Watched tickers with their latest cached prices (null until first tick)."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT ticker, added_at FROM watchlist
               WHERE user_id = ? ORDER BY added_at, ticker""",
            (DEFAULT_USER_ID,),
        ).fetchall()

    entries = []
    for row in rows:
        update = cache.get(row["ticker"])
        entries.append(
            {
                "ticker": row["ticker"],
                "added_at": row["added_at"],
                "price": update.to_dict() if update else None,
            }
        )
    return entries


def watchlist_tickers() -> list[str]:
    """Just the watched ticker symbols."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ?", (DEFAULT_USER_ID,)
        ).fetchall()
    return [row["ticker"] for row in rows]


async def add_ticker(source: MarketDataSource, ticker: str) -> dict:
    """Add a ticker to the watchlist and register it with the data source.

    Adding an already-watched ticker is a no-op success.
    """
    ticker = normalize_ticker(ticker)
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, ticker, added_at) VALUES (?, ?, ?)",
            (DEFAULT_USER_ID, ticker, utc_now_iso()),
        )
        added = cursor.rowcount == 1
    await source.add_ticker(ticker)
    return {"ticker": ticker, "added": added}


async def remove_ticker(source: MarketDataSource, ticker: str) -> None:
    """Remove a ticker from the watchlist.

    The data source keeps streaming it if a position still holds it.
    Raises NotWatchedError if the ticker is not on the watchlist.
    """
    ticker = normalize_ticker(ticker)
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
            (DEFAULT_USER_ID, ticker),
        )
        if cursor.rowcount == 0:
            raise NotWatchedError(f"{ticker} is not on the watchlist")
        has_position = (
            conn.execute(
                "SELECT 1 FROM positions WHERE user_id = ? AND ticker = ?",
                (DEFAULT_USER_ID, ticker),
            ).fetchone()
            is not None
        )
    if not has_position:
        await source.remove_ticker(ticker)
