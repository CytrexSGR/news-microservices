#!/bin/bash

# Analytics Service Smoke Test - Port 8107
# Metrics, dashboards, and analytics data

set +e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "=== Analytics Service Smoke Test ==="
echo "Port: 8107"
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
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8107/health 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 2: Get Metrics (Critical)
echo -n "2. Get Metrics... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8107/api/v1/metrics" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 3: Dashboard Data (Warning)
echo -n "3. Dashboard Data... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8107/api/v1/dashboard" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}WARN (HTTP $RESPONSE)${NC}"
    ((WARNINGS++))
fi

# Test 4: Service Stats (Warning)
echo -n "4. Service Stats... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8107/api/v1/stats" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}WARN (HTTP $RESPONSE)${NC}"
    ((WARNINGS++))
fi

# Test 5: No Auth Check (Critical)
echo -n "5. No Auth Check... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:8107/api/v1/metrics" 2>/dev/null)
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
    echo -e "${GREEN}Analytics Service: OPERATIONAL${NC}"
    exit 0
else
    echo -e "${RED}Analytics Service: DEGRADED${NC}"
    exit 1
fi
