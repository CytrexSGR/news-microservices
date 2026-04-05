#!/bin/bash
# Health Check Validator Script
# Tests if all critical services can import their dependencies
# Usage: ./scripts/healthcheck-validator.sh [service-name]

set -e

SERVICE=${1:-""}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🏥 Health Check Validator"
echo "========================="
echo ""

# Services with special dependency requirements
SERVICES_WITH_SHARED=(
    "notification-service"
    "feed-service"
    "research-service"
)

# Function to check import in container
check_service_imports() {
    local service=$1
    local container="news-${service}"

    echo -n "Checking ${service}... "

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "${YELLOW}SKIP${NC} (container not running)"
        return 0
    fi

    # Try to import main app module
    if docker exec "$container" python3 -c "from app.main import app" 2>/dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  → Import failed. Checking details..."

        # Get detailed error
        docker exec "$container" python3 -c "from app.main import app" 2>&1 | head -5 | sed 's/^/     /'
        return 1
    fi
}

# Function to check shared volume mount
check_shared_mount() {
    local service=$1
    local container="news-${service}"

    echo -n "  Checking shared volume mount... "

    if docker exec "$container" test -d /app/shared 2>/dev/null; then
        echo -e "${GREEN}✓ Present${NC}"

        # Check if news-mcp-common is installed
        if docker exec "$container" pip list 2>/dev/null | grep -q "news-mcp-common"; then
            echo -e "  news-mcp-common: ${GREEN}✓ Installed${NC}"
        else
            echo -e "  news-mcp-common: ${YELLOW}⚠ Not installed${NC}"
        fi
    else
        echo -e "${RED}✗ Missing${NC}"
        return 1
    fi
}

# Main validation
ERRORS=0

if [ -n "$SERVICE" ]; then
    # Single service check
    if ! check_service_imports "$SERVICE"; then
        ERRORS=$((ERRORS + 1))

        # If service uses shared deps, check mount
        if [[ " ${SERVICES_WITH_SHARED[@]} " =~ " ${SERVICE} " ]]; then
            check_shared_mount "$SERVICE"
        fi
    fi
else
    # Check all services
    echo "Running health checks on all services..."
    echo ""

    for service in auth feed content-analysis-v2-1 research osint notification search analytics scheduler; do
        if ! check_service_imports "$service"; then
            ERRORS=$((ERRORS + 1))

            # If service uses shared deps, check mount
            if [[ " ${SERVICES_WITH_SHARED[@]} " =~ " ${service} " ]]; then
                check_shared_mount "$service"
            fi
        fi
    done
fi

echo ""
echo "─────────────────────────────────────"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All health checks passed${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS service(s) with import failures${NC}"
    echo ""
    echo "💡 Common fixes:"
    echo "   1. Check if service has required volume mounts (./shared:/app/shared)"
    echo "   2. Verify requirements.txt dependencies are installed"
    echo "   3. Check for circular imports or missing modules"
    echo "   4. Review service logs: docker logs <container-name>"
    exit 1
fi
