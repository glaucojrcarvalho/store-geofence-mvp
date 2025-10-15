#!/usr/bin/env bash
set -euo pipefail

# Helper to reproduce CI-like e2e flow locally.
# Usage: ./scripts/run_e2e_local.sh

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo ".env not found. Copy from .env.example and edit if needed:"
  echo "  cp .env.example .env"
  exit 1
fi

echo "Starting PostGIS and Redis services (detached)..."
docker compose up -d db redis

echo "Waiting for Postgres to be ready (will try 60s)..."
for i in $(seq 1 60); do
  if docker compose exec db pg_isready -U "${POSTGRES_USER:-geofence}" -d "${POSTGRES_DB:-geofence}" >/dev/null 2>&1; then
    echo "Postgres ready"
    break
  fi
  echo "waiting for postgres... ($i)"
  sleep 1
done

echo "Applying alembic migrations inside api service..."
docker compose run --rm api alembic upgrade head

echo "Running e2e tests inside api service (pytest tests/test_e2e.py)..."
docker compose run --rm api pytest tests/test_e2e.py -q

echo "Done. You can bring down services with: docker compose down -v"

