from __future__ import annotations

from typing import Any

from polymarket.api.markets import fetch_market
from polymarket.catalog.order_books import best_quotes_for_market
from polymarket.catalog.queries import market_from_db


def _truthy_closed(m: dict[str, Any]) -> bool:
    c = m.get("closed")
    if c is True:
        return True
    if isinstance(c, (int, float)) and int(c) == 1:
        return True
    if isinstance(c, str) and c.strip().lower() in ("1", "true", "yes"):
        return True
    return False


def market_detail_payload(query: str) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        raise ValueError("market not found")

    cached = market_from_db(q)
    live: dict[str, Any] | None = None
    try:
        live = fetch_market(q)
    except Exception:
        live = None

    if cached is not None and _truthy_closed(cached):
        return {
            "closed": True,
            "source": "database",
            "market": cached,
            "best_quotes": [],
        }

    if live is not None and _truthy_closed(live):
        if cached is not None:
            return {
                "closed": True,
                "source": "database",
                "market": cached,
                "best_quotes": [],
            }
        return {
            "closed": True,
            "source": "live",
            "market": live,
            "best_quotes": [],
        }

    if live is not None:
        return {
            "closed": False,
            "source": "live",
            "market": live,
            "best_quotes": best_quotes_for_market(live),
        }

    if cached is not None and not _truthy_closed(cached):
        return {
            "closed": False,
            "source": "database",
            "stale": True,
            "market": cached,
            "best_quotes": best_quotes_for_market(cached),
        }

    raise ValueError("market not found")
