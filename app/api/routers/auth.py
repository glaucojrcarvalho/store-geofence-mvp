from fastapi import APIRouter, HTTPException
from app.schemas.schemas import LoginRequest, TokenResponse
from app.core.auth import create_access_token
from app.core.config import settings

router = APIRouter()


@router.post("/login", response_model=TokenResponse, include_in_schema=False)
def login(payload: LoginRequest):
    # This legacy convenience endpoint must never issue production credentials.
    if settings.APP_ENV not in {"dev", "test"} or not settings.ALLOW_INSECURE_DEV_LOGIN:
        raise HTTPException(status_code=404, detail="Not found")
    return TokenResponse(access_token=create_access_token(subject=payload.email, role=payload.role))
