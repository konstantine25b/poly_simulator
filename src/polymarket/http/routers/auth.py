from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from polymarket.auth import (
    Access,
    fetch_user_by_email,
    fetch_user_by_id,
    fetch_user_by_username,
    hash_password,
    insert_user,
    issue_access_token,
    normalize_email,
    normalize_username,
    update_user_password,
    update_user_username,
    verify_password,
)
from polymarket.config import settings
from polymarket.db import get_connection
from polymarket.http.deps import get_access
from polymarket.http.schemas import (
    LoginBody,
    ProfileUpdateBody,
    RegisterBody,
    ResetPasswordBody,
    email_ok,
    username_ok,
)

router = APIRouter(tags=["auth"])


def user_public(row: dict[str, Any]) -> dict[str, Any]:
    un = row.get("username")
    return {
        "id": int(row["id"]),
        "email": str(row["email"]),
        "username": str(un) if un else None,
        "is_admin": bool(int(row["is_admin"])),
    }


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
        row = fetch_user_by_id(conn, uid)
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=500, detail="user create failed")
    tok = issue_access_token(
        user_id=uid,
        is_admin=False,
        secret=settings.jwt_secret,
        ttl_seconds=settings.access_token_ttl_seconds,
    )
    return {
        "access_token": tok,
        "token_type": "bearer",
        "user": user_public(row),
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
        "user": user_public(row),
    }


@router.get("/auth/me")
def auth_me(access: Access = Depends(get_access)) -> dict[str, Any]:
    conn = get_connection()
    try:
        row = fetch_user_by_id(conn, access.user_id)
        if not row:
            raise HTTPException(status_code=401, detail="user not found")
        return user_public(row)
    finally:
        conn.close()


@router.patch("/auth/profile")
def auth_update_profile(
    body: ProfileUpdateBody,
    access: Access = Depends(get_access),
) -> dict[str, Any]:
    raw = body.username
    if raw is None:
        raise HTTPException(status_code=400, detail="username is required")
    conn = get_connection()
    try:
        row = fetch_user_by_id(conn, access.user_id)
        if not row:
            raise HTTPException(status_code=401, detail="user not found")
        if raw == "":
            update_user_username(conn, access.user_id, None)
        else:
            username = normalize_username(raw)
            if not username_ok(username):
                raise HTTPException(
                    status_code=400,
                    detail="username must be 3–24 characters (letters, numbers, underscore)",
                )
            taken = fetch_user_by_username(conn, username)
            if taken and int(taken["id"]) != access.user_id:
                raise HTTPException(status_code=409, detail="username already taken")
            update_user_username(conn, access.user_id, username)
        conn.commit()
        updated = fetch_user_by_id(conn, access.user_id)
        if not updated:
            raise HTTPException(status_code=401, detail="user not found")
        return user_public(updated)
    finally:
        conn.close()


@router.post("/auth/reset-password")
def auth_reset_password(
    body: ResetPasswordBody,
    access: Access = Depends(get_access),
) -> dict[str, str]:
    email = normalize_email(body.email)
    if not email_ok(email):
        raise HTTPException(status_code=400, detail="invalid email")
    conn = get_connection()
    try:
        row = fetch_user_by_id(conn, access.user_id)
        if not row:
            raise HTTPException(status_code=401, detail="user not found")
        if normalize_email(str(row["email"])) != email:
            raise HTTPException(status_code=400, detail="email does not match your account")
        if not verify_password(body.current_password, str(row["password_hash"])):
            raise HTTPException(status_code=401, detail="current password is incorrect")
        update_user_password(conn, access.user_id, hash_password(body.new_password))
        conn.commit()
    finally:
        conn.close()
    return {"status": "ok"}
