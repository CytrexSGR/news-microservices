#!/bin/bash
# init-migrations.sh - Initialize Alembic migrations from current models
#
# This script creates the initial migration from all models in database/models/
# Run this after drop-recreate-dbs.sh to set up the schema.
#
# Usage: ./scripts/init-migrations.sh [migration-message]

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DATABASE_DIR="${DATABASE_DIR:-/home/cytrex/database}"
MIGRATION_MESSAGE="${1:-Initial migration - all service models}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Alembic Migration Initialization${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if database directory exists
if [ ! -d "$DATABASE_DIR" ]; then
    echo -e "${RED}Error: Database directory not found at $DATABASE_DIR${NC}"
    exit 1
fi

# Check if alembic.ini exists
if [ ! -f "$DATABASE_DIR/alembic.ini" ]; then
    echo -e "${RED}Error: alembic.ini not found at $DATABASE_DIR/alembic.ini${NC}"
    exit 1
fi

# Check if models can be imported
echo -e "${YELLOW}Step 1: Checking if models are importable...${NC}"
python3 -c "
import sys
sys.path.insert(0, '/home/cytrex')
try:
    from news_mcp.app.models.base import Base
    print('✓ Models imported successfully')
except ImportError as e:
    print(f'✗ Failed to import models: {e}')
    sys.exit(1)
" || {
    echo -e "${RED}Failed to import models. Check Python path and model structure.${NC}"
    exit 1
}

# Change to database directory
cd "$DATABASE_DIR"

echo ""
echo -e "${YELLOW}Step 2: Checking Alembic initialization...${NC}"

# Check if alembic is initialized
if [ ! -d "alembic/versions" ]; then
    echo -e "${YELLOW}Alembic not initialized. Initializing...${NC}"
    # Note: We manually created alembic structure, so this should already exist
    mkdir -p alembic/versions
    echo -e "${GREEN}✓ Created versions directory${NC}"
fi

echo ""
echo -e "${YELLOW}Step 3: Cleaning old migrations...${NC}"

# Remove any existing migration files
MIGRATION_COUNT=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)
if [ "$MIGRATION_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Found $MIGRATION_COUNT existing migration(s). Removing...${NC}"
    rm -f alembic/versions/*.py
    echo -e "${GREEN}✓ Removed old migrations${NC}"
else
    echo -e "${GREEN}✓ No old migrations to remove${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Creating initial migration...${NC}"

# Set database URL from environment or use default
export ALEMBIC_DATABASE_URL="${ALEMBIC_DATABASE_URL:-postgresql://news_user:news_password@localhost:5433/news_mcp}"

# Generate initial migration
alembic revision --autogenerate -m "$MIGRATION_MESSAGE" && {
    echo -e "${GREEN}✓ Initial migration created successfully${NC}"
} || {
    echo -e "${RED}✗ Failed to create migration${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}Step 5: Reviewing migration...${NC}"

# Show the created migration file
LATEST_MIGRATION=$(ls -t alembic/versions/*.py | head -1)
if [ -f "$LATEST_MIGRATION" ]; then
    echo -e "${GREEN}Migration file: $LATEST_MIGRATION${NC}"
    echo ""
    echo "Preview (first 50 lines):"
    echo "----------------------------------------"
    head -50 "$LATEST_MIGRATION"
    echo "----------------------------------------"
    echo ""
    echo -e "${YELLOW}Full migration file created at: $LATEST_MIGRATION${NC}"
else
    echo -e "${RED}Warning: Could not find created migration file${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Migration initialization complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the migration file at: $LATEST_MIGRATION"
echo "  2. Apply migration: cd database && alembic upgrade head"
echo "  3. Verify tables: psql -h localhost -p 5433 -U news_user -d news_mcp -c '\dt *.*'"
echo ""
echo -e "${YELLOW}Note: Always review auto-generated migrations before applying!${NC}"
