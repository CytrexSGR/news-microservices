#!/bin/bash
# Rollback Script - Revert to legacy table if migration issues detected
# Stops workers, reverts code, restarts feed-service

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="/home/cytrex/news-microservices"
cd "$PROJECT_ROOT"

echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  ROLLBACK: Reverting to Legacy Table                      ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will revert feed-service to read from legacy table${NC}"
echo ""
read -p "Continue with rollback? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 1. STOP WORKERS
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 1: Stopping analysis workers${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose stop feed-service-analysis-consumer \
                     content-analysis-v2-worker-1 \
                     content-analysis-v2-worker-2 \
                     content-analysis-v2-worker-3

echo -e "${GREEN}✓${NC} Workers stopped"
echo ""

# ════════════════════════════════════════════════════════════════════
# 2. RESTORE LEGACY TABLE (if renamed)
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 2: Checking legacy table${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if deprecated table exists
DEPRECATED_EXISTS=$(docker exec postgres psql -U news_user -d news_mcp -t -A -c \
    "SELECT COUNT(*) FROM information_schema.tables
     WHERE table_schema='content_analysis_v2' AND table_name='pipeline_executions_deprecated';" 2>/dev/null | xargs)

if [ "$DEPRECATED_EXISTS" = "1" ]; then
    echo "Found deprecated table, restoring..."

    docker exec postgres psql -U news_user -d news_mcp -c \
        "ALTER TABLE content_analysis_v2.pipeline_executions_deprecated
         RENAME TO pipeline_executions;"

    echo -e "${GREEN}✓${NC} Legacy table restored"
else
    echo -e "${GREEN}✓${NC} Legacy table already exists (no restore needed)"
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 3. REVERT CODE CHANGES
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 3: Reverting code changes${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Save current version as backup
if [ -f "services/feed-service/app/services/analysis_loader.py" ]; then
    cp services/feed-service/app/services/analysis_loader.py \
       services/feed-service/app/services/analysis_loader.py.migration_backup
    echo "Saved migration version as .migration_backup"
fi

# Check if git has changes
if git status --porcelain | grep -q "analysis_loader.py"; then
    echo "Reverting analysis_loader.py via git..."
    git checkout HEAD -- services/feed-service/app/services/analysis_loader.py

    echo -e "${GREEN}✓${NC} Code reverted to legacy version"
else
    echo -e "${YELLOW}⚠${NC} No git changes found (already reverted or not committed)"
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 4. RESTART FEED-SERVICE
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 4: Restarting feed-service${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose restart feed-service

echo "Waiting for service to start..."
sleep 10

if docker ps --filter "name=feed-service" --format "{{.Names}}" | grep -q "feed-service"; then
    echo -e "${GREEN}✓${NC} Feed-service restarted"
else
    echo -e "${RED}✗${NC} Feed-service failed to start!"
    docker logs news-microservices-feed-service-1 --tail 50
    exit 1
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 5. VERIFY API
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 5: Verifying API${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sleep 5

if curl -sf http://localhost:8101/health >/dev/null; then
    echo -e "${GREEN}✓${NC} API is healthy"
else
    echo -e "${RED}✗${NC} API not responding!"
    exit 1
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 6. RESTART WORKERS
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 6: Restarting workers${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose start feed-service-analysis-consumer \
                     content-analysis-v2-worker-1 \
                     content-analysis-v2-worker-2 \
                     content-analysis-v2-worker-3

sleep 5
echo -e "${GREEN}✓${NC} Workers restarted"
echo ""

# ════════════════════════════════════════════════════════════════════
# 7. SUMMARY
# ════════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}ROLLBACK SUMMARY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ ROLLBACK SUCCESSFUL${NC}"
echo ""
echo "Reverted to:"
echo "  ✓ Legacy table (content_analysis_v2.pipeline_executions)"
echo "  ✓ Legacy code (HTTP proxy to content-analysis-v2 API)"
echo "  ✓ Feed-service restarted and healthy"
echo "  ✓ Workers restarted"
echo ""
echo "Next steps:"
echo "  1. Review what went wrong (check logs)"
echo "  2. Fix issues"
echo "  3. Retry migration on another day"
echo ""
echo "Logs to review:"
echo "  - docker logs news-microservices-feed-service-1"
echo "  - /tmp/backfill_execution_*.log"
echo "  - /tmp/post_migration_output.log"
echo ""
