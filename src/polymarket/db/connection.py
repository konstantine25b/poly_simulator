from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Union

from polymarket.config import settings

try:
    import psycopg2
    import psycopg2.extras

    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False

Connection = Union[sqlite3.Connection, Any]


def get_connection(db_path: Path | None = None) -> Connection:
    if settings.db_backend == "postgres":
        if not _PG_AVAILABLE:
            raise RuntimeError("psycopg2 not installed — run: pip install psycopg2-binary")
        conn = psycopg2.connect(
            settings.postgres_dsn,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        return conn

    import polymarket.db as db_pkg

    path = db_path or db_pkg.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
