#!/bin/bash

# FMP Service Smoke Test - Port 8113
# Financial Market Primitives: Stock quotes, market data, predictions

set +e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "=== FMP Service Smoke Test ==="
echo "Port: 8113"
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
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8113/health 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 2: Stock Quote - AAPL (Critical)
echo -n "2. Stock Quote (AAPL)... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8113/api/v1/quote/AAPL" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 3: Market Status (Warning)
echo -n "3. Market Status... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:8113/api/v1/market/status" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
elif [ "$RESPONSE" == "401" ] || [ "$RESPONSE" == "403" ]; then
    echo -e "${YELLOW}WARN (requires auth)${NC}"
    ((WARNINGS++))
else
    echo -e "${RED}FAIL (HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 4: Historical Data (Warning)
echo -n "4. Historical Data (AAPL)... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8113/api/v1/historical/AAPL" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}WARN (HTTP $RESPONSE)${NC}"
    ((WARNINGS++))
fi

# Test 5: Invalid Symbol (Critical)
echo -n "5. Invalid Symbol... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8113/api/v1/quote/INVALID123XYZ" 2>/dev/null)
if [ "$RESPONSE" == "404" ] || [ "$RESPONSE" == "400" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL (Expected 404, got HTTP $RESPONSE)${NC}"
    ((FAILED++))
fi

# Test 6: DCC-GARCH Prediction (Warning)
echo -n "6. DCC-GARCH Prediction... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8113/api/v1/predict/AAPL" 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}WARN (HTTP $RESPONSE)${NC}"
    ((WARNINGS++))
fi

echo ""
echo "=== Summary ==="
echo -e "Passed:   ${GREEN}$PASSED${NC}"
echo -e "Failed:   ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}FMP Service: OPERATIONAL${NC}"
    exit 0
else
    echo -e "${RED}FMP Service: DEGRADED${NC}"
    exit 1
fi
