from unittest.mock import MagicMock

import httpx

from polymarket.api.markets import (
    _normalize,
    _parse_json_field,
    get_all_active_markets,
    get_market_by_id,
    get_markets,
)


class TestParseJsonField:
    def test_parses_valid_json_array(self) -> None:
        assert _parse_json_field('["Yes", "No"]') == ["Yes", "No"]

    def test_parses_numeric_array(self) -> None:
        assert _parse_json_field('["0.65", "0.35"]') == ["0.65", "0.35"]

    def test_returns_empty_list_for_none(self) -> None:
        assert _parse_json_field(None) == []

    def test_returns_empty_list_for_empty_string(self) -> None:
        assert _parse_json_field("") == []

    def test_returns_empty_list_for_invalid_json(self) -> None:
        assert _parse_json_field("not-json") == []

    def test_returns_empty_list_for_malformed_json(self) -> None:
        assert _parse_json_field("[unclosed") == []


class TestNormalize:
    def test_parses_all_json_string_fields(self, raw_market: dict) -> None:
        result = _normalize(raw_market)
        assert result["outcomes"] == ["Yes", "No"]
        assert result["outcomePrices"] == ["0.65", "0.35"]
        assert result["clobTokenIds"] == ["token-yes", "token-no"]

    def test_returns_empty_lists_when_fields_missing(self) -> None:
        result = _normalize({"id": "1", "question": "Q?"})
        assert result["outcomes"] == []
        assert result["outcomePrices"] == []
        assert result["clobTokenIds"] == []

    def test_mutates_and_returns_same_dict(self, raw_market: dict) -> None:
        result = _normalize(raw_market)
        assert result is raw_market


class TestGetMarkets:
    def test_returns_normalized_markets(self, raw_market: dict) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = [raw_market]

        result = get_markets(client=mock_client, limit=10)

        assert len(result) == 1
        assert result[0]["outcomes"] == ["Yes", "No"]
        assert result[0]["outcomePrices"] == ["0.65", "0.35"]
        assert result[0]["clobTokenIds"] == ["token-yes", "token-no"]

    def test_sends_correct_params_defaults(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = []

        get_markets(client=mock_client)

        mock_client.get.assert_called_once_with(
            "/markets",
            params={
                "limit": 100,
                "offset": 0,
                "active": "true",
                "closed": "false",
                "order": "createdAt",
                "ascending": "false",
            },
        )

    def test_sends_correct_params_custom(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = []

        get_markets(client=mock_client, limit=10, offset=20, active=False, closed=True)

        mock_client.get.assert_called_once_with(
            "/markets",
            params={
                "limit": 10,
                "offset": 20,
                "active": "false",
                "closed": "true",
                "order": "createdAt",
                "ascending": "false",
            },
        )

    def test_returns_empty_list_when_api_returns_empty(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = []

        assert get_markets(client=mock_client) == []

    def test_handles_non_list_api_response_gracefully(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = {"error": "unexpected"}

        assert get_markets(client=mock_client) == []

    def test_returns_multiple_markets(self, raw_market: dict) -> None:
        second = dict(raw_market)
        second["id"] = "456"
        mock_client = MagicMock()
        mock_client.get.return_value = [raw_market, second]

        result = get_markets(client=mock_client)

        assert len(result) == 2
        assert result[1]["id"] == "456"


class TestGetAllActiveMarkets:
    def test_fetches_single_page_when_less_than_limit(self, raw_market: dict) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = [raw_market]

        result = get_all_active_markets(client=mock_client)

        assert len(result) == 1
        assert mock_client.get.call_count == 1

    def test_paginates_until_partial_page(self, raw_market: dict) -> None:
        full_page = [dict(raw_market, id=str(i)) for i in range(100)]
        partial_page = [dict(raw_market, id=str(i)) for i in range(100, 120)]

        mock_client = MagicMock()
        mock_client.get.side_effect = [full_page, partial_page]

        result = get_all_active_markets(client=mock_client)

        assert len(result) == 120
        assert mock_client.get.call_count == 2

    def test_stops_on_empty_page(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = []

        result = get_all_active_markets(client=mock_client)

        assert result == []
        assert mock_client.get.call_count == 1

    def test_second_page_uses_correct_offset(self, raw_market: dict) -> None:
        full_page = [dict(raw_market, id=str(i)) for i in range(100)]

        mock_client = MagicMock()
        mock_client.get.side_effect = [full_page, []]

        get_all_active_markets(client=mock_client)

        first_call_params = mock_client.get.call_args_list[0][1]["params"]
        second_call_params = mock_client.get.call_args_list[1][1]["params"]

        assert first_call_params["offset"] == 0
        assert second_call_params["offset"] == 100


class TestGetMarketById:
    def test_returns_normalized_market(self, raw_market: dict) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = [raw_market]

        result = get_market_by_id("123", client=mock_client)

        assert result is not None
        assert result["id"] == "123"
        assert result["outcomes"] == ["Yes", "No"]

    def test_sends_correct_params(self, raw_market: dict) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = [raw_market]

        get_market_by_id("123", client=mock_client)

        mock_client.get.assert_called_once_with(
            "/markets", params={"id": "123", "limit": 1}
        )

    def test_returns_none_when_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = []

        assert get_market_by_id("999", client=mock_client) is None

    def test_returns_none_on_http_error(self) -> None:
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "422", request=MagicMock(), response=MagicMock()
        )

        assert get_market_by_id("bad-id", client=mock_client) is None

    def test_returns_none_on_non_list_response(self) -> None:
        mock_client = MagicMock()
        mock_client.get.return_value = {}

        assert get_market_by_id("123", client=mock_client) is None
