#!/bin/bash
# Quick verification script for rate limiting implementation
# Tests basic functionality across all 7 services

set -e

echo "=========================================="
echo "Rate Limiting Verification Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Services to test
declare -A SERVICES=(
    ["auth"]="8100"
    ["feed"]="8101"
    ["analytics"]="8107"
    ["research"]="8103"
    ["osint"]="8104"
    ["notification"]="8105"
    ["search"]="8106"
)

# Test counter
PASSED=0
FAILED=0

# Function to test a service
test_service() {
    local name=$1
    local port=$2
    local endpoint="http://localhost:${port}"

    echo -n "Testing ${name} (port ${port})... "

    # Test 1: Health endpoint should be accessible
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "${endpoint}/health" 2>/dev/null || echo "000")

    if [ "$http_code" == "200" ] || [ "$http_code" == "503" ]; then
        echo -e "${GREEN}✓${NC} Service is running"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} Service not responding (HTTP $http_code)"
        ((FAILED++))
        return 1
    fi

    # Test 2: Check if rate limiting headers are present (if service has auth endpoints)
    if [ "$name" == "auth" ]; then
        echo -n "  Testing rate limit headers... "

        # Make a single request and check for headers
        headers=$(curl -s -I "${endpoint}/api/v1/auth/status" 2>/dev/null || echo "")

        if echo "$headers" | grep -qi "X-RateLimit-Remaining"; then
            echo -e "${GREEN}✓${NC} Headers present"
            ((PASSED++))
        else
            echo -e "${YELLOW}⚠${NC} Headers not found (middleware may not be active)"
            ((FAILED++))
        fi
    fi

    echo ""
}

# Function to test Redis connectivity
test_redis() {
    echo "Testing Redis connectivity..."

    if docker ps | grep -q redis; then
        echo -e "  ${GREEN}✓${NC} Redis container is running"
        ((PASSED++))

        # Try to ping Redis
        if docker exec news-microservices-redis-1 redis-cli -a redis_secret_2024 ping 2>/dev/null | grep -q "PONG"; then
            echo -e "  ${GREEN}✓${NC} Redis responds to ping"
            ((PASSED++))
        else
            echo -e "  ${RED}✗${NC} Redis not responding"
            ((FAILED++))
        fi
    else
        echo -e "  ${RED}✗${NC} Redis container not found"
        ((FAILED++))
    fi

    echo ""
}

# Function to test rate limiting enforcement
test_rate_limit_enforcement() {
    echo "Testing rate limit enforcement..."
    echo "  (Making 35 unauthenticated requests to auth service)"

    local triggered=false
    local endpoint="http://localhost:8100/api/v1/auth/status"

    for i in {1..35}; do
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" 2>/dev/null || echo "000")

        if [ "$http_code" == "429" ]; then
            echo -e "  ${GREEN}✓${NC} Rate limit triggered after $i requests"
            triggered=true
            ((PASSED++))
            break
        fi

        # Small delay to avoid hammering
        sleep 0.05
    done

    if [ "$triggered" = false ]; then
        echo -e "  ${YELLOW}⚠${NC} Rate limit not triggered after 35 requests"
        echo "     This could be normal if limits are higher or Redis is not configured"
        ((FAILED++))
    fi

    echo ""
}

# Function to check if services have the integration
check_integration() {
    echo "Checking service integration..."

    for name in "${!SERVICES[@]}"; do
        service_file="/home/cytrex/news-microservices/services/${name}-service/app/main.py"

        if [ -f "$service_file" ]; then
            if grep -q "setup_rate_limiting" "$service_file"; then
                echo -e "  ${GREEN}✓${NC} ${name}-service has rate limiting integrated"
                ((PASSED++))
            else
                echo -e "  ${RED}✗${NC} ${name}-service missing integration"
                ((FAILED++))
            fi
        else
            echo -e "  ${YELLOW}⚠${NC} ${name}-service main.py not found"
        fi
    done

    echo ""
}

# Function to check dependencies
check_dependencies() {
    echo "Checking dependencies..."

    for name in "${!SERVICES[@]}"; do
        req_file="/home/cytrex/news-microservices/services/${name}-service/requirements.txt"

        if [ -f "$req_file" ]; then
            if grep -q "slowapi" "$req_file"; then
                echo -e "  ${GREEN}✓${NC} ${name}-service has slowapi dependency"
                ((PASSED++))
            else
                echo -e "  ${RED}✗${NC} ${name}-service missing slowapi"
                ((FAILED++))
            fi
        fi
    done

    echo ""
}

# Run all tests
main() {
    echo "Starting verification..."
    echo ""

    # 1. Check Redis
    test_redis

    # 2. Check integration in code
    check_integration

    # 3. Check dependencies
    check_dependencies

    # 4. Test each service
    echo "Testing services..."
    for name in "${!SERVICES[@]}"; do
        test_service "$name" "${SERVICES[$name]}"
    done

    # 5. Test actual rate limiting (if services are running)
    if [ $PASSED -gt 0 ]; then
        test_rate_limit_enforcement
    fi

    # Summary
    echo "=========================================="
    echo "Verification Summary"
    echo "=========================================="
    echo -e "${GREEN}Passed: $PASSED${NC}"
    echo -e "${RED}Failed: $FAILED${NC}"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Some checks failed. Review output above.${NC}"
        exit 1
    fi
}

# Run main function
main
