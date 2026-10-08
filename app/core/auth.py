from datetime import datetime, timedelta, timezone
from hmac import compare_digest
from typing import Literal

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel, ValidationError
from app.core.config import settings

security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    sub: str
    role: Literal["worker", "admin"]


def create_access_token(subject: str, role: Literal["worker", "admin"], expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    lifetime = settings.ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    if not 1 <= lifetime <= 1440:
        raise ValueError("Invalid token lifetime")
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=lifetime)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_demo_token: str | None = Header(default=None, alias="X-Demo-Token"),
) -> TokenData:
    if settings.APP_ENV in {"dev", "test"} and settings.DEMO_TOKEN and x_demo_token:
        if compare_digest(x_demo_token, settings.DEMO_TOKEN):
            return TokenData(sub="demo@user", role="worker")
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["sub", "role", "iat", "exp"]},
        )
        return TokenData.model_validate({"sub": payload["sub"], "role": payload["role"]})
    except (jwt.PyJWTError, ValidationError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None


def require_role(expected: str):
    async def dep(user: TokenData = Depends(get_current_user)):
        if user.role != expected:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dep
