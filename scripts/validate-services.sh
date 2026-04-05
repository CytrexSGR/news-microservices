#!/bin/bash
# Service Validation Script - News Microservices
# Tests actual functionality of each service

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "News-Microservices Service Validation"
echo "================================================"
echo ""

# Check if docker-compose is running
echo "Checking Docker Compose status..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}ERROR: Docker Compose services not running!${NC}"
    echo "Start with: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose running${NC}"
echo ""

# Function to test service health
test_health() {
    local service=$1
    local port=$2
    local endpoint=${3:-/health}

    echo -n "Testing $service (port $port)... "

    if curl -sf "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Health endpoint OK${NC}"
        return 0
    else
        echo -e "${RED}✗ Health endpoint FAILED${NC}"
        return 1
    fi
}

# Function to test API endpoint
test_api() {
    local service=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_code=$5

    echo -n "  Testing $method $endpoint... "

    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            "http://localhost$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            "http://localhost$endpoint" 2>&1)
    fi

    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ ($http_code)${NC}"
        return 0
    else
        echo -e "${RED}✗ Expected $expected_code, got $http_code${NC}"
        return 1
    fi
}

# Test Infrastructure Services
echo "=== Infrastructure Services ==="
test_health "PostgreSQL" 5432 || true
test_health "Redis" 6379 || true
test_health "RabbitMQ" 15672 "/api/health/checks/alarms" || true
test_health "MinIO" 9000 "/minio/health/live" || true
test_health "Traefik" 8080 "/api/http/routers" || true
echo ""

# Test Auth Service
echo "=== Auth Service (Port 8000) ==="
if test_health "Auth Service" 8000; then
    echo "Testing registration endpoint..."
    test_api "Auth" "POST" ":8000/api/auth/register" \
        '{"email":"test@example.com","password":"test123","username":"testuser"}' \
        "201" || echo -e "${YELLOW}  Registration may already exist or endpoint incomplete${NC}"

    echo "Testing login endpoint..."
    test_api "Auth" "POST" ":8000/api/auth/login" \
        '{"email":"test@example.com","password":"test123"}' \
        "200" || echo -e "${RED}  Login FAILED - Auth service incomplete!${NC}"
fi
echo ""

# Test Feed Service
echo "=== Feed Service (Port 8001) ==="
if test_health "Feed Service" 8001; then
    # First, get JWT token from auth service
    echo "Getting JWT token..."
    TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"test123"}' 2>&1)

    TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token' 2>/dev/null || echo "")

    if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
        echo "Testing feed creation..."
        FEED_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
            http://localhost:8001/api/v1/feeds \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"url":"https://example.com/feed.xml","name":"Test Feed"}' 2>&1)

        FEED_CODE=$(echo "$FEED_RESPONSE" | tail -n1)
        if [ "$FEED_CODE" = "201" ]; then
            echo -e "${GREEN}✓ Feed creation successful${NC}"
        else
            echo -e "${RED}✗ Feed creation FAILED (code: $FEED_CODE)${NC}"
            echo -e "${YELLOW}  Feed Service may not be fully implemented!${NC}"
        fi
    else
        echo -e "${YELLOW}  Could not get auth token - skipping authenticated tests${NC}"
    fi
fi
echo ""

# Test Content Analysis Service
echo "=== Content Analysis Service (Port 8002) ==="
test_health "Content Analysis" 8002 "/api/v1/health" || echo -e "${RED}✗ Service not responding${NC}"
echo ""

# Test Research Service
echo "=== Research Service (Port 8003) ==="
test_health "Research Service" 8003 "/api/v1/health" || echo -e "${RED}✗ Service not responding${NC}"
echo ""

# Test OSINT Service
echo "=== OSINT Service (Port 8004) ==="
test_health "OSINT Service" 8004 "/api/v1/health" || echo -e "${RED}✗ Service not responding${NC}"
echo ""

# Test Notification Service
echo "=== Notification Service (Port 8005) ==="
if test_health "Notification Service" 8005; then
    echo -e "${YELLOW}  Service health OK, but implementation needs verification${NC}"
else
    echo -e "${RED}✗ Service not responding - likely template only${NC}"
fi
echo ""

# Test Search Service
echo "=== Search Service (Port 8006) ==="
if test_health "Search Service" 8006; then
    echo -e "${YELLOW}  Service health OK, but implementation needs verification${NC}"
else
    echo -e "${RED}✗ Service not responding - likely template only${NC}"
fi
echo ""

# Test Analytics Service
echo "=== Analytics Service (Port 8007) ==="
if test_health "Analytics Service" 8007; then
    echo -e "${YELLOW}  Service health OK, but implementation needs verification${NC}"
else
    echo -e "${RED}✗ Service not responding - likely template only${NC}"
fi
echo ""

echo "================================================"
echo "Validation Complete"
echo "================================================"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Review failed tests above"
echo "2. Check service logs: docker-compose logs <service-name>"
echo "3. Verify actual implementation vs. template code"
echo "4. Update CLAUDE.md with validated status"
