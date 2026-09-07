from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    email: str


def _supabase_user(token: str) -> AuthenticatedUser:
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase authentication is not configured")
    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
            headers={"apikey": settings.supabase_publishable_key, "Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service is unavailable") from exc
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    try:
        payload = response.json()
        user_id = UUID(str(payload["id"]))
        email = payload.get("email")
        if not isinstance(email, str) or not email:
            raise ValueError("missing email")
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication response") from exc
    return AuthenticatedUser(id=user_id, email=email)


def _legacy_jwt_user(token: str) -> AuthenticatedUser:
    if not settings.jwt_secret_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication is not configured")
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"require": ["sub", "exp", "iss"]},
        )
        user_id = UUID(str(payload["sub"]))
        email = payload.get("email")
        if not isinstance(email, str) or not email:
            raise ValueError("missing email")
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
    return AuthenticatedUser(id=user_id, email=email)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = credentials.credentials
    if settings.supabase_url and settings.supabase_publishable_key:
        return _supabase_user(token)
    return _legacy_jwt_user(token)
