#!/usr/bin/env bash
# Normalize DATABASE_URL for this FastAPI app (Render Postgres OR Neon),
# create tables + admin if needed, then start uvicorn on Render's $PORT.
set -euo pipefail

RAW="${DATABASE_URL:-}"
if [ -z "$RAW" ]; then
  echo "ERROR: DATABASE_URL is not set" >&2
  exit 1
fi

# Render / some hosts provide postgres://… — normalize to postgresql://…
case "$RAW" in
  postgres://*)
    RAW="postgresql://${RAW#postgres://}"
    ;;
esac

# Strip query string for rebuilding driver-specific URLs
BASE="${RAW%%\?*}"
QUERY=""
case "$RAW" in
  *\?*) QUERY="${RAW#*\?}" ;;
esac

# Sync URL: keep sslmode=require for Neon/psycopg2
SYNC_URL="$BASE"
if echo "$BASE" | grep -qi "neon.tech\|pooler"; then
  SYNC_URL="${BASE}?sslmode=require"
elif [ -n "$QUERY" ]; then
  # Keep original query if present (non-Neon)
  SYNC_URL="${BASE}?${QUERY}"
fi
export DATABASE_URL_SYNC="$SYNC_URL"

# Async URL for asyncpg: use ssl=require (NOT sslmode / channel_binding)
ASYNC_BASE="postgresql+asyncpg://${BASE#postgresql://}"
if echo "$BASE" | grep -qi "neon.tech\|pooler"; then
  export DATABASE_URL="${ASYNC_BASE}?ssl=require"
else
  export DATABASE_URL="$ASYNC_BASE"
fi
export LANGRAPH_CHECKPOINT_DB_URL="$DATABASE_URL"

echo "DB target: $(echo "$BASE" | sed -E 's#://[^:]+:[^@]+@#://***:***@#')"

# Free-tier friendly: create tables + admin on boot
echo "Initializing database tables and admin user…"
python init_db.py

echo "Starting S Combinator backend on port ${PORT:-8000}…"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
