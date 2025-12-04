from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from ..models import AuthRequest, AuthResponse, TokenResponse, UserResponse
from ..repositories import (
    consume_token,
    generate_magic_token,
    is_admin,
    put_token,
)
from ..security import bearer_scheme, create_admin_token, get_current_user, require_super_admin, decode_bearer
from ..settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("", response_model=UserResponse)
async def whoami(user=Depends(get_current_user)) -> UserResponse:
    return UserResponse(user=user)


@router.post("", responses={201: {"model": TokenResponse}})
async def handle_auth(body: AuthRequest, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    intent = body.intent or "exchange"
    user = decode_bearer(credentials.credentials) if credentials else None

    if intent == "password":
        if body.password != settings.ADMIN_STATIC_PASSWORD:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password errata")
        token = create_admin_token(settings.SUPER_ADMIN_USERNAME)
        return AuthResponse(bearer=token, expiresInMinutes=settings.TOKEN_TTL_MINUTES)

    if intent == "create":
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token mancante")
        await require_super_admin(user)
        if not body.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username obbligatorio")
        tmp_token = await generate_magic_token()
        await put_token(tmp_token, body.username, settings.TOKEN_TTL_MINUTES * 60)
        return TokenResponse(token=tmp_token, expiresInMinutes=settings.TOKEN_TTL_MINUTES)

    if intent == "exchange":
        if not body.token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token obbligatorio")
        owner = await consume_token(body.token)
        if not owner or not await is_admin(owner):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token non valido")
        token = create_admin_token(owner)
        return AuthResponse(bearer=token, expiresInMinutes=settings.TOKEN_TTL_MINUTES)

    if intent == "impersonate":
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token mancante")
        await require_super_admin(user)
        if not body.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username obbligatorio")
        if not await is_admin(body.username):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin non valido")
        token = create_admin_token(body.username)
        return AuthResponse(bearer=token, expiresInMinutes=settings.TOKEN_TTL_MINUTES)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Intent non supportato")
