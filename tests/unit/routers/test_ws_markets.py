from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


@patch(
    "polymarket.http.routers.ws_markets.resolve_market_live_or_db",
    return_value=(
        {
            "id": "999",
            "slug": "my-example-market",
            "clobTokenIds": ["111", "222"],
        },
        False,
    ),
)
def test_ws_docs_resolves_query(_mock: object, client: TestClient) -> None:
    r = client.get("/markets/my-example-market/best-bid-ask/ws-docs")
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == "my-example-market"
    assert data["market_id"] == "999"
    assert data["slug"] == "my-example-market"
    assert data["subscribed_asset_ids"] == ["111", "222"]
    assert data["websocket_path"] == "/ws/markets/my-example-market/best-bid-ask"
    assert data["message_shape"]["event_type"] == "best_bid_ask"


@patch(
    "polymarket.http.routers.ws_markets.resolve_market_live_or_db",
    return_value=(None, False),
)
def test_ws_docs_not_found(_mock: object, client: TestClient) -> None:
    r = client.get("/markets/missing-slug-zz/best-bid-ask/ws-docs")
    assert r.status_code == 404


@patch(
    "polymarket.http.routers.ws_markets.resolve_market_live_or_db",
    return_value=({"id": "m1", "slug": "s", "clobTokenIds": []}, False),
)
def test_ws_docs_no_tokens(_mock: object, client: TestClient) -> None:
    r = client.get("/markets/s/best-bid-ask/ws-docs")
    assert r.status_code == 404


@patch(
    "polymarket.http.routers.ws_markets.resolve_market_live_or_db",
    return_value=(None, False),
)
def test_ws_best_bid_ask_market_not_found(_mock: object, client: TestClient) -> None:
    with client.websocket_connect("/ws/markets/no-such-market-slug-zz/best-bid-ask") as ws:
        body = ws.receive_json()
    assert body == {"error": "market not found"}


@patch(
    "polymarket.http.routers.ws_markets.resolve_market_live_or_db",
    return_value=({"id": "m1", "slug": "s", "clobTokenIds": []}, False),
)
def test_ws_best_bid_ask_no_tokens(_mock: object, client: TestClient) -> None:
    with client.websocket_connect("/ws/markets/s/best-bid-ask") as ws:
        body = ws.receive_json()
    assert body == {"error": "no clob tokens for market"}
