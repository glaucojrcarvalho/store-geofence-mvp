import os
import time
import httpx
import psycopg2
from app.core.config import settings

# By default run the tests against the ASGI app in-process (avoids starting uvicorn in CI).
USE_EXTERNAL_API = os.getenv("USE_EXTERNAL_API", "false").lower() in ("1", "true", "yes")

# When running in-process, ensure migrations are applied before importing the app
if not USE_EXTERNAL_API:
    # attempt to run alembic upgrade head programmatically (harmless if already applied)
    try:
        from alembic.config import Config
        from alembic import command
        cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
        cfg.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
        command.upgrade(cfg, 'head')
    except Exception:
        # if alembic is not available or fails, we'll still attempt to wait for migrations below
        pass

# If running in-process, wait for DB and migrations to be applied (companies table exists)
if not USE_EXTERNAL_API:
    deadline = time.time() + int(os.getenv("E2E_DB_WAIT", "120"))
    while time.time() < deadline:
        try:
            conn = psycopg2.connect(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                dbname=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
            )
            try:
                cur = conn.cursor()
                cur.execute("SELECT to_regclass('public.companies')")
                res = cur.fetchone()[0]
                if res is not None:
                    # migrations applied
                    cur.close()
                    conn.close()
                    break
            except Exception:
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(1)
    else:
        raise RuntimeError("Database not ready or migrations not applied in time")

if USE_EXTERNAL_API:
    API_URL = "http://127.0.0.1:8000"
    def make_client():
        return httpx.Client()
else:
    # use FastAPI's TestClient for in-process testing (stable wrapper around ASGI)
    from fastapi.testclient import TestClient
    from app.main import app as asgi_app
    API_URL = "http://testserver"
    def make_client():
        return TestClient(asgi_app)


def wait_for_api(timeout=5):
    # when running in-process this is instantaneous; keep a tiny wait for external mode
    if not USE_EXTERNAL_API:
        return True
    client = httpx.Client()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = client.get(f"{API_URL}/healthz", timeout=5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("API did not become ready in time")


def db_connect():
    # Use settings; in CI POSTGRES_HOST is set accordingly
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )


def test_end_to_end_flow():
    # Wait for API (no-op for in-process mode)
    wait_for_api(timeout=120)

    # Use either in-process client or external client
    with make_client() as client:
        # Login as admin to get JWT
        r = client.post(f"{API_URL}/auth/login", json={"email": "admin@example.com", "role": "admin"}, timeout=10)
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a company
        r = client.post(f"{API_URL}/companies", json={"name": "E2E Co", "geofence_radius_m": 100}, headers=headers, timeout=10)
        assert r.status_code == 200, r.text
        company_id = r.json()["id"]

    # Insert a store directly into the DB with a known location (avoid external geocoder)
    lat, lng = 50.4501, 30.5234
    conn = db_connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO stores (company_id, name, address_lines, city, country, postal_code, location, geocode_status) "
            "VALUES (%s,%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, 'success') RETURNING id",
            (company_id, 'E2E Store', 'addr', 'City', 'Country', '00000', lng, lat),
        )
        store_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    with make_client() as client:
        # Create a task for the store
        r = client.post(f"{API_URL}/tasks", json={"store_id": store_id, "title": "E2E task"}, headers=headers, timeout=10)
        assert r.status_code == 200, r.text
        task_id = r.json()["id"]

        # Run the task using the previously created JWT (Authorization header)
        r = client.post(f"{API_URL}/tasks/{task_id}/run", json={"lat": lat, "lng": lng}, headers=headers, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["allowed"] is True
        assert body["distance_m"] >= 0
