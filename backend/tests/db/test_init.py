"""Tests for database initialization and seeding."""

from app.db import (
    DEFAULT_CASH,
    DEFAULT_TICKERS,
    DEFAULT_USER_ID,
    get_connection,
    init_db,
)

EXPECTED_TABLES = {
    "users_profile",
    "watchlist",
    "positions",
    "trades",
    "portfolio_snapshots",
    "chat_messages",
}


def test_init_creates_file_and_tables(temp_db):
    assert temp_db.exists()
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    tables = {row["name"] for row in rows}
    assert EXPECTED_TABLES <= tables


def test_seed_profile(db_conn):
    row = db_conn.execute(
        "SELECT cash_balance FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
    ).fetchone()
    assert row["cash_balance"] == DEFAULT_CASH


def test_seed_watchlist(db_conn):
    rows = db_conn.execute(
        "SELECT ticker FROM watchlist WHERE user_id = ?", (DEFAULT_USER_ID,)
    ).fetchall()
    assert sorted(row["ticker"] for row in rows) == sorted(DEFAULT_TICKERS)


def test_init_is_idempotent(temp_db):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users_profile SET cash_balance = 5000.0 WHERE id = ?",
            (DEFAULT_USER_ID,),
        )

    init_db()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
        ).fetchone()
        count = conn.execute("SELECT COUNT(*) AS n FROM watchlist").fetchone()
    assert row["cash_balance"] == 5000.0
    assert count["n"] == len(DEFAULT_TICKERS)
