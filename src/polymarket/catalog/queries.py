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


def _created_at_order_column() -> str:
    return "createdat" if settings.db_backend == "postgres" else "createdAt"


def list_markets_from_db(
    *,
    limit: int = 100,
    offset: int = 0,
    active: bool | None = None,
    closed: bool | None = None,
    q: str | None = None,
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
    oc = _created_at_order_column()
    conn = get_connection()
    try:
        count_rows = fetchall(conn, f"SELECT COUNT(*) AS c FROM markets WHERE {where_sql}", tuple(params))
        total = int(count_rows[0]["c"])
        rows = fetchall(
            conn,
            f"SELECT * FROM markets WHERE {where_sql} ORDER BY {oc} DESC LIMIT {ph} OFFSET {ph}",
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
