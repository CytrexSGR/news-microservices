#!/bin/bash

# Test Routes Script
# Tests all configured routes and validates responses

set -e

# Configuration
BASE_URL=${BASE_URL:-"http://localhost"}
JWT_TOKEN=${JWT_TOKEN:-""}
VERBOSE=${VERBOSE:-false}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
declare -A test_results
total_tests=0
passed_tests=0
failed_tests=0

# Log functions
log_test() {
    echo -e "${BLUE}Testing:${NC} $1"
}

log_success() {
    echo -e "  ${GREEN}✓${NC} $1"
    passed_tests=$((passed_tests + 1))
}

log_failure() {
    echo -e "  ${RED}✗${NC} $1"
    failed_tests=$((failed_tests + 1))
}

log_info() {
    if [ "$VERBOSE" = "true" ]; then
        echo -e "  ${YELLOW}ℹ${NC} $1"
    fi
}

# Helper function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5

    total_tests=$((total_tests + 1))

    local curl_cmd="curl -s -X $method"
    curl_cmd="$curl_cmd -w '\n%{http_code}'"

    if [ -n "$JWT_TOKEN" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $JWT_TOKEN'"
    fi

    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi

    curl_cmd="$curl_cmd ${BASE_URL}${endpoint}"

    if [ "$VERBOSE" = "true" ]; then
        log_info "Command: $curl_cmd"
    fi

    # Execute curl and capture output
    local response=$(eval $curl_cmd 2>/dev/null || echo "000")
    local status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$VERBOSE" = "true" ]; then
        log_info "Response: $body"
        log_info "Status: $status_code"
    fi

    if [ "$status_code" = "$expected_status" ]; then
        log_success "$description (Status: $status_code)"
        test_results["$endpoint"]="PASS"
        return 0
    else
        log_failure "$description (Expected: $expected_status, Got: $status_code)"
        test_results["$endpoint"]="FAIL"
        return 1
    fi
}

# Test public endpoints (no auth required)
test_public_endpoints() {
    echo -e "\n${BLUE}=== Testing Public Endpoints ===${NC}\n"

    log_test "Health Check Endpoint"
    api_call "GET" "/health" "" "200" "Gateway health check"

    log_test "Auth Service - Public Endpoints"
    api_call "GET" "/api/v1/auth/health" "" "200" "Auth service health"

    # Test login endpoint (should exist but return 400/401 without credentials)
    api_call "POST" "/api/v1/auth/login" "" "400" "Login endpoint (no credentials)"

    # Test registration endpoint
    api_call "POST" "/api/v1/auth/register" "" "400" "Register endpoint (no data)"
}

# Test authentication flow
test_authentication() {
    echo -e "\n${BLUE}=== Testing Authentication Flow ===${NC}\n"

    log_test "Registration"
    local register_data='{"email":"test@example.com","password":"TestPass123!","name":"Test User"}'
    api_call "POST" "/api/v1/auth/register" "$register_data" "201" "User registration" || true

    log_test "Login"
    local login_data='{"email":"test@example.com","password":"TestPass123!"}'

    # Attempt login and capture token
    local login_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$login_data" \
        "${BASE_URL}/api/v1/auth/login" 2>/dev/null)

    if echo "$login_response" | grep -q "token"; then
        JWT_TOKEN=$(echo "$login_response" | grep -o '"token":"[^"]*' | grep -o '[^"]*$')
        if [ -n "$JWT_TOKEN" ]; then
            log_success "Login successful, token received"
        else
            log_failure "Login failed, no token in response"
        fi
    else
        log_info "Login endpoint not fully implemented yet"
    fi
}

