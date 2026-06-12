"""Database layer for FinAlly.

Public API:
    get_connection  - Context manager yielding a sqlite3 connection
    init_db         - Lazy schema creation + default seed (idempotent)
    DEFAULT_USER_ID - The single-user id used throughout
"""

from .connection import get_connection, get_db_path, init_db
from .seed import DEFAULT_CASH, DEFAULT_TICKERS, DEFAULT_USER_ID

__all__ = [
    "get_connection",
    "get_db_path",
    "init_db",
    "DEFAULT_USER_ID",
    "DEFAULT_CASH",
    "DEFAULT_TICKERS",
]
