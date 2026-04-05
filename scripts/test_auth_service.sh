#!/bin/bash
# Auth Service Smoke Test - Port 8100
set +e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
echo "=== Auth Service Smoke Test (Port 8100) ==="
PASSED=0; FAILED=0

# Test health endpoint
echo -n "Health Check... "
[ "$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8100/health)" == "200" ] && \
    echo -e "${GREEN}✅${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

# Test database
echo -n "Database (andreas user)... "
count=$(docker exec -i postgres psql -U news_user -d news_mcp -t -c \
    "SELECT COUNT(*) FROM users WHERE username = 'andreas'" 2>/dev/null | xargs)
[ "$count" == "1" ] && echo -e "${GREEN}✅${NC}" && ((PASSED++)) || echo -e "${RED}❌${NC}" && ((FAILED++))

echo -e "\nPassed: ${GREEN}$PASSED${NC} | Failed: ${RED}$FAILED${NC}"
echo "Note: Login endpoint has async/await bug (known issue)"
