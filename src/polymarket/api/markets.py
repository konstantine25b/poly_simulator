import json
import time
from collections.abc import Iterator

import httpx

from polymarket.api.cache import TTLCache
from polymarket.api.client import PolymarketClient, gamma_client

_DEFAULT_LIMIT = 100
_MAX_OFFSET = 10_000

_market_cache = TTLCache(ttl_seconds=30.0, miss_ttl_seconds=10.0, max_size=2048)


def _parse_json_field(value: str | None) -> list:
    if not value:
        return []
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []


def _normalize(market: dict) -> dict:
    market["outcomes"] = _parse_json_field(market.get("outcomes"))
    market["outcomePrices"] = _parse_json_field(market.get("outcomePrices"))
    market["clobTokenIds"] = _parse_json_field(market.get("clobTokenIds"))
    events = market.get("events") or []
    market["event_title"] = events[0].get("title") if events else None
    market["event_slug"] = events[0].get("slug") if events else None
    return market


def _list_params(
    *,
    limit: int,
    active: bool,
    closed: bool,
    order: str,
    ascending: bool,
) -> dict:
    return {
        "limit": limit,
        "active": str(active).lower(),
        "closed": str(closed).lower(),
        "order": order,
        "ascending": str(ascending).lower(),
    }


def _filter_accepting_orders(markets: list[dict], accepting_orders: bool) -> list[dict]:
    if not accepting_orders:
        return markets
    return [m for m in markets if m.get("acceptingOrders") is True]


def get_markets(
    client: PolymarketClient | None = None,
    limit: int = _DEFAULT_LIMIT,
    offset: int = 0,
    active: bool = True,
    closed: bool = False,
    accepting_orders: bool = True,
    order: str = "createdAt",
    ascending: bool = False,
) -> list[dict]:
    c = client or gamma_client()
    params = _list_params(
        limit=limit, active=active, closed=closed, order=order, ascending=ascending
    )
    params["offset"] = offset
    raw = c.get("/markets", params=params)
    markets = [_normalize(m) for m in (raw if isinstance(raw, list) else [])]
    return _filter_accepting_orders(markets, accepting_orders)


def get_markets_keyset(
    client: PolymarketClient | None = None,
    limit: int = _DEFAULT_LIMIT,
    after_cursor: str | None = None,
    active: bool = True,
    closed: bool = False,
    order: str = "createdAt",
    ascending: bool = False,
) -> tuple[list[dict], str | None]:
    c = client or gamma_client()
    params = _list_params(
        limit=limit, active=active, closed=closed, order=order, ascending=ascending
    )
    if after_cursor:
        params["after_cursor"] = after_cursor
    raw = c.get("/markets/keyset", params=params)
    if not isinstance(raw, dict):
        return [], None
    markets = [_normalize(m) for m in raw.get("markets") or []]
    return markets, raw.get("next_cursor")


def iter_market_batches(
    client: PolymarketClient | None = None,
    limit: int = _DEFAULT_LIMIT,
    active: bool = True,
    closed: bool = False,
    accepting_orders: bool = True,
    order: str = "createdAt",
    ascending: bool = False,
) -> Iterator[list[dict]]:
    c = client or gamma_client()
    after_cursor: str | None = None

    while True:
        raw_batch, after_cursor = get_markets_keyset(
            client=c,
            limit=limit,
            after_cursor=after_cursor,
            active=active,
            closed=closed,
            order=order,
            ascending=ascending,
        )
        yield _filter_accepting_orders(raw_batch, accepting_orders)
        if not raw_batch or len(raw_batch) < limit or not after_cursor:
            break


def get_all_active_markets(client: PolymarketClient | None = None) -> list[dict]:
    c = client or gamma_client()
    all_markets: list[dict] = []
    for batch in iter_market_batches(client=c):
        all_markets.extend(batch)
    return all_markets


def get_market_tags(market_id: str, client: PolymarketClient | None = None) -> list[dict]:
    c = client or gamma_client()
    try:
        raw = c.get(f"/markets/{market_id}/tags")
        return raw if isinstance(raw, list) else []
    except httpx.HTTPStatusError:
        return []


def get_market_by_id(market_id: str, client: PolymarketClient | None = None) -> dict | None:
    c = client or gamma_client()
    try:
        raw = c.get("/markets", params={"id": market_id, "limit": 1})
        results: list = raw if isinstance(raw, list) else []
    except httpx.HTTPStatusError:
        return None
    if not results:
        return None
    return _normalize(results[0])


def get_market_by_slug(slug: str, client: PolymarketClient | None = None) -> dict | None:
    c = client or gamma_client()
    try:
        raw = c.get("/markets", params={"slug": slug, "limit": 1})
        results: list = raw if isinstance(raw, list) else []
    except httpx.HTTPStatusError:
        return None
    if not results:
        return None
    return _normalize(results[0])


def _fetch_market_uncached(
    query: str, client: PolymarketClient | None, attempts: int
) -> dict | None:
    owns = client is None
    c = client or gamma_client()
    try:
        for i in range(max(1, attempts)):
            if i:
                time.sleep(0.25 * i)
            try:
                if query.isdigit():
                    m = get_market_by_id(query, c)
                else:
                    m = get_market_by_slug(query, c)
            except httpx.HTTPError:
                m = None
            if m:
                return m
        return None
    finally:
        if owns:
            c.close()


def fetch_market(query: str, client: PolymarketClient | None = None, attempts: int = 3) -> dict | None:
    if not isinstance(query, str) or not query.strip():
        return None
    key = query.strip().lower()
    return _market_cache.get_or_compute(
        key, lambda: _fetch_market_uncached(query, client, attempts)
    )
