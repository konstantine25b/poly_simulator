from __future__ import annotations

from fastapi.testclient import TestClient


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
