#!/bin/bash

# Quick Start Script for Traefik Gateway
# This script sets up and starts the gateway with all dependencies

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}     Traefik Gateway Quick Start${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed!${NC}"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"

# Create network if it doesn't exist
echo -e "\n${YELLOW}Setting up Docker network...${NC}"
if ! docker network ls | grep -q news-microservices; then
    docker network create news-microservices
    echo -e "${GREEN}✓ Created news-microservices network${NC}"
else
    echo -e "${GREEN}✓ Network already exists${NC}"
fi

# Setup environment
echo -e "\n${YELLOW}Setting up environment...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
    echo -e "${YELLOW}  Please edit .env file with your configuration${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Generate certificates for development
echo -e "\n${YELLOW}Checking certificates...${NC}"
if [ ! -f certs/cert.pem ]; then
    mkdir -p certs
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout certs/key.pem -out certs/cert.pem \
        -subj "/C=US/ST=State/L=City/O=NewsMCP/CN=*.news-mcp.local" \
        2>/dev/null
    echo -e "${GREEN}✓ Generated development certificates${NC}"
else
    echo -e "${GREEN}✓ Certificates already exist${NC}"
fi

# Check if services are running
echo -e "\n${YELLOW}Checking microservices...${NC}"

services_running=true
if ! docker ps | grep -q auth-service; then
    echo -e "${YELLOW}⚠ Auth Service not running${NC}"
    services_running=false
fi

if ! docker ps | grep -q feed-service; then
    echo -e "${YELLOW}⚠ Feed Service not running${NC}"
    services_running=false
fi

if [ "$services_running" = false ]; then
    echo -e "${YELLOW}Note: Some services are not running. Gateway will start but routes may not work.${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ All services are running${NC}"
fi

# Start Traefik
echo -e "\n${YELLOW}Starting Traefik Gateway...${NC}"
docker compose up -d

# Wait for Traefik to be ready
echo -e "\n${YELLOW}Waiting for Traefik to be ready...${NC}"
sleep 5

# Check if Traefik is running
if docker ps | grep -q news-gateway; then
    echo -e "${GREEN}✓ Traefik is running${NC}"
else
    echo -e "${RED}✗ Traefik failed to start${NC}"
    echo -e "${YELLOW}Check logs with: docker compose logs traefik${NC}"
    exit 1
fi

# Run health check
echo -e "\n${YELLOW}Running health check...${NC}"
if ./scripts/health-check.sh 2>/dev/null | grep -q "All health checks passed"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠ Some health checks failed${NC}"
fi

# Display access information
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}     Gateway is Ready!${NC}"
echo -e "${BLUE}================================================${NC}\n"

echo -e "${GREEN}Access Points:${NC}"
echo -e "  • API Gateway:    http://localhost"
echo -e "  • Secure API:     https://localhost"
echo -e "  • Dashboard:      http://localhost:8080"
echo -e "  • Metrics:        http://localhost:8082/metrics"
echo -e "  • Health Check:   http://localhost/health"

echo -e "\n${GREEN}Service Routes:${NC}"
echo -e "  • Auth Service:   http://localhost/api/v1/auth"
echo -e "  • Users API:      http://localhost/api/v1/users"
echo -e "  • Feeds API:      http://localhost/api/v1/feeds"

echo -e "\n${GREEN}Management Commands:${NC}"
echo -e "  • View logs:      make logs"
echo -e "  • Stop gateway:   make down"
echo -e "  • Test routes:    make test"
echo -e "  • Health check:   make health"

if [ "$services_running" = false ]; then
    echo -e "\n${YELLOW}Remember to start the microservices for full functionality!${NC}"
fi

echo -e "\n${BLUE}Happy routing! 🚀${NC}\n"