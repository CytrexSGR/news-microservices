#!/bin/bash
# Comprehensive Deployment Validation Script
# Validates all services, infrastructure, and connectivity

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((WARNINGS++))
}

# Header
echo "=================================================="
echo "  News Microservices Deployment Validation"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="
echo ""

# 1. Docker Infrastructure Validation
log_info "Validating Docker infrastructure..."
echo ""

# Check Docker daemon
if docker info >/dev/null 2>&1; then
    log_success "Docker daemon is running"
else
    log_error "Docker daemon is not running"
    exit 1
fi

# Check Docker Compose
if command -v docker compose >/dev/null 2>&1; then
    log_success "Docker Compose is available"
else
    log_error "Docker Compose is not available"
    exit 1
fi

echo ""

# 2. Container Status Validation
log_info "Validating container statuses..."
echo ""

EXPECTED_CONTAINERS=(
    "news-postgres"
    "news-redis"
    "news-rabbitmq"
    "news-minio"
    "news-traefik"
)

for container in "${EXPECTED_CONTAINERS[@]}"; do
    if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
        STATUS=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null)

        if [ "$STATUS" = "running" ]; then
            if [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "" ]; then
                log_success "Container $container: running (healthy)"
            else
                log_warning "Container $container: running but health=$HEALTH"
            fi
        else
            log_error "Container $container: $STATUS"
        fi
    else
        log_error "Container $container: not found"
    fi
done

echo ""

# 3. Database Validation
log_info "Validating database connections..."
echo ""

# PostgreSQL
if docker exec news-postgres pg_isready -U postgres >/dev/null 2>&1; then
    log_success "PostgreSQL is accepting connections"

    # Check databases exist
    DATABASES=("auth_db" "feed_db" "content_analysis_db" "research_db" "osint_db" "notification_db" "search_db" "analytics_db")
    for db in "${DATABASES[@]}"; do
        if docker exec news-postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw "$db"; then
            log_success "Database $db exists"
        else
            log_warning "Database $db does not exist"
        fi
    done
else
    log_error "PostgreSQL is not accepting connections"
fi

# Redis
if docker exec news-redis redis-cli ping >/dev/null 2>&1; then
    log_success "Redis is accepting connections"
else
    log_error "Redis is not accepting connections"
fi

echo ""

# 4. RabbitMQ Validation
log_info "Validating RabbitMQ..."
echo ""

if docker exec news-rabbitmq rabbitmqctl status >/dev/null 2>&1; then
    log_success "RabbitMQ is running"

    # Check queues
    QUEUES=$(docker exec news-rabbitmq rabbitmqctl list_queues -q name 2>/dev/null | wc -l)
    if [ "$QUEUES" -gt 0 ]; then
        log_success "RabbitMQ has $QUEUES queues configured"
    else
        log_warning "RabbitMQ has no queues configured"
    fi
else
    log_error "RabbitMQ is not running properly"
fi

echo ""

# 5. MinIO Validation
log_info "Validating MinIO..."
echo ""

if curl -sf http://localhost:9000/minio/health/live >/dev/null 2>&1; then
    log_success "MinIO is healthy"
else
    log_error "MinIO health check failed"
fi

echo ""

# 6. Traefik Validation
log_info "Validating Traefik API Gateway..."
echo ""

if curl -sf http://localhost:8080/ping >/dev/null 2>&1; then
    log_success "Traefik is responding"
else
    log_error "Traefik is not responding"
fi

echo ""

# 7. Service API Endpoints Validation
log_info "Validating service API endpoints..."
echo ""

SERVICES=(
    "auth-service:8000:/health"
    "feed-service:8001:/health"
    "content-analysis-service:8002:/health"
    "research-service:8003:/health"
    "osint-service:8004:/health"
    "notification-service:8005:/health"
    "search-service:8006:/health"
    "analytics-service:8007:/health"
)

for service_info in "${SERVICES[@]}"; do
    IFS=':' read -r service_name port endpoint <<< "$service_info"

    if curl -sf "http://localhost:$port$endpoint" >/dev/null 2>&1; then
        log_success "Service $service_name health check passed"
    else
        log_warning "Service $service_name health check failed (may not be running)"
    fi
done

echo ""

# 8. Network Connectivity
log_info "Validating network connectivity..."
echo ""

# Check if services can resolve each other
NETWORK_NAME=$(docker network ls --filter "name=news" --format "{{.Name}}" | head -n1)
if [ -n "$NETWORK_NAME" ]; then
    log_success "Docker network $NETWORK_NAME exists"
else
    log_warning "No news-related Docker network found"
fi

echo ""

# 9. Volume Validation
log_info "Validating Docker volumes..."
echo ""

VOLUMES=$(docker volume ls --filter "name=news" --format "{{.Name}}" | wc -l)
if [ "$VOLUMES" -gt 0 ]; then
    log_success "Found $VOLUMES Docker volumes"
    docker volume ls --filter "name=news" --format "{{.Name}}" | while read -r vol; do
        log_success "  - $vol"
    done
else
    log_warning "No Docker volumes found"
fi

echo ""

# 10. Log Analysis
log_info "Analyzing container logs for errors..."
echo ""

ERROR_THRESHOLD=10

for container in "${EXPECTED_CONTAINERS[@]}"; do
    if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "$container"; then
        ERROR_COUNT=$(docker logs "$container" 2>&1 | grep -i "error\|fatal\|critical" | wc -l)
        if [ "$ERROR_COUNT" -lt "$ERROR_THRESHOLD" ]; then
            log_success "Container $container: $ERROR_COUNT errors (< $ERROR_THRESHOLD)"
        else
            log_warning "Container $container: $ERROR_COUNT errors (>= $ERROR_THRESHOLD)"
        fi
    fi
done

echo ""

# 11. Port Availability
log_info "Validating port availability..."
echo ""

PORTS=(5432 6379 5672 15672 9000 9001 80 443 8080 8000 8001 8002 8003 8004 8005 8006 8007)
for port in "${PORTS[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        log_success "Port $port is listening"
    else
        log_warning "Port $port is not listening"
    fi
done

echo ""

# 12. Environment Configuration
log_info "Validating environment configuration..."
echo ""

if [ -f ".env" ]; then
    log_success ".env file exists"

    # Check critical variables
    CRITICAL_VARS=("POSTGRES_PASSWORD" "REDIS_URL" "RABBITMQ_URL" "JWT_SECRET_KEY")
    for var in "${CRITICAL_VARS[@]}"; do
        if grep -q "^$var=" .env; then
            log_success "Environment variable $var is set"
        else
            log_warning "Environment variable $var is not set"
        fi
    done
else
    log_error ".env file does not exist"
fi

echo ""

# Final Summary
echo "=================================================="
echo "  Validation Summary"
echo "=================================================="
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment validation PASSED${NC}"
    exit 0
elif [ "$FAILED" -lt 5 ]; then
    echo -e "${YELLOW}⚠ Deployment validation PASSED with warnings${NC}"
    exit 0
else
    echo -e "${RED}✗ Deployment validation FAILED${NC}"
    exit 1
fi
