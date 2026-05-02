import json
import time

import httpx

from polymarket.api.cache import TTLCache
from polymarket.api.client import PolymarketClient, gamma_client

_DEFAULT_LIMIT = 100

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
    params: dict = {
        "limit": limit,
        "offset": offset,
        "active": str(active).lower(),
        "closed": str(closed).lower(),
        "order": order,
        "ascending": str(ascending).lower(),
    }
    raw = c.get("/markets", params=params)
    markets = [_normalize(m) for m in (raw if isinstance(raw, list) else [])]
    if accepting_orders:
        markets = [m for m in markets if m.get("acceptingOrders") is True]
    return markets


def get_all_active_markets(client: PolymarketClient | None = None) -> list[dict]:
    c = client or gamma_client()
    all_markets: list[dict] = []
    offset = 0

    while True:
        batch = get_markets(client=c, limit=_DEFAULT_LIMIT, offset=offset)
        if not batch:
            break
        all_markets.extend(batch)
        if len(batch) < _DEFAULT_LIMIT:
            break
        offset += _DEFAULT_LIMIT

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
