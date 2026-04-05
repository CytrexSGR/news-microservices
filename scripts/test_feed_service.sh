#!/bin/bash
# Feed Service Smoke Test - Port 8101
set +e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
echo "=== Feed Service Smoke Test (Port 8101) ==="
PASSED=0; FAILED=0

# Test health endpoint
echo -n "Health Check... "
[ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8101/health)" == "200" ] && \
    echo -e "${GREEN}✅${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

# Test database
echo -n "Database (feeds)... "
count=$(docker exec -i postgres psql -U news_user -d news_mcp -t -c "SELECT COUNT(*) FROM feeds" 2>/dev/null | xargs)
[ -n "$count" ] && echo -e "${GREEN}✅ ($count feeds)${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

# Test Celery worker
echo -n "Celery Worker... "
docker exec news-feed-service-celery-worker celery -A app.celery_app inspect ping 2>&1 | grep -q "pong" && \
    echo -e "${GREEN}✅${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

echo -e "\nPassed: ${GREEN}$PASSED${NC} | Failed: ${RED}$FAILED${NC}"
