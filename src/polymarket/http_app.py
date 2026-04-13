from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from polymarket.api.markets import fetch_market, get_markets
from polymarket.api.prices import get_order_book
from polymarket.config import settings
from polymarket.db import create_tables, fetchall, get_connection, placeholder
from polymarket.refresh_catalog import refresh_catalog
from polymarket.trading.service import TradingService


def _parse_list_field(value: object) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            pass
    return []


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


def _market_from_db(query: str) -> dict[str, Any] | None:
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


def _resolve_market_live_or_db(query: str) -> tuple[dict[str, Any] | None, bool]:
    try:
        live = fetch_market(query)
        if live:
            return live, False
    except Exception:
        pass
    cached = _market_from_db(query)
    return cached, cached is not None


def _order_books_for_market(market: dict[str, Any]) -> list[dict[str, Any]]:
    tokens = _parse_list_field(market.get("clobTokenIds"))
    outcomes = _parse_list_field(market.get("outcomes"))
    books: list[dict[str, Any]] = []
    for i, token_id in enumerate(tokens):
        label = str(outcomes[i]) if i < len(outcomes) else f"token_{i}"
        book = get_order_book(str(token_id))
        books.append({"outcome": label, "token_id": str(token_id), "book": book})
    return books


@asynccontextmanager
async def _lifespan(app: FastAPI):
    conn = get_connection()
    try:
        create_tables(conn)
        conn.commit()
    finally:
        conn.close()
    yield


app = FastAPI(title="Poly Simulator API", lifespan=_lifespan)


class RefreshBody(BaseModel):
    incremental: bool = False


class PortfolioCreateBody(BaseModel):
    name: str | None = None
    balance: float | None = None


class BetBody(BaseModel):
    market_id: str
    outcome: str
    shares: float = Field(gt=0)


class CloseBody(BaseModel):
    position_id: int
    shares: float | None = None


class SettleBody(BaseModel):
    position_id: int
    won: bool


def _svc_exc(fn):
    try:
        return fn()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/markets/refresh")
def post_markets_refresh(body: RefreshBody) -> dict[str, Any]:
    return refresh_catalog(incremental=body.incremental, quiet=True)


@app.get("/db/markets")
def get_db_markets(
    limit: int = 100,
    offset: int = 0,
    active: bool | None = None,
    closed: bool | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    return list_markets_from_db(limit=limit, offset=offset, active=active, closed=closed, q=q)


@app.get("/markets/{query}/live")
def get_market_live(query: str) -> dict[str, Any]:
    m = _svc_exc(lambda: fetch_market(query))
    if not m:
        raise HTTPException(status_code=404, detail="market not found")
    return m


@app.get("/markets/{query}/cached")
def get_market_cached(query: str) -> dict[str, Any]:
    m = _market_from_db(query)
    if not m:
        raise HTTPException(status_code=404, detail="market not in database")
    return m


@app.get("/markets/{query}/resolved")
def get_market_resolved(query: str) -> dict[str, Any]:
    m, stale = _resolve_market_live_or_db(query)
    if not m:
        raise HTTPException(status_code=404, detail="market not found")
    return {"market": m, "stale": stale}


@app.get("/markets/{query}/full")
def get_market_full(query: str) -> dict[str, Any]:
    m, stale = _resolve_market_live_or_db(query)
    if not m:
        raise HTTPException(status_code=404, detail="market not found")
    books = _order_books_for_market(m)
    return {"market": m, "stale": stale, "order_books": books}


@app.get("/gamma/markets")
def get_gamma_markets(
    limit: int = 100,
    offset: int = 0,
    active: bool = True,
    closed: bool = False,
    accepting_orders: bool = True,
    order: str = "createdAt",
    ascending: bool = False,
) -> list[dict[str, Any]]:
    return get_markets(
        limit=limit,
        offset=offset,
        active=active,
        closed=closed,
        accepting_orders=accepting_orders,
        order=order,
        ascending=ascending,
    )


@app.get("/portfolios")
def list_portfolios() -> list[dict[str, Any]]:
    return TradingService.list_portfolios()


@app.post("/portfolios")
def create_portfolio(body: PortfolioCreateBody) -> dict[str, Any]:
    return _svc_exc(
        lambda: TradingService.create_portfolio(name=body.name, balance=body.balance)
    )


@app.get("/portfolios/{portfolio}/summary")
def get_portfolio_summary(portfolio: str) -> dict[str, Any]:
    svc = TradingService(portfolio)
    return _svc_exc(lambda: svc.get_portfolio())


@app.get("/portfolios/{portfolio}/positions")
def get_portfolio_positions(portfolio: str) -> list[dict[str, Any]]:
    svc = TradingService(portfolio)
    return _svc_exc(lambda: svc.get_positions())


@app.get("/portfolios/{portfolio}/trades")
def get_portfolio_trades(portfolio: str) -> list[dict[str, Any]]:
    svc = TradingService(portfolio)
    return _svc_exc(lambda: svc.get_trades())


@app.post("/portfolios/{portfolio}/bet")
def post_portfolio_bet(portfolio: str, body: BetBody) -> dict[str, Any]:
    svc = TradingService(portfolio)
    return _svc_exc(
        lambda: svc.place_bet(
            market_id=body.market_id,
            outcome=body.outcome,
            shares=body.shares,
        )
    )


@app.post("/portfolios/{portfolio}/close")
def post_portfolio_close(portfolio: str, body: CloseBody) -> dict[str, Any]:
    svc = TradingService(portfolio)
    return _svc_exc(
        lambda: svc.close_position(position_id=body.position_id, shares=body.shares)
    )


@app.post("/portfolios/{portfolio}/settle")
def post_portfolio_settle(portfolio: str, body: SettleBody) -> dict[str, Any]:
    svc = TradingService(portfolio)
    return _svc_exc(
        lambda: svc.close_position_settled(position_id=body.position_id, won=body.won)
    )
