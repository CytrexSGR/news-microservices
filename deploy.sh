#!/bin/bash

# ============================================================================
# Production Deployment Script - News Microservices
# ============================================================================
# Deploys the complete trading terminal infrastructure on port 80
# ============================================================================

set -e  # Exit on any error

echo "=========================================="
echo "News Microservices - Production Deployment"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ ERROR: docker-compose.prod.yml not found!"
    echo "   Please run this script from the project root directory."
    exit 1
fi

echo "✓ Found docker-compose.prod.yml"
echo ""

# Stop and remove all existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
echo ""

# Build and start all services
echo "🚀 Building and starting production services..."
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

# Wait for services to become healthy
echo ""
echo "⏳ Waiting for services to become healthy (30s)..."
sleep 30

# Check service status
echo ""
echo "📊 Service Status:"
docker compose -f docker-compose.prod.yml ps

# Cleanup unused images
echo ""
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "🌐 Access Points:"
echo "   Frontend (Trading Terminal): http://$(hostname -I | awk '{print $1}')"
echo "   RabbitMQ Management:         http://$(hostname -I | awk '{print $1}'):15672"
echo ""
echo "📝 Next Steps:"
echo "   1. Open http://$(hostname -I | awk '{print $1}') in your browser"
echo "   2. Login with: andreas / Aug2012#"
echo "   3. Monitor logs: docker compose -f docker-compose.prod.yml logs -f frontend"
echo ""
echo "🔍 Debugging:"
echo "   - View all logs:       docker compose -f docker-compose.prod.yml logs -f"
echo "   - Restart services:    docker compose -f docker-compose.prod.yml restart"
echo "   - Stop all:            docker compose -f docker-compose.prod.yml down"
echo ""
