#!/usr/bin/env bash
# Create PostgreSQL database, write .env with DATABASE_URL, run migrations.
# Usage: ./scripts/setup_local_db.sh
# Optional: PGUSER=postgres PGPASSWORD=secret ./scripts/setup_local_db.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

DB_NAME="${DB_NAME:-algo_trading}"
PGUSER="${PGUSER:-$(whoami)}"
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"

# Build DATABASE_URL (include password only if set)
if [ -n "${PGPASSWORD:-}" ]; then
  DATABASE_URL="postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${DB_NAME}"
else
  DATABASE_URL="postgresql://${PGUSER}@${PGHOST}:${PGPORT}/${DB_NAME}"
fi

echo "Creating database: $DB_NAME (user=$PGUSER host=$PGHOST port=$PGPORT)"
createdb "$DB_NAME" 2>/dev/null || true

echo "Writing .env with DATABASE_URL..."
if [ ! -f .env ]; then
  cp .env.example .env
fi
if grep -q "^DATABASE_URL=" .env; then
  sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env 2>/dev/null || \
  sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env
else
  echo "DATABASE_URL=$DATABASE_URL" >> .env
fi
rm -f .env.bak 2>/dev/null || true

echo "Running migrations..."
alembic upgrade head

echo "Done. Database ready and .env set."
