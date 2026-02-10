"""Auth: JWT and API key validation."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

# Use a fixed user id for single-user; can be replaced with DB lookup later
CURRENT_USER_ID = 1

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """JWT payload."""

    sub: str  # user id as string
    exp: datetime


def create_access_token(user_id: int = CURRENT_USER_ID) -> str:
    """Create JWT for user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate JWT; return payload or None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return TokenPayload(sub=payload["sub"], exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc))
    except (JWTError, KeyError):
        return None


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    api_key: Annotated[str | None, Depends(api_key_header)],
) -> int:
    """
    Resolve user from Bearer JWT or X-API-Key (simple: accept secret_key as API key for dev).
    Raises 401 if neither valid.
    """
    # 1) Bearer token
    if credentials:
        payload = decode_token(credentials.credentials)
        if payload:
            return int(payload.sub)

    # 2) API key: for single-user, accept SECRET_KEY as API key (or add separate API_KEY in env)
    if api_key and settings.secret_key and api_key == settings.secret_key:
        return CURRENT_USER_ID

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication",
    )


# Dependency alias for routes
CurrentUserId = Annotated[int, Depends(get_current_user_id)]
