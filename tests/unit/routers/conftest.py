from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from polymarket import db


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "api.db")
    monkeypatch.setattr(db.settings, "admin_bootstrap_email", "admin@test.local")
    monkeypatch.setattr(db.settings, "admin_bootstrap_password", "password12345")
    monkeypatch.setattr(db.settings, "jwt_secret", "unit-test-jwt-secret")
    from polymarket.http.app import app

    with TestClient(app) as tc:
        yield tc


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/auth/login",
        json={"email": "admin@test.local", "password": "password12345"},
    )
    assert r.status_code == 200
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}
