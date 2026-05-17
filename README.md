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
