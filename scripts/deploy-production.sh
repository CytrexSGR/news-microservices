#!/bin/bash
# ============================================================================
# FMP Service - Production Deployment Script
# ============================================================================
# This script helps deploy the FMP service to production with proper
# security checks and validation.
#
# Usage: ./scripts/deploy-production.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/cytrex/news-microservices"
ENV_PROD="$PROJECT_ROOT/.env.production"
FMP_ENV_PROD="$PROJECT_ROOT/services/fmp-service/.env.production"

# Helper functions
print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_file_exists() {
    if [ ! -f "$1" ]; then
        print_error "File not found: $1"
        return 1
    fi
    return 0
}

check_git_ignored() {
    if git status --porcelain | grep -q "$1"; then
        print_error "File not gitignored: $1"
        return 1
    fi
    return 0
}

# ============================================================================
# Pre-deployment Checks
# ============================================================================

print_header "FMP Service - Production Deployment"
echo

print_info "Running pre-deployment security checks..."
echo

CHECKS_PASSED=0
CHECKS_TOTAL=0

# Check 1: Main .env.production exists
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if check_file_exists "$ENV_PROD"; then
    print_success "Main .env.production exists"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check 2: FMP service .env.production exists
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if check_file_exists "$FMP_ENV_PROD"; then
    print_success "FMP service .env.production exists"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check 3: Files are gitignored
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
cd "$PROJECT_ROOT"
if ! git status --porcelain | grep -q ".env.production"; then
    print_success "Production credentials are gitignored"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    print_error "Production credentials NOT gitignored!"
fi

# Check 4: Environment is set to production
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if grep -q "ENVIRONMENT=production" "$FMP_ENV_PROD"; then
    print_success "Environment set to production"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    print_warning "Environment not set to production in $FMP_ENV_PROD"
fi

# Check 5: JWT secret is not default
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if grep -q "your-secret-key-min-32-characters-long-change-in-production" "$FMP_ENV_PROD"; then
    print_error "JWT_SECRET_KEY is still using default value!"
else
    print_success "JWT_SECRET_KEY is customized"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check 6: Log level is production-appropriate
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if grep -q "LOG_LEVEL=WARNING\|LOG_LEVEL=ERROR" "$FMP_ENV_PROD"; then
    print_success "Log level set to production value"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    print_warning "Log level not set to WARNING or ERROR"
fi

# Check 7: Docker is running
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if docker ps > /dev/null 2>&1; then
    print_success "Docker daemon is running"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    print_error "Docker daemon is not running!"
fi

echo
echo "Security checks: $CHECKS_PASSED/$CHECKS_TOTAL passed"
echo

# Exit if critical checks failed
if [ $CHECKS_PASSED -lt $((CHECKS_TOTAL - 1)) ]; then
    print_error "Critical security checks failed. Fix issues before deploying."
    exit 1
fi

# ============================================================================
# CORS Configuration Warning
# ============================================================================

print_warning "IMPORTANT: Verify CORS origins before proceeding!"
echo
echo "Current CORS configuration:"
grep "CORS_ORIGINS" "$FMP_ENV_PROD" || echo "(not set)"
echo
read -p "Have you updated CORS_ORIGINS with production domains? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Deployment cancelled. Update CORS_ORIGINS first:"
    echo "  Edit: $FMP_ENV_PROD"
    echo "  Set: CORS_ORIGINS=[\"https://your-domain.com\"]"
    exit 1
fi

# ============================================================================
# Deployment Confirmation
# ============================================================================

echo
print_info "Ready to deploy FMP Service to production"
echo
echo "This will:"
echo "  1. Stop current containers"
echo "  2. Deploy production configuration"
echo "  3. Wait for health checks"
echo "  4. Verify deployment"
echo
read -p "Continue with deployment? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled by user"
    exit 0
fi

# ============================================================================
# Deployment
# ============================================================================

print_header "Deploying to Production"
echo

# Step 1: Stop development environment
print_info "Stopping development environment..."
docker compose down
print_success "Development environment stopped"
echo

# Step 2: Deploy production environment
print_info "Deploying production environment..."
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
print_success "Production containers started"
echo

# Step 3: Wait for health checks
print_info "Waiting for health checks (may take 30-60 seconds)..."
sleep 10

MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker ps | grep -q "news-fmp-service-prod.*healthy"; then
        print_success "FMP service is healthy"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done
echo

if [ $WAITED -ge $MAX_WAIT ]; then
    print_error "Health check timeout! Check logs:"
    echo "  docker logs news-fmp-service-prod"
    exit 1
fi

# ============================================================================
# Verification
# ============================================================================

print_header "Verifying Deployment"
echo

# Check 1: Health endpoint
print_info "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8113/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    print_success "Health endpoint responding"
    if echo "$HEALTH_RESPONSE" | grep -q '"environment":"production"'; then
        print_success "Environment confirmed as production"
    else
        print_warning "Environment not showing as production!"
        echo "Response: $HEALTH_RESPONSE"
    fi
else
    print_error "Health endpoint not responding correctly"
    echo "Response: $HEALTH_RESPONSE"
fi
echo

# Check 2: Container status
print_info "Checking container status..."
docker compose -f docker-compose.prod.yml ps
echo

# Check 3: Run tests
print_info "Running test suite..."
if docker exec news-fmp-service-prod python -m pytest tests/ -v --tb=short; then
    print_success "All tests passed"
else
    print_warning "Some tests failed - check output above"
fi
echo

# ============================================================================
# Summary
# ============================================================================

print_header "Deployment Complete"
echo

print_success "FMP Service deployed to production!"
echo
echo "Next steps:"
echo "  1. Monitor logs: docker logs news-fmp-service-prod -f"
echo "  2. Check metrics: curl http://localhost:8113/api/v1/admin/rate-limit/stats"
echo "  3. Test endpoint: curl http://localhost:8113/health"
echo
echo "Rollback if needed:"
echo "  docker compose -f docker-compose.prod.yml down"
echo "  docker compose up -d"
echo
echo "Documentation:"
echo "  $PROJECT_ROOT/services/fmp-service/docs/PRODUCTION_DEPLOYMENT.md"
echo

print_info "Deployment timestamp: $(date)"
