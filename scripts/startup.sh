#!/bin/bash
# Startup script for News Microservices platform
# Starts infrastructure, backend services, and frontend
# Last Updated: 2026-02-08 (Resource optimization: 12 GiB RAM / 6 CPUs)

set -e

echo "Starting News Microservices Platform..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project root
cd /home/cytrex/news-microservices

# 1. Start infrastructure first
echo -e "${YELLOW}1. Starting Infrastructure (PostgreSQL, Redis, RabbitMQ, Neo4j)...${NC}"
docker compose up -d postgres redis rabbitmq neo4j

echo -e "${BLUE}Waiting for infrastructure to be healthy...${NC}"
# Wait for health checks instead of fixed sleep
for i in $(seq 1 60); do
    healthy=$(docker compose ps --format json 2>/dev/null | python3 -c "
import sys, json
lines = sys.stdin.read().strip().split('\n')
healthy = 0
for line in lines:
    try:
        svc = json.loads(line)
        if svc.get('Name') in ['postgres', 'redis', 'rabbitmq', 'neo4j'] and 'healthy' in svc.get('Status', ''):
            healthy += 1
    except: pass
print(healthy)
" 2>/dev/null || echo "0")
    if [ "$healthy" -ge 4 ]; then
        break
    fi
    sleep 2
done

# 2. Check infrastructure health
echo ""
echo -e "${YELLOW}2. Checking infrastructure health...${NC}"

# PostgreSQL
if docker compose exec -T postgres pg_isready -U news_user > /dev/null 2>&1; then
    echo -e "${GREEN}  PostgreSQL ready${NC}"
else
    echo -e "${RED}  PostgreSQL not ready${NC}"
fi

# Redis
if docker compose exec -T redis redis-cli -a redis_secret_2024 ping > /dev/null 2>&1; then
    echo -e "${GREEN}  Redis ready${NC}"
else
    echo -e "${RED}  Redis not ready${NC}"
fi

# RabbitMQ
if docker compose exec -T rabbitmq rabbitmq-diagnostics -q ping > /dev/null 2>&1; then
    echo -e "${GREEN}  RabbitMQ ready${NC}"
else
    echo -e "${RED}  RabbitMQ not ready${NC}"
fi

# Neo4j
if curl -sf http://localhost:7474 > /dev/null 2>&1; then
    echo -e "${GREEN}  Neo4j ready${NC}"
else
    echo -e "${RED}  Neo4j not ready${NC}"
fi

# 3. Start all application services
echo ""
echo -e "${YELLOW}3. Starting application services...${NC}"
docker compose up -d \
    auth-service \
    feed-service feed-service-celery-worker feed-service-celery-beat feed-service-analysis-consumer \
    content-analysis-v3-api content-analysis-v3-consumer content-analysis-v3-consumer-2 content-analysis-v3-consumer-3 \
    research-service research-celery-worker \
    search-service search-celery-worker \
    analytics-service analytics-celery-worker analytics-celery-beat \
    scheduler-service \
    scraping-service \
    knowledge-graph-service \
    entity-canonicalization-service entity-canonicalization-celery-worker \
    geolocation-service geolocation-service-consumer \
    clustering-service clustering-celery-worker clustering-celery-beat \
    intelligence-service intelligence-celery-worker intelligence-celery-beat \
    narrative-service narrative-celery-worker narrative-celery-beat \
    narrative-intelligence-gateway \
    fmp-service \
    mediastack-service \
    ontology-proposals-service oss-service \
    sitrep-service \
    mcp-intelligence-server mcp-search-server \
    nexus-agent \
    n8n prometheus grafana \
    frontend intelligence-frontend nginx-proxy

echo -e "${BLUE}Waiting for services to start (30s)...${NC}"
sleep 30

# 4. Check service health
echo ""
echo -e "${YELLOW}4. Checking service health...${NC}"

services=(
    "8100:auth-service"
    "8101:feed-service"
    "8117:content-analysis-v3"
    "8106:search-service"
    "8107:analytics-service"
    "8103:research-service"
    "8111:knowledge-graph"
    "8112:entity-canonicalization"
    "8113:fmp-service"
    "8115:geolocation"
    "8118:intelligence"
    "8119:narrative"
    "8122:clustering"
    "8123:sitrep"
    "8121:mediastack"
    "8109:ontology-proposals"
    "8110:oss-service"
    "8120:nexus-agent"
)

for service in "${services[@]}"; do
    port="${service%%:*}"
    name="${service##*:}"

    if curl -sf -o /dev/null -w "%{http_code}" "http://localhost:$port/health" | grep -q "200"; then
        echo -e "${GREEN}  $name (port $port)${NC}"
    else
        echo -e "${RED}  $name (port $port) - not responding${NC}"
    fi
done

# 5. Check frontends
echo ""
echo -e "${YELLOW}5. Checking frontends...${NC}"
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}  Main Frontend (port 3000)${NC}"
else
    echo -e "${RED}  Main Frontend (port 3000) - not responding${NC}"
fi

if curl -sf http://localhost:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}  Intelligence Frontend (port 3001)${NC}"
else
    echo -e "${RED}  Intelligence Frontend (port 3001) - not responding${NC}"
fi

# 6. Memory check
echo ""
echo -e "${YELLOW}6. Memory usage...${NC}"
free -h | grep "Mem:" | awk '{printf "  RAM: %s used / %s total (%s available)\n", $3, $2, $7}'

# Summary
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Platform started!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Access points:"
echo -e "  ${BLUE}Frontend:${NC}            http://localhost:3000"
echo -e "  ${BLUE}Intelligence:${NC}        http://localhost:3000/intelligence"
echo -e "  ${BLUE}Intelligence FE:${NC}     http://localhost:3001"
echo -e "  ${BLUE}Backend APIs:${NC}        http://localhost:8100-8123"
echo -e "  ${BLUE}RabbitMQ UI:${NC}         http://localhost:15672"
echo -e "  ${BLUE}n8n UI:${NC}              http://localhost:5678"
echo -e "  ${BLUE}Grafana:${NC}             http://localhost:3002"
echo -e "  ${BLUE}Prometheus:${NC}          http://localhost:9090"
echo ""
echo "Monitoring:"
echo "  docker compose logs -f <service-name>"
echo "  docker compose ps"
echo "  docker stats"
echo ""
echo -e "${YELLOW}To stop everything:${NC}"
echo "  cd /home/cytrex/news-microservices && docker compose down"
