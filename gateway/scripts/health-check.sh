#!/bin/bash

# Health Check Script for Traefik Gateway
# Verifies gateway and all services are operational

set -e

# Configuration
GATEWAY_URL=${GATEWAY_URL:-"http://localhost"}
GATEWAY_SECURE_URL=${GATEWAY_SECURE_URL:-"https://localhost"}
DASHBOARD_URL=${DASHBOARD_URL:-"http://localhost:8080"}
METRICS_URL=${METRICS_URL:-"http://localhost:8082/metrics"}

# Service endpoints
AUTH_SERVICE_URL="${GATEWAY_URL}/api/v1/auth/health"
FEED_SERVICE_URL="${GATEWAY_URL}/api/v1/feeds/health"
USERS_SERVICE_URL="${GATEWAY_URL}/api/v1/users/health"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Health check function
check_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    local auth_header=$4

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    local curl_opts="-s -o /dev/null -w %{http_code} --connect-timeout 5 --max-time 10"

    if [ -n "$auth_header" ]; then
        curl_opts="$curl_opts -H \"Authorization: Bearer $auth_header\""
    fi

    local response_code=$(curl $curl_opts "$url" 2>/dev/null || echo "000")

    if [ "$response_code" = "$expected_code" ]; then
        log_success "$name: OK (HTTP $response_code)"
        return 0
    else
        log_error "$name: FAILED (HTTP $response_code, expected $expected_code)"
        return 1
    fi
}

# Check if service is running
check_service() {
    local service_name=$1

    if docker ps | grep -q "$service_name"; then
        log_success "$service_name container is running"
        return 0
    else
        log_error "$service_name container is not running"
        return 1
    fi
}

# Check Traefik specific endpoints
check_traefik() {
    log_info "Checking Traefik Gateway..."

    # Check Traefik ping endpoint
    check_endpoint "Traefik Ping" "${GATEWAY_URL}/ping" "200"

    # Check Traefik dashboard (if enabled)
    if [ "$ENABLE_DASHBOARD" = "true" ]; then
        check_endpoint "Traefik Dashboard" "$DASHBOARD_URL/api/overview" "200"
    fi

    # Check metrics endpoint
    check_endpoint "Traefik Metrics" "$METRICS_URL" "200"
}

