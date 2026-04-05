#!/bin/bash
# drop-recreate-dbs.sh - Drop and recreate all PostgreSQL databases for News MCP
#
# WARNING: This script will DELETE all data in the databases!
# Use only for development/testing or when starting fresh.
#
# Usage: ./scripts/drop-recreate-dbs.sh

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Database configuration
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5433}"
DB_USER="${POSTGRES_USER:-news_user}"
DB_PASSWORD="${POSTGRES_PASSWORD:-news_password}"
MAIN_DB="${POSTGRES_DB:-news_mcp}"

# List of all service databases (if using separate DBs per service)
# Note: Currently using single shared DB with schemas
SERVICE_DBS=(
    "auth_db"
    "scheduler_db"
    "content_analysis_db"
    "research_db"
    "osint_db"
    "notification_db"
    "search_db"
    "analytics_db"
    "feed_db"
    "scraping_db"
)

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  News MCP Database Reset Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${RED}WARNING: This will DELETE all data!${NC}"
echo ""
echo "Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo "  Main DB: $MAIN_DB"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${GREEN}Cancelled. No changes made.${NC}"
    exit 0
fi

# Export password for psql commands
export PGPASSWORD="$DB_PASSWORD"

echo -e "${YELLOW}Step 1: Terminating existing connections...${NC}"

# Terminate all connections to the main database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$MAIN_DB'
  AND pid <> pg_backend_pid();
" 2>/dev/null || echo "  No active connections to $MAIN_DB"

# Terminate connections to service databases
for db in "${SERVICE_DBS[@]}"; do
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = '$db'
      AND pid <> pg_backend_pid();
    " 2>/dev/null || echo "  No active connections to $db"
done

echo -e "${GREEN}✓ Connections terminated${NC}"
echo ""

echo -e "${YELLOW}Step 2: Dropping existing databases...${NC}"

# Drop main database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $MAIN_DB;" 2>/dev/null \
    && echo -e "${GREEN}✓ Dropped $MAIN_DB${NC}" \
    || echo -e "${RED}✗ Failed to drop $MAIN_DB (may not exist)${NC}"

# Drop service databases
for db in "${SERVICE_DBS[@]}"; do
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $db;" 2>/dev/null \
        && echo -e "${GREEN}✓ Dropped $db${NC}" \
        || echo -e "${RED}✗ Failed to drop $db (may not exist)${NC}"
done

echo ""
echo -e "${YELLOW}Step 3: Creating fresh databases...${NC}"

# Create main database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
CREATE DATABASE $MAIN_DB
    WITH OWNER = $DB_USER
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TEMPLATE = template0;
" && echo -e "${GREEN}✓ Created $MAIN_DB${NC}" \
  || { echo -e "${RED}✗ Failed to create $MAIN_DB${NC}"; exit 1; }

# Create service databases (optional - currently using single DB with schemas)
# Uncomment if switching to separate databases per service
# for db in "${SERVICE_DBS[@]}"; do
#     psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
#     CREATE DATABASE $db
#         WITH OWNER = $DB_USER
#         ENCODING = 'UTF8'
#         LC_COLLATE = 'en_US.utf8'
#         LC_CTYPE = 'en_US.utf8'
#         TEMPLATE = template0;
#     " && echo -e "${GREEN}✓ Created $db${NC}" \
#       || echo -e "${RED}✗ Failed to create $db${NC}"
# done

echo ""
echo -e "${YELLOW}Step 4: Creating extensions...${NC}"

# Enable required PostgreSQL extensions
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$MAIN_DB" -c "
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";
CREATE EXTENSION IF NOT EXISTS \"btree_gin\";
" && echo -e "${GREEN}✓ Extensions created${NC}" \
  || echo -e "${RED}✗ Failed to create extensions${NC}"

echo ""
echo -e "${YELLOW}Step 5: Creating schemas for services...${NC}"

# Create schemas for each service in the main database
SCHEMAS=(
    "auth"
    "scheduler"
    "content_analysis"
    "research"
    "osint"
    "notification"
    "search"
    "analytics"
    "feed"
    "scraping"
)

for schema in "${SCHEMAS[@]}"; do
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$MAIN_DB" -c "
    CREATE SCHEMA IF NOT EXISTS $schema AUTHORIZATION $DB_USER;
    " && echo -e "${GREEN}✓ Created schema: $schema${NC}" \
      || echo -e "${RED}✗ Failed to create schema: $schema${NC}"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Database reset complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Run: ./scripts/init-migrations.sh"
echo "  2. Run: cd database && alembic upgrade head"
echo ""
echo -e "${YELLOW}Note: All data has been deleted. Run migrations to recreate tables.${NC}"

# Unset password
unset PGPASSWORD
