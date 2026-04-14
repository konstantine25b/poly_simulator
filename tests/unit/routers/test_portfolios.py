from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_portfolios(client: TestClient, admin_headers: dict[str, str]) -> None:
    r = client.get("/portfolios", headers=admin_headers)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    assert "id" in rows[0]


def test_portfolios_requires_auth(client: TestClient) -> None:
    r = client.get("/portfolios")
    assert r.status_code == 401
