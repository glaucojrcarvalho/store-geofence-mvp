#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

echo "Cleaning pytest and ruff caches..."
# Try to take ownership if possible
if command -v sudo >/dev/null 2>&1; then
  sudo chown -R "$(id -u):$(id -g)" .pytest_cache || true
  sudo chown -R "$(id -u):$(id -g)" .ruff_cache || true
fi

rm -rf .pytest_cache .ruff_cache || true
mkdir -p .pytest_cache .ruff_cache
chmod -R u+rwX .pytest_cache .ruff_cache

echo "Done."

