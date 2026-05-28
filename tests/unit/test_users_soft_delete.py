from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from polymarket.auth import (
    fetch_user_by_email,
    fetch_user_by_id,
    hash_password,
    insert_user,
    is_user_deleted,
    list_users_public,
    restore_user,
    soft_delete_user,
)
from polymarket.db import create_tables, get_connection


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = get_connection(Path(":memory:"))
    create_tables(c)
    return c


def _new_user(conn: sqlite3.Connection, email: str) -> int:
    return insert_user(
        conn,
        email=email,
        password_hash=hash_password("password12345"),
        is_admin=False,
    )


def test_new_user_is_not_deleted(conn: sqlite3.Connection) -> None:
    uid = _new_user(conn, "alive@example.com")
    row = fetch_user_by_id(conn, uid)
    assert row is not None
    assert row["deleted_at"] is None
    assert is_user_deleted(row) is False


def test_soft_delete_sets_deleted_at(conn: sqlite3.Connection) -> None:
    uid = _new_user(conn, "soft@example.com")
    soft_delete_user(conn, uid)
    conn.commit()
    row = fetch_user_by_id(conn, uid)
    assert row is not None
    assert row["deleted_at"] is not None
    assert is_user_deleted(row) is True

    by_email = fetch_user_by_email(conn, "soft@example.com")
    assert by_email is not None
    assert is_user_deleted(by_email) is True


def test_restore_clears_deleted_at(conn: sqlite3.Connection) -> None:
    uid = _new_user(conn, "restoreme@example.com")
    soft_delete_user(conn, uid)
    conn.commit()
    restore_user(conn, uid)
    conn.commit()
    row = fetch_user_by_id(conn, uid)
    assert row is not None
    assert row["deleted_at"] is None
    assert is_user_deleted(row) is False


def test_list_users_public_exposes_is_deleted(conn: sqlite3.Connection) -> None:
    uid = _new_user(conn, "listed@example.com")
    soft_delete_user(conn, uid)
    conn.commit()
    rows = list_users_public(conn)
    target = next(r for r in rows if r["email"] == "listed@example.com")
    assert target["is_deleted"] is True
    assert target["deleted_at"] is not None
