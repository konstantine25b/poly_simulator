from __future__ import annotations

from fastapi.testclient import TestClient


def test_admin_list_users(client: TestClient, admin_headers: dict[str, str]) -> None:
    r = client.get("/admin/users", headers=admin_headers)
    assert r.status_code == 200
    emails = {row["email"] for row in r.json()}
    assert "admin@test.local" in emails
