#!/bin/bash
# Script to test feed assessment for all feeds in the system
# This validates that the refactored assessment logic works with all feeds

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Feed Assessment Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Get authentication token
echo -e "${YELLOW}→ Getting authentication token...${NC}"
TOKEN=$(curl -s -X POST "http://localhost:8100/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"andreas","password":"Aug2012#"}' | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo -e "${RED}✗ Failed to get authentication token${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Authentication successful${NC}"
echo

# Get all feeds
echo -e "${YELLOW}→ Fetching all feeds...${NC}"
FEEDS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds?limit=100" | jq -c '.[]')

if [ -z "$FEEDS" ]; then
  echo -e "${RED}✗ No feeds found${NC}"
  exit 1
fi

FEED_COUNT=$(echo "$FEEDS" | wc -l)
echo -e "${GREEN}✓ Found $FEED_COUNT feeds${NC}"
echo

# Test each feed
SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

echo -e "${BLUE}Starting feed assessments...${NC}"
echo

while IFS= read -r feed; do
  FEED_ID=$(echo "$feed" | jq -r '.id')
  FEED_NAME=$(echo "$feed" | jq -r '.name // "Unknown"')
  FEED_URL=$(echo "$feed" | jq -r '.url')

  echo -e "${YELLOW}Testing: ${NC}$FEED_NAME"
  echo -e "  ID: $FEED_ID"
  echo -e "  URL: $FEED_URL"

  # Check if feed is active
  IS_ACTIVE=$(echo "$feed" | jq -r '.is_active')
  if [ "$IS_ACTIVE" != "true" ]; then
    echo -e "  ${YELLOW}⊘ Skipped (inactive)${NC}"
    ((SKIP_COUNT++))
    echo
    continue
  fi

  # Trigger assessment
  RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8101/api/v1/feeds/${FEED_ID}/assess")

  # Check response
  STATUS=$(echo "$RESPONSE" | jq -r '.status // .detail // "unknown"')

  if [ "$STATUS" == "completed" ]; then
    echo -e "  ${GREEN}✓ Assessment completed${NC}"
    ((SUCCESS_COUNT++))
  elif [ "$STATUS" == "pending" ]; then
    echo -e "  ${YELLOW}⟳ Assessment pending (async mode)${NC}"
    ((SUCCESS_COUNT++))
  elif [ "$STATUS" == "Not authenticated" ] || [ "$STATUS" == "Forbidden" ]; then
    echo -e "  ${RED}✗ Authentication error: $STATUS${NC}"
    ((FAIL_COUNT++))
  else
    echo -e "  ${RED}✗ Failed: $STATUS${NC}"
    echo -e "  ${RED}   Response: $(echo "$RESPONSE" | jq -c)${NC}"
    ((FAIL_COUNT++))
  fi

  echo

  # Rate limiting - wait 2 seconds between assessments
  sleep 2
done <<< "$FEEDS"

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total feeds:    $FEED_COUNT"
echo -e "${GREEN}Successful:     $SUCCESS_COUNT${NC}"
echo -e "${RED}Failed:         $FAIL_COUNT${NC}"
echo -e "${YELLOW}Skipped:        $SKIP_COUNT${NC}"
echo

if [ $FAIL_COUNT -eq 0 ]; then
  echo -e "${GREEN}✓ All active feeds tested successfully!${NC}"
  exit 0
else
  echo -e "${RED}✗ Some feeds failed assessment${NC}"
  exit 1
fi
