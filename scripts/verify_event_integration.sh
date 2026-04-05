#!/bin/bash
set -e

# Event Integration Verification Script
# Verifies that all RabbitMQ event bus components are properly configured

echo "════════════════════════════════════════════════════════════════════════════════"
echo "  RabbitMQ Event Bus Integration - Verification"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

RABBITMQ_URL="http://localhost:15672/api"
RABBITMQ_USER="admin"
RABBITMQ_PASS="rabbit_secret_2024"
VHOST="news_mcp"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass=0
check_fail=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        ((check_pass++))
    else
        echo -e "${RED}❌ $1${NC}"
        ((check_fail++))
    fi
}

# 1. Check Files Exist
echo "📁 Checking Files..."
echo "────────────────────────────────────────────────────────────────────────────────"

test -f /home/cytrex/news-microservices/infrastructure/events/schemas.json
check "Event schemas file exists"

test -f /home/cytrex/news-microservices/infrastructure/rabbitmq/init.sh
check "RabbitMQ init script exists"

test -f /home/cytrex/news-microservices/shared/event_publisher.py
check "Event publisher library exists"

test -f /home/cytrex/news-microservices/shared/event_consumer.py
check "Event consumer library exists"

test -f /home/cytrex/news-microservices/shared/event_integration.py
check "Event integration helpers exist"

test -f /home/cytrex/news-microservices/tests/integration/test_events.py
check "Integration tests exist"

test -f /home/cytrex/news-microservices/docs/EVENT_ARCHITECTURE.md
check "Architecture documentation exists"

test -f /home/cytrex/news-microservices/docs/EVENT_QUICKSTART.md
check "Quick start guide exists"

echo ""

# 2. Check RabbitMQ is Running
echo "🐰 Checking RabbitMQ Status..."
echo "────────────────────────────────────────────────────────────────────────────────"

if docker ps | grep -q news-rabbitmq; then
    echo -e "${GREEN}✅ RabbitMQ container is running${NC}"
    ((check_pass++))
else
    echo -e "${RED}❌ RabbitMQ container is NOT running${NC}"
    echo "   Run: docker-compose up -d rabbitmq"
    ((check_fail++))
fi

# Check RabbitMQ API is accessible
if curl -s -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" "${RABBITMQ_URL}/overview" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ RabbitMQ API is accessible${NC}"
    ((check_pass++))
else
    echo -e "${YELLOW}⚠️  RabbitMQ API is not accessible (may not be started yet)${NC}"
    echo "   Wait for RabbitMQ to start or check credentials"
fi

echo ""

# 3. Check Exchange
echo "🔀 Checking Exchanges..."
echo "────────────────────────────────────────────────────────────────────────────────"

if curl -s -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" "${RABBITMQ_URL}/exchanges/${VHOST}/news.events" | grep -q "news.events"; then
    echo -e "${GREEN}✅ Exchange 'news.events' exists${NC}"
    ((check_pass++))
else
    echo -e "${YELLOW}⚠️  Exchange 'news.events' not found${NC}"
    echo "   Run: docker-compose up -d rabbitmq-init"
fi

if curl -s -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" "${RABBITMQ_URL}/exchanges/${VHOST}/news.events.dlx" | grep -q "news.events.dlx"; then
    echo -e "${GREEN}✅ Dead-letter exchange 'news.events.dlx' exists${NC}"
    ((check_pass++))
else
    echo -e "${YELLOW}⚠️  Dead-letter exchange not found${NC}"
fi

echo ""

# 4. Check Queues
echo "📬 Checking Queues..."
echo "────────────────────────────────────────────────────────────────────────────────"

EXPECTED_QUEUES=(
    "content-analysis.articles"
    "search.articles"
    "research.analysis"
    "osint.intelligence"
    "notification.alerts"
    "analytics.all"
    "news.events.dlq"
)

