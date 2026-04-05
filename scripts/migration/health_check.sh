#!/bin/bash
# Health Check Script - Verify feed-service API is working correctly
# Tests health endpoint, authentication, and data retrieval

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

FEED_SERVICE_URL="${FEED_SERVICE_URL:-http://localhost:8101}"
AUTH_SERVICE_URL="${AUTH_SERVICE_URL:-http://localhost:8100}"

# Track checks
CHECKS_PASSED=0
CHECKS_TOTAL=5

# ════════════════════════════════════════════════════════════════════
# 1. SERVICE HEALTH
# ════════════════════════════════════════════════════════════════════
if curl -sf "$FEED_SERVICE_URL/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Service health endpoint responds"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Service health endpoint not responding"
fi

# ════════════════════════════════════════════════════════════════════
# 2. AUTHENTICATION
# ════════════════════════════════════════════════════════════════════
TOKEN=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"andreas@test.com","password":"Aug2012#"}' | jq -r '.access_token // empty')

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo -e "${GREEN}✓${NC} Authentication successful"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Authentication failed"
    exit 1
fi

# ════════════════════════════════════════════════════════════════════
# 3. ARTICLE LIST ENDPOINT
# ════════════════════════════════════════════════════════════════════
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "$FEED_SERVICE_URL/api/v1/feeds/items?limit=1")

if echo "$RESPONSE" | jq -e '.items' >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Article list endpoint returns data"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Article list endpoint failed"
    echo "Response: $RESPONSE"
fi

# ════════════════════════════════════════════════════════════════════
# 4. ANALYSIS DATA STRUCTURE
# ════════════════════════════════════════════════════════════════════
HAS_PIPELINE=$(echo "$RESPONSE" | jq -e '.items[0].pipeline_execution' >/dev/null 2>&1 && echo "1" || echo "0")

if [ "$HAS_PIPELINE" = "1" ]; then
    echo -e "${GREEN}✓${NC} Response contains pipeline_execution"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Response missing pipeline_execution"
fi

# ════════════════════════════════════════════════════════════════════
# 5. DATA FIELDS PRESENT
# ════════════════════════════════════════════════════════════════════
HAS_TRIAGE=$(echo "$RESPONSE" | jq -e '.items[0].pipeline_execution.triage_decision' >/dev/null 2>&1 && echo "1" || echo "0")
HAS_TIER1=$(echo "$RESPONSE" | jq -e '.items[0].pipeline_execution.entity_results' >/dev/null 2>&1 && echo "1" || echo "0")

if [ "$HAS_TRIAGE" = "1" ] && [ "$HAS_TIER1" = "1" ]; then
    echo -e "${GREEN}✓${NC} Analysis data fields present"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Analysis data incomplete"
    echo "Triage: $HAS_TRIAGE, Tier1: $HAS_TIER1"
fi

# ════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════
echo ""
if [ "$CHECKS_PASSED" -eq "$CHECKS_TOTAL" ]; then
    echo -e "${GREEN}✅ Health check passed ($CHECKS_PASSED/$CHECKS_TOTAL)${NC}"
    exit 0
else
    echo -e "${RED}✗ Health check failed ($CHECKS_PASSED/$CHECKS_TOTAL)${NC}"
    exit 1
fi
