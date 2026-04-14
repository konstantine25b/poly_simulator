from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from polymarket import db
from polymarket.db import get_connection, upsert_markets


def test_db_markets_list(client: TestClient) -> None:
    conn = get_connection()
    upsert_markets(
        conn,
        [
            {
                "id": "m_api_list",
                "question": "API list unique question",
                "slug": "api-list-unique-slug",
                "active": 1,
                "closed": 0,
            }
        ],
    )
    conn.close()
    r = client.get("/db/markets?q=API+list+unique&limit=20")
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] >= 1
    assert any(row.get("id") == "m_api_list" for row in payload["items"])


@patch("polymarket.http.routers.markets.refresh_catalog")
def test_refresh_quiet(mock_refresh, client: TestClient, admin_headers: dict[str, str]) -> None:
    mock_refresh.return_value = {"inserted": 0}
    r = client.post(
        "/markets/refresh",
        json={"incremental": True},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json() == {"inserted": 0}
    mock_refresh.assert_called_once_with(incremental=True, quiet=True)


def test_refresh_requires_admin(client: TestClient) -> None:
    r = client.post("/auth/register", json={"email": "nobody@test.local", "password": "password12345"})
    tok = r.json()["access_token"]
    r2 = client.post(
        "/markets/refresh",
        json={"incremental": True},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r2.status_code == 403


def test_refresh_requires_auth(client: TestClient) -> None:
    r = client.post("/markets/refresh", json={"incremental": True})
    assert r.status_code == 401


@patch("polymarket.http.routers.markets.refresh_catalog")
def test_refresh_via_x_refresh_api_key(
    mock_refresh, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_refresh.return_value = {"inserted": 0}
    monkeypatch.setattr(db.settings, "refresh_api_key", "unit-test-refresh-secret")
    r = client.post(
        "/markets/refresh",
        json={"incremental": False},
        headers={"X-Refresh-Api-Key": "unit-test-refresh-secret"},
    )
    assert r.status_code == 200
    assert r.json() == {"inserted": 0}
    mock_refresh.assert_called_once_with(incremental=False, quiet=True)
