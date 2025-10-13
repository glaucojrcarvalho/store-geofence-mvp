from __future__ import annotations
import time
from typing import Callable
from fastapi import HTTPException, Depends
import redis
from app.core.config import settings
from app.core.auth import get_current_user, TokenData

try:
    _redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    _redis = None

def rate_limit(bucket: str, limit: int, window_sec: int) -> Callable[[TokenData], None]:
    def _inner(user: TokenData = Depends(get_current_user)):
        if _redis is None:
            return
        try:
            now = int(time.time())
            key = f"rl:{bucket}:{user.sub}:{now // window_sec}"
            current = _redis.incr(key)
            if current == 1:
                _redis.expire(key, window_sec)
            if current > limit:
                raise HTTPException(status_code=429, detail=f"Rate limit exceeded for {bucket}")
        except Exception:
            return
    return _inner

