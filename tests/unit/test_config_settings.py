from __future__ import annotations

import pytest

from polymarket.config import Settings
from polymarket.auth import issue_access_token, parse_access_token


def test_jwt_secret_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-loaded-from-environment")
    fresh = Settings()
    assert fresh.jwt_secret == "test-jwt-secret-loaded-from-environment"


def test_token_issue_and_parse_use_settings_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "roundtrip-secret-for-token-test")
    s = Settings()
    tok = issue_access_token(
        user_id=42,
        is_admin=False,
        secret=s.jwt_secret,
        ttl_seconds=3600,
    )
    payload = parse_access_token(tok, s.jwt_secret)
    assert int(payload["sub"]) == 42
    assert int(payload.get("adm", 0)) == 0
