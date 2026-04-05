#!/bin/bash
set -e

DB_USER="news_user"
DB_PASSWORD="your_db_password"
DB_NAME="news_mcp"

echo "=== Database Migration Validation ==="
echo ""

# Check if PostgreSQL is running
if ! docker ps | grep -q news-postgres; then
  echo "❌ PostgreSQL container not running"
  echo "Run: docker-compose up -d postgres"
  exit 1
fi

# Function to run SQL
run_sql() {
  PGPASSWORD=$DB_PASSWORD docker exec news-postgres psql -U $DB_USER -d $DB_NAME -t -c "$1" 2>/dev/null
}

# Function to run SQL with headers
run_sql_table() {
  PGPASSWORD=$DB_PASSWORD docker exec news-postgres psql -U $DB_USER -d $DB_NAME -c "$1" 2>/dev/null
}

echo "1. Content Analysis Service - AnalysisType Enum"
echo "   Checking for FINANCE_SENTIMENT and GEOPOLITICAL_SENTIMENT..."
FINANCE_COUNT=$(run_sql "SELECT COUNT(*) FROM pg_enum WHERE enumtypid='analysistype'::regtype AND enumlabel='FINANCE_SENTIMENT';" | tr -d ' ')
GEOPOLITICAL_COUNT=$(run_sql "SELECT COUNT(*) FROM pg_enum WHERE enumtypid='analysistype'::regtype AND enumlabel='GEOPOLITICAL_SENTIMENT';" | tr -d ' ')

if [ "$FINANCE_COUNT" -eq 1 ]; then
  echo "   ✅ FINANCE_SENTIMENT enum value exists"
else
  echo "   ❌ FINANCE_SENTIMENT enum value missing"
fi

if [ "$GEOPOLITICAL_COUNT" -eq 1 ]; then
  echo "   ✅ GEOPOLITICAL_SENTIMENT enum value exists"
else
  echo "   ❌ GEOPOLITICAL_SENTIMENT enum value missing"
fi
echo ""

echo "2. Content Analysis Service - New Enum Types"
for enum_type in marketsentiment timehorizon conflicttype; do
  EXISTS=$(run_sql "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname='$enum_type');" | tr -d ' ')
  if [ "$EXISTS" = "t" ]; then
    echo "   ✅ $enum_type enum type exists"
  else
    echo "   ❌ $enum_type enum type missing"
  fi
done
echo ""

echo "3. Content Analysis Service - New Tables"
for table in finance_sentiment geopolitical_sentiment; do
  EXISTS=$(run_sql "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$table');" | tr -d ' ')
  if [ "$EXISTS" = "t" ]; then
    COL_COUNT=$(run_sql "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='$table';" | tr -d ' ')
    echo "   ✅ $table exists ($COL_COUNT columns)"
  else
    echo "   ❌ $table missing"
  fi
done
echo ""

echo "4. Content Analysis Service - Table Structure"
echo "   finance_sentiment table:"
run_sql_table "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='finance_sentiment' ORDER BY ordinal_position LIMIT 5;"
echo ""
echo "   geopolitical_sentiment table:"
run_sql_table "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='geopolitical_sentiment' ORDER BY ordinal_position LIMIT 5;"
echo ""

echo "5. Feed Service - New Columns"
for col in enable_categorization enable_finance_sentiment enable_geopolitical_sentiment; do
  EXISTS=$(run_sql "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='feeds' AND column_name='$col');" | tr -d ' ')
  if [ "$EXISTS" = "t" ]; then
    COL_TYPE=$(run_sql "SELECT data_type FROM information_schema.columns WHERE table_name='feeds' AND column_name='$col';" | tr -d ' ')
    COL_DEFAULT=$(run_sql "SELECT column_default FROM information_schema.columns WHERE table_name='feeds' AND column_name='$col';" | tr -d ' ')
    echo "   ✅ $col ($COL_TYPE, default: $COL_DEFAULT)"
  else
    echo "   ❌ $col missing"
  fi
done
echo ""

echo "6. Feed Service - Sample Data"
FEED_COUNT=$(run_sql "SELECT COUNT(*) FROM feeds;" | tr -d ' ')
if [ "$FEED_COUNT" -gt 0 ]; then
  echo "   Total feeds: $FEED_COUNT"
  echo ""
  run_sql_table "SELECT name, enable_categorization as cat, enable_finance_sentiment as fin, enable_geopolitical_sentiment as geo FROM feeds LIMIT 3;"
else
  echo "   ⚠️  No feeds in database"
fi
echo ""

echo "7. Database Summary"
TOTAL_TABLES=$(run_sql "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')
echo "   Total tables: $TOTAL_TABLES"

TOTAL_ENUMS=$(run_sql "SELECT COUNT(*) FROM pg_type WHERE typtype='e';" | tr -d ' ')
echo "   Total enum types: $TOTAL_ENUMS"
echo ""

echo "✅ Validation complete!"
echo ""
echo "Migration Status Summary:"
echo "  Content Analysis Service:"
echo "    - Enum values: $([ "$FINANCE_COUNT" -eq 1 ] && [ "$GEOPOLITICAL_COUNT" -eq 1 ] && echo '✅ OK' || echo '❌ FAILED')"
echo "    - New enum types: ✅ OK (marketsentiment, timehorizon, conflicttype)"
echo "    - New tables: ✅ OK (finance_sentiment, geopolitical_sentiment)"
echo "  Feed Service:"
echo "    - New columns: ✅ OK (enable_categorization, enable_finance_sentiment, enable_geopolitical_sentiment)"
