#!/bin/bash
# Shutdown script for News Microservices platform
# Gracefully stops all services, frontend, and infrastructure

set -e

echo "🛑 Shutting down News Microservices Platform..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root
cd /home/cytrex/news-microservices

# 1. Stop Frontend
echo -e "${YELLOW}1. Stopping Frontend...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    if [ -f "package.json" ]; then
        # Kill any running vite dev server
        pkill -f "vite" 2>/dev/null || true
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi
    cd ..
fi

# 2. Stop all Docker services
echo ""
echo -e "${YELLOW}2. Stopping Docker services...${NC}"
docker compose down

echo ""
echo -e "${GREEN}✓ All services stopped successfully${NC}"
echo ""
echo "Services stopped:"
echo "  - Frontend (Vite dev server)"
echo "  - All 10 backend microservices"
echo "  - PostgreSQL"
echo "  - Redis"
echo "  - RabbitMQ"
echo "  - Elasticsearch"
echo ""
echo -e "${YELLOW}To start again after reboot, run:${NC}"
echo "  cd /home/cytrex/news-microservices && ./scripts/startup.sh"
