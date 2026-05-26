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
    assert r2.json()["username"] is None
    assert r2.json()["is_admin"] is False


def test_profile_username_and_reset_password(client: TestClient) -> None:
    r = client.post(
        "/auth/register",
        json={"email": "u2@example.com", "password": "password12345"},
    )
    assert r.status_code == 200
    tok = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {tok}"}

    r2 = client.patch("/auth/profile", headers=headers, json={"username": "trader_u2"})
    assert r2.status_code == 200
    assert r2.json()["username"] == "trader_u2"

    r3 = client.get("/auth/me", headers=headers)
    assert r3.json()["username"] == "trader_u2"

    r4 = client.post(
        "/auth/reset-password",
        headers=headers,
        json={
            "email": "u2@example.com",
            "current_password": "password12345",
            "new_password": "newpassword99",
        },
    )
    assert r4.status_code == 200

    r5 = client.post(
        "/auth/login",
        json={"email": "u2@example.com", "password": "newpassword99"},
    )
    assert r5.status_code == 200
