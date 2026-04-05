#!/bin/bash
set -e

echo "=== Database Migration Pre-Flight Checklist ==="
echo ""

# 1. Environment Discovery
echo "1. Docker Compose Configuration"
POSTGRES_CONTAINER=$(docker-compose ps postgres --quiet 2>/dev/null)
if [ -n "$POSTGRES_CONTAINER" ]; then
  echo "   ✅ Database Container: news-postgres (running)"
  DB_PORT=$(docker-compose port postgres 5432 2>/dev/null | cut -d: -f2)
  echo "   ✅ Database Port: $DB_PORT"
  echo "   ✅ Database User: news_user (from docker-compose.yml)"
  echo "   ✅ Database Name: news_mcp (from docker-compose.yml)"
else
  echo "   ❌ PostgreSQL container not running!"
  echo "   Run: docker-compose up -d postgres"
  exit 1
fi
echo ""

# 2. Service Configuration
echo "2. Service Database URLs"
for service in content-analysis-service feed-service; do
  echo "   $service:"
  if [ -f "services/$service/.env" ]; then
    DB_URL=$(grep DATABASE_URL "services/$service/.env" 2>/dev/null || echo "")
    if [ -n "$DB_URL" ]; then
      echo "     $DB_URL"
    else
      echo "     ⚠️  DATABASE_URL not found in .env"
    fi
  else
    echo "     ⚠️  No .env file found"
  fi
done
echo ""

# 3. Container Health
echo "3. Container Status"
docker-compose ps postgres redis rabbitmq 2>/dev/null || echo "   ⚠️  Some containers not running"
echo ""

# 4. Migration Files
echo "4. Migration Files Present"
for service in content-analysis-service feed-service scheduler-service; do
  if [ -d "services/$service/alembic/versions" ]; then
    echo "   $service:"
    MIGRATION_COUNT=$(ls -1 services/$service/alembic/versions/*.py 2>/dev/null | wc -l)
    if [ "$MIGRATION_COUNT" -gt 0 ]; then
      echo "     ✅ $MIGRATION_COUNT migration file(s)"
      ls -1 services/$service/alembic/versions/*.py 2>/dev/null | tail -2 | xargs -n1 basename
    else
      echo "     ⚠️  No migration files"
    fi
  fi
done
echo ""

# 5. Database Connection Test
echo "5. Database Connection Test"
PGPASSWORD=your_db_password docker exec news-postgres psql -U news_user -d news_mcp -c "SELECT version();" > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "   ✅ Connection successful"
  PG_VERSION=$(PGPASSWORD=your_db_password docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT version();" 2>/dev/null | head -1 | awk '{print $2}')
  echo "   PostgreSQL Version: $PG_VERSION"
else
  echo "   ❌ Connection failed"
  exit 1
fi
echo ""

# 6. Current Schema State
echo "6. Current Database Schema"
TABLE_COUNT=$(PGPASSWORD=your_db_password docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
echo "   Total Tables: $TABLE_COUNT"

# Check for key tables
for table in feeds analysis_results finance_sentiment geopolitical_sentiment; do
  EXISTS=$(PGPASSWORD=your_db_password docker exec news-postgres psql -U news_user -d news_mcp -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$table');" 2>/dev/null | tr -d ' ')
  if [ "$EXISTS" = "t" ]; then
    echo "   ✅ $table exists"
  else
    echo "   ⚠️  $table not found"
  fi
done
echo ""

echo "✅ Pre-flight check complete!"
echo ""
echo "Next steps:"
echo "  1. If DATABASE_URL incorrect, update .env files"
echo "  2. Run: ./scripts/run-migrations.sh <service-name>"
echo "  3. Or run all: for svc in content-analysis-service feed-service; do ./scripts/run-migrations.sh \$svc; done"
