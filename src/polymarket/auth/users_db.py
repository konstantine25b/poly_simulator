from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from polymarket.config import settings
from polymarket.db import Connection, execute, fetchall, placeholder


def normalize_email(email: str) -> str:
    return email.strip().lower()


def insert_user(
    conn: Connection,
    *,
    email: str,
    password_hash: str,
    is_admin: bool,
) -> int:
    ph = placeholder()
    now = datetime.now(timezone.utc).isoformat()
    if is_admin:
        flag = 1
    else:
        flag = 0
    if settings.db_backend == "postgres":
        rows = fetchall(
            conn,
            f"INSERT INTO users (email, password_hash, is_admin, created_at) VALUES ({ph}, {ph}, {ph}, {ph}) RETURNING id",
            (email, password_hash, flag, now),
        )
        return int(rows[0]["id"])
    execute(
        conn,
        f"INSERT INTO users (email, password_hash, is_admin, created_at) VALUES ({ph}, {ph}, {ph}, {ph})",
        (email, password_hash, flag, now),
    )
    rid = fetchall(conn, "SELECT last_insert_rowid() AS id")
    return int(rid[0]["id"])


def fetch_user_by_email(conn: Connection, email: str) -> dict[str, Any] | None:
    ph = placeholder()
    rows = fetchall(conn, f"SELECT id, email, password_hash, is_admin, created_at FROM users WHERE email = {ph}", (email,))
    if not rows:
        return None
    r = rows[0]
    if isinstance(r, dict):
        return dict(r)
    return {k: r[k] for k in r.keys()}


def fetch_user_by_id(conn: Connection, user_id: int) -> dict[str, Any] | None:
    ph = placeholder()
    rows = fetchall(conn, f"SELECT id, email, password_hash, is_admin, created_at FROM users WHERE id = {ph}", (user_id,))
    if not rows:
        return None
    r = rows[0]
    if isinstance(r, dict):
        return dict(r)
    return {k: r[k] for k in r.keys()}


def list_users_public(conn: Connection) -> list[dict[str, Any]]:
    rows = fetchall(conn, "SELECT id, email, is_admin, created_at FROM users ORDER BY id")
    out: list[dict[str, Any]] = []
    for r in rows:
        if isinstance(r, dict):
            d = dict(r)
        else:
            d = {k: r[k] for k in r.keys()}
        if d.get("is_admin"):
            d["is_admin"] = True
        else:
            d["is_admin"] = False
        out.append(d)
    return out


def update_user_password(conn: Connection, user_id: int, password_hash: str) -> None:
    ph = placeholder()
    execute(conn, f"UPDATE users SET password_hash = {ph} WHERE id = {ph}", (password_hash, user_id))


def update_user_admin(conn: Connection, user_id: int, is_admin: bool) -> None:
    ph = placeholder()
    v = 1 if is_admin else 0
    execute(conn, f"UPDATE users SET is_admin = {ph} WHERE id = {ph}", (v, user_id))


def delete_user_cascade(conn: Connection, user_id: int) -> None:
    ph = placeholder()
    pids = fetchall(conn, f"SELECT id FROM portfolios WHERE user_id = {ph}", (user_id,))
    for row in pids:
        pid = int(row["id"])
        execute(conn, f"DELETE FROM trades WHERE portfolio_id = {ph}", (pid,))
        execute(conn, f"DELETE FROM positions WHERE portfolio_id = {ph}", (pid,))
    execute(conn, f"DELETE FROM portfolios WHERE user_id = {ph}", (user_id,))
    execute(conn, f"DELETE FROM users WHERE id = {ph}", (user_id,))


def count_users(conn: Connection) -> int:
    rows = fetchall(conn, "SELECT COUNT(*) AS c FROM users")
    return int(rows[0]["c"])


def default_owner_user_id(conn: Connection) -> int:
    rows = fetchall(conn, "SELECT id FROM users ORDER BY id ASC LIMIT 1")
    if not rows:
        raise RuntimeError("no users")
    return int(rows[0]["id"])
