#!/bin/bash
set -e

HOST="${1:-db}"
PORT="${2:-5432}"

echo "Waiting for $HOST:$PORT..."

until nc -z "$HOST" "$PORT" 2>/dev/null || pg_isready -h "$HOST" -p "$PORT" -U "${POSTGRES_USER:-postgres}" 2>/dev/null; do
  echo "Postgres is unavailable at $HOST:$PORT - sleeping"
  sleep 2
done

echo "Postgres is available at $HOST:$PORT"
