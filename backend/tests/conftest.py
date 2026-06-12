"""Pytest configuration and fixtures."""

import pytest

from app.db import get_connection, init_db


@pytest.fixture
def event_loop_policy():
    """Use the default event loop policy for all async tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point FINALLY_DB_PATH at a temp file and initialize it."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(db_path))
    init_db()
    return db_path


@pytest.fixture
def db_conn(temp_db):
    """A connection to the initialized temp database."""
    with get_connection() as conn:
        yield conn
