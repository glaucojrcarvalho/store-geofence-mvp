import time
import httpx
import psycopg2
from app.core.config import settings

API_URL = "http://localhost:8000"


def wait_for_api(timeout=60):
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
    # Use settings but assume CI will set POSTGRES_HOST=localhost for runner tests
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )


def test_end_to_end_flow():
    # Wait for API
    wait_for_api(timeout=60)

    # Login as admin to get JWT
    r = httpx.post(f"{API_URL}/auth/login", json={"email": "admin@example.com", "role": "admin"}, timeout=10)
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a company
    r = httpx.post(f"{API_URL}/companies", json={"name": "E2E Co", "geofence_radius_m": 100}, headers=headers, timeout=10)
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

    # Create a task for the store
    r = httpx.post(f"{API_URL}/tasks", json={"store_id": store_id, "title": "E2E task"}, headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    task_id = r.json()["id"]

    # Run the task using the previously created JWT (Authorization header)
    # Using the JWT keeps this test independent from external DEMO_TOKEN env configuration.
    r = httpx.post(f"{API_URL}/tasks/{task_id}/run", json={"lat": lat, "lng": lng}, headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["allowed"] is True
    assert body["distance_m"] >= 0
