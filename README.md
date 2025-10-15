# Store Geofence — FastAPI + Celery + PostGIS

<p align="left">
  <a href="https://github.com/glaucojrcarvalho/store-geofence-mvp/actions">
    <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/glaucojrcarvalho/store-geofence-mvp/ci.yml?branch=main">
  </a>
  <a href="#license">
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg">
  </a>
</p>

A compact, backend-focused MVP that demonstrates geofencing for store tasks. The service lets companies register stores (by address), automatically geocode them (via Google Maps) in background jobs, and validate whether a worker's reported location is inside the store's configured geofence before allowing task execution.

Why this project is portfolio-ready:
- Focused, small surface area that shows system design (API + worker), async background processing, and PostGIS usage.
- Clear domain (companies → stores → tasks) and real-world constraints (geocoding, distance checks, rate limits).
- Deployable with Docker Compose and Cloud Run.

Table of contents
- Features
- Architecture (high level)
- Quick start (local)
- API overview + examples
- Testing & CI
- Improvements & notes
- Troubleshooting & tests
- Contributing
- License

---

## Features
- Register companies, stores and tasks
- Background geocoding (Celery + Redis) when a store has no coordinates
- Geofence validation: tasks can only be run when worker is within configured radius (default 100 m)
- JWT auth + optional demo token for quick testing
- Rate-limiting for task execution endpoints
- PostGIS for accurate distance calculations
- Docker Compose setup and Cloud Run deploy scripts

---

## Architecture (high level)
- FastAPI exposes the REST API and OpenAPI docs.
- PostgreSQL + PostGIS stores store geometries and runs spatial queries (ST_DWithin, ST_Distance).
- Celery workers (broker: Redis) run geocoding jobs and update the DB asynchronously.
- Optional Google Maps Geocoding provider for address -> coordinates.

---

## Quick start (local)

1. Copy example env and start services:

```bash
cp .env.example .env
docker compose up -d
```

2. Apply DB migrations and seed demo data:

```bash
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m scripts.seed
```

3. Open the API docs: http://localhost:8000/docs

Notes:
- The `worker` service runs the Celery worker. Geocoding jobs are queued when stores are created without coordinates.
- Flower dashboard (task monitoring) is available at http://localhost:5555

---

## API overview & examples

Endpoints (high-level):
- POST /auth/login — create a JWT token (demo token supported)
- POST /companies — create company (admin)
- POST /stores — register store (admin); queues geocode job
- GET /stores/{id} — view store and geocode status
- POST /tasks — create a task (admin)
- POST /tasks/{id}/run — execute a task with worker location (rate-limited)

Example: run a task (inside radius)

```bash
curl -s http://localhost:8000/tasks/1/run \
  -H 'X-Demo-Token: mydemo' \
  -H 'Content-Type: application/json' \
  -d '{"lat":50.4501,"lng":30.5234}'
# → {"allowed": true, "distance_m": 23.7}
```

If a store hasn't been geocoded, the run endpoint returns 409 (location not ready).

---

## Testing & CI
Run unit tests:

```bash
docker compose run --rm api pytest -q
```

CI checks (GitHub Actions) include linting (ruff), tests, and a Docker build validation.

### CI / GitHub Actions
The repository runs a `CI` workflow (see `.github/workflows/ci.yml`) which executes linting, unit tests and an end-to-end job that starts PostGIS and Redis as services and runs the application inside the runner.

Required repository secrets for the e2e job (add these in GitHub → Settings → Secrets and Variables → Actions):
- `SECRET_KEY` — application secret used to sign JWTs (use a long random string)
- `DEMO_TOKEN` — demo token used by tests (you can set this to an arbitrary long string)

How to re-run the workflow:
- Use the GitHub Actions UI: open the workflow run and click "Re-run jobs".
- Or push an empty commit locally and push to `main` to trigger the workflow:

```bash
git commit --allow-empty -m "ci: rerun workflow"
git push origin main
```

If you want to reproduce the e2e flow locally (recommended before pushing), see `scripts/run_e2e_local.sh` which wraps `docker compose` + migrations + tests.

---

## Improvements & notes (suggested edits for portfolio polish)
If you want this project to look even more professional on a portfolio, consider the following (I can implement these with you):

1. Add a short architecture diagram (ASCII or image) and a README section that walks through the request flow.
2. Expand test coverage: add tests for the geocoding worker, distance checks, auth (demo token and JWT) and rate-limiting behavior.
3. Add example Postman/HTTPie collection or a tiny CLI script that demonstrates the main flows.
4. Move developer-only packages (ruff, pytest) to a `dev-requirements.txt` and document code style checks in CI.
5. Add more detailed error responses and examples in README (HTTP status & JSON examples).
6. Improve the demo landing page to show API usage or a cURL playground for non-technical reviewers.

I can implement low-risk items now (README polish, small docs) and help scaffold tests or CI changes next.

---

## Troubleshooting & tests

If you see "No module named pytest" when running tests locally, install the development dependencies first:

```bash
python -m pip install -r dev-requirements.txt
```

Run unit tests:

```bash
pytest -q
```

Lint (ruff):

```bash
python -m pip install ruff
ruff check app
```

If you use Docker Compose the development container already contains the required tools and the commands in this README should work inside the `api` service.

---

## Contributing
Small repo — contributions welcome.
- Open an issue or a PR with a short description.
- Follow the existing code style (Ruff is configured in CI).

---

## License
MIT © [glaucojrcarvalho](https://github.com/glaucojrcarvalho)