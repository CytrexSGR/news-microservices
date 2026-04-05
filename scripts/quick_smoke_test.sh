#!/bin/bash

# Quick Smoke Test - All 18 Services
# Fast parallel health checks with timeout

TIMEOUT=3

# Service list: name:port (18 active services)
SERVICES=(
    # Tier 1: Mission-Critical
    "auth-service:8100"
    "feed-service:8101"
    "content-analysis-v3:8117"
    "fmp-service:8113"
    "scraping-service:8009"
    # Tier 2: Important
    "search-service:8106"
    "analytics-service:8107"
    "notification-service:8105"
    "scheduler-service:8108"
    "prediction-service:8116"
    "narrative-service:8119"
    "entity-canonicalization:8112"
    # Tier 3: Nice-to-Have
    "research-service:8103"
    "osint-service:8104"
    "intelligence-service:8118"
    "knowledge-graph:8111"
    "oss-service:8110"
    "ontology-service:8109"
)

TOTAL=${#SERVICES[@]}
echo "=== Quick Smoke Test - All $TOTAL Services ==="
echo "Date: $(date)"
echo ""

PASSED=0
FAILED=0

for service in "${SERVICES[@]}"; do
    name="${service%:*}"
    port="${service#*:}"

    response=$(timeout $TIMEOUT curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" 2>&1)

    if [ "$response" == "200" ]; then
        echo "✅ $name (port $port) - PASS"
        ((PASSED++))
    else
        echo "❌ $name (port $port) - FAIL (HTTP $response)"
        ((FAILED++))
    fi
done

echo ""
echo "=== Summary ==="
echo "Total:  $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Success Rate: $(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")%"
