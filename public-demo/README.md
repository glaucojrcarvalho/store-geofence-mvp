# Safe static production showcase

This is the **only directory** intended to be deployed publicly on Vercel.
Select **Framework Preset: Other** and **Root Directory: `public-demo`** with
no build command or production environment variables. It contains only local
HTML, CSS and JavaScript. The calculation happens in the visitor's browser
with hard-coded synthetic coordinates; there is **no network API** and no
persistent storage, real GPS ingestion, admin route, Redis, PostgreSQL or worker.

The Python FastAPI/PostGIS/Celery implementation remains in the repository as
a developer-run, unaudited business prototype. Do not expose that implementation
to public customers. Do not describe this deployed static UI as a live PostGIS
or FastAPI API. Its Haversine output illustrates the geofence concept.

Vercel must be configured for the `public-demo` root, not the repository root.
Review its response headers, test mobile and keyboard usage, and verify Vercel
project-to-GitHub main synchronization before promoting a preview. Restrict
hostnames to HTTPS. Enable platform spend limits/usage alerts and observability.

Rollback to the previous verified static deployment. The UI has no database
migrations and does not handle or retain personal data.

See ../docs/production-demo.md for backend security-release gates.
