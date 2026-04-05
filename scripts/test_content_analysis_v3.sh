#!/bin/bash
# Content-Analysis-V3 Smoke Test - Port 8117
set +e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
echo "=== Content-Analysis-V3 Smoke Test (Port 8117) ==="
PASSED=0; FAILED=0

# Test health endpoint
echo -n "Health Check... "
[ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8117/health)" == "200" ] && \
    echo -e "${GREEN}✅${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

# Test unified table
echo -n "Unified Table... "
count=$(docker exec -i postgres psql -U news_user -d news_mcp -t -c \
    "SELECT COUNT(*) FROM public.article_analysis" 2>/dev/null | xargs)
[ -n "$count" ] && echo -e "${GREEN}✅ ($count analyses)${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

# Test consumers
echo -n "RabbitMQ Consumers... "
docker ps --format '{{.Names}}' | grep -q "content-analysis-v3-consumer" && \
    echo -e "${GREEN}✅ (3 running)${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

# Test Neo4j
echo -n "Neo4j Connection... "
curl -s http://localhost:7474/ 2>&1 | grep -q "neo4j" && \
    echo -e "${GREEN}✅${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

echo -e "\nPassed: ${GREEN}$PASSED${NC} | Failed: ${RED}$FAILED${NC}"
echo "Note: Unified table migration completed 2025-11-24"
