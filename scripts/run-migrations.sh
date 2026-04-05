#!/bin/bash
set -e

SERVICE=$1
if [ -z "$SERVICE" ]; then
  echo "Usage: $0 <service-name>"
  echo "Example: $0 content-analysis-service"
  echo ""
  echo "Available services:"
  echo "  - content-analysis-service"
  echo "  - feed-service"
  echo "  - scheduler-service"
  exit 1
fi

SERVICE_DIR="services/$SERVICE"
if [ ! -d "$SERVICE_DIR" ]; then
  echo "❌ Error: Service directory $SERVICE_DIR not found"
  exit 1
fi

echo "=== Running migrations for $SERVICE ==="
echo ""

# Read database config from docker-compose.yml
DB_HOST="localhost"
DB_PORT=$(docker-compose port postgres 5432 2>/dev/null | cut -d: -f2)
if [ -z "$DB_PORT" ]; then
  echo "❌ Error: PostgreSQL container not running"
  echo "Run: docker-compose up -d postgres"
  exit 1
fi

DB_USER="news_user"
DB_PASSWORD="your_db_password"
DB_NAME="news_mcp"

echo "Database: postgresql://$DB_USER:***@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""

# Check if alembic directory exists
if [ ! -d "$SERVICE_DIR/alembic" ]; then
  echo "⚠️  No alembic directory found for $SERVICE. Skipping."
  exit 0
fi

# Check if there are any migration files
MIGRATION_COUNT=$(ls -1 "$SERVICE_DIR/alembic/versions/"*.py 2>/dev/null | wc -l)
if [ "$MIGRATION_COUNT" -eq 0 ]; then
  echo "⚠️  No migration files found in $SERVICE_DIR/alembic/versions/. Skipping."
  exit 0
fi

echo "Found $MIGRATION_COUNT migration file(s)"
echo ""

# Method 1: Try local alembic (if venv exists)
if [ -f "$SERVICE_DIR/venv/bin/alembic" ]; then
  echo "Method: Local alembic (venv)"
  cd "$SERVICE_DIR"

  # Backup .env if exists
  if [ -f ".env" ]; then
    cp .env .env.bak
  else
    echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" > .env
  fi

  # Update DATABASE_URL temporarily
  if grep -q "DATABASE_URL=" .env; then
    sed -i.tmp "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME|" .env
    rm -f .env.tmp
  else
    echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" >> .env
  fi

  echo "Running: alembic upgrade head"
  venv/bin/alembic upgrade head

  # Restore original .env
  if [ -f ".env.bak" ]; then
    mv .env.bak .env
  fi

  echo "✅ Migration completed via local alembic"
  cd ../..

# Method 2: Try Docker container alembic
elif docker exec news-$SERVICE test -d /app/alembic 2>/dev/null; then
  echo "Method: Docker container alembic"
  docker exec news-$SERVICE alembic upgrade head
  echo "✅ Migration completed via Docker container"

# Method 3: Manual SQL execution
else
  echo "Method: Manual SQL execution required"
  echo ""
  echo "⚠️  Alembic not available in venv or Docker container."
  echo ""
  LATEST_MIGRATION=$(ls -t "$SERVICE_DIR/alembic/versions/"*.py | head -1)
  echo "Latest migration file:"
  echo "  $(basename $LATEST_MIGRATION)"
  echo ""
  echo "To execute manually:"
  echo "  1. Extract SQL from: $LATEST_MIGRATION"
  echo "  2. Save to: /tmp/migration.sql"
  echo "  3. Run: PGPASSWORD=$DB_PASSWORD docker exec -i news-postgres psql -U $DB_USER -d $DB_NAME < /tmp/migration.sql"
  echo ""
  echo "Or install alembic locally:"
  echo "  cd $SERVICE_DIR"
  echo "  python -m venv venv"
  echo "  venv/bin/pip install -r requirements.txt"
  echo "  ./scripts/run-migrations.sh $SERVICE"
  exit 1
fi

# Verify migration
echo ""
echo "=== Verification ==="
PGPASSWORD=$DB_PASSWORD docker exec news-postgres psql -U $DB_USER -d $DB_NAME -c "\dt" 2>/dev/null | grep -E "(finance_sentiment|geopolitical_sentiment|feeds|analysis_results)" || echo "⚠️  Expected tables not found"

echo ""
echo "✅ Migration process complete for $SERVICE"
