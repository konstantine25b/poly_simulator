from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

import polymarket.api.prices as prices_module
from polymarket.api.prices import (
    best_bid_ask_from_order_book,
    get_last_trade_price,
    get_midpoint,
    get_order_book,
)


@pytest.fixture(autouse=True)
def _clear_book_cache() -> None:
    prices_module._book_cache.clear()


class TestBestBidAskFromOrderBook:
    def test_returns_top_of_book(self) -> None:
        book = {
            "bids": [{"price": "0.40"}, {"price": "0.45"}, {"price": "0.42"}],
            "asks": [{"price": "0.55"}, {"price": "0.50"}, {"price": "0.52"}],
        }
        result = best_bid_ask_from_order_book(book)
        assert result == {"best_bid": 0.45, "best_ask": 0.50}

    def test_handles_empty_book(self) -> None:
        assert best_bid_ask_from_order_book({"bids": [], "asks": []}) == {
            "best_bid": None,
            "best_ask": None,
        }

    def test_handles_none(self) -> None:
        assert best_bid_ask_from_order_book(None) == {"best_bid": None, "best_ask": None}

    def test_handles_non_dict(self) -> None:
        assert best_bid_ask_from_order_book("not-a-dict") == {  # type: ignore[arg-type]
            "best_bid": None,
            "best_ask": None,
        }

    def test_handles_only_bids(self) -> None:
        book = {"bids": [{"price": "0.30"}]}
        result = best_bid_ask_from_order_book(book)
        assert result == {"best_bid": 0.30, "best_ask": None}


class TestGetOrderBook:
    def test_returns_book_dict(self) -> None:
        client = MagicMock()
        client.get.return_value = {"bids": [{"price": "0.5"}], "asks": []}
        result = get_order_book("token-1", client=client)
        assert result == {"bids": [{"price": "0.5"}], "asks": []}
        client.get.assert_called_once_with("/book", params={"token_id": "token-1"})

    def test_returns_none_on_http_error(self) -> None:
        client = MagicMock()
        client.get.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )
        assert get_order_book("token-1", client=client) is None

    def test_returns_none_on_non_dict_response(self) -> None:
        client = MagicMock()
        client.get.return_value = ["not", "a", "dict"]
        assert get_order_book("token-1", client=client) is None

    def test_returns_none_for_empty_token_id(self) -> None:
        client = MagicMock()
        assert get_order_book("", client=client) is None
        client.get.assert_not_called()


class TestGetOrderBookCaching:
    def test_caches_successful_response(self) -> None:
        client = MagicMock()
        client.get.return_value = {"bids": [], "asks": []}
        get_order_book("token-1", client=client)
        get_order_book("token-1", client=client)
        assert client.get.call_count == 1

    def test_caches_per_token_id(self) -> None:
        client = MagicMock()
        client.get.return_value = {"bids": [], "asks": []}
        get_order_book("token-1", client=client)
        get_order_book("token-2", client=client)
        assert client.get.call_count == 2

    def test_caches_none_results(self) -> None:
        client = MagicMock()
        client.get.return_value = "garbage"
        assert get_order_book("token-1", client=client) is None
        assert get_order_book("token-1", client=client) is None
        assert client.get.call_count == 1

    def test_cache_clear_forces_refetch(self) -> None:
        client = MagicMock()
        client.get.return_value = {"bids": [], "asks": []}
        get_order_book("token-1", client=client)
        prices_module._book_cache.clear()
        get_order_book("token-1", client=client)
        assert client.get.call_count == 2


class TestGetLastTradePrice:
    def test_parses_price(self) -> None:
        client = MagicMock()
        client.get.return_value = {"price": "0.42"}
        assert get_last_trade_price("t", client=client) == pytest.approx(0.42)

    def test_returns_none_on_missing_price(self) -> None:
        client = MagicMock()
        client.get.return_value = {}
        assert get_last_trade_price("t", client=client) is None

    def test_returns_none_on_http_error(self) -> None:
        client = MagicMock()
        client.get.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        assert get_last_trade_price("t", client=client) is None


class TestGetMidpoint:
    def test_parses_midpoint(self) -> None:
        client = MagicMock()
        client.get.return_value = {"mid": "0.55"}
        assert get_midpoint("t", client=client) == pytest.approx(0.55)

    def test_returns_none_on_missing_mid(self) -> None:
        client = MagicMock()
        client.get.return_value = {}
        assert get_midpoint("t", client=client) is None

    def test_returns_none_on_http_error(self) -> None:
        client = MagicMock()
        client.get.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        assert get_midpoint("t", client=client) is None
