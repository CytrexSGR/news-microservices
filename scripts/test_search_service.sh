#!/bin/bash

# Search Service Smoke Test - Port 8106
# Full-text search across articles and content

set +e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "=== Search Service Smoke Test ==="
echo "Port: 8106"
echo "Date: $(date)"
echo ""

PASSED=0
FAILED=0
WARNINGS=0

# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"andreas@test.com","password":"Aug2012#"}' 2>/dev/null | jq -r '.access_token' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo -e "${RED}ERROR: Failed to get auth token. Auth service may be down.${NC}"
    exit 1
fi

# Test 1: Health Check (Critical)
echo -n "1. Health Check... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8106/health 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 2: Search Query (Critical)
echo -n "2. Search Query (test)... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8106/api/v1/search?q=test" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 3: Empty Query (Critical)
echo -n "3. Empty Query Validation... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8106/api/v1/search?q=" 2>/dev/null)
if [ "$RESPONSE" == "400" ] || [ "$RESPONSE" == "422" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
elif [ "$RESPONSE" == "200" ]; then
    echo -e "${YELLOW}WARN (accepts empty query)${NC}"
    ((WARNINGS++))
else
    echo -e "${RED}FAIL (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 4: Pagination (Warning)
echo -n "4. Pagination... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8106/api/v1/search?q=news&page=1&limit=10" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}WARN (HTTP $RESPONSE)${NC}"
    ((WARNINGS++))
fi

# Test 5: No Auth (Critical)
echo -n "5. No Auth Check... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:8106/api/v1/search?q=test" 2>/dev/null)
if [ "$RESPONSE" == "401" ] || [ "$RESPONSE" == "403" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL (Expected 401/403, got HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

echo ""
echo "=== Summary ==="
echo -e "Passed:   ${GREEN}$PASSED${NC}"
echo -e "Failed:   ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}Search Service: OPERATIONAL${NC}"
    exit 0
else
    echo -e "${RED}Search Service: DEGRADED${NC}"
    exit 1
fi
