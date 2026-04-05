#!/bin/bash

# ==============================================================================
# Smoke Test Suite - News Microservices
# ==============================================================================
# Tests all 13 critical microservices with real data
# Week 4 validation of Week 2/Week 3 work
# ==============================================================================

set +e  # Don't exit on error - we handle errors gracefully

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Report file
REPORT_DIR="/home/cytrex/news-microservices/reports/testing"
REPORT_FILE="$REPORT_DIR/SMOKE_TEST_RESULTS_WEEK4_$(date +%Y%m%d_%H%M%S).md"
ERROR_LOG="$REPORT_DIR/smoke_test_errors_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$REPORT_DIR"

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$ERROR_LOG"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

test_start() {
    ((TOTAL_TESTS++))
    log_info "TEST $TOTAL_TESTS: $1"
}

test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    local headers=$4

    test_start "$name"

    if [ -z "$headers" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -H "$headers" "$url" 2>&1)
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -eq "$expected_status" ]; then
        log_success "$name (HTTP $http_code)"
        return 0
    else
        log_error "$name (Expected: $expected_status, Got: $http_code)"
        echo "Response: $body" >> "$ERROR_LOG"
        return 1
    fi
}

get_auth_token() {
    log_info "Authenticating as andreas..."

    response=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"andreas@test.com","password":"Aug2012#"}')

    token=$(echo "$response" | jq -r '.access_token' 2>/dev/null)

    if [ "$token" != "null" ] && [ -n "$token" ]; then
        log_success "Authentication successful"
        echo "$token" > /tmp/token.txt
        echo "$token"
        return 0
    else
        log_error "Authentication failed"
        echo "Response: $response" >> "$ERROR_LOG"
        return 1
    fi
}

db_query() {
    local query=$1
    docker exec -i postgres psql -U news_user -d news_mcp -t -c "$query" 2>/dev/null | xargs
}

redis_command() {
    local cmd=$1
    docker exec -i redis redis-cli -a redis_secret_2024 --no-auth-warning $cmd 2>/dev/null
}

# ==============================================================================
# Main Test Suite
# ==============================================================================

main() {
    echo "================================================================================"
    echo "                    Smoke Test Suite - Week 4 Validation"
    echo "================================================================================"
    echo "Start Time: $(date)"
    echo ""

    # TIER 1: Critical Services
    echo ""
    echo "================================================================================"
    echo "TIER 1: Critical Services"
    echo "================================================================================"

    # Test 1: Auth Service - Login
    test_start "Auth Service - User Login"
    TOKEN=$(get_auth_token)
    if [ $? -eq 0 ]; then
        AUTH_HEADER="Authorization: Bearer $TOKEN"
    else
        log_error "Cannot proceed without authentication"
        generate_report
        exit 1
    fi

    # Test 2: Feed Service
    test_endpoint "Feed Service - Health Check" "http://localhost:8101/health" 200
    test_endpoint "Feed Service - List Feeds" "http://localhost:8101/api/v1/feeds" 200 "$AUTH_HEADER"

    # Test 3: Content-Analysis-V3
    test_endpoint "Content-Analysis-V3 - Health Check" "http://localhost:8117/health" 200

    # Test 4: FMP Service
    test_endpoint "FMP Service - Health Check" "http://localhost:8113/health" 200

    # Test 5: Scraping Service
    test_endpoint "Scraping Service - Health Check" "http://localhost:8009/health" 200

    # TIER 2: Supporting Services
    echo ""
    echo "================================================================================"
    echo "TIER 2: Supporting Services"
    echo "================================================================================"

    test_endpoint "Scheduler Service - Health Check" "http://localhost:8108/health" 200
    test_endpoint "Notification Service - Health Check" "http://localhost:8105/health" 200
    test_endpoint "Analytics Service - Health Check" "http://localhost:8107/health" 200
    test_endpoint "Prediction Service - Health Check" "http://localhost:8116/health" 200
    test_endpoint "Narrative Service - Health Check" "http://localhost:8119/health" 200

    # TIER 3: External Integration Services
    echo ""
    echo "================================================================================"
    echo "TIER 3: External Integration Services"
    echo "================================================================================"

    test_endpoint "Research Service - Health Check" "http://localhost:8103/health" 200
    test_endpoint "OSINT Service - Health Check" "http://localhost:8104/health" 200
    test_endpoint "Intelligence Service - Health Check" "http://localhost:8118/health" 200

    # Generate Report
    generate_report
}

generate_report() {
    echo ""
    echo "================================================================================"
    echo "                              TEST SUMMARY"
    echo "================================================================================"
    echo "Total Tests:  $TOTAL_TESTS"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
    echo "Success Rate: $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%"
    echo ""
    echo "Report saved to: $REPORT_FILE"
    echo "================================================================================"

    # Generate markdown report
    cat > "$REPORT_FILE" <<EOF
# Smoke Test Results - Week 4
**Date:** $(date '+%Y-%m-%d %H:%M:%S')

## Summary
- **Total Tests:** $TOTAL_TESTS
- **Passed:** $PASSED_TESTS
- **Failed:** $FAILED_TESTS
- **Success Rate:** $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%

## Test Results

### TIER 1: Critical Services
| Service | Status |
|---------|--------|
| auth-service (8100) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| feed-service (8101) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| content-analysis-v3 (8117) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| fmp-service (8113) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| scraping-service (8009) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |

### TIER 2: Supporting Services
| Service | Status |
|---------|--------|
| scheduler-service (8108) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| notification-service (8105) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| analytics-service (8107) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| prediction-service (8116) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| narrative-service (8119) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |

### TIER 3: External Integration Services
| Service | Status |
|---------|--------|
| research-service (8103) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| osint-service (8104) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |
| intelligence-service (8118) | $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "⚠️ CHECK") |

---
**Generated by:** \`scripts/smoke_test_suite.sh\`
EOF

    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Execute
main
