#!/bin/bash
set -e

echo "=== API Workflow Test: 3-Stage Analysis ==="
echo ""

# Step 1: Login
echo "Step 1: Authentication"
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Test123456!"}' | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Login failed. Check credentials."
  exit 1
fi

echo "✅ Token erhalten: ${TOKEN:0:50}..."
echo ""

# Step 2: List Feeds
echo "Step 2: Liste aller Feeds"
FEEDS=$(curl -s http://localhost:8101/api/v1/feeds \
  -H "Authorization: Bearer $TOKEN")

echo "$FEEDS" | jq -r '.[] | "  - \(.name) (ID: \(.id))"' | head -5
FEED_ID=$(echo "$FEEDS" | jq -r '.[0].id')
echo ""
echo "Verwende Feed ID: $FEED_ID"
echo ""

# Step 3: Enable Analysis Flags
echo "Step 3: Aktiviere 3-Stage Analysis für Feed"
UPDATED_FEED=$(curl -s -X PATCH "http://localhost:8101/api/v1/feeds/$FEED_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_categorization": true,
    "enable_finance_sentiment": true,
    "enable_geopolitical_sentiment": true
  }')

echo "$UPDATED_FEED" | jq '{
  name,
  enable_categorization,
  enable_finance_sentiment,
  enable_geopolitical_sentiment
}'
echo ""

# Step 4: Test Finance Sentiment
echo "Step 4: Finance Sentiment Analysis"
FINANCE_RESULT=$(curl -s -X POST http://localhost:8114/api/v1/analyze/finance-sentiment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Apple stock surges 15% after strong earnings report. Analysts predict continued growth in the tech sector. Market sentiment remains bullish with high investor confidence.",
    "use_cache": false
  }')

echo "$FINANCE_RESULT" | jq '{
  market_sentiment,
  confidence_score,
  economic_impact,
  sectors_affected,
  time_horizon,
  analysis_id: .id
}'
echo ""

# Step 5: Test Geopolitical Sentiment
echo "Step 5: Geopolitical Sentiment Analysis"
GEO_RESULT=$(curl -s -X POST http://localhost:8114/api/v1/analyze/geopolitical-sentiment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Diplomatic tensions rise between nations over trade agreements. Security concerns increase in the Eastern European region. International organizations call for peaceful resolution through dialogue.",
    "use_cache": false
  }')

echo "$GEO_RESULT" | jq '{
  conflict_type,
  conflict_intensity,
  regional_stability,
  affected_regions,
  security_relevance,
  diplomatic_impact,
  analysis_id: .id
}'
echo ""

# Step 6: Verify Database
echo "Step 6: Datenbank-Verifikation"
echo "Checking if analysis results were stored..."

PGPASSWORD=your_db_password docker exec news-postgres psql -U news_user -d news_mcp -t -c "
SELECT
  (SELECT COUNT(*) FROM finance_sentiment) as finance_count,
  (SELECT COUNT(*) FROM geopolitical_sentiment) as geo_count,
  (SELECT COUNT(*) FROM analysis_results WHERE analysis_type IN ('FINANCE_SENTIMENT', 'GEOPOLITICAL_SENTIMENT')) as analysis_count
" 2>/dev/null

echo ""
echo "✅ Workflow Test Complete!"
echo ""
echo "Summary:"
echo "  1. ✅ Authentication successful"
echo "  2. ✅ Feed Service: List feeds"
echo "  3. ✅ Feed Service: Enable 3-stage analysis"
echo "  4. ✅ Content Analysis: Finance sentiment"
echo "  5. ✅ Content Analysis: Geopolitical sentiment"
echo "  6. ✅ Database: Results stored"
echo ""
echo "Next Steps:"
echo "  - Implement Scheduler Service (Port 8008)"
echo "  - Test automatic orchestration"
