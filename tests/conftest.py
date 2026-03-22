import pytest


@pytest.fixture
def raw_market() -> dict:
    return {
        "id": "123",
        "question": "Will X happen?",
        "conditionId": "0xabc",
        "slug": "will-x-happen",
        "outcomes": '["Yes", "No"]',
        "outcomePrices": '["0.65", "0.35"]',
        "clobTokenIds": '["token-yes", "token-no"]',
        "active": True,
        "closed": False,
        "volumeNum": 10000.0,
        "liquidityNum": 5000.0,
        "lastTradePrice": 0.65,
        "bestBid": 0.64,
        "bestAsk": 0.66,
        "events": [{"id": "99", "title": "Event X"}],
    }


@pytest.fixture
def normalized_market(raw_market: dict) -> dict:
    m = dict(raw_market)
    m["outcomes"] = ["Yes", "No"]
    m["outcomePrices"] = ["0.65", "0.35"]
    m["clobTokenIds"] = ["token-yes", "token-no"]
    return m
