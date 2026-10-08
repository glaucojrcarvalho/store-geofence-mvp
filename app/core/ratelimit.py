from __future__ import annotations
import time
from typing import Callable
from fastapi import HTTPException, Depends, Request
import redis
from app.core.config import settings
from app.core.auth import get_current_user, TokenData

_redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _check_rate_limit(bucket: str, subject: str, limit: int, window_sec: int) -> None:
    if not subject or limit <= 0 or window_sec <= 0:
        raise ValueError("Invalid rate-limit configuration")
    try:
        key = f"rl:{bucket}:{subject}:{int(time.time()) // window_sec}"
        if _redis is None:
            raise redis.RedisError("Redis unavailable")
        current = _redis.incr(key)
        if current == 1:
            _redis.expire(key, window_sec + 1)
    except redis.RedisError:
        if settings.APP_ENV in {"prod", "staging"}:
            raise HTTPException(status_code=503, detail="Rate limiting unavailable") from None
        return
    if current > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": str(window_sec)})


def rate_limit(bucket: str, limit: int, window_sec: int) -> Callable:
    def _inner(user: TokenData = Depends(get_current_user)):
        _check_rate_limit(bucket, user.sub, limit, window_sec)
    return _inner


def public_rate_limit(bucket: str, limit: int, window_sec: int) -> Callable:
    def _inner(request: Request):
        # Ignore untrusted X-Forwarded-For data supplied directly by clients.
        client_ip = request.client.host if request.client else "unknown"
        _check_rate_limit(bucket, client_ip, limit, window_sec)
    return _inner
