from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.db import get_db
import app.services.distances as distances_module


class FakeDB:
    def __init__(self, task_obj, store_obj, company_obj, insert_id=1):
        self._task = task_obj
        self._store = store_obj
        self._company = company_obj
        self._insert_id = insert_id

    def get(self, model, id_):
        name = getattr(model, "__name__", None)
        if name == "Task":
            return self._task if self._task and self._task.id == id_ else None
        if name == "Store":
            return self._store if self._store and self._store.id == id_ else None
        if name == "Company":
            return self._company if self._company and self._company.id == id_ else None
        return None

    def execute(self, sql, params=None):
        # used for inserting the task_run; return object with scalar_one()
        return SimpleNamespace(scalar_one=lambda: self._insert_id)

    def add(self, *args, **kwargs):
        return None

    def commit(self):
        return None

    def flush(self):
        return None

    def close(self):
        return None


client = TestClient(app)


def setup_demo_token(token_value: str = "demo-test"):
    settings.DEMO_TOKEN = token_value
    return token_value


def test_run_task_allowed_within_radius(monkeypatch):
    # Arrange
    demo_token = setup_demo_token("demo-test")

    task_obj = SimpleNamespace(id=1, store_id=10, active=True)
    store_obj = SimpleNamespace(id=10, company_id=100, geocode_status="success", location=object(), custom_radius_m=None)
    company_obj = SimpleNamespace(id=100, geofence_radius_m=100)

    fake_db = FakeDB(task_obj, store_obj, company_obj, insert_id=123)

    # Override get_db dependency to return our fake DB
    app.dependency_overrides[get_db] = lambda: fake_db

    # Ensure rate limiter is a no-op by setting redis to None (the implementation checks this)
    monkeypatch.setattr("app.core.ratelimit._redis", None)

    # Stub the distance calculation used by the tasks router to return within=True
    monkeypatch.setattr("app.api.routers.tasks.within_radius_and_distance", lambda db, s_id, lat, lng, radius: (True, 23.7))

    # Act
    resp = client.post(
        "/tasks/1/run",
        json={"lat": 50.0, "lng": 30.0},
        headers={"X-Demo-Token": demo_token},
    )

    # Cleanup override
    app.dependency_overrides.pop(get_db, None)

    # Assert
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["allowed"] is True
    assert abs(data["distance_m"] - 23.7) < 0.001


def test_run_task_store_not_ready(monkeypatch):
    # Arrange
    demo_token = setup_demo_token("demo-test")

    task_obj = SimpleNamespace(id=1, store_id=10, active=True)
    store_obj = SimpleNamespace(id=10, company_id=100, geocode_status="pending", location=None, custom_radius_m=None)
    company_obj = SimpleNamespace(id=100, geofence_radius_m=100)

    fake_db = FakeDB(task_obj, store_obj, company_obj, insert_id=123)

    app.dependency_overrides[get_db] = lambda: fake_db
    monkeypatch.setattr("app.core.ratelimit._redis", None)

    # Act
    resp = client.post(
        "/tasks/1/run",
        json={"lat": 50.0, "lng": 30.0},
        headers={"X-Demo-Token": demo_token},
    )

    app.dependency_overrides.pop(get_db, None)

    # Assert
    assert resp.status_code == 409
    assert resp.json().get("detail") == "Store location not ready"
