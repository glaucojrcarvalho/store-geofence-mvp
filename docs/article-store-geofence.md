# Store Geofence — FastAPI + Celery + PostGIS

## TL;DR

Store Geofence is a small backend MVP that demonstrates how to enforce geofencing for tasks: companies register stores by address, stores are geocoded asynchronously, and worker-submitted locations are validated against the store geofence (default 100 m). This repo shows how to wire FastAPI, Celery, Redis and PostGIS together with CI and tests.

## Architecture (short)

API (FastAPI)
  ↕ (DB queries using PostGIS ST_DWithin / ST_Distance)
Postgres + PostGIS
  ↕ (job queue)
Redis (broker)
  ↔ Celery worker (geocoder) → updates store location

### Flow
- POST /stores (address) → enqueue geocode job
- Celery worker geocodes via Google Maps (async) and writes geography point to DB
- Client calls POST /tasks/{id}/run with {lat, lng}
- API checks ST_DWithin + ST_Distance and persists TaskRun

## Quick start (local)

1. Copy environment and start services:

```bash
cp .env.example .env
docker compose up -d
```

2. Apply DB migrations and seed:

```bash
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m scripts.seed
```

3. Open the API docs: http://localhost:8000/docs

## Key design notes
- Use PostGIS for geospatial accuracy instead of attempting Haversine in application code.
- Insert geography points atomically (single INSERT with ST_SetSRID(...)) to avoid NULL constraints.
- Background geocoding keeps the API non-blocking and resilient to provider delays.

## Running tests
- Unit + mocked integration tests run quickly without a full PostGIS instance.
- Full end-to-end tests require PostGIS; CI has a job to run these using a PostGIS service container.

```bash
python -m pip install -r requirements.txt
python -m pip install -r dev-requirements.txt
pytest -q
```

## Lessons learned
- Keep geospatial logic in the DB when possible.
- Use a demo token and good test coverage to make sharing a demo safe and reproducible.

## Next steps
- Add a small front-end demo to visualize runs on a map.
- Add metrics/monitoring (task durations, failed geocodes).