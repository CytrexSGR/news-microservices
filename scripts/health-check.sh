#!/bin/bash
# Health check script for all News MCP services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_health() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}

    printf "%-30s" "Checking $service_name..."

    if response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" 2>/dev/null); then
        if [ "$response" -eq "$expected_status" ]; then
            echo -e "${GREEN}✓ Healthy${NC} (HTTP $response)"
            return 0
        else
            echo -e "${YELLOW}⚠ Unexpected status${NC} (HTTP $response)"
            return 1
        fi
    else
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    fi
}

# Function to check database connection
check_database() {
    printf "%-30s" "Checking PostgreSQL..."

    if docker exec news-postgres pg_isready -U news_user -d news_mcp > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    fi
}

# Function to check Redis
check_redis() {
    printf "%-30s" "Checking Redis..."

    if docker exec news-redis redis-cli -a redis_secret_2024 ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    fi
}

# Function to check RabbitMQ
check_rabbitmq() {
    printf "%-30s" "Checking RabbitMQ..."

    if docker exec news-rabbitmq rabbitmq-diagnostics check_running > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    fi
}

# Main health check
echo "=================================================="
echo "News MCP Microservices - Health Check"
echo "=================================================="
echo ""

echo "Infrastructure Services:"
echo "------------------------"
check_database
check_redis
check_rabbitmq
check_health "MinIO" "http://localhost:9000/minio/health/live"
echo ""

echo "Application Services:"
echo "---------------------"
check_health "Auth Service" "http://localhost:8000/health"
check_health "Feed Service" "http://localhost:8001/health"
check_health "Content Analysis" "http://localhost:8002/api/v1/health"
check_health "Research Service" "http://localhost:8003/api/v1/health"
check_health "OSINT Service" "http://localhost:8004/api/v1/health"
check_health "Notification Service" "http://localhost:8005/health"
check_health "Search Service" "http://localhost:8006/health"
check_health "Analytics Service" "http://localhost:8007/health"
echo ""

echo "API Gateway & Monitoring:"
echo "-------------------------"
check_health "Traefik Dashboard" "http://localhost:8080/api/overview" 200
check_health "Prometheus" "http://localhost:9090/-/healthy" 200
check_health "Grafana" "http://localhost:3001/api/health" 200
check_health "Loki" "http://localhost:3100/ready" 200
echo ""

echo "=================================================="
echo "Service URLs:"
echo "=================================================="
echo "Auth Service:          http://localhost:8000"
echo "Feed Service:          http://localhost:8001"
echo "Content Analysis:      http://localhost:8002"
echo "Research Service:      http://localhost:8003"
echo "OSINT Service:         http://localhost:8004"
echo "Notification Service:  http://localhost:8005"
echo "Search Service:        http://localhost:8006"
echo "Analytics Service:     http://localhost:8007"
echo ""
echo "Traefik Dashboard:     http://localhost:8080"
echo "RabbitMQ Management:   http://localhost:15672 (admin/rabbit_secret_2024)"
echo "MinIO Console:         http://localhost:9001 (admin/minio_secret_2024)"
echo "Prometheus:            http://localhost:9090"
echo "Grafana:               http://localhost:3001 (admin/admin)"
echo "=================================================="
