#!/usr/bin/env bash
set -euo pipefail
echo "BLOCKED: A Celery long-running worker must not be deployed as an ordinary Cloud Run request service."
echo "The public geofence demo does not require a worker; see docs/production-demo.md."
exit 1
