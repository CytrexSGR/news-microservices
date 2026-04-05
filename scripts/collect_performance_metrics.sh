#!/bin/bash
#
# Performance Metrics Collection
# Measures API response times, database query performance
#

# Don't exit on individual command failures
set +e

OUTPUT_DIR="reports/metrics/performance"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$OUTPUT_DIR/performance-$TIMESTAMP.json"

mkdir -p "$OUTPUT_DIR"

echo "=== Performance Metrics Collection ==="
echo "Timestamp: $(date)"
echo ""

# Initialize JSON
cat > "$RESULTS_FILE" << 'JSON'
{
  "timestamp": "TIMESTAMP_PLACEHOLDER",
  "api_endpoints": {},
  "database_queries": {},
  "system_resources": {}
}
JSON

sed -i "s/TIMESTAMP_PLACEHOLDER/$(date -Iseconds)/" "$RESULTS_FILE"

# Function to measure API endpoint performance
measure_endpoint() {
  local service=$1
  local port=$2
  local endpoint=$3
  local auth_required=$4

  echo "Testing: $service $endpoint"

  # Get auth token if required
  local token=""
  if [ "$auth_required" = "true" ]; then
    # Login to get token
    token=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d '{"username":"andreas","password":"Aug2012#"}' | jq -r '.access_token')
  fi

  # Measure response time (5 requests, average)
  total_time=0
  success_count=0

  for i in {1..5}; do
    if [ "$auth_required" = "true" ]; then
      response_time=$(curl -s -w "%{time_total}" -o /dev/null \
        -H "Authorization: Bearer $token" \
        "http://localhost:$port$endpoint")
    else
      response_time=$(curl -s -w "%{time_total}" -o /dev/null \
        "http://localhost:$port$endpoint")
    fi

    if [ $? -eq 0 ]; then
      total_time=$(echo "$total_time + $response_time" | bc)
      success_count=$((success_count + 1))
    fi

    sleep 0.5  # Brief pause between requests
  done

  if [ $success_count -gt 0 ]; then
    avg_time=$(echo "scale=4; $total_time / $success_count" | bc)
    echo "  Average: ${avg_time}s ($success_count/5 successful)"

    # Update JSON
    jq --arg service "$service" \
       --arg endpoint "$endpoint" \
       --arg time "$avg_time" \
       --arg success "$success_count" \
       '.api_endpoints[$service + $endpoint] = {
         "avg_response_time": ($time | tonumber),
         "success_rate": (($success | tonumber) / 5 * 100)
       }' "$RESULTS_FILE" > "$RESULTS_FILE.tmp" && mv "$RESULTS_FILE.tmp" "$RESULTS_FILE"
  else
    echo "  ❌ All requests failed"
  fi
}

# Test critical API endpoints
echo "=== Testing API Endpoints ==="
measure_endpoint "auth-service" 8100 "/health" false
measure_endpoint "auth-service" 8100 "/api/v1/users/me" true
measure_endpoint "feed-service" 8101 "/health" false
measure_endpoint "feed-service" 8101 "/api/v1/feeds?limit=10" true
measure_endpoint "content-analysis" 8102 "/health" false
measure_endpoint "research-service" 8103 "/health" false
measure_endpoint "osint-service" 8104 "/health" false
measure_endpoint "notification-service" 8105 "/health" false
measure_endpoint "search-service" 8106 "/health" false
measure_endpoint "analytics-service" 8107 "/health" false
echo ""

# Database query performance
echo "=== Testing Database Queries ==="
echo "Simple SELECT (COUNT):"
db_time_count=$(docker exec postgres bash -c "time psql -U news_user -d news_mcp -c 'SELECT COUNT(*) FROM feed_items;' 2>&1" | grep real | awk '{print $2}')
echo "  Time: $db_time_count"

echo "Complex JOIN (feed items + feeds):"
db_time_join=$(docker exec postgres bash -c "time psql -U news_user -d news_mcp -c 'SELECT fi.id, fi.title, f.name FROM feed_items fi JOIN feeds f ON fi.feed_id = f.id LIMIT 100;' 2>&1" | grep real | awk '{print $2}')
echo "  Time: $db_time_join"

echo "Aggregate query (feed statistics):"
db_time_agg=$(docker exec postgres bash -c "time psql -U news_user -d news_mcp -c 'SELECT feed_id, COUNT(*) as item_count FROM feed_items GROUP BY feed_id;' 2>&1" | grep real | awk '{print $2}')
echo "  Time: $db_time_agg"
echo ""

# Generate summary
echo "===================================="
echo "Results saved to: $RESULTS_FILE"
echo "===================================="

# Create human-readable report
cat > "$OUTPUT_DIR/performance-$TIMESTAMP.md" << MDEOF
# Performance Metrics Baseline

**Date:** $(date)
**Purpose:** Pre-refactoring performance baseline

---

## API Response Times

$(jq -r '.api_endpoints | to_entries[] | "- **\(.key)**: \(.value.avg_response_time)s (success: \(.value.success_rate)%)"' "$RESULTS_FILE")

---

## Database Query Performance

- Simple SELECT: $db_time_count
- Complex JOIN: $db_time_join
- Aggregate: $db_time_agg

---

**Next Steps:**
- Run this script weekly to track performance trends
- Compare results after refactoring
- Identify performance regressions early
MDEOF

cat "$OUTPUT_DIR/performance-$TIMESTAMP.md"
