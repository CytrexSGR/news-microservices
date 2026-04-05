#!/bin/bash
# E2E Test Runner Script
# Runs comprehensive end-to-end tests for News MCP

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}News MCP E2E Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if services are running
echo -e "\n${YELLOW}Checking service health...${NC}"

SERVICES=(8000 8001 8002 8003 8004 8005 8006 8007)
SERVICE_NAMES=("Auth" "Feed" "Content Analysis" "Research" "OSINT" "Notification" "Search" "Analytics")

for i in "${!SERVICES[@]}"; do
    PORT=${SERVICES[$i]}
    NAME=${SERVICE_NAMES[$i]}

    if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $NAME Service (port $PORT) - Healthy"
    else
        echo -e "${RED}✗${NC} $NAME Service (port $PORT) - Not responding"
        echo -e "${RED}Please start services with: docker-compose up -d${NC}"
        exit 1
    fi
done

# Wait for services to be fully ready
echo -e "\n${YELLOW}Waiting for services to stabilize (10 seconds)...${NC}"
sleep 10

# Create reports directory
mkdir -p reports

# Run tests based on argument
case "${1:-all}" in
    "all")
        echo -e "\n${YELLOW}Running all E2E tests...${NC}"
        pytest -v \
            --html=reports/e2e-report.html \
            --self-contained-html \
            --cov=. \
            --cov-report=html:reports/coverage \
            --cov-report=term-missing \
            --maxfail=5
        ;;

    "smoke")
        echo -e "\n${YELLOW}Running smoke tests...${NC}"
        pytest -v -m smoke \
            --html=reports/smoke-report.html \
            --self-contained-html
        ;;

    "user-flow")
        echo -e "\n${YELLOW}Running user flow tests...${NC}"
        pytest -v test_user_flow.py \
            --html=reports/user-flow-report.html \
            --self-contained-html
        ;;

    "auth")
        echo -e "\n${YELLOW}Running authentication tests...${NC}"
        pytest -v test_auth_integration.py \
            --html=reports/auth-report.html \
            --self-contained-html
        ;;

    "events")
        echo -e "\n${YELLOW}Running event flow tests...${NC}"
        pytest -v test_event_flow.py \
            --html=reports/event-report.html \
            --self-contained-html
        ;;

    "search")
        echo -e "\n${YELLOW}Running search tests...${NC}"
        pytest -v test_search_integration.py \
            --html=reports/search-report.html \
            --self-contained-html
        ;;

    "parallel")
        echo -e "\n${YELLOW}Running tests in parallel...${NC}"
        pytest -v -n auto \
            --html=reports/parallel-report.html \
            --self-contained-html \
            --maxfail=10
        ;;

    "coverage")
        echo -e "\n${YELLOW}Running tests with detailed coverage...${NC}"
        pytest -v \
            --cov=. \
            --cov-report=html:reports/coverage \
            --cov-report=term-missing \
            --cov-report=xml:reports/coverage.xml \
            --html=reports/coverage-report.html \
            --self-contained-html
        ;;

    "load-locust")
        echo -e "\n${YELLOW}Starting Locust load testing...${NC}"
        echo -e "${GREEN}Web UI available at: http://localhost:8089${NC}"
        cd load
        locust -f locustfile.py --host=http://localhost:8000
        ;;

    "load-k6")
        echo -e "\n${YELLOW}Running K6 load tests...${NC}"
        cd load
        k6 run k6_script.js --out json=../reports/k6-results.json
        ;;

    "docker")
        echo -e "\n${YELLOW}Running tests in Docker...${NC}"
        docker-compose -f docker-compose.test.yml up --build e2e-tests
        ;;

    "clean")
        echo -e "\n${YELLOW}Cleaning test artifacts...${NC}"
        rm -rf reports/
        rm -rf .pytest_cache/
        rm -rf __pycache__/
        rm -rf .coverage
        echo -e "${GREEN}✓${NC} Clean complete"
        exit 0
        ;;

    *)
        echo -e "\n${RED}Invalid option: $1${NC}"
        echo -e "\nUsage: $0 [option]"
        echo -e "\nOptions:"
        echo -e "  all          - Run all E2E tests (default)"
        echo -e "  smoke        - Run smoke tests only"
        echo -e "  user-flow    - Run user flow tests"
        echo -e "  auth         - Run authentication tests"
        echo -e "  events       - Run event flow tests"
        echo -e "  search       - Run search tests"
        echo -e "  parallel     - Run tests in parallel"
        echo -e "  coverage     - Run with detailed coverage"
        echo -e "  load-locust  - Start Locust load testing"
        echo -e "  load-k6      - Run K6 load tests"
        echo -e "  docker       - Run tests in Docker"
        echo -e "  clean        - Clean test artifacts"
        exit 1
        ;;
esac

TEST_EXIT_CODE=$?

# Print results
echo -e "\n${GREEN}========================================${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Tests Passed${NC}"
    echo -e "\n${YELLOW}Test reports available in:${NC}"
    echo -e "  - reports/e2e-report.html"
    echo -e "  - reports/coverage/index.html"
else
    echo -e "${RED}✗ Tests Failed${NC}"
    echo -e "\n${YELLOW}Check test output above for details${NC}"
fi
echo -e "${GREEN}========================================${NC}\n"

exit $TEST_EXIT_CODE
