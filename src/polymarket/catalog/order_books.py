from __future__ import annotations

import json
from typing import Any

from polymarket.api.prices import get_order_book


def _parse_list_field(value: object) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            pass
    return []


def clob_token_ids_for_market(market: dict[str, Any]) -> list[str]:
    return [str(t) for t in _parse_list_field(market.get("clobTokenIds"))]


def order_books_for_market(market: dict[str, Any]) -> list[dict[str, Any]]:
    tokens = clob_token_ids_for_market(market)
    outcomes = _parse_list_field(market.get("outcomes"))
    books: list[dict[str, Any]] = []
    for i, token_id in enumerate(tokens):
        label = str(outcomes[i]) if i < len(outcomes) else f"token_{i}"
        book = get_order_book(str(token_id))
        books.append({"outcome": label, "token_id": str(token_id), "book": book})
    return books
