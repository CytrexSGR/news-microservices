#!/bin/bash

# Individual Service Tests - Direct Health Checks
# Tests each service independently without auth dependencies

echo "=== Testing All 13 Microservices ==="
echo "Date: $(date)"
echo ""

# Test function
test_service() {
    local name=$1
    local url=$2
    local port=$3
    
    echo -n "Testing $name (port $port)... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)
    
    if [ "$response" == "200" ]; then
        echo "✅ PASS (HTTP 200)"
        return 0
    else
        echo "❌ FAIL (HTTP $response)"
        return 1
    fi
}

# TIER 1: Critical Services
echo "=== TIER 1: Critical Services ==="
test_service "auth-service" "http://localhost:8100/health" "8100"
test_service "feed-service" "http://localhost:8101/health" "8101"
test_service "content-analysis-v3" "http://localhost:8117/health" "8117"
test_service "fmp-service" "http://localhost:8113/health" "8113"
test_service "scraping-service" "http://localhost:8009/health" "8009"
echo ""

# TIER 2: Supporting Services
echo "=== TIER 2: Supporting Services ==="
test_service "scheduler-service" "http://localhost:8108/health" "8108"
test_service "notification-service" "http://localhost:8105/health" "8105"
test_service "analytics-service" "http://localhost:8107/health" "8107"
test_service "prediction-service" "http://localhost:8116/health" "8116"
test_service "narrative-service" "http://localhost:8119/health" "8119"
echo ""

# TIER 3: External Integration Services
echo "=== TIER 3: External Integration Services ==="
test_service "research-service" "http://localhost:8103/health" "8103"
test_service "osint-service" "http://localhost:8104/health" "8104"
test_service "intelligence-service" "http://localhost:8118/health" "8118"
echo ""

echo "=== Testing Complete ==="
