from __future__ import annotations

from pathlib import Path

from polymarket.config import settings
from polymarket.db.connection import Connection, get_connection
from polymarket.db.schema import (
    CREATE_MARKETS_TABLE,
    CREATE_PORTFOLIOS_TABLE_PG,
    CREATE_PORTFOLIOS_TABLE_SQLITE,
    CREATE_POSITIONS_TABLE_PG,
    CREATE_POSITIONS_TABLE_SQLITE,
    CREATE_TRADES_TABLE_PG,
    CREATE_TRADES_TABLE_SQLITE,
    CREATE_USERS_TABLE_PG,
    CREATE_USERS_TABLE_SQLITE,
    create_tables,
)
from polymarket.db.sql import (
    _serialize,
    execute,
    executemany,
    fetchall,
    placeholder,
    upsert_markets,
)

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "markets.db"

__all__ = [
    "DB_PATH",
    "Connection",
    "CREATE_MARKETS_TABLE",
    "CREATE_PORTFOLIOS_TABLE_PG",
    "CREATE_PORTFOLIOS_TABLE_SQLITE",
    "CREATE_POSITIONS_TABLE_PG",
    "CREATE_POSITIONS_TABLE_SQLITE",
    "CREATE_TRADES_TABLE_PG",
    "CREATE_TRADES_TABLE_SQLITE",
    "CREATE_USERS_TABLE_PG",
    "CREATE_USERS_TABLE_SQLITE",
    "create_tables",
    "execute",
    "executemany",
    "fetchall",
    "get_connection",
    "placeholder",
    "settings",
    "upsert_markets",
    "_serialize",
]
