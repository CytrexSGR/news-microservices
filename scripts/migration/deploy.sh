#!/bin/bash
# Deployment Script - Deploy feed-service update after backfill
# Stops workers, restarts feed-service, verifies health, restarts workers

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

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  DEPLOYMENT: Feed-Service Update                          ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
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

# Verify stopped
sleep 2
RUNNING=$(docker ps --filter "name=analysis-consumer" --format "{{.Names}}" | wc -l)
if [ "$RUNNING" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Analysis consumer stopped"
else
    echo -e "${RED}✗${NC} Analysis consumer still running!"
    exit 1
fi

WORKER_COUNT=$(docker ps --filter "name=content-analysis-v2-worker" --format "{{.Names}}" | wc -l)
if [ "$WORKER_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All workers stopped"
else
    echo -e "${RED}✗${NC} $WORKER_COUNT workers still running!"
    exit 1
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 2. RESTART FEED-SERVICE
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 2: Restarting feed-service${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose restart feed-service

# Wait for service to start
echo "Waiting for service to start..."
sleep 10

# Check if running
if docker ps --filter "name=feed-service" --format "{{.Names}}" | grep -q "feed-service"; then
    echo -e "${GREEN}✓${NC} Feed-service restarted"
else
    echo -e "${RED}✗${NC} Feed-service failed to start!"
    docker logs news-microservices-feed-service-1 --tail 50
    exit 1
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 3. HEALTH CHECK
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 3: Health check${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run health check script
if [ -f "$PROJECT_ROOT/scripts/migration/health_check.sh" ]; then
    if bash "$PROJECT_ROOT/scripts/migration/health_check.sh"; then
        echo -e "${GREEN}✓${NC} Health check passed"
    else
        echo -e "${RED}✗${NC} Health check failed!"
        echo ""
        echo "Checking logs..."
        docker logs news-microservices-feed-service-1 --tail 30
        exit 1
    fi
else
    # Fallback: Simple health check
    sleep 5
    if curl -sf http://localhost:8101/health >/dev/null; then
        echo -e "${GREEN}✓${NC} Feed-service is healthy"
    else
        echo -e "${RED}✗${NC} Feed-service not responding!"
        exit 1
    fi
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 4. RESTART WORKERS
# ════════════════════════════════════════════════════════════════════
echo -e "${BLUE}▶ Step 4: Restarting analysis workers${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker compose start feed-service-analysis-consumer \
                     content-analysis-v2-worker-1 \
                     content-analysis-v2-worker-2 \
                     content-analysis-v2-worker-3

# Wait for workers to start
sleep 5

# Verify started
CONSUMER_UP=$(docker ps --filter "name=analysis-consumer" --format "{{.Status}}" | grep -c "Up" || echo "0")
if [ "$CONSUMER_UP" -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Analysis consumer started"
else
    echo -e "${RED}✗${NC} Analysis consumer failed to start!"
    exit 1
fi

WORKERS_UP=$(docker ps --filter "name=content-analysis-v2-worker" --format "{{.Names}}" | wc -l)
if [ "$WORKERS_UP" -eq 3 ]; then
    echo -e "${GREEN}✓${NC} All workers started ($WORKERS_UP/3)"
else
    echo -e "${YELLOW}⚠${NC} Only $WORKERS_UP/3 workers started"
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 5. SUMMARY
# ════════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}DEPLOYMENT SUMMARY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL${NC}"
echo ""
echo "Services updated:"
echo "  ✓ Workers stopped (analysis paused)"
echo "  ✓ Feed-service restarted (now reads from unified table)"
echo "  ✓ Health check passed"
echo "  ✓ Workers restarted (analysis resumed)"
echo ""
echo "Next steps:"
echo "  1. Run post-migration tests: ./tests/migration/test_post_migration.sh"
echo "  2. Trigger test analysis to verify end-to-end"
echo "  3. Start 24h monitoring: ./scripts/migration/monitor_migration.sh"
echo ""
