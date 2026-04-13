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
    from polymarket.http_app import app

    with TestClient(app) as tc:
        yield tc


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_portfolios(client: TestClient) -> None:
    r = client.get("/portfolios")
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


@patch("polymarket.http_app.refresh_catalog")
def test_refresh_quiet(mock_refresh, client: TestClient) -> None:
    mock_refresh.return_value = {"inserted": 0}
    r = client.post("/markets/refresh", json={"incremental": True})
    assert r.status_code == 200
    assert r.json() == {"inserted": 0}
    mock_refresh.assert_called_once_with(incremental=True, quiet=True)
