from __future__ import annotations

import hashlib
import hmac
import secrets

_ITER = 480_000
_PREFIX = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        _ITER,
    )
    return f"{_PREFIX}${_ITER}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored or not stored.startswith(f"{_PREFIX}$"):
        return False
    parts = stored.split("$", 3)
    if len(parts) != 4:
        return False
    _, it_s, salt, hx = parts
    try:
        iterations = int(it_s)
    except ValueError:
        return False
    try:
        expected = bytes.fromhex(hx)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        iterations,
    )
    return hmac.compare_digest(dk, expected)
