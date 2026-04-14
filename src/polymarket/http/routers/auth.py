from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from polymarket.auth import (
    Access,
    fetch_user_by_email,
    fetch_user_by_id,
    hash_password,
    insert_user,
    issue_access_token,
    normalize_email,
    verify_password,
)
from polymarket.config import settings
from polymarket.db import get_connection
from polymarket.http.deps import get_access
from polymarket.http.schemas import LoginBody, RegisterBody, email_ok

router = APIRouter(tags=["auth"])


@router.post("/auth/register")
def auth_register(body: RegisterBody) -> dict[str, Any]:
    email = normalize_email(body.email)
    if not email_ok(email):
        raise HTTPException(status_code=400, detail="invalid email")
    conn = get_connection()
    try:
        if fetch_user_by_email(conn, email):
            raise HTTPException(status_code=409, detail="email already registered")
        uid = insert_user(
            conn,
            email=email,
            password_hash=hash_password(body.password),
            is_admin=False,
        )
        conn.commit()
    finally:
        conn.close()
    tok = issue_access_token(
        user_id=uid,
        is_admin=False,
        secret=settings.jwt_secret,
        ttl_seconds=settings.access_token_ttl_seconds,
    )
    return {
        "access_token": tok,
        "token_type": "bearer",
        "user": {"id": uid, "email": email, "is_admin": False},
    }


@router.post("/auth/login")
def auth_login(body: LoginBody) -> dict[str, Any]:
    email = normalize_email(body.email)
    conn = get_connection()
    try:
        row = fetch_user_by_email(conn, email)
        if not row or not verify_password(body.password, str(row["password_hash"])):
            raise HTTPException(status_code=401, detail="invalid email or password")
        uid = int(row["id"])
        ia = bool(int(row["is_admin"]))
    finally:
        conn.close()
    tok = issue_access_token(
        user_id=uid,
        is_admin=ia,
        secret=settings.jwt_secret,
        ttl_seconds=settings.access_token_ttl_seconds,
    )
    return {
        "access_token": tok,
        "token_type": "bearer",
        "user": {"id": uid, "email": email, "is_admin": ia},
    }


@router.get("/auth/me")
def auth_me(access: Access = Depends(get_access)) -> dict[str, Any]:
    conn = get_connection()
    try:
        row = fetch_user_by_id(conn, access.user_id)
        if not row:
            raise HTTPException(status_code=401, detail="user not found")
        return {
            "id": int(row["id"]),
            "email": str(row["email"]),
            "is_admin": bool(int(row["is_admin"])),
        }
    finally:
        conn.close()
