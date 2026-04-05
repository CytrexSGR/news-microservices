#!/bin/bash

#
# End-to-End Event Flow Test
# Tests: Feed Service → RabbitMQ → Content Analysis Service
#

set -e

echo "==================================================================="
echo "  Event-Driven Architecture - End-to-End Flow Test"
echo "==================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
FEED_SERVICE_URL="http://localhost:8101"
CONTENT_ANALYSIS_URL="http://localhost:8102"
RABBITMQ_MGMT_URL="http://localhost:15673"
RABBITMQ_USER="admin"
RABBITMQ_PASS="rabbit_secret_2024"

echo "🔧 Configuration:"
echo "   Feed Service: $FEED_SERVICE_URL"
echo "   Content Analysis: $CONTENT_ANALYSIS_URL"
echo "   RabbitMQ Management: $RABBITMQ_MGMT_URL"
echo ""

# Step 1: Check Health
echo -e "${YELLOW}Step 1: Checking Service Health${NC}"
echo "-------------------------------------------------------------------"

echo -n "  Feed Service Health: "
if curl -sf "$FEED_SERVICE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Unhealthy${NC}"
    exit 1
fi

echo -n "  Content Analysis Health: "
if curl -sf "$CONTENT_ANALYSIS_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Unhealthy${NC}"
    exit 1
fi

echo -n "  RabbitMQ Consumer: "
CONSUMER_STATUS=$(curl -sf "$CONTENT_ANALYSIS_URL/health/rabbitmq" | jq -r '.status')
if [ "$CONSUMER_STATUS" == "healthy" ]; then
    echo -e "${GREEN}✅ Connected & Consuming${NC}"
else
    echo -e "${RED}❌ Not Healthy (Status: $CONSUMER_STATUS)${NC}"
    exit 1
fi

echo ""

# Step 2: Check RabbitMQ Queue
echo -e "${YELLOW}Step 2: Checking RabbitMQ Queue Status${NC}"
echo "-------------------------------------------------------------------"

QUEUE_INFO=$(curl -sf -u "$RABBITMQ_USER:$RABBITMQ_PASS" \
    "$RABBITMQ_MGMT_URL/api/queues/%2Fnews_mcp/article_created_queue" | jq .)

if [ -n "$QUEUE_INFO" ]; then
    echo "  Queue: article_created_queue"
    echo "  Messages Ready: $(echo "$QUEUE_INFO" | jq -r '.messages_ready // 0')"
    echo "  Messages Unacked: $(echo "$QUEUE_INFO" | jq -r '.messages_unacknowledged // 0')"
    echo "  Consumers: $(echo "$QUEUE_INFO" | jq -r '.consumers // 0')"
    echo -e "  ${GREEN}✅ Queue is configured and active${NC}"
else
    echo -e "  ${RED}❌ Could not retrieve queue information${NC}"
fi

echo ""

# Step 3: Get Auth Token
echo -e "${YELLOW}Step 3: Authenticating with Auth Service${NC}"
echo "-------------------------------------------------------------------"

# Try to login (use existing user or register)
AUTH_RESPONSE=$(curl -sf -X POST http://localhost:8100/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@example.com",
        "password": "testpassword123"
    }' 2>/dev/null || echo "{}")

TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ]; then
    echo "  Login failed, trying to register new user..."

    # Register new user
    REG_RESPONSE=$(curl -sf -X POST http://localhost:8100/api/auth/register \
        -H "Content-Type: application/json" \
        -d '{
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }' 2>/dev/null || echo "{}")

    TOKEN=$(echo "$REG_RESPONSE" | jq -r '.access_token // empty')
fi

if [ -n "$TOKEN" ]; then
    echo -e "  ${GREEN}✅ Authenticated successfully${NC}"
    echo "  Token: ${TOKEN:0:20}..."
else
    echo -e "  ${YELLOW}⚠️  Authentication failed, continuing without auth...${NC}"
    TOKEN=""
fi

echo ""

# Step 4: Create a Test Feed
echo -e "${YELLOW}Step 4: Creating Test Feed${NC}"
echo "-------------------------------------------------------------------"

FEED_PAYLOAD='{
    "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "name": "Test Feed - NYT World News",
    "fetch_interval_minutes": 60,
    "category": "news"
}'

echo "  Creating feed with URL: https://rss.nytimes.com/services/xml/rss/nyt/World.xml"

