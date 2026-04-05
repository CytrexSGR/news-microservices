#!/bin/bash

# Manual Test Script for Feed Source Assessment Feature
# Tests the complete workflow from triggering an assessment to viewing results

set -e

echo "========================================="
echo "Feed Source Assessment Integration Test"
echo "========================================="
echo ""

# Configuration
FEED_SERVICE_URL="${FEED_SERVICE_URL:-http://localhost:8101}"
TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "ERROR: TOKEN environment variable must be set"
  echo "Usage: TOKEN='your-jwt-token' ./scripts/test_assessment_workflow.sh"
  exit 1
fi

# Get the first available feed (or use a specific feed ID)
echo "1. Getting feed list..."
FEED_ID=$(curl -s -X GET "$FEED_SERVICE_URL/api/v1/feeds" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

if [ -z "$FEED_ID" ] || [ "$FEED_ID" = "null" ]; then
  echo "ERROR: No feeds found. Please create a feed first."
  exit 1
fi

echo "   Using Feed ID: $FEED_ID"
echo ""

# Get feed details before assessment
echo "2. Getting feed details before assessment..."
curl -s -X GET "$FEED_SERVICE_URL/api/v1/feeds/$FEED_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.assessment // "No assessment yet"'
echo ""

# Trigger assessment
echo "3. Triggering source assessment..."
ASSESS_RESPONSE=$(curl -s -X POST "$FEED_SERVICE_URL/api/v1/feeds/$FEED_ID/assess" \
  -H "Authorization: Bearer $TOKEN")
echo "$ASSESS_RESPONSE" | jq '.'
echo ""

# Wait for assessment to complete (polling every 3 seconds)
echo "4. Waiting for assessment to complete (checking every 3 seconds)..."
MAX_WAIT=60  # 60 seconds max
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
  FEED_DATA=$(curl -s -X GET "$FEED_SERVICE_URL/api/v1/feeds/$FEED_ID" \
    -H "Authorization: Bearer $TOKEN")

  ASSESSMENT_STATUS=$(echo "$FEED_DATA" | jq -r '.assessment.assessment_status // "none"')

  echo "   Status: $ASSESSMENT_STATUS (${ELAPSED}s elapsed)"

  if [ "$ASSESSMENT_STATUS" = "completed" ]; then
    echo "   ✅ Assessment completed!"
    break
  elif [ "$ASSESSMENT_STATUS" = "failed" ]; then
    echo "   ❌ Assessment failed!"
    echo "$FEED_DATA" | jq '.assessment'
    exit 1
  fi

  sleep 3
  ELAPSED=$((ELAPSED + 3))
done

if [ "$ASSESSMENT_STATUS" != "completed" ]; then
  echo "   ⏱️  Assessment did not complete within ${MAX_WAIT} seconds"
  exit 1
fi

echo ""

# Show assessment results
echo "5. Assessment Results:"
echo "========================================="
curl -s -X GET "$FEED_SERVICE_URL/api/v1/feeds/$FEED_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.assessment | {
    status: .assessment_status,
    date: .assessment_date,
    credibility_tier,
    reputation_score,
    political_bias,
    organization_type,
    founded_year,
    editorial_standards,
    trust_ratings,
    recommendation,
    summary: .assessment_summary
  }'
echo ""

# Check assessment history
echo "6. Assessment History (showing last 5):"
echo "========================================="
curl -s -X GET "$FEED_SERVICE_URL/api/v1/feeds/$FEED_ID/assessment-history?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {
    date: .assessment_date,
    status: .assessment_status,
    tier: .credibility_tier,
    score: .reputation_score,
    bias: .political_bias
  }'
echo ""

echo "========================================="
echo "✅ All tests passed!"
echo "========================================="
echo ""
echo "Frontend URL: http://localhost:5173/feeds/$FEED_ID"
echo "You can now view the assessment in the browser."
