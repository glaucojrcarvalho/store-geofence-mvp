import json
import os
import subprocess
import sys
from types import SimpleNamespace

import jwt
import pytest
import redis
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import create_access_token
from app.core.config import settings
import app.core.ratelimit as limiter


@pytest.fixture
def api_client(monkeypatch):
    # Unit-level public demo checks do not need an external Redis service.
    monkeypatch.setattr(limiter, "_redis", None)
    with TestClient(app) as client:
        yield client


def test_arbitrary_admin_login_disabled_by_default(api_client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_INSECURE_DEV_LOGIN", False)
    response = api_client.post("/auth/login", json={"email": "intruder@example.invalid", "role": "admin"})
    assert response.status_code == 404


def test_public_demo_uses_synthetic_coordinates_and_no_database(api_client):
    inside = api_client.post("/demo/check", json={"lat": 50.4502, "lng": 30.5234})
    outside = api_client.post("/demo/check", json={"lat": 50.4540, "lng": 30.5234})
    assert inside.status_code == outside.status_code == 200
    assert inside.json()["allowed"] is True
    assert outside.json()["allowed"] is False
    assert inside.json()["synthetic"] is True
    assert "physical presence" in inside.json()["disclaimer"]


@pytest.mark.parametrize("payload", [
    {"lat": 91, "lng": 30},
    {"lat": -91, "lng": 30},
    {"lat": 50, "lng": 181},
])
def test_public_demo_rejects_invalid_coordinates(api_client, payload):
    assert api_client.post("/demo/check", json=payload).status_code == 422


def test_business_read_endpoints_require_authentication(api_client):
    assert api_client.get("/stores/1").status_code == 401
    assert api_client.get("/tasks", params={"store_id": 1}).status_code == 401


def test_limiter_returns_429_instead_of_swallowing_exception(monkeypatch):
    counter = SimpleNamespace(value=0)
    class FakeRedis:
        def incr(self, key):
            counter.value += 1
            return counter.value
        def expire(self, key, ttl):
            return True
    monkeypatch.setattr(limiter, "_redis", FakeRedis())
    limiter._check_rate_limit("test", "user", 1, 60)
    with pytest.raises(HTTPException) as caught:
        limiter._check_rate_limit("test", "user", 1, 60)
    assert caught.value.status_code == 429


def test_limiter_fails_closed_in_production(monkeypatch):
    class BrokenRedis:
        def incr(self, key):
            raise redis.RedisError("offline")
    monkeypatch.setattr(limiter, "_redis", BrokenRedis())
    monkeypatch.setattr(settings, "APP_ENV", "prod")
    with pytest.raises(HTTPException) as caught:
        limiter._check_rate_limit("test", "user", 10, 60)
    assert caught.value.status_code == 503


def test_invalid_token_role_rejected(api_client):
    token = jwt.encode(
        {"sub": "x", "role": "admin-and-superuser",
         "iat": 1, "exp": 4102444800},
        settings.SECRET_KEY, algorithm="HS256")
    response = api_client.get("/stores/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_worker_cannot_read_admin_store_data(api_client):
    token = create_access_token("worker@example.invalid", "worker")
    response = api_client.get("/stores/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_public_production_does_not_mount_business_api():
    env = dict(os.environ,
               APP_ENV="prod",
               SECRET_KEY="A" * 48,
               POSTGRES_PASSWORD="B" * 32,
               DEMO_TOKEN="",
               ALLOW_INSECURE_DEV_LOGIN="false",
               ENABLE_PRIVATE_API="false")
    code = ("from app.main import app; "
            "routes=set(app.openapi()['paths']); "
            "assert '/demo/check' in routes; "
            "assert '/auth/login' not in routes; "
            "assert '/companies' not in routes; "
            "assert '/stores/{store_id}' not in routes; "
            "assert '/tasks/{task_id}/run' not in routes")
    result = subprocess.run([sys.executable, "-c", code], env=env,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_prod_refuses_default_secrets():
    env = dict(os.environ, APP_ENV="prod", SECRET_KEY="changeme", POSTGRES_PASSWORD="geofence", ENABLE_PRIVATE_API="false")
    result = subprocess.run([sys.executable, "-c", "from app.core.config import settings"],
                            env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr
