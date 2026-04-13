from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def issue_access_token(
    *,
    user_id: int,
    is_admin: bool,
    secret: str,
    ttl_seconds: int,
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "adm": 1 if is_admin else 0,
        "iat": now,
        "exp": now + max(60, ttl_seconds),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(secret.encode("utf-8"), b64.encode("ascii"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    return f"{b64}.{sig_b64}"


def parse_access_token(token: str, secret: str) -> dict[str, Any]:
    parts = token.strip().split(".", 1)
    if len(parts) != 2:
        raise ValueError("invalid token")
    b64, sig_b64 = parts
    pad = "=" * ((4 - len(b64) % 4) % 4)
    sig = base64.urlsafe_b64decode(sig_b64 + ("=" * ((4 - len(sig_b64) % 4) % 4)))
    expected = hmac.new(secret.encode("utf-8"), b64.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid token")
    payload = json.loads(base64.urlsafe_b64decode(b64 + pad))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("token expired")
    return payload
