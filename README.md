> **Public release boundary (v0.2 candidate):** This repository includes an isolated
> synthetic demo designed for public hosting with `APP_ENV=prod`. That mode exposes
> only the demo and health/documentation endpoints; it **does not expose** the
> business, authentication, stores, task-management, or geocoding APIs.
> The actual store/worker platform is **not production-ready**.
> See [production demo runbook](docs/production-demo.md) and
> [security hardening PR](https://github.com/glaucojrcarvalho/store-geofence-mvp/pull/4).
> Do not treat client-submitted coordinates as proof of physical presence.
>
> Private business API routes are disabled by default. For isolated local development
> only, set `ENABLE_PRIVATE_API=true` (the development Docker Compose sets it).
> Local developer-only JWT minting is disabled by default. The legacy
> `/auth/login` route works only when `ALLOW_INSECURE_DEV_LOGIN=true` with
> `APP_ENV=dev` or `test`; never enable it on a public host.

# Store Geofence — FastAPI + Celery + PostGIS

<p align="left">
  <a href="https://github.com/glaucojrcarvalho/store-geofence-mvp/actions">
    <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/glaucojrcarvalho/store-geofence-mvp/ci.yml?branch=main">
  </a>
  <a href="#license">
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg">
  </a>
</p>

A production-style FastAPI backend service that validates whether a worker is inside a store geofence before allowing task execution.

The project demonstrates API design, asynchronous background processing, geospatial queries with PostGIS, Redis-backed workers, authentication, rate limiting, Docker-based local development, tests, and CI.

## Why this project matters

Many field-operation, retail-execution, logistics, and workforce-management systems need to validate whether an action happened at the correct physical location.

This project models that scenario through a small but realistic backend domain:

- Companies register stores.
- Stores can be geocoded asynchronously from addresses.
- Tasks are assigned to stores.
- Workers can execute tasks only when their reported location is inside the configured store radius.

## Technical highlights

- REST API with FastAPI and OpenAPI documentation
- PostgreSQL + PostGIS for spatial queries
- Celery workers with Redis broker for background geocoding jobs
- JWT authentication and demo-token support
- Rate limiting for task execution endpoints
- Docker Compose local environment
- Alembic migrations and seeded demo data
- GitHub Actions CI with linting, tests, and Docker build validation
