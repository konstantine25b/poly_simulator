import json

import httpx

from polymarket.api.client import PolymarketClient, gamma_client

_DEFAULT_LIMIT = 100


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
    return market


def get_markets(
    client: PolymarketClient | None = None,
    limit: int = _DEFAULT_LIMIT,
    offset: int = 0,
    active: bool = True,
    closed: bool = False,
) -> list[dict]:
    c = client or gamma_client()
    params: dict = {
        "limit": limit,
        "offset": offset,
        "active": str(active).lower(),
        "closed": str(closed).lower(),
    }
    raw = c.get("/markets", params=params)
    return [_normalize(m) for m in (raw if isinstance(raw, list) else [])]


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
