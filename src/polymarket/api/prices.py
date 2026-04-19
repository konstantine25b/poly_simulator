from typing import Any

import httpx

from polymarket.api.client import PolymarketClient, clob_client


def best_bid_ask_from_order_book(book: dict | None) -> dict[str, Any]:
    if not book or not isinstance(book, dict):
        return {"best_bid": None, "best_ask": None}
    bids = sorted(book.get("bids", []), key=lambda x: float(x["price"]), reverse=True)
    asks = sorted(book.get("asks", []), key=lambda x: float(x["price"]))
    best_bid = float(bids[0]["price"]) if bids else None
    best_ask = float(asks[0]["price"]) if asks else None
    return {"best_bid": best_bid, "best_ask": best_ask}


def get_order_book(token_id: str, client: PolymarketClient | None = None) -> dict | None:
    c = client or clob_client()
    try:
        raw = c.get("/book", params={"token_id": token_id})
        return raw if isinstance(raw, dict) else None
    except httpx.HTTPStatusError:
        return None


def get_last_trade_price(token_id: str, client: PolymarketClient | None = None) -> float | None:
    c = client or clob_client()
    try:
        raw = c.get("/last-trade-price", params={"token_id": token_id})
        price = raw.get("price") if isinstance(raw, dict) else None  # type: ignore[union-attr]
        return float(price) if price else None
    except (httpx.HTTPStatusError, ValueError, TypeError):
        return None


def get_midpoint(token_id: str, client: PolymarketClient | None = None) -> float | None:
    c = client or clob_client()
    try:
        raw = c.get("/midpoint", params={"token_id": token_id})
        mid = raw.get("mid") if isinstance(raw, dict) else None  # type: ignore[union-attr]
        return float(mid) if mid else None
    except (httpx.HTTPStatusError, ValueError, TypeError):
        return None
