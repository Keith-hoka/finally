"""SQLite connection handling and lazy initialization."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .seed import seed_if_empty

DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "db" / "finally.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db_path() -> Path:
    """Resolve the database file path. FINALLY_DB_PATH overrides the default."""
    override = os.environ.get("FINALLY_DB_PATH", "").strip()
    return Path(override) if override else DEFAULT_DB_PATH


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection with row access by name. Commits on success, rolls back on error."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the schema and seed default data if missing. Idempotent."""
    schema = SCHEMA_PATH.read_text()
    with get_connection() as conn:
        conn.executescript(schema)
        seed_if_empty(conn)
