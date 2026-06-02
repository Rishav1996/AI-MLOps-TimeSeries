# syntax=docker/dockerfile:1
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app/visualization

COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-emit-project --no-dev -o /tmp/requirements.txt \
 && uv pip install --system --no-cache -r /tmp/requirements.txt

COPY . .
