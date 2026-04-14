from __future__ import annotations

import json
import sqlite3
from typing import Any

from polymarket.config import settings

from polymarket.db.connection import Connection


def _serialize(value: object) -> object:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value


def _get_columns_sqlite(conn: sqlite3.Connection) -> set[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM pragma_table_info('markets')")
    return {row[0] for row in cur.fetchall()}


def _get_columns_pg(conn: Any) -> set[str]:
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'markets'"
    )
    cols = {row["column_name"] for row in cur.fetchall()}
    cur.close()
    return cols


def placeholder() -> str:
    """Return the correct parameter placeholder for the active backend."""
    return "%s" if settings.db_backend == "postgres" else "?"


def fetchall(conn: Connection, sql: str, params: tuple = ()) -> list:
    if settings.db_backend == "postgres":
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows
    return conn.execute(sql, params).fetchall()


def execute(conn: Connection, sql: str, params: tuple = ()) -> None:
    if settings.db_backend == "postgres":
        cur = conn.cursor()
        cur.execute(sql, params)
        cur.close()
    else:
        conn.execute(sql, params)


def executemany(conn: Connection, sql: str, params_list: list) -> None:
    if settings.db_backend == "postgres":
        cur = conn.cursor()
        cur.executemany(sql, params_list)
        cur.close()
    else:
        conn.executemany(sql, params_list)


def upsert_markets(conn: Connection, markets: list[dict]) -> int:
    if settings.db_backend == "postgres":
        return _upsert_pg(conn, markets)
    return _upsert_sqlite(conn, markets)


def _upsert_sqlite(conn: sqlite3.Connection, markets: list[dict]) -> int:
    columns = _get_columns_sqlite(conn)
    cursor = conn.cursor()
    inserted = 0
    for market in markets:
        row = {k: _serialize(v) for k, v in market.items() if k in columns}
        col_names = ", ".join(row.keys())
        placeholders = ", ".join(f":{k}" for k in row)
        cursor.execute(
            f"INSERT OR REPLACE INTO markets ({col_names}) VALUES ({placeholders})",
            row,
        )
        inserted += 1
    conn.commit()
    return inserted


def _upsert_pg(conn: Any, markets: list[dict]) -> int:
    columns = _get_columns_pg(conn)
    cur = conn.cursor()
    inserted = 0
    for market in markets:
        row = {k.lower(): _serialize(v) for k, v in market.items() if k.lower() in columns}
        col_names = ", ".join(row.keys())
        placeholders = ", ".join(f"%({k})s" for k in row)
        update_set = ", ".join(f"{k} = EXCLUDED.{k}" for k in row if k != "id")
        cur.execute(
            f"""
            INSERT INTO markets ({col_names}) VALUES ({placeholders})
            ON CONFLICT (id) DO UPDATE SET {update_set}
            """,
            row,
        )
        inserted += 1
    conn.commit()
    cur.close()
    return inserted
