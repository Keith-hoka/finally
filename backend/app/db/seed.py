"""Default seed data: one user profile and ten watchlist tickers."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

DEFAULT_USER_ID = "default"
DEFAULT_CASH = 10000.0
DEFAULT_TICKERS = [
    "AAPL",
    "GOOGL",
    "MSFT",
    "AMZN",
    "TSLA",
    "NVDA",
    "META",
    "JPM",
    "V",
    "NFLX",
]


def utc_now_iso() -> str:
    """Current UTC time as an ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def seed_if_empty(conn: sqlite3.Connection) -> None:
    """Insert the default profile and watchlist if no profile exists yet."""
    row = conn.execute(
        "SELECT 1 FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
    ).fetchone()
    if row:
        return

    now = utc_now_iso()
    conn.execute(
        "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
        (DEFAULT_USER_ID, DEFAULT_CASH, now),
    )
    conn.executemany(
        "INSERT INTO watchlist (user_id, ticker, added_at) VALUES (?, ?, ?)",
        [(DEFAULT_USER_ID, ticker, now) for ticker in DEFAULT_TICKERS],
    )
