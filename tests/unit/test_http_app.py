from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from polymarket import db
from polymarket.db import get_connection, upsert_markets


@pytest.fixture(autouse=True)
def force_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db.settings, "db_backend", "sqlite")


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "api.db")
    monkeypatch.setattr(db.settings, "admin_bootstrap_email", "admin@test.local")
    monkeypatch.setattr(db.settings, "admin_bootstrap_password", "password12345")
    monkeypatch.setattr(db.settings, "jwt_secret", "unit-test-jwt-secret")
    from polymarket.http.app import app

    with TestClient(app) as tc:
        yield tc


def _admin_headers(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/auth/login",
        json={"email": "admin@test.local", "password": "password12345"},
    )
    assert r.status_code == 200
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_portfolios(client: TestClient) -> None:
    r = client.get("/portfolios", headers=_admin_headers(client))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    assert "id" in rows[0]


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
def test_refresh_quiet(mock_refresh, client: TestClient) -> None:
    mock_refresh.return_value = {"inserted": 0}
    r = client.post(
        "/markets/refresh",
        json={"incremental": True},
        headers=_admin_headers(client),
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
def test_refresh_via_x_refresh_api_key(mock_refresh, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_portfolios_requires_auth(client: TestClient) -> None:
    r = client.get("/portfolios")
    assert r.status_code == 401


def test_register_then_me(client: TestClient) -> None:
    r = client.post(
        "/auth/register",
        json={"email": "u1@example.com", "password": "password12345"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    tok = body["access_token"]
    r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 200
    assert r2.json()["email"] == "u1@example.com"
    assert r2.json()["is_admin"] is False


def test_admin_list_users(client: TestClient) -> None:
    r = client.get("/admin/users", headers=_admin_headers(client))
    assert r.status_code == 200
    emails = {row["email"] for row in r.json()}
    assert "admin@test.local" in emails
