# Store Geofence v0.2.0 — Secure public-demo boundary

This release hardens the original FastAPI/PostGIS/Celery geofencing prototype and
adds a standalone, accessible, static portfolio showcase.

## Security and reliability
- Removes unrestricted production JWT role selection and adds fail-fast secret validation.
- Keeps all database-backed business and administrative routes disabled by default
  and never mounts them under production mode.
- Validates location and geofence inputs; rate limiting now fails closed rather
  than swallowing HTTP 429 or a backend outage.
- Restricts developer service ports to loopback, runs container with non-root user,
  and disables unsafe legacy Cloud Run deployment scripts.
- Improves Celery registration and retry reporting; adds security regression tests.
- CI covers tests, migration, dependency vulnerabilities and Docker builds.

## Public showcase
- `public-demo/`: interactive browser-only Haversine simulation with synthetic
  sample coordinates, keyboard-accessible controls and no network requests.
- GitHub Pages workflow publishes **only** these static files after contract tests.
  The live site URL is only confirmed once the Pages deployment succeeds.
- Vercel may optionally host the static folder in a separate Git-linked project.

## Explicit limitations
**The public website is not a hosted FastAPI/PostGIS service.** The original
business backend remains a developer prototype, not a production tenant-aware
location-verification service. Caller-supplied GPS is spoofable; no claim of
physical presence is made. Do not expose real stores, customers or production
worker traffic through these routes.

See `docs/production-demo.md` for rollout/rollback and remaining infrastructure
and operational release gates.
