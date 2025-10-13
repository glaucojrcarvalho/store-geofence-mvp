from fastapi import APIRouter
from app.schemas.schemas import LoginRequest, TokenResponse
from app.core.auth import create_access_token

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    token = create_access_token(subject=payload.email, role=payload.role)
    return TokenResponse(access_token=token)

