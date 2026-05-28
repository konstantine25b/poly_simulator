from __future__ import annotations

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str, password: str = "password12345") -> tuple[str, int]:
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200
    body = r.json()
    return body["access_token"], body["user"]["id"]


def test_delete_account_requires_correct_password(client: TestClient) -> None:
    tok, _ = _register(client, "del1@example.com")
    r = client.post(
        "/auth/delete-account",
        headers={"Authorization": f"Bearer {tok}"},
        json={"password": "wrong-password"},
    )
    assert r.status_code == 401


def test_delete_account_blocks_login_and_me(client: TestClient) -> None:
    tok, _ = _register(client, "del2@example.com")
    headers = {"Authorization": f"Bearer {tok}"}

    r = client.post("/auth/delete-account", headers=headers, json={"password": "password12345"})
    assert r.status_code == 200
    assert r.json()["deleted"] is True

    r2 = client.get("/auth/me", headers=headers)
    assert r2.status_code == 401

    r3 = client.post(
        "/auth/login",
        json={"email": "del2@example.com", "password": "password12345"},
    )
    assert r3.status_code == 403


def test_delete_account_idempotent_rejection(client: TestClient) -> None:
    tok, _ = _register(client, "del3@example.com")
    headers = {"Authorization": f"Bearer {tok}"}
    r = client.post("/auth/delete-account", headers=headers, json={"password": "password12345"})
    assert r.status_code == 200
    r2 = client.post("/auth/delete-account", headers=headers, json={"password": "password12345"})
    assert r2.status_code == 401


def test_admin_cannot_self_delete(client: TestClient, admin_headers: dict[str, str]) -> None:
    r = client.post("/auth/delete-account", headers=admin_headers, json={"password": "password12345"})
    assert r.status_code == 400


def test_admin_restore_flow(client: TestClient, admin_headers: dict[str, str]) -> None:
    tok, uid = _register(client, "del4@example.com")
    r = client.post(
        "/auth/delete-account",
        headers={"Authorization": f"Bearer {tok}"},
        json={"password": "password12345"},
    )
    assert r.status_code == 200

    users = client.get("/admin/users", headers=admin_headers).json()
    target = next(u for u in users if u["email"] == "del4@example.com")
    assert target["is_deleted"] is True

    r2 = client.post(f"/admin/users/{uid}/restore", headers=admin_headers)
    assert r2.status_code == 200
    assert r2.json()["restored"] is True

    r3 = client.post(
        "/auth/login",
        json={"email": "del4@example.com", "password": "password12345"},
    )
    assert r3.status_code == 200


def test_admin_restore_rejects_active_user(client: TestClient, admin_headers: dict[str, str]) -> None:
    _, uid = _register(client, "del5@example.com")
    r = client.post(f"/admin/users/{uid}/restore", headers=admin_headers)
    assert r.status_code == 400


def test_admin_restore_unknown_user(client: TestClient, admin_headers: dict[str, str]) -> None:
    r = client.post("/admin/users/99999/restore", headers=admin_headers)
    assert r.status_code == 404


def test_admin_restore_requires_admin(client: TestClient) -> None:
    tok, _ = _register(client, "del6@example.com")
    r = client.post(
        "/admin/users/1/restore",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 403


def test_delete_account_requires_auth(client: TestClient) -> None:
    r = client.post("/auth/delete-account", json={"password": "password12345"})
    assert r.status_code == 401


def test_portfolio_summary_shows_owner_deleted(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    tok, _ = _register(client, "del7@example.com")
    headers = {"Authorization": f"Bearer {tok}"}
    r = client.post(
        "/portfolios",
        headers=headers,
        json={"name": "delowner", "balance": 100.0},
    )
    assert r.status_code == 200
    pid = r.json()["id"]

    r = client.post("/auth/delete-account", headers=headers, json={"password": "password12345"})
    assert r.status_code == 200

    rows = client.get("/portfolios", headers=admin_headers).json()
    target = next(p for p in rows if p["id"] == pid)
    assert target["owner_deleted"] is True

    summary = client.get(f"/portfolios/{pid}/summary", headers=admin_headers).json()
    assert summary["owner_deleted"] is True
    assert summary["portfolio_id"] == pid
