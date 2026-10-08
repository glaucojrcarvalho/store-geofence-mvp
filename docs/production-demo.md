## Public static showcase (GitHub Pages / Vercel)

For a production portfolio URL without a hosted Redis service, deploy **only**
the contents of `public-demo/`. This is a wholly separate static Haversine
demonstration with browser-only computation, not a deployed FastAPI endpoint.
It has no backend, data store, external geocoding, location upload, or billing.

- **Preferred automated publication:** `.github/workflows/pages.yml`
  builds and deploys solely `public-demo/` on `main` after its contract tests
  pass. If the GitHub Pages site has never been enabled, a repository administrator
  must visit **Settings → Pages → Build and deployment → Source: GitHub Actions**
  once, then rerun **Publish Public Geofence Demo**.
- **Alternative:** on Vercel create a new Git-linked project with Root Directory
  `public-demo`, Framework Preset **Other**, no build command or environment
  secrets. Use a Vercel team authorized for project creation.
- The HTML includes a portable restrictive CSP meta tag; on Vercel additional
  CSP, framing, HSTS and privacy response headers are in
  `public-demo/vercel.json`. GitHub Pages does not honor `vercel.json`
  response headers, so expect only the meta CSP there.
- Verify the deployed document, JS/CSS loading, inside/outside examples,
  invalid-coordinate behavior, mobile layout, keyboard navigation, and
  source link before announcing the URL.
- Never present the static experience as a live PostGIS or FastAPI service.

# Public synthetic geofence demo — release runbook

## Security boundary

The public service runs **APP_ENV=prod**. In this mode the FastAPI app
mounts only `GET /`, `POST /demo/check`, OpenAPI docs, `/healthz` and
`/readyz`. It **does not mount** `/auth/login`, `/companies`,
`/stores`, `/tasks`, or any geocoding/worker routes.

The demo uses only hard-coded illustrative coordinates and a 100-metre
radius. It does not access a customer database, external geocoding, or
personal GPS data. It uses a Haversine estimate, while the private
business API uses PostGIS. **Do not claim that client-supplied coordinates
prove physical presence**.

Do not use any real customer names, addresses, photos or user accounts in
this public demo. Do not deploy the business API or the Celery worker
alongside this public frontend until tenant authorization and operations
have been audited separately.

## Preflight and environment

- Use an ingress with HTTPS, TLS termination, fixed custom domain, request
  body limits, a trusted proxy configuration and upstream IP/WAF throttling.
- Provide a private Redis instance reachable only from the API service.
  The public check is limited to 30 requests per minute per connection
  address; if Redis fails, it returns HTTP 503 instead of silently bypassing
  the limit. Ensure the reverse proxy and application agree on the client
  address; the code intentionally ignores unauthenticated forwarded headers.
- Set `APP_ENV=prod`, a random `SECRET_KEY` of at least 32 characters, and
  a strong `POSTGRES_PASSWORD` even though the public app never connects to
  PostgreSQL. Do not set `DEMO_TOKEN` or
  `ALLOW_INSECURE_DEV_LOGIN`. Set `REDIS_URL` with TLS and authentication
  where supported by the managed service.
- Store environment values in the hosting platform's secret manager, never
  in Git or build logs. Keep the network/database private. Disable Flower.
- Use the production `Dockerfile` without the development Compose bind mount,
  host port publishing, or `uvicorn --reload`. The image runs as a
  non-root user.
- The legacy Cloud Run deploy scripts are intentionally blocked. They
  exposed secrets via command-line arguments and treated a long-running
  Celery worker as a request-serving service.

## Release gates

1. Review the exact main commit, dependency audit and Docker image digest.
2. Require green GitHub Actions checks: Python compilation, dependency
   vulnerability audit, migrations and tests, and Docker build.
3. Confirm production import unmounts all business/API routes. Run the
   production-isolation regression test on the exact artifact.
4. Deploy a **staged private preview** with the production environment
   (not the dev stack). No public DNS or traffic yet.
5. Check `GET /healthz` and `GET /readyz`; readiness must be HTTP 503
   when Redis is unreachable.
6. Check `POST /demo/check` on the synthetic inside/outside coordinates:
   (50.4502, 30.5234) => inside, (50.4540, 30.5234) => outside.
   Invalid coordinates => 422; more than 30 requests per minute per
   connection => 429.
7. Verify `POST /auth/login`, `GET /stores/1`,
   `GET /tasks?store_id=1` and `POST /companies` return 404.
8. Review reverse-proxy logs for inadvertent request-body/location logging,
   configure uptime alerts, error tracking and basic Redis availability.
   Establish an owner for the response to Redis outages.
9. Confirm rollback to the previous image digest, and test that rollback
   can be executed without restoring any user data.
10. Attach a stable demo URL and screenshot to the release notes only
    after all checks pass.

## Rollback

Immediately route traffic to the previous verified image revision via your
deployment platform. Since public demo writes no durable business state,
there are no customer-data migrations to reverse. If Redis is unavailable,
the service will fail closed until its private connectivity is restored.

## Limitations / future architecture

Set `ENABLE_PRIVATE_API=false` for production (it defaults to false).
The private routes require an explicit `ENABLE_PRIVATE_API=true` in local
and private non-production environments; production rejects it.

The private business API intentionally remains a **single-tenant
development prototype**. Its JWT issuer, ownership model, worker/job
lifecycle, geocoding provider quotas, durable scheduling, abuse protection,
observability and backups require independent production design before it
can serve real store or worker data.

On `APP_ENV=dev`, `/auth/login` may mint arbitrary roles **only if**
`ALLOW_INSECURE_DEV_LOGIN=true` was deliberately set, and this is never
suitable for an Internet-exposed runtime.