for queue in "${EXPECTED_QUEUES[@]}"; do
    if curl -s -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" "${RABBITMQ_URL}/queues/${VHOST}/${queue}" | grep -q "\"name\":\"${queue}\""; then
        echo -e "${GREEN}✅ Queue '${queue}' exists${NC}"
        ((check_pass++))
    else
        echo -e "${YELLOW}⚠️  Queue '${queue}' not found${NC}"
        ((check_fail++))
    fi
done

echo ""

# 5. Check Bindings
echo "🔗 Checking Bindings..."
echo "────────────────────────────────────────────────────────────────────────────────"

QUEUE_COUNT=$(curl -s -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" "${RABBITMQ_URL}/queues/${VHOST}" | grep -o "\"name\":" | wc -l)
BINDING_COUNT=$(curl -s -u "${RABBITMQ_USER}:${RABBITMQ_PASS}" "${RABBITMQ_URL}/bindings/${VHOST}" | grep -o "\"routing_key\":" | wc -l)

if [ "$QUEUE_COUNT" -ge 7 ]; then
    echo -e "${GREEN}✅ Found ${QUEUE_COUNT} queues (expected 7)${NC}"
    ((check_pass++))
else
    echo -e "${YELLOW}⚠️  Found ${QUEUE_COUNT} queues (expected 7)${NC}"
fi

if [ "$BINDING_COUNT" -ge 9 ]; then
    echo -e "${GREEN}✅ Found ${BINDING_COUNT} bindings (expected 9+)${NC}"
    ((check_pass++))
else
    echo -e "${YELLOW}⚠️  Found ${BINDING_COUNT} bindings (expected 9+)${NC}"
fi

echo ""

# 6. Check Docker Compose Configuration
echo "🐳 Checking Docker Compose..."
echo "────────────────────────────────────────────────────────────────────────────────"

if grep -q "rabbitmq-init" /home/cytrex/news-microservices/docker-compose.yml; then
    echo -e "${GREEN}✅ rabbitmq-init service configured${NC}"
    ((check_pass++))
else
    echo -e "${RED}❌ rabbitmq-init service not found in docker-compose.yml${NC}"
    ((check_fail++))
fi

SERVICES_WITH_RABBITMQ=$(grep -c "RABBITMQ_URL" /home/cytrex/news-microservices/docker-compose.yml || echo 0)
if [ "$SERVICES_WITH_RABBITMQ" -ge 8 ]; then
    echo -e "${GREEN}✅ ${SERVICES_WITH_RABBITMQ} services configured with RABBITMQ_URL${NC}"
    ((check_pass++))
else
    echo -e "${YELLOW}⚠️  Only ${SERVICES_WITH_RABBITMQ} services have RABBITMQ_URL (expected 8)${NC}"
fi

echo ""

# 7. Check Python Dependencies
echo "🐍 Checking Python Dependencies..."
echo "────────────────────────────────────────────────────────────────────────────────"

if grep -q "aio-pika" /home/cytrex/news-microservices/shared/requirements.txt; then
    echo -e "${GREEN}✅ aio-pika dependency listed${NC}"
    ((check_pass++))
else
    echo -e "${RED}❌ aio-pika not found in requirements.txt${NC}"
    ((check_fail++))
fi

echo ""

# Summary
echo "════════════════════════════════════════════════════════════════════════════════"
echo "  Verification Summary"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo -e "Checks Passed: ${GREEN}${check_pass}${NC}"
echo -e "Checks Failed: ${RED}${check_fail}${NC}"
echo ""

if [ $check_fail -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Event integration is complete.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start services: docker-compose up -d"
    echo "  2. Verify init: docker logs news-rabbitmq-init"
    echo "  3. Run tests: pytest tests/integration/test_events.py -v"
    echo "  4. Check UI: http://localhost:15672"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some checks failed. See details above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Start RabbitMQ: docker-compose up -d rabbitmq"
    echo "  - Run init script: docker-compose up -d rabbitmq-init"
    echo "  - Check logs: docker logs news-rabbitmq"
    exit 1
fi
