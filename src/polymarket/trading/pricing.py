from __future__ import annotations

from typing import Any

from polymarket.api.prices import best_bid_ask_from_order_book, get_order_book
from polymarket.catalog.order_books import clob_token_ids_for_market


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _outcome_token_quote(market: dict[str, Any], outcome: str) -> tuple[float | None, float | None]:
    idx = _outcome_book_index(market, outcome)
    if idx is None:
        return None, None
    tokens = clob_token_ids_for_market(market)
    if idx >= len(tokens):
        return None, None
    book = get_order_book(str(tokens[idx]))
    bb_ba = best_bid_ask_from_order_book(book)
    return _float_or_none(bb_ba.get("best_bid")), _float_or_none(bb_ba.get("best_ask"))


def _resolve_outcome_price(market: dict[str, Any], outcome: str) -> float:
    label = (outcome or "").strip()
    outcomes = market.get("outcomes") or []
    prices = market.get("outcomePrices") or []
    for i, o in enumerate(outcomes):
        if str(o).strip().lower() == label.lower() and i < len(prices):
            p = _float_or_none(prices[i])
            if p is not None:
                return p
    if label.lower() == "yes" and len(prices) > 0:
        p = _float_or_none(prices[0])
        if p is not None:
            return p
    if label.lower() == "no" and len(prices) > 1:
        p = _float_or_none(prices[1])
        if p is not None:
            return p
    lt = _float_or_none(market.get("lastTradePrice"))
    if lt is not None:
        return lt
    raise ValueError("no price available for this market")


def _outcome_book_index(market: dict[str, Any], outcome: str) -> int | None:
    label = (outcome or "").strip().lower()
    outcomes = market.get("outcomes") or []
    for i, o in enumerate(outcomes):
        if str(o).strip().lower() == label:
            return i
    if label == "yes":
        return 0
    if label == "no" and len(outcomes) >= 2:
        return 1
    return None


def _buy_fill_price(market: dict[str, Any], outcome: str) -> float:
    tok_bb, tok_ba = _outcome_token_quote(market, outcome)
    if tok_ba is not None:
        return tok_ba
    if tok_bb is not None:
        return tok_bb
    bb = _float_or_none(market.get("bestBid"))
    ba = _float_or_none(market.get("bestAsk"))
    idx = _outcome_book_index(market, outcome)
    if idx == 0 and ba is not None:
        return ba
    if idx == 1 and len(market.get("outcomes") or []) >= 2 and bb is not None:
        return 1.0 - bb
    return _resolve_outcome_price(market, outcome)


def _sell_fill_price(market: dict[str, Any], outcome: str) -> float:
    tok_bb, tok_ba = _outcome_token_quote(market, outcome)
    if tok_bb is not None:
        return tok_bb
    if tok_ba is not None:
        return tok_ba
    bb = _float_or_none(market.get("bestBid"))
    ba = _float_or_none(market.get("bestAsk"))
    idx = _outcome_book_index(market, outcome)
    if idx == 0 and bb is not None:
        return bb
    if idx == 1 and len(market.get("outcomes") or []) >= 2 and ba is not None:
        return 1.0 - ba
    return _resolve_outcome_price(market, outcome)


def _mark_price(market: dict[str, Any], outcome: str) -> float:
    tok_bb, tok_ba = _outcome_token_quote(market, outcome)
    if tok_bb is not None:
        return tok_bb
    if tok_ba is not None:
        return tok_ba
    bb = _float_or_none(market.get("bestBid"))
    ba = _float_or_none(market.get("bestAsk"))
    idx = _outcome_book_index(market, outcome)
    if bb is not None and ba is not None:
        mid = (bb + ba) / 2.0
        if idx == 0:
            return mid
        if idx == 1 and len(market.get("outcomes") or []) >= 2:
            return 1.0 - mid
    return _resolve_outcome_price(market, outcome)