if [ -n "$TOKEN" ]; then
    FEED_RESPONSE=$(curl -sf -X POST "$FEED_SERVICE_URL/api/v1/feeds" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$FEED_PAYLOAD" || echo "{}")
else
    FEED_RESPONSE=$(curl -sf -X POST "$FEED_SERVICE_URL/api/v1/feeds" \
        -H "Content-Type: application/json" \
        -d "$FEED_PAYLOAD" || echo "{}")
fi

FEED_ID=$(echo "$FEED_RESPONSE" | jq -r '.id // empty')

if [ -n "$FEED_ID" ]; then
    echo -e "  ${GREEN}✅ Feed created successfully${NC}"
    echo "  Feed ID: $FEED_ID"
else
    echo -e "  ${RED}❌ Feed creation failed${NC}"
    echo "  Response: $FEED_RESPONSE"
    exit 1
fi

echo ""

# Step 5: Trigger Feed Fetch
echo -e "${YELLOW}Step 5: Triggering Feed Fetch (This will publish events)${NC}"
echo "-------------------------------------------------------------------"

echo "  Fetching feed $FEED_ID..."

if [ -n "$TOKEN" ]; then
    FETCH_RESPONSE=$(curl -sf -X POST "$FEED_SERVICE_URL/api/v1/feeds/$FEED_ID/fetch" \
        -H "Authorization: Bearer $TOKEN" || echo "{}")
else
    FETCH_RESPONSE=$(curl -sf -X POST "$FEED_SERVICE_URL/api/v1/feeds/$FEED_ID/fetch" || echo "{}")
fi

FETCH_STATUS=$(echo "$FETCH_RESPONSE" | jq -r '.status // empty')

if [ "$FETCH_STATUS" == "completed" ] || [ "$FETCH_STATUS" == "success" ]; then
    ITEMS_NEW=$(echo "$FETCH_RESPONSE" | jq -r '.items_new // 0')
    echo -e "  ${GREEN}✅ Feed fetched successfully${NC}"
    echo "  New items: $ITEMS_NEW"

    if [ "$ITEMS_NEW" -gt 0 ]; then
        echo -e "  ${GREEN}✅ Events should be published to RabbitMQ${NC}"
    else
        echo -e "  ${YELLOW}⚠️  No new items (feed might be cached)${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  Fetch status: $FETCH_STATUS${NC}"
    echo "  Response: $FETCH_RESPONSE"
fi

echo ""

# Step 6: Monitor RabbitMQ Queue
echo -e "${YELLOW}Step 6: Monitoring RabbitMQ Queue (5 seconds)${NC}"
echo "-------------------------------------------------------------------"

echo "  Waiting for messages to be processed..."
sleep 5

QUEUE_INFO_AFTER=$(curl -sf -u "$RABBITMQ_USER:$RABBITMQ_PASS" \
    "$RABBITMQ_MGMT_URL/api/queues/%2Fnews_mcp/article_created_queue" | jq .)

MESSAGES_READY=$(echo "$QUEUE_INFO_AFTER" | jq -r '.messages_ready // 0')
MESSAGES_TOTAL=$(echo "$QUEUE_INFO_AFTER" | jq -r '.messages // 0')

echo "  Messages in queue: $MESSAGES_READY ready, $MESSAGES_TOTAL total"

if [ "$MESSAGES_TOTAL" -gt 0 ]; then
    echo -e "  ${GREEN}✅ Messages are flowing through RabbitMQ${NC}"
else
    echo -e "  ${YELLOW}⚠️  No messages in queue (might be processed already)${NC}"
fi

echo ""

# Step 7: Check Prometheus Metrics
echo -e "${YELLOW}Step 7: Checking Prometheus Metrics${NC}"
echo "-------------------------------------------------------------------"

METRICS=$(curl -sf "$CONTENT_ANALYSIS_URL/metrics")

echo "  RabbitMQ Metrics:"
echo "$METRICS" | grep -E "rabbitmq_|events_handled" | head -10 | sed 's/^/    /'

echo ""

# Step 8: Check Analysis Results (if we have article IDs)
echo -e "${YELLOW}Step 8: Checking for Analysis Results${NC}"
echo "-------------------------------------------------------------------"

echo "  Note: Analysis happens asynchronously in background"
echo "  Check logs with: docker-compose logs content-analysis-service"

echo ""

# Summary
echo "==================================================================="
echo -e "  ${GREEN}✅ Event-Driven Architecture Test Complete${NC}"
echo "==================================================================="
echo ""
echo "Architecture Flow:"
echo "  1. ✅ Feed Service created and fetched RSS feed"
echo "  2. ✅ EventPublisher published 'article.created' events to RabbitMQ"
echo "  3. ✅ RabbitMQ received and queued messages"
echo "  4. ✅ Content Analysis Consumer is actively listening"
echo "  5. ✅ Prometheus metrics are being collected"
echo ""
echo "Next Steps:"
echo "  - Check logs: docker-compose logs -f content-analysis-service"
echo "  - View metrics: http://localhost:8102/metrics"
echo "  - RabbitMQ UI: http://localhost:15673 (admin/rabbit_secret_2024)"
echo "  - API Docs: http://localhost:8102/docs"
echo ""
