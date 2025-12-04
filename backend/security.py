from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .repositories import is_admin
from .settings import settings

bearer_scheme = HTTPBearer(auto_error=False)


def create_admin_token(username: str) -> str:
    payload = {
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.ADMIN_JWT_SECRET, algorithm="HS256")


def decode_bearer(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.ADMIN_JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token non valido") from exc


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer mancante")
    return decode_bearer(credentials.credentials)


async def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    username = user.get("username")
    if not username or not await is_admin(username):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non autorizzato")
    return user


async def require_super_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    username = user.get("username")
    if username != settings.SUPER_ADMIN_USERNAME:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Solo il super admin può farlo")
    return user
