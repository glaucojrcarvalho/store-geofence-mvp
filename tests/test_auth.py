import asyncio
import jwt
from app.core.config import settings
from app.core.auth import create_access_token, get_current_user, TokenData


def test_create_access_token():
    token = create_access_token(subject="user@example.com", role="admin", expires_minutes=1)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == "user@example.com"
    assert payload["role"] == "admin"


def test_demo_token_allows_get_current_user():
    # set a demo token on the runtime settings and call the auth helper directly
    settings.DEMO_TOKEN = "demo-test-123"
    user: TokenData = asyncio.get_event_loop().run_until_complete(get_current_user(None, "demo-test-123"))
    assert isinstance(user, TokenData)
    assert user.sub == "demo@user"
    assert user.role == "worker"

