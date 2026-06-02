#!/usr/bin/env bash
# Run the end-to-end pipeline test against a running stack.
# Precondition: `docker compose up` is healthy (API reachable on :8000).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/backend"

export RUN_INTEGRATION=1
export API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

uv run pytest tests/integration -v
