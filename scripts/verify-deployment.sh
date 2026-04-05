#!/bin/bash
set -euo pipefail

# ============================================================================
# Deployment Verification Script
# ============================================================================
# Comprehensive health checks for all services and database
# Author: DevOps Engineer (Claude Flow Swarm)
# Last Updated: 2025-10-15
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Service endpoints
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${API_BASE_URL}/health"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-news_db}"
DB_USER="${DB_USER:-postgres}"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# ============================================================================
# Logging Functions
# ============================================================================

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $*"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ✗${NC} $*"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠${NC} $*"
}

check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

# ============================================================================
# Docker Service Checks
# ============================================================================

check_docker_services() {
    log "Checking Docker services..."
    echo ""

    local services=(
        "postgres:PostgreSQL Database"
        "redis:Redis Cache"
        "rabbitmq:RabbitMQ Message Broker"
        "app:Application Server"
    )

    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name service_desc <<< "$service_info"
        check

        if docker ps --format '{{.Names}}' | grep -q "$service_name"; then
            local status
            status=$(docker inspect --format='{{.State.Status}}' "$service_name" 2>/dev/null)
            if [[ "$status" == "running" ]]; then
                log_success "$service_desc is running"
            else
                log_error "$service_desc is not running (status: $status)"
            fi
        else
            log_error "$service_desc container not found"
        fi
    done

    echo ""
}

# ============================================================================
# Database Connectivity Checks
# ============================================================================

check_database_connectivity() {
    log "Checking database connectivity..."
    echo ""

    # Check if PostgreSQL is accepting connections
    check
    if docker exec postgres pg_isready -U "$DB_USER" &> /dev/null; then
        log_success "PostgreSQL is accepting connections"
    else
        log_error "PostgreSQL is not accepting connections"
        return 1
    fi

    # Check if database exists
    check
    if docker exec postgres psql -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        log_success "Database '$DB_NAME' exists"
    else
        log_error "Database '$DB_NAME' does not exist"
        return 1
    fi

    # Test database query
    check
    if docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
        log_success "Database query execution successful"
    else
        log_error "Database query execution failed"
        return 1
    fi

    echo ""
}

# ============================================================================
# Database Schema Checks
# ============================================================================

check_database_schema() {
    log "Checking database schema..."
    echo ""

    # Expected tables (customize based on your schema)
    local expected_tables=(
        "alembic_version"
        "feeds"
        "articles"
        "users"
    )

    for table in "${expected_tables[@]}"; do
        check
        if docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "\dt" | grep -q "$table"; then
            log_success "Table '$table' exists"
        else
            log_warning "Table '$table' not found (may be optional)"
        fi
    done

    # Check Alembic version
    check
    local alembic_version
    alembic_version=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;" 2>/dev/null | xargs)

    if [[ -n "$alembic_version" ]]; then
        log_success "Alembic migration version: $alembic_version"
    else
        log_warning "No Alembic migrations applied yet"
    fi

    echo ""
}

# ============================================================================
# Redis Checks
# ============================================================================

check_redis() {
    log "Checking Redis connectivity..."
    echo ""

    check
    if docker exec redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis is responding to PING"
    else
        log_error "Redis is not responding"
        return 1
    fi

    # Check Redis info
    check
    local redis_version
    redis_version=$(docker exec redis redis-cli INFO server | grep "redis_version" | cut -d: -f2 | tr -d '\r')
    if [[ -n "$redis_version" ]]; then
        log_success "Redis version: $redis_version"
    else
        log_warning "Could not retrieve Redis version"
    fi

    echo ""
}

# ============================================================================
# RabbitMQ Checks
# ============================================================================

check_rabbitmq() {
    log "Checking RabbitMQ status..."
    echo ""

    check
    if docker exec rabbitmq rabbitmqctl status &> /dev/null; then
        log_success "RabbitMQ is running"
    else
        log_error "RabbitMQ is not running"
        return 1
    fi

    # Check RabbitMQ version
    check
    local rabbitmq_version
    rabbitmq_version=$(docker exec rabbitmq rabbitmqctl version 2>/dev/null)
    if [[ -n "$rabbitmq_version" ]]; then
        log_success "RabbitMQ version: $rabbitmq_version"
    else
        log_warning "Could not retrieve RabbitMQ version"
    fi

    # List queues
    check
    log "RabbitMQ queues:"
    docker exec rabbitmq rabbitmqctl list_queues 2>/dev/null | while read -r line; do
        log "  $line"
    done

    echo ""
}

# ============================================================================
# API Health Checks
# ============================================================================

