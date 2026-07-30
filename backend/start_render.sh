#!/usr/bin/env bash
# Convert Render's Postgres URL into the formats this FastAPI app expects,
# then start uvicorn on Render's $PORT.
set -euo pipefail

RAW="${DATABASE_URL:-}"
if [ -z "$RAW" ]; then
  echo "ERROR: DATABASE_URL is not set" >&2
  exit 1
fi

# Render often provides postgres://… — normalize to postgresql://…
case "$RAW" in
  postgres://*)
    RAW="postgresql://${RAW#postgres://}"
    ;;
esac

# Sync driver URL for SQLAlchemy sync / Alembic-style use
export DATABASE_URL_SYNC="$RAW"

# Async driver URL for asyncpg
export DATABASE_URL="postgresql+asyncpg://${RAW#postgresql://}"
export LANGRAPH_CHECKPOINT_DB_URL="$DATABASE_URL"

echo "Starting S Combinator backend on port ${PORT:-8000}…"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
