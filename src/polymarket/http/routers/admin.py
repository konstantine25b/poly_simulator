from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from polymarket.auth import (
    Access,
    delete_user_cascade,
    fetch_user_by_email,
    fetch_user_by_id,
    hash_password,
    insert_user,
    list_users_public,
    normalize_email,
    update_user_password,
)
from polymarket.db import get_connection
from polymarket.http.deps import require_admin
from polymarket.http.schemas import AdminResetPasswordBody, AdminUserCreateBody, email_ok

router = APIRouter()


@router.get("/admin/users")
def admin_list_users(_access: Access = Depends(require_admin)) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        return list_users_public(conn)
    finally:
        conn.close()


@router.post("/admin/users")
def admin_create_user(body: AdminUserCreateBody, _access: Access = Depends(require_admin)) -> dict[str, Any]:
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
            is_admin=body.is_admin,
        )
        conn.commit()
    finally:
        conn.close()
    return {"id": uid, "email": email, "is_admin": body.is_admin}


@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, access: Access = Depends(require_admin)) -> dict[str, Any]:
    if user_id == access.user_id:
        raise HTTPException(status_code=400, detail="cannot delete own account")
    conn = get_connection()
    try:
        row = fetch_user_by_id(conn, user_id)
        if not row:
            raise HTTPException(status_code=404, detail="user not found")
        delete_user_cascade(conn, user_id)
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@router.post("/admin/users/{user_id}/password")
def admin_reset_password(
    user_id: int, body: AdminResetPasswordBody, _access: Access = Depends(require_admin)
) -> dict[str, Any]:
    conn = get_connection()
    try:
        row = fetch_user_by_id(conn, user_id)
        if not row:
            raise HTTPException(status_code=404, detail="user not found")
        update_user_password(conn, user_id, hash_password(body.password))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}
