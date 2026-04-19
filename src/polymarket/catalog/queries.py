from __future__ import annotations

import json
from typing import Any

from polymarket.api.markets import fetch_market
from polymarket.config import settings
from polymarket.db import fetchall, get_connection, placeholder


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    return {k: row[k] for k in row.keys()}


def _json_ready_market(m: dict[str, Any]) -> dict[str, Any]:
    out = dict(m)
    for k in (
        "outcomes",
        "outcomePrices",
        "clobTokenIds",
        "events",
        "tags",
        "clobRewards",
        "umaResolutionStatuses",
    ):
        v = out.get(k)
        if isinstance(v, str):
            try:
                out[k] = json.loads(v)
            except (ValueError, TypeError):
                pass
    return out


def _sql_col(sqlite_name: str, pg_name: str) -> str:
    return pg_name if settings.db_backend == "postgres" else sqlite_name


def _order_by_sql(sort: str | None) -> str:
    raw = (sort or "created_desc").strip().lower().replace("-", "_")
    aliases = {"newest": "created_desc", "oldest": "created_asc"}
    key = aliases.get(raw, raw)
    allowed = {
        "created_desc",
        "created_asc",
        "volume_desc",
        "volume_asc",
        "end_desc",
        "end_asc",
        "start_desc",
        "start_asc",
    }
    if key not in allowed:
        key = "created_desc"
    ca = _sql_col("createdAt", "createdat")
    vn = _sql_col("volumeNum", "volumenum")
    ed = _sql_col("endDate", "enddate")
    sd = _sql_col("startDate", "startdate")
    if key == "created_desc":
        return f"ORDER BY {ca} DESC"
    if key == "created_asc":
        return f"ORDER BY {ca} ASC"
    if key == "volume_desc":
        return f"ORDER BY ({vn} IS NULL) ASC, {vn} DESC"
    if key == "volume_asc":
        return f"ORDER BY ({vn} IS NULL) ASC, {vn} ASC"
    if key == "end_desc":
        return f"ORDER BY ({ed} IS NULL) ASC, ({ed} = '') ASC, {ed} DESC"
    if key == "end_asc":
        return f"ORDER BY ({ed} IS NULL) ASC, ({ed} = '') ASC, {ed} ASC"
    if key == "start_desc":
        return f"ORDER BY ({sd} IS NULL) ASC, ({sd} = '') ASC, {sd} DESC"
    if key == "start_asc":
        return f"ORDER BY ({sd} IS NULL) ASC, ({sd} = '') ASC, {sd} ASC"
    return f"ORDER BY {ca} DESC"


def list_markets_from_db(
    *,
    limit: int = 100,
    offset: int = 0,
    active: bool | None = None,
    closed: bool | None = None,
    q: str | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    lim = max(1, min(500, limit))
    off = max(0, offset)
    ph = placeholder()
    conds = ["1=1"]
    params: list[Any] = []
    if active is not None:
        conds.append(f"active = {ph}")
        params.append(1 if active else 0)
    if closed is not None:
        conds.append(f"closed = {ph}")
        params.append(1 if closed else 0)
    if q and q.strip():
        needle = f"%{q.strip()}%"
        if settings.db_backend == "postgres":
            conds.append(f"(question ILIKE {ph} OR slug ILIKE {ph})")
        else:
            conds.append(f"(question LIKE {ph} OR slug LIKE {ph})")
        params.extend([needle, needle])
    where_sql = " AND ".join(conds)
    order_sql = _order_by_sql(sort)
    conn = get_connection()
    try:
        count_rows = fetchall(conn, f"SELECT COUNT(*) AS c FROM markets WHERE {where_sql}", tuple(params))
        total = int(count_rows[0]["c"])
        rows = fetchall(
            conn,
            f"SELECT * FROM markets WHERE {where_sql} {order_sql} LIMIT {ph} OFFSET {ph}",
            tuple(params + [lim, off]),
        )
        items = [_json_ready_market(_row_to_dict(r)) for r in rows]
        return {"items": items, "total": total, "limit": lim, "offset": off}
    finally:
        conn.close()


def market_from_db(query: str) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        ph = placeholder()
        rows = fetchall(
            conn,
            f"SELECT * FROM markets WHERE id={ph} OR slug={ph} LIMIT 1",
            (query, query),
        )
        if not rows:
            return None
        return _json_ready_market(_row_to_dict(rows[0]))
    finally:
        conn.close()


def resolve_market_live_or_db(query: str) -> tuple[dict[str, Any] | None, bool]:
    try:
        live = fetch_market(query)
        if live:
            return live, False
    except Exception:
        pass
    cached = market_from_db(query)
    return cached, cached is not None
