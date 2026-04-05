#!/bin/bash
# Load Testing Suite for Migration Performance Verification
# Tests single article and batch endpoints with concurrent requests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}\")\" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

init_test "LOAD TESTING"

# Configuration
FEED_SERVICE_URL="${FEED_SERVICE_URL:-http://localhost:8101}"
AUTH_SERVICE_URL="${AUTH_SERVICE_URL:-http://localhost:8100}"
CONCURRENT_SINGLE=100  # 100 concurrent requests for single article
CONCURRENT_BATCH=50    # 50 concurrent requests for batch
BATCH_SIZE=20          # 20 articles per batch

# Arrays to store response times
declare -a single_times=()
declare -a batch_times=()

# ════════════════════════════════════════════════════════════════════
# Helper Functions
# ════════════════════════════════════════════════════════════════════

calculate_percentile() {
    local -n arr=$1
    local percentile=$2

    # Sort array
    IFS=$'\n' sorted=($(sort -n <<<"${arr[*]}"))
    unset IFS

    # Calculate index
    local count=${#sorted[@]}
    local index=$(echo "scale=0; ($count * $percentile / 100)" | bc)

    echo "${sorted[$index]}"
}

calculate_average() {
    local -n arr=$1
    local sum=0
    local count=${#arr[@]}

    for time in "${arr[@]}"; do
        sum=$((sum + time))
    done

    echo $((sum / count))
}

# ════════════════════════════════════════════════════════════════════
# 1. SETUP
# ════════════════════════════════════════════════════════════════════
print_section "1. Load Test Setup"

# Get auth token
print_info "Getting auth token..."
TOKEN=$(get_auth_token)
if [ -z "$TOKEN" ]; then
    print_error "Failed to get auth token"
    exit 1
fi
print_success "Auth token obtained"

# Get random article ID for testing
print_info "Getting test article..."
TEST_ARTICLE_ID=$(execute_sql "SELECT article_id FROM public.article_analysis ORDER BY RANDOM() LIMIT 1;")
if [ -z "$TEST_ARTICLE_ID" ]; then
    print_error "No articles found in unified table"
    exit 1
fi
print_success "Test article: $TEST_ARTICLE_ID"

echo ""

# ════════════════════════════════════════════════════════════════════
# 2. SINGLE ARTICLE LOAD TEST
# ════════════════════════════════════════════════════════════════════
print_section "2. Single Article Load Test"
print_info "Running $CONCURRENT_SINGLE concurrent requests..."

# Run concurrent requests
for i in $(seq 1 $CONCURRENT_SINGLE); do
    (
        start_time=$(date +%s%3N)
        curl -s -H "Authorization: Bearer $TOKEN" \
            "$FEED_SERVICE_URL/api/v1/feeds/items/$TEST_ARTICLE_ID" > /dev/null
        end_time=$(date +%s%3N)
        echo $((end_time - start_time))
    ) &
done | while read -r time; do
    single_times+=("$time")
done

# Wait for all background jobs
wait

print_info "Collected ${#single_times[@]} response times"

# Calculate statistics
single_avg=$(calculate_average single_times)
single_p50=$(calculate_percentile single_times 50)
single_p95=$(calculate_percentile single_times 95)
single_p99=$(calculate_percentile single_times 99)

echo ""
echo "┌────────────────────────────────────────┐"
echo "│ SINGLE ARTICLE RESULTS                 │"
echo "├────────────────────────────────────────┤"
printf "│ Requests:     %4d                    │\n" "${#single_times[@]}"
printf "│ Average:      %4dms                   │\n" "$single_avg"
printf "│ p50:          %4dms                   │\n" "$single_p50"
printf "│ p95:          %4dms                   │\n" "$single_p95"
printf "│ p99:          %4dms                   │\n" "$single_p99"
echo "└────────────────────────────────────────┘"
echo ""

# ════════════════════════════════════════════════════════════════════
# 3. BATCH ENDPOINT LOAD TEST
# ════════════════════════════════════════════════════════════════════
print_section "3. Batch Endpoint Load Test"
print_info "Running $CONCURRENT_BATCH concurrent requests (batch size: $BATCH_SIZE)..."

# Run concurrent batch requests
for i in $(seq 1 $CONCURRENT_BATCH); do
    (
        start_time=$(date +%s%3N)
        curl -s -H "Authorization: Bearer $TOKEN" \
            "$FEED_SERVICE_URL/api/v1/feeds/items?limit=$BATCH_SIZE" > /dev/null
        end_time=$(date +%s%3N)
        echo $((end_time - start_time))
    ) &
done | while read -r time; do
    batch_times+=("$time")
done

# Wait for all background jobs
wait

print_info "Collected ${#batch_times[@]} response times"

# Calculate statistics
batch_avg=$(calculate_average batch_times)
batch_p50=$(calculate_percentile batch_times 50)
batch_p95=$(calculate_percentile batch_times 95)
batch_p99=$(calculate_percentile batch_times 99)

echo ""
echo "┌────────────────────────────────────────┐"
echo "│ BATCH ENDPOINT RESULTS                 │"
echo "├────────────────────────────────────────┤"
printf "│ Requests:     %4d                    │\n" "${#batch_times[@]}"
printf "│ Batch size:   %4d                    │\n" "$BATCH_SIZE"
printf "│ Average:      %4dms                   │\n" "$batch_avg"
printf "│ p50:          %4dms                   │\n" "$batch_p50"
printf "│ p95:          %4dms                   │\n" "$batch_p95"
printf "│ p99:          %4dms                   │\n" "$batch_p99"
echo "└────────────────────────────────────────┘"
echo ""

# ════════════════════════════════════════════════════════════════════
# 4. PERFORMANCE COMPARISON
# ════════════════════════════════════════════════════════════════════
print_section "4. Performance Comparison"

# Load baseline if available
if [ -f "/tmp/migration_baseline/pre_migration.json" ]; then
    BASELINE_QUERY_TIME=$(jq -r '.query_time_ms' /tmp/migration_baseline/pre_migration.json 2>/dev/null || echo "0")

    if [ "$BASELINE_QUERY_TIME" != "0" ] && [ "$BASELINE_QUERY_TIME" != "null" ]; then
        # Calculate improvement
        improvement=$((BASELINE_QUERY_TIME - single_avg))
        improvement_pct=$(echo "scale=1; $improvement * 100 / $BASELINE_QUERY_TIME" | bc)

        echo "┌─────────────────────────────────────────┐"
        echo "│ PERFORMANCE COMPARISON                  │"
        echo "├─────────────────────────────────────────┤"
        printf "│ Before (legacy):  %4dms              │\n" "$BASELINE_QUERY_TIME"
        printf "│ After (unified):  %4dms              │\n" "$single_avg"
        printf "│ Improvement:      %4dms (%s%%)     │\n" "$improvement" "${improvement_pct%.*}"
        echo "└─────────────────────────────────────────┘"

        # Check if improvement target met (2-3x = 50-66% improvement)
        if [ "${improvement_pct%.*}" -gt 50 ]; then
            print_success "✅ Performance target achieved (>50% improvement)"
            ((TESTS_PASSED++))
        else
            print_warning "⚠️ Performance improvement < 50% (expected: 50-66%)"
        fi
    else
        print_warning "Baseline available but query time not valid"
    fi
else
    print_warning "No baseline available for comparison"
    echo "Run this test again after migration to see improvement."
fi

echo ""

# ════════════════════════════════════════════════════════════════════
# 5. SAVE RESULTS
# ════════════════════════════════════════════════════════════════════
print_section "5. Save Results"

mkdir -p /tmp/migration_baseline

cat > /tmp/migration_baseline/load_test_results.json <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "single_article": {
    "concurrent_requests": $CONCURRENT_SINGLE,
    "avg_ms": $single_avg,
    "p50_ms": $single_p50,
    "p95_ms": $single_p95,
    "p99_ms": $single_p99
  },
  "batch_endpoint": {
    "concurrent_requests": $CONCURRENT_BATCH,
    "batch_size": $BATCH_SIZE,
    "avg_ms": $batch_avg,
    "p50_ms": $batch_p50,
    "p95_ms": $batch_p95,
    "p99_ms": $batch_p99
  }
}
EOF

print_success "Results saved to /tmp/migration_baseline/load_test_results.json"

# ════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════
print_section "Load Test Summary"

echo "┌────────────────────────────────────────┐"
echo "│ LOAD TEST RESULTS                      │"
echo "├────────────────────────────────────────┤"
printf "│ Single (avg):     %4dms              │\n" "$single_avg"
printf "│ Single (p95):     %4dms              │\n" "$single_p95"
printf "│ Batch (avg):      %4dms              │\n" "$batch_avg"
printf "│ Batch (p95):      %4dms              │\n" "$batch_p95"
echo "└────────────────────────────────────────┘"
echo ""

# Performance targets
if [ "$single_p95" -lt 200 ] && [ "$batch_p95" -lt 700 ]; then
    print_success "✅ ALL PERFORMANCE TARGETS MET"
    echo ""
    echo "  Single p95 < 200ms: $single_p95ms ✓"
    echo "  Batch p95 < 700ms: $batch_p95ms ✓"
else
    print_warning "⚠️ Some performance targets not met"
    echo ""
    [ "$single_p95" -ge 200 ] && echo "  Single p95 >= 200ms: $single_p95ms ✗"
    [ "$batch_p95" -ge 700 ] && echo "  Batch p95 >= 700ms: $batch_p95ms ✗"
fi

finish_test
