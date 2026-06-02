# syntax=docker/dockerfile:1
FROM python:3.12-slim

# uv provides fast, reproducible dependency installation from uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /uvx /bin/

# Build toolchain for any sdist-only scientific deps (pmdarima / prophet fallbacks)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential gcc g++ \
 && rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Resolve + install dependencies into the SYSTEM interpreter (outside /app, so the
# api_data volume mounted at /app does not shadow them). Code is added afterwards.
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-emit-project --no-dev -o /tmp/requirements.txt \
 && uv pip install --system --no-cache -r /tmp/requirements.txt

COPY . .
