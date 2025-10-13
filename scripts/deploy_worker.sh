#!/usr/bin/env bash
set -euo pipefail

# ==== Configure these ====
PROJECT_ID="${PROJECT_ID:-your-gcp-project-id}"
REGION="${REGION:-europe-west3}"
SERVICE_NAME="${SERVICE_NAME:-geofence-worker}"
IMAGE="gcr.io/${PROJECT_ID}/store-geofence-mvp"

# Build & push container (same image as API)
gcloud builds submit --tag "${IMAGE}"

# Deploy Celery worker as a Cloud Run service
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform=managed \
  --port=8000 \
  --no-allow-unauthenticated \
  --set-env-vars "APP_ENV=prod" \
  --set-env-vars "SECRET_KEY=${SECRET_KEY:-change-me}" \
  --set-env-vars "ACCESS_TOKEN_EXPIRE_MINUTES=60" \
  --set-env-vars "DEMO_TOKEN=${DEMO_TOKEN:-}" \
  --set-env-vars "POSTGRES_HOST=${POSTGRES_HOST:-127.0.0.1}" \
  --set-env-vars "POSTGRES_PORT=${POSTGRES_PORT:-5432}" \
  --set-env-vars "POSTGRES_DB=${POSTGRES_DB:-geofence}" \
  --set-env-vars "POSTGRES_USER=${POSTGRES_USER:-geofence}" \
  --set-env-vars "POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-geofence}" \
  --set-env-vars "REDIS_URL=${REDIS_URL:-redis://127.0.0.1:6379/0}" \
  --set-env-vars "GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY:-}" \
  --command "celery" \
  --args "-A","app.workers.celery_app","worker","-l","info"