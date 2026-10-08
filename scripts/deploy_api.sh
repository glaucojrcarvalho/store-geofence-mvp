#!/usr/bin/env bash
set -euo pipefail
echo "BLOCKED: Legacy Cloud Run script passed credentials through CLI flags and could expose business APIs."
echo "Use docs/production-demo.md to provision reviewed secrets, Redis, private networking and a public-demo-only app."
exit 1