# Test protected endpoints (auth required)
test_protected_endpoints() {
    echo -e "\n${BLUE}=== Testing Protected Endpoints ===${NC}\n"

    log_test "Protected Endpoints Without Token"
    local old_token=$JWT_TOKEN
    JWT_TOKEN=""

    api_call "GET" "/api/v1/users/me" "" "401" "Users endpoint without token"
    api_call "GET" "/api/v1/feeds" "" "401" "Feeds endpoint without token"

    JWT_TOKEN=$old_token

    if [ -n "$JWT_TOKEN" ]; then
        log_test "Protected Endpoints With Token"
        api_call "GET" "/api/v1/users/me" "" "200" "Users endpoint with token"
        api_call "GET" "/api/v1/feeds" "" "200" "Feeds list endpoint with token"
        api_call "POST" "/api/v1/feeds" '{"url":"https://example.com/rss"}' "201" "Create feed with token"
    else
        log_info "Skipping authenticated endpoint tests (no token available)"
    fi
}

# Test middleware functionality
test_middleware() {
    echo -e "\n${BLUE}=== Testing Middleware ===${NC}\n"

    log_test "CORS Headers"
    local cors_response=$(curl -s -I -X OPTIONS \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" \
        "${BASE_URL}/api/v1/feeds" 2>/dev/null)

    if echo "$cors_response" | grep -q "Access-Control-Allow-Origin"; then
        log_success "CORS headers present"
    else
        log_failure "CORS headers missing"
    fi

    log_test "Security Headers"
    local headers_response=$(curl -s -I "${BASE_URL}/health" 2>/dev/null)

    for header in "X-Content-Type-Options" "X-Frame-Options" "X-XSS-Protection"; do
        if echo "$headers_response" | grep -q "$header"; then
            log_success "Security header $header present"
        else
            log_failure "Security header $header missing"
        fi
    done

    log_test "Rate Limiting"
    echo -n "  Testing rate limit..."
    local rate_limited=false

    for i in {1..150}; do
        local status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/auth/health" 2>/dev/null)
        if [ "$status" = "429" ]; then
            rate_limited=true
            break
        fi
    done

    if [ "$rate_limited" = true ]; then
        log_success "Rate limiting triggered (429 status received)"
    else
        log_failure "Rate limiting not triggered after 150 requests"
    fi
}

# Test service discovery and load balancing
test_load_balancing() {
    echo -e "\n${BLUE}=== Testing Load Balancing ===${NC}\n"

    log_test "Service Discovery"

    # Check if multiple instances are running
    local auth_instances=$(docker ps --filter "name=auth-service" --format "{{.Names}}" | wc -l)
    local feed_instances=$(docker ps --filter "name=feed-service" --format "{{.Names}}" | wc -l)

    log_info "Auth service instances: $auth_instances"
    log_info "Feed service instances: $feed_instances"

    if [ "$auth_instances" -gt 1 ] || [ "$feed_instances" -gt 1 ]; then
        log_test "Load Balancing Distribution"

        declare -A server_hits
        for i in {1..20}; do
            local server=$(curl -s "${BASE_URL}/api/v1/auth/health" 2>/dev/null | grep -o '"instance":"[^"]*' | cut -d'"' -f4)
            if [ -n "$server" ]; then
                server_hits["$server"]=$((${server_hits["$server"]:-0} + 1))
            fi
        done

        echo "  Request distribution:"
        for server in "${!server_hits[@]}"; do
            echo "    - $server: ${server_hits[$server]} hits"
        done

        if [ ${#server_hits[@]} -gt 1 ]; then
            log_success "Load balancing is distributing requests"
        else
            log_failure "Load balancing not working (all requests to one instance)"
        fi
    else
        log_info "Single instance deployment, skipping load balance test"
    fi
}

# Test WebSocket endpoints
test_websocket() {
    echo -e "\n${BLUE}=== Testing WebSocket Endpoints ===${NC}\n"

    if command -v wscat &> /dev/null; then
        log_test "WebSocket Connection"

        # Test WebSocket upgrade
        local ws_response=$(curl -s -i -N \
            -H "Connection: Upgrade" \
            -H "Upgrade: websocket" \
            -H "Sec-WebSocket-Version: 13" \
            -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
            "${BASE_URL}/ws/feeds" 2>/dev/null | head -n1)

        if echo "$ws_response" | grep -q "101"; then
            log_success "WebSocket upgrade successful"
        else
            log_info "WebSocket endpoint not configured or not available"
        fi
    else
        log_info "wscat not installed, skipping WebSocket tests"
    fi
}

# Test canary deployment
test_canary() {
    echo -e "\n${BLUE}=== Testing Canary Deployment ===${NC}\n"

    log_test "Canary Header Detection"

    local canary_hits=0
    local stable_hits=0

    for i in {1..100}; do
        local response_headers=$(curl -s -I "${BASE_URL}/api/v1/auth/health" 2>/dev/null)
        if echo "$response_headers" | grep -q "X-Canary: true"; then
            canary_hits=$((canary_hits + 1))
        else
            stable_hits=$((stable_hits + 1))
        fi
    done

    if [ $canary_hits -gt 0 ]; then
        log_success "Canary deployment active (Canary: $canary_hits%, Stable: $stable_hits%)"
    else
        log_info "No canary deployment detected (100% stable)"
    fi
}

# Performance test
test_performance() {
    echo -e "\n${BLUE}=== Performance Testing ===${NC}\n"

    log_test "Response Times"

    local endpoints=("/health" "/api/v1/auth/health" "/api/v1/feeds/health")

    for endpoint in "${endpoints[@]}"; do
        local total_time=0
        local iterations=10

        for i in $(seq 1 $iterations); do
            local response_time=$(curl -s -o /dev/null -w "%{time_total}" "${BASE_URL}${endpoint}" 2>/dev/null)
            total_time=$(echo "$total_time + $response_time" | bc)
        done

        local avg_time=$(echo "scale=3; $total_time / $iterations" | bc)

        if (( $(echo "$avg_time < 0.5" | bc -l) )); then
            log_success "$endpoint: ${avg_time}s average (Good)"
        elif (( $(echo "$avg_time < 1" | bc -l) )); then
            log_info "$endpoint: ${avg_time}s average (Acceptable)"
        else
            log_failure "$endpoint: ${avg_time}s average (Slow)"
        fi
    done
}

# Generate report
generate_report() {
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}              TEST RESULTS SUMMARY${NC}"
    echo -e "${BLUE}================================================${NC}\n"

    echo "Total Tests: $total_tests"
    echo -e "Passed: ${GREEN}$passed_tests${NC}"
    echo -e "Failed: ${RED}$failed_tests${NC}"

    local success_rate=$((passed_tests * 100 / total_tests))
    echo -e "Success Rate: ${success_rate}%\n"

    echo "Endpoint Status:"
    for endpoint in "${!test_results[@]}"; do
        if [ "${test_results[$endpoint]}" = "PASS" ]; then
            echo -e "  ${GREEN}✓${NC} $endpoint"
        else
            echo -e "  ${RED}✗${NC} $endpoint"
        fi
    done

    if [ $failed_tests -eq 0 ]; then
        echo -e "\n${GREEN}All tests passed successfully!${NC}"
        exit 0
    else
        echo -e "\n${YELLOW}Some tests failed. Please review the results above.${NC}"
        exit 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}         TRAEFIK GATEWAY ROUTE TESTING${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo -e "Base URL: $BASE_URL\n"

    # Run all test suites
    test_public_endpoints
    test_authentication
    test_protected_endpoints
    test_middleware
    test_load_balancing
    test_websocket
    test_canary
    test_performance

    # Generate final report
    generate_report
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --url) BASE_URL="$2"; shift ;;
        --token) JWT_TOKEN="$2"; shift ;;
        --verbose) VERBOSE=true ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --url URL       Base URL for testing (default: http://localhost)"
            echo "  --token TOKEN   JWT token for authenticated requests"
            echo "  --verbose       Enable verbose output"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Run tests
main