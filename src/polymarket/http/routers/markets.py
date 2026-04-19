from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from polymarket.api.markets import fetch_market, get_markets
from polymarket.catalog.order_books import order_books_for_market
from polymarket.catalog.queries import list_markets_from_db, market_from_db, resolve_market_live_or_db
from polymarket.config import settings
from polymarket.http.common import svc_exc
from polymarket.http.deps import _access_from_bearer, _bearer
from polymarket.http.schemas import RefreshBody
from polymarket.refresh_catalog import refresh_catalog

router = APIRouter(tags=["markets"])


@router.post(
    "/markets/refresh",
    summary="Refresh market catalog",
    description=(
        "Use **Authorize** (HTTPBearer) with an admin `access_token` from **POST /auth/login**, "
        "or fill **X-Refresh-Api-Key** here to match the server's **REFRESH_API_KEY** env value (no JWT)."
    ),
)
def post_markets_refresh(
    body: RefreshBody,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    x_refresh_api_key: str | None = Header(
        default=None,
        alias="X-Refresh-Api-Key",
        description="When REFRESH_API_KEY is set on the server, paste that value here.",
    ),
) -> dict[str, Any]:
    rk = (settings.refresh_api_key or "").strip()
    if rk and (x_refresh_api_key or "").strip() == rk:
        return refresh_catalog(incremental=body.incremental, quiet=True)
    access = _access_from_bearer(credentials)
    if not access.is_admin:
        raise HTTPException(status_code=403, detail="admin only")
    return refresh_catalog(incremental=body.incremental, quiet=True)


@router.get("/db/markets")
def get_db_markets(
    limit: int = 100,
    offset: int = 0,
    active: bool | None = None,
    closed: bool | None = None,
    q: str | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    return list_markets_from_db(
        limit=limit, offset=offset, active=active, closed=closed, q=q, sort=sort
    )


@router.get("/markets/{query}/live")
def get_market_live(query: str) -> dict[str, Any]:
    m = svc_exc(lambda: fetch_market(query))
    if not m:
        raise HTTPException(status_code=404, detail="market not found")
    return m


@router.get("/markets/{query}/cached")
def get_market_cached(query: str) -> dict[str, Any]:
    m = market_from_db(query)
    if not m:
        raise HTTPException(status_code=404, detail="market not in database")
    return m


@router.get("/markets/{query}/resolved")
def get_market_resolved(query: str) -> dict[str, Any]:
    m, stale = resolve_market_live_or_db(query)
    if not m:
        raise HTTPException(status_code=404, detail="market not found")
    return {"market": m, "stale": stale}


@router.get("/markets/{query}/full")
def get_market_full(query: str) -> dict[str, Any]:
    m, stale = resolve_market_live_or_db(query)
    if not m:
        raise HTTPException(status_code=404, detail="market not found")
    books = order_books_for_market(m)
    return {"market": m, "stale": stale, "order_books": books}


@router.get("/gamma/markets")
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
