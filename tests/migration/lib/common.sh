#!/bin/bash
# Common functions for migration tests

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database connection
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-news_mcp}"
DB_USER="${POSTGRES_USER:-news_user}"
DB_PASSWORD="${POSTGRES_PASSWORD:-news_pass}"

# API endpoints
FEED_SERVICE_URL="${FEED_SERVICE_URL:-http://localhost:8101}"
AUTH_SERVICE_URL="${AUTH_SERVICE_URL:-http://localhost:8100}"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TEST_START_TIME=""

# Initialize test run
init_test() {
    TEST_START_TIME=$(date +%s)
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Migration Test Suite - $1${NC}"
    echo -e "${BLUE}║  Started: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
}

# Finish test run
finish_test() {
    local end_time=$(date +%s)
    local duration=$((end_time - TEST_START_TIME))

    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Test Summary${NC}"
    echo -e "${BLUE}║  Duration: ${duration}s${NC}"
    echo -e "${GREEN}║  Passed: ${TESTS_PASSED}${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}║  Failed: ${TESTS_FAILED}${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
        echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
        exit 0
    else
        echo -e "${RED}║  Failed: ${TESTS_FAILED}${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
        echo -e "${RED}❌ TESTS FAILED${NC}"
        exit 1
    fi
}

# Execute SQL query
execute_sql() {
    local query="$1"
    docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c "$query" 2>/dev/null | xargs
}

# Execute SQL query with JSON output
execute_sql_json() {
    local query="$1"
    docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -F',' -c "$query" 2>/dev/null
}

# Check if value matches expected
assert_equals() {
    local test_name="$1"
    local actual="$2"
    local expected="$3"

    if [ "$actual" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} $test_name: $actual"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name: Expected $expected, got $actual"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if value is greater than expected
assert_greater_than() {
    local test_name="$1"
    local actual="$2"
    local expected="$3"

    if [ "$actual" -gt "$expected" ]; then
        echo -e "${GREEN}✓${NC} $test_name: $actual > $expected"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name: Expected > $expected, got $actual"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if value is less than expected
assert_less_than() {
    local test_name="$1"
    local actual="$2"
    local expected="$3"

    if [ "$actual" -lt "$expected" ]; then
        echo -e "${GREEN}✓${NC} $test_name: $actual < $expected"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name: Expected < $expected, got $actual"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if value exists (not empty)
assert_not_empty() {
    local test_name="$1"
    local value="$2"

    if [ -n "$value" ]; then
        echo -e "${GREEN}✓${NC} $test_name: Value exists"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name: Value is empty"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Get auth token
get_auth_token() {
    local email="${1:-andreas@test.com}"
    local password="${2:-Aug2012#}"

    local response=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$email\",\"password\":\"$password\"}")

    echo "$response" | jq -r '.access_token // empty'
}

# Test API endpoint
test_api_endpoint() {
    local endpoint="$1"
    local token="$2"
    local expected_status="${3:-200}"

    local response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $token" "$endpoint")
    local body=$(echo "$response" | head -n -1)
    local status=$(echo "$response" | tail -n 1)

    if [ "$status" = "$expected_status" ]; then
        echo "$body"
        return 0
    else
        return 1
    fi
}

# Print section header
print_section() {
    echo ""
    echo -e "${YELLOW}▶ $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Print info message
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Print success message
print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

# Print error message
print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}