check_api_health() {
    log "Checking API health endpoints..."
    echo ""

    check
    if command -v curl &> /dev/null; then
        local response
        response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")

        if [[ "$response" == "200" ]]; then
            log_success "API health endpoint returned 200 OK"
        else
            log_error "API health endpoint returned $response"
        fi
    else
        log_warning "curl not installed, skipping API health check"
    fi

    echo ""
}

# ============================================================================
# RSS Feed Test (derstandard.at)
# ============================================================================

check_rss_feed_fetch() {
    log "Testing RSS feed fetch (derstandard.at)..."
    echo ""

    check
    local test_feed_url="https://www.derstandard.at/rss"

    if command -v curl &> /dev/null; then
        local response
        response=$(curl -s -L -w "%{http_code}" -o /dev/null "$test_feed_url" 2>/dev/null || echo "000")

        if [[ "$response" == "200" ]]; then
            log_success "derstandard.at RSS feed is accessible (HTTP $response)"

            # Try to fetch actual content
            local feed_content
            feed_content=$(curl -s -L "$test_feed_url" 2>/dev/null | head -c 500)

            if echo "$feed_content" | grep -q "<?xml"; then
                log_success "RSS feed returns valid XML content"
            else
                log_warning "RSS feed content might not be valid XML"
            fi
        else
            log_error "derstandard.at RSS feed returned HTTP $response"
        fi
    else
        log_warning "curl not installed, skipping RSS feed test"
    fi

    echo ""
}

# ============================================================================
# Application Service Checks
# ============================================================================

check_application_services() {
    log "Checking application service health..."
    echo ""

    local services=("app" "worker" "scheduler")

    for service in "${services[@]}"; do
        check
        if docker ps --format '{{.Names}}' | grep -q "$service"; then
            local health
            health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "unknown")

            if [[ "$health" == "healthy" ]]; then
                log_success "$service is healthy"
            elif [[ "$health" == "unknown" ]]; then
                # No health check defined, check if running
                local status
                status=$(docker inspect --format='{{.State.Status}}' "$service")
                if [[ "$status" == "running" ]]; then
                    log_success "$service is running (no health check)"
                else
                    log_error "$service status: $status"
                fi
            else
                log_error "$service health: $health"
            fi

            # Check for recent errors in logs
            local error_count
            error_count=$(docker logs "$service" --since 5m 2>&1 | grep -ci "error" || echo "0")
            if [[ "$error_count" -gt 10 ]]; then
                log_warning "$service has $error_count errors in last 5 minutes"
            fi
        else
            log_warning "$service container not found (may be optional)"
        fi
    done

    echo ""
}

# ============================================================================
# Performance Metrics
# ============================================================================

check_performance_metrics() {
    log "Collecting performance metrics..."
    echo ""

    # PostgreSQL connections
    check
    local pg_connections
    pg_connections=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | xargs)
    if [[ -n "$pg_connections" ]]; then
        log_success "PostgreSQL active connections: $pg_connections"
    fi

    # Database size
    check
    local db_size
    db_size=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
    if [[ -n "$db_size" ]]; then
        log_success "Database size: $db_size"
    fi

    # Redis memory usage
    check
    local redis_memory
    redis_memory=$(docker exec redis redis-cli INFO memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
    if [[ -n "$redis_memory" ]]; then
        log_success "Redis memory usage: $redis_memory"
    fi

    echo ""
}

# ============================================================================
# Summary Report
# ============================================================================

print_summary() {
    echo ""
    echo "=============================================="
    log "DEPLOYMENT VERIFICATION SUMMARY"
    echo "=============================================="
    echo ""

    local success_rate=0
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        success_rate=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    fi

    echo -e "Total Checks:  ${BLUE}$TOTAL_CHECKS${NC}"
    echo -e "Passed:        ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed:        ${RED}$FAILED_CHECKS${NC}"
    echo -e "Success Rate:  ${BLUE}${success_rate}%${NC}"
    echo ""

    if [[ $FAILED_CHECKS -eq 0 ]]; then
        echo -e "${GREEN}✓ All checks passed! Deployment is healthy.${NC}"
        echo ""
        return 0
    else
        echo -e "${YELLOW}⚠ Some checks failed. Please review the output above.${NC}"
        echo ""
        return 1
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "=============================================="
    log "Starting Deployment Verification"
    log "=============================================="
    echo ""

    # Run all checks
    check_docker_services
    check_database_connectivity
    check_database_schema
    check_redis
    check_rabbitmq
    check_api_health
    check_rss_feed_fetch
    check_application_services
    check_performance_metrics

    # Print summary
    print_summary
}

# Run main function
main "$@"
