#!/bin/bash
# Integration Test Runner for Knowledge-Graph Service
# Usage: ./run_integration_tests.sh [OPTIONS]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVICE_DIR="/home/cytrex/news-microservices/services/knowledge-graph-service"
COMPOSE_DIR="/home/cytrex/news-microservices"

# Service URLs
KNOWLEDGE_GRAPH_URL="${KNOWLEDGE_GRAPH_URL:-http://localhost:8111}"
FMP_SERVICE_URL="${FMP_SERVICE_URL:-http://localhost:8109}"
NEO4J_URL="${NEO4J_URL:-bolt://localhost:7687}"

# Default test options
TEST_MARKER="${TEST_MARKER:-integration}"
TEST_VERBOSITY="${TEST_VERBOSITY:--v}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Print header
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Knowledge-Graph Integration Test Runner${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Function: Check if service is running
check_service() {
    local name=$1
    local url=$2

    echo -n "Checking $name... "

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not reachable${NC}"
        return 1
    fi
}

# Function: Start services
start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    cd "$COMPOSE_DIR"

    docker compose up -d fmp-service knowledge-graph-service neo4j postgres

    echo "Waiting for services to be ready (15 seconds)..."
    sleep 15

    echo ""
}

# Function: Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check if Docker Compose is running
    if ! docker compose ps > /dev/null 2>&1; then
        echo -e "${RED}✗ Docker Compose not available${NC}"
        echo "Please ensure Docker is running"
        exit 1
    fi

    # Check services
    local all_running=true

    if ! check_service "FMP Service" "$FMP_SERVICE_URL/health"; then
        all_running=false
    fi

    if ! check_service "Knowledge-Graph Service" "$KNOWLEDGE_GRAPH_URL/health"; then
        all_running=false
    fi

    echo ""

    if [ "$all_running" = false ]; then
        echo -e "${YELLOW}Some services are not running.${NC}"
        echo -e "${YELLOW}Do you want to start them? [y/N]${NC}"
        read -r response

        if [[ "$response" =~ ^[Yy]$ ]]; then
            start_services
        else
            echo -e "${RED}Cannot run tests without services. Exiting.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ All services running${NC}"
        echo ""
    fi
}

# Function: Run tests
run_tests() {
    echo -e "${YELLOW}Running integration tests...${NC}"
    echo "Marker: $TEST_MARKER"
    echo "Verbosity: $TEST_VERBOSITY"
    echo "Log level: $LOG_LEVEL"
    echo ""

    cd "$SERVICE_DIR"

    # Build pytest command
    local cmd="pytest tests/integration/ $TEST_VERBOSITY -m \"$TEST_MARKER\" --log-cli-level=$LOG_LEVEL"

    # Add additional options from arguments
    if [ $# -gt 0 ]; then
        cmd="$cmd $*"
    fi

    echo -e "${YELLOW}Command: $cmd${NC}"
    echo ""

    # Run tests
    if eval "$cmd"; then
        echo ""
        echo -e "${GREEN}================================================${NC}"
        echo -e "${GREEN}✓ All tests passed!${NC}"
        echo -e "${GREEN}================================================${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}================================================${NC}"
        echo -e "${RED}✗ Some tests failed${NC}"
        echo -e "${RED}================================================${NC}"
        return 1
    fi
}

# Function: Show usage
show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS] [PYTEST_ARGS]

Options:
  -h, --help              Show this help message
  -s, --start-services    Start services before running tests
  -m, --marker MARKER     Test marker to run (default: integration)
  -v, --verbose           Verbose output
  -d, --debug             Debug logging
  --no-check              Skip service health checks
  --fast                  Run fast tests only (exclude slow)
  --perf                  Run performance tests only

Examples:
  # Run all integration tests
  $0

  # Run fast tests only
  $0 --fast

  # Run specific test
  $0 tests/integration/test_fmp_kg_integration.py::test_e2e_market_sync_small

  # Run with debug logging
  $0 --debug

  # Start services and run tests
  $0 --start-services

  # Run performance tests
  $0 --perf

Environment Variables:
  KNOWLEDGE_GRAPH_URL     Knowledge-Graph Service URL (default: http://localhost:8111)
  FMP_SERVICE_URL         FMP Service URL (default: http://localhost:8109)
  NEO4J_URL               Neo4j URL (default: bolt://localhost:7687)
  TEST_MARKER             Pytest marker (default: integration)
  LOG_LEVEL               Log level (default: INFO)

EOF
}

# Parse arguments
SKIP_CHECKS=false
START_SERVICES=false
PYTEST_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -s|--start-services)
            START_SERVICES=true
            shift
            ;;
        -m|--marker)
            TEST_MARKER="$2"
            shift 2
            ;;
        -v|--verbose)
            TEST_VERBOSITY="-vv"
            shift
            ;;
        -d|--debug)
            LOG_LEVEL="DEBUG"
            shift
            ;;
        --no-check)
            SKIP_CHECKS=true
            shift
            ;;
        --fast)
            TEST_MARKER="integration and not slow"
            shift
            ;;
        --perf)
            TEST_MARKER="performance"
            shift
            ;;
        *)
            PYTEST_ARGS+=("$1")
            shift
            ;;
    esac
done

# Main execution
main() {
    # Start services if requested
    if [ "$START_SERVICES" = true ]; then
        start_services
    fi

    # Check prerequisites (unless skipped)
    if [ "$SKIP_CHECKS" = false ]; then
        check_prerequisites
    fi

    # Run tests
    run_tests "${PYTEST_ARGS[@]}"
}

main
