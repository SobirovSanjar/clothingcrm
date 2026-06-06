#!/usr/bin/env bash
# Local development runner (expects PostgreSQL reachable via DATABASE_URL).
set -e

if [ ! -f .env ]; then
  echo "No .env found — copying .env.example"
  cp .env.example .env
fi

python -m app.seed
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
