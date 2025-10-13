from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel
from app.core.config import settings

security = HTTPBearer(auto_error=False)

class TokenData(BaseModel):
    sub: str
    role: str

def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "iat": int(now.timestamp()), "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_demo_token: str | None = Header(default=None, alias="X-Demo-Token")
) -> TokenData:
    if settings.DEMO_TOKEN and x_demo_token == settings.DEMO_TOKEN:
        return TokenData(sub="demo@user", role="worker")
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return TokenData(sub=payload["sub"], role=payload.get("role", "worker"))
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_role(expected: str):
    async def dep(user: TokenData = Depends(get_current_user)):
        if user.role != expected:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dep

