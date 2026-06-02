# Run the end-to-end pipeline test against a running stack.
# Precondition: `docker compose up` is healthy (API reachable on :8000).
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $RepoRoot "backend")

$env:RUN_INTEGRATION = "1"
if (-not $env:API_BASE_URL) { $env:API_BASE_URL = "http://localhost:8000" }

uv run pytest tests/integration -v
