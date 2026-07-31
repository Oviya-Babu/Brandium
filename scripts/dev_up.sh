#!/usr/bin/env bash
# Bring up the full local stack and apply migrations. Never a security
# bypass (CLAUDE.md §6) — just sequencing convenience.
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d postgres redis minio qdrant ollama

echo "Waiting for Postgres to be healthy..."
until docker compose ps postgres | grep -q "healthy"; do
  sleep 1
done

docker compose run --rm backend alembic upgrade head

docker compose up -d backend worker frontend

echo "Brandium local stack is up:"
echo "  API:      http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo "  MinIO:    http://localhost:9001"
echo "  Qdrant:   http://localhost:6333/dashboard"