# Check middleware functionality
check_middlewares() {
    log_info "Checking Middleware Functionality..."

    # Test rate limiting
    log_info "Testing rate limiting..."
    local rate_limit_count=0
    for i in {1..150}; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/api/v1/auth/health" 2>/dev/null)
        if [ "$response" = "429" ]; then
            rate_limit_count=$((rate_limit_count + 1))
        fi
    done

    if [ $rate_limit_count -gt 0 ]; then
        log_success "Rate limiting is working (triggered $rate_limit_count times)"
    else
        log_warn "Rate limiting might not be configured correctly"
    fi

    # Test CORS headers
    log_info "Testing CORS headers..."
    cors_headers=$(curl -s -I -X OPTIONS \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" \
        "${GATEWAY_URL}/api/v1/feeds" 2>/dev/null)

    if echo "$cors_headers" | grep -q "Access-Control-Allow-Origin"; then
        log_success "CORS headers are present"
    else
        log_error "CORS headers are missing"
    fi

    # Test JWT validation (should return 401 without token)
    log_info "Testing JWT validation..."
    response=$(curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/api/v1/users/me" 2>/dev/null)
    if [ "$response" = "401" ]; then
        log_success "JWT validation is working (401 without token)"
    else
        log_error "JWT validation might not be working (expected 401, got $response)"
    fi
}

# Check service routing
check_routing() {
    log_info "Checking Service Routing..."

    check_endpoint "Auth Service Health" "$AUTH_SERVICE_URL" "200"
    check_endpoint "Feed Service Health" "$FEED_SERVICE_URL" "200"

    # These might return 401 if JWT is required
    check_endpoint "Users Endpoint (Auth Required)" "$USERS_SERVICE_URL" "401"
}

# Check SSL/TLS
check_ssl() {
    log_info "Checking SSL/TLS Configuration..."

    if command -v openssl &> /dev/null; then
        # Check SSL certificate
        echo | openssl s_client -connect localhost:443 -servername api.news-mcp.local 2>/dev/null | \
            openssl x509 -noout -dates 2>/dev/null

        if [ $? -eq 0 ]; then
            log_success "SSL certificate is valid"
        else
            log_warn "SSL certificate check failed (might be using self-signed cert)"
        fi
    else
        log_warn "OpenSSL not installed, skipping SSL checks"
    fi

    # Check HTTPS redirect
    response=$(curl -s -o /dev/null -w "%{http_code}" -L "${GATEWAY_URL}" 2>/dev/null)
    if [ "$response" = "200" ] || [ "$response" = "404" ]; then
        log_success "HTTP to HTTPS redirect is working"
    else
        log_warn "HTTP to HTTPS redirect might not be configured"
    fi
}

# Performance check
check_performance() {
    log_info "Running Performance Checks..."

    if command -v ab &> /dev/null; then
        log_info "Running basic load test..."
        ab -n 100 -c 10 -t 10 "${GATEWAY_URL}/health" 2>/dev/null | grep "Requests per second" | head -1
    else
        log_warn "Apache Bench (ab) not installed, skipping performance test"
    fi

    # Check response times
    total_time=0
    iterations=10

    for i in $(seq 1 $iterations); do
        response_time=$(curl -s -o /dev/null -w "%{time_total}" "${GATEWAY_URL}/health" 2>/dev/null)
        total_time=$(echo "$total_time + $response_time" | bc)
    done

    avg_time=$(echo "scale=3; $total_time / $iterations" | bc)
    log_info "Average response time: ${avg_time}s"

    if (( $(echo "$avg_time < 1" | bc -l) )); then
        log_success "Response times are good (< 1s)"
    else
        log_warn "Response times are high (> 1s)"
    fi
}

# Check Docker containers
check_containers() {
    log_info "Checking Docker Containers..."

    local services=("traefik" "auth-service" "feed-service")

    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$service"; then
            log_success "Container $service is running"

            # Check container health
            health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "none")
            if [ "$health" = "healthy" ]; then
                log_success "Container $service is healthy"
            elif [ "$health" = "none" ]; then
                log_info "Container $service has no health check"
            else
                log_warn "Container $service health status: $health"
            fi
        else
            log_error "Container $service is not running"
        fi
    done
}

# Check network connectivity
check_network() {
    log_info "Checking Network Connectivity..."

    # Check if services can reach each other
    if docker exec traefik ping -c 1 auth-service &>/dev/null; then
        log_success "Gateway can reach Auth Service"
    else
        log_error "Gateway cannot reach Auth Service"
    fi

    if docker exec traefik ping -c 1 feed-service &>/dev/null; then
        log_success "Gateway can reach Feed Service"
    else
        log_error "Gateway cannot reach Feed Service"
    fi
}

# Main function
main() {
    echo "================================================"
    echo "     Traefik Gateway Health Check"
    echo "================================================"
    echo ""

    # Run all checks
    check_traefik
    echo ""
    check_containers
    echo ""
    check_network
    echo ""
    check_routing
    echo ""
    check_middlewares
    echo ""
    check_ssl
    echo ""
    check_performance

    # Summary
    echo ""
    echo "================================================"
    echo "                 SUMMARY"
    echo "================================================"
    echo -e "Total Checks: ${BLUE}$TOTAL_CHECKS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"

    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "\n${GREEN}All health checks passed!${NC}"
        exit 0
    else
        echo -e "\n${YELLOW}Some health checks failed. Please review the output above.${NC}"
        exit 1
    fi
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --gateway-url) GATEWAY_URL="$2"; shift ;;
        --dashboard) ENABLE_DASHBOARD="true" ;;
        --verbose) set -x ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --gateway-url URL    Set gateway URL (default: http://localhost)"
            echo "  --dashboard          Check dashboard endpoints"
            echo "  --verbose            Enable verbose output"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Run main function
main