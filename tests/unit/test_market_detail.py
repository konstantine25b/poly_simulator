from __future__ import annotations

from unittest.mock import patch

import pytest

from polymarket.catalog import market_detail


def test_closed_prefers_database() -> None:
    cached = {"id": "x", "closed": 1, "question": "Old Q", "slug": "s"}
    with patch.object(market_detail, "market_from_db", return_value=cached):
        with patch.object(market_detail, "fetch_market", return_value=None):
            out = market_detail.market_detail_payload("s")
    assert out["closed"] is True
    assert out["source"] == "database"
    assert out["market"]["question"] == "Old Q"
    assert out["best_quotes"] == []


def test_live_open_returns_quotes() -> None:
    live = {"id": "1", "closed": False, "question": "L", "clobTokenIds": ["t1"], "outcomes": ["Yes"]}
    quotes = [{"outcome": "Yes", "token_id": "t1", "best_bid": 0.4, "best_ask": 0.41}]
    with patch.object(market_detail, "market_from_db", return_value={"id": "1", "closed": 0}):
        with patch.object(market_detail, "fetch_market", return_value=live):
            with patch.object(market_detail, "best_quotes_for_market", return_value=quotes):
                out = market_detail.market_detail_payload("1")
    assert out["closed"] is False
    assert out["source"] == "live"
    assert out["best_quotes"] == quotes


def test_not_found() -> None:
    with patch.object(market_detail, "market_from_db", return_value=None):
        with patch.object(market_detail, "fetch_market", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                market_detail.market_detail_payload("ghost")
