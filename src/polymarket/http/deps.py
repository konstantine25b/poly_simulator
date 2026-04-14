from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from polymarket.auth import Access, parse_access_token
from polymarket.config import settings

_bearer = HTTPBearer(auto_error=False)

_MISSING_BEARER = (
    "missing credentials: open /docs, click Authorize, scheme HTTPBearer, paste the access_token "
    "from POST /auth/login (admin account for this route). Or send header "
    "Authorization: Bearer <token>. If the server has REFRESH_API_KEY set in env, send "
    "header X-Refresh-Api-Key with that value instead."
)


def _access_from_bearer(credentials: HTTPAuthorizationCredentials | None) -> Access:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail=_MISSING_BEARER)
    raw = credentials.credentials.strip()
    try:
        payload = parse_access_token(raw, settings.jwt_secret)
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid or expired token") from None
    uid = int(payload["sub"])
    adm = bool(int(payload.get("adm", 0)))
    return Access(user_id=uid, is_admin=adm)


def get_access(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Access:
    return _access_from_bearer(credentials)


def require_admin(access: Access = Depends(get_access)) -> Access:
    if not access.is_admin:
        raise HTTPException(status_code=403, detail="admin only")
    return access
