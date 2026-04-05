#!/bin/bash
# Backfill Execution Wrapper with Safety Checks and Logging
# Executes backfill_unified_table.sql with comprehensive error handling

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_USER="${POSTGRES_USER:-news_user}"
DB_NAME="${POSTGRES_DB:-news_mcp}"
LOG_FILE="/tmp/backfill_execution_$(date +%Y%m%d_%H%M%S).log"

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  BACKFILL EXECUTION WRAPPER                                ║${NC}"
echo -e "${CYAN}║  Migrating 3733 rows from legacy to unified table          ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ════════════════════════════════════════════════════════════════════
# 1. PRE-FLIGHT CHECKS
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Pre-Flight Checks${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if SQL file exists
if [ ! -f "$PROJECT_ROOT/tests/migration/backfill_unified_table.sql" ]; then
    echo -e "${RED}✗ Backfill SQL file not found!${NC}"
    echo "Expected: $PROJECT_ROOT/tests/migration/backfill_unified_table.sql"
    exit 1
fi
echo -e "${GREEN}✓${NC} Backfill SQL file exists"

# Check if PostgreSQL is accessible
if ! docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${RED}✗ PostgreSQL not accessible${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} PostgreSQL accessible"

# Check row counts before migration
LEGACY_COUNT=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;" 2>/dev/null | xargs)
UNIFIED_COUNT_BEFORE=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT COUNT(*) FROM public.article_analysis;" 2>/dev/null | xargs)
EXPECTED_MISSING=$((LEGACY_COUNT - UNIFIED_COUNT_BEFORE))

echo -e "${GREEN}✓${NC} Legacy table: $LEGACY_COUNT rows"
echo -e "${GREEN}✓${NC} Unified table (before): $UNIFIED_COUNT_BEFORE rows"
echo -e "${GREEN}✓${NC} Expected to migrate: $EXPECTED_MISSING rows"
echo ""

# Safety check: If no rows to migrate, abort
if [ "$EXPECTED_MISSING" -le 0 ]; then
    echo -e "${YELLOW}⚠️  No rows to migrate (unified table already complete)${NC}"
    echo "Aborting. If this is unexpected, investigate data state."
    exit 1
fi

# ════════════════════════════════════════════════════════════════════
# 2. EXECUTE BACKFILL
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Executing Backfill${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "This may take 2-5 minutes for $EXPECTED_MISSING rows..."
echo ""

START_TIME=$(date +%s)

# Execute backfill SQL with logging
if docker exec -i postgres psql -U "$DB_USER" -d "$DB_NAME" \
    < "$PROJECT_ROOT/tests/migration/backfill_unified_table.sql" \
    > "$LOG_FILE" 2>&1; then

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo -e "${GREEN}✅ Backfill completed successfully${NC}"
    echo "Duration: ${DURATION}s"
    echo "Log: $LOG_FILE"
    echo ""
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo -e "${RED}✗ Backfill FAILED${NC}"
    echo "Duration: ${DURATION}s"
    echo "Log: $LOG_FILE"
    echo ""
    echo "Last 20 lines of log:"
    tail -20 "$LOG_FILE"
    exit 1
fi

# ════════════════════════════════════════════════════════════════════
# 3. POST-BACKFILL VERIFICATION
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Post-Backfill Verification${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check row counts after migration
UNIFIED_COUNT_AFTER=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT COUNT(*) FROM public.article_analysis;" 2>/dev/null | xargs)
ROWS_INSERTED=$((UNIFIED_COUNT_AFTER - UNIFIED_COUNT_BEFORE))

echo "Legacy table: $LEGACY_COUNT rows"
echo "Unified table (after): $UNIFIED_COUNT_AFTER rows"
echo "Rows inserted: $ROWS_INSERTED"
echo ""

# Verification checks
CHECKS_PASSED=0
CHECKS_TOTAL=4

# 1. Counts match
if [ "$UNIFIED_COUNT_AFTER" -eq "$LEGACY_COUNT" ]; then
    echo -e "${GREEN}✓${NC} Counts match (unified = legacy)"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Counts mismatch! Expected $LEGACY_COUNT, got $UNIFIED_COUNT_AFTER"
fi

# 2. No missing analyses
MISSING=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions pe
     LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id
     WHERE aa.id IS NULL;" 2>/dev/null | xargs)

if [ "$MISSING" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No missing analyses"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} $MISSING analyses still missing!"
fi

# 3. No duplicates
DUPLICATES=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT COUNT(*) FROM (
       SELECT article_id, COUNT(*) as cnt
       FROM public.article_analysis
       GROUP BY article_id
       HAVING COUNT(*) > 1
     ) sub;" 2>/dev/null | xargs)

if [ "$DUPLICATES" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No duplicates"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} $DUPLICATES duplicate article_ids found!"
fi

# 4. Data quality (relevance scores extracted)
RELEVANCE_COUNT=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT COUNT(*) FROM public.article_analysis
     WHERE success = true AND relevance_score IS NOT NULL;" 2>/dev/null | xargs)
SUCCESS_COUNT=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT COUNT(*) FROM public.article_analysis WHERE success = true;" 2>/dev/null | xargs)
RELEVANCE_PCT=$((RELEVANCE_COUNT * 100 / SUCCESS_COUNT))

if [ "$RELEVANCE_PCT" -gt 80 ]; then
    echo -e "${GREEN}✓${NC} Relevance scores extracted ($RELEVANCE_PCT%)"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Low relevance score extraction ($RELEVANCE_PCT% < 80%)"
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 4. SUMMARY
# ════════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}SUMMARY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$CHECKS_PASSED" -eq "$CHECKS_TOTAL" ]; then
    echo -e "${GREEN}✅ BACKFILL SUCCESSFUL${NC}"
    echo ""
    echo "Results:"
    echo "  - Migrated: $ROWS_INSERTED rows"
    echo "  - Total in unified table: $UNIFIED_COUNT_AFTER"
    echo "  - Duration: ${DURATION}s"
    echo "  - All verification checks passed ($CHECKS_PASSED/$CHECKS_TOTAL)"
    echo ""
    echo "Next steps:"
    echo "  1. Deploy feed-service update (reads from unified table)"
    echo "  2. Run post-migration tests"
    echo "  3. Start 24h monitoring"
    exit 0
else
    echo -e "${RED}⚠️  BACKFILL COMPLETED WITH ISSUES${NC}"
    echo ""
    echo "Results:"
    echo "  - Migrated: $ROWS_INSERTED rows"
    echo "  - Verification: $CHECKS_PASSED/$CHECKS_TOTAL checks passed"
    echo "  - Duration: ${DURATION}s"
    echo ""
    echo "⚠️  Review log file: $LOG_FILE"
    echo "⚠️  Consider rollback if critical checks failed"
    exit 1
fi
