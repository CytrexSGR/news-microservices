#!/bin/bash
# E2E Test Suite Validation Script
# Verifies that all components are ready for testing

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}E2E Test Suite Validation${NC}"
echo -e "${BLUE}========================================${NC}\n"

ERRORS=0

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION installed"
else
    echo -e "${RED}✗${NC} Python 3 not found"
    ERRORS=$((ERRORS + 1))
fi

# Check pip
echo -e "\n${YELLOW}Checking pip...${NC}"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip3 available"
else
    echo -e "${RED}✗${NC} pip3 not found"
    ERRORS=$((ERRORS + 1))
fi

# Check test files
echo -e "\n${YELLOW}Checking test files...${NC}"
TEST_FILES=(
    "conftest.py"
    "test_user_flow.py"
    "test_auth_integration.py"
    "test_event_flow.py"
    "test_search_integration.py"
    "test_notification_flow.py"
    "test_analytics_flow.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file not found"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check fixtures
echo -e "\n${YELLOW}Checking test fixtures...${NC}"
FIXTURES=(
    "fixtures/users.json"
    "fixtures/feeds.json"
    "fixtures/articles.json"
)

for fixture in "${FIXTURES[@]}"; do
    if [ -f "$fixture" ]; then
        echo -e "${GREEN}✓${NC} $fixture"
    else
        echo -e "${RED}✗${NC} $fixture not found"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check load testing files
echo -e "\n${YELLOW}Checking load testing files...${NC}"
if [ -f "load/locustfile.py" ]; then
    echo -e "${GREEN}✓${NC} load/locustfile.py"
else
    echo -e "${RED}✗${NC} load/locustfile.py not found"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "load/k6_script.js" ]; then
    echo -e "${GREEN}✓${NC} load/k6_script.js"
else
    echo -e "${RED}✗${NC} load/k6_script.js not found"
    ERRORS=$((ERRORS + 1))
fi

# Check configuration files
echo -e "\n${YELLOW}Checking configuration files...${NC}"
CONFIG_FILES=(
    "pytest.ini"
    "requirements.txt"
    "docker-compose.test.yml"
    "Dockerfile.test"
)

for config in "${CONFIG_FILES[@]}"; do
    if [ -f "$config" ]; then
        echo -e "${GREEN}✓${NC} $config"
    else
        echo -e "${RED}✗${NC} $config not found"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check documentation
echo -e "\n${YELLOW}Checking documentation...${NC}"
if [ -f "README.md" ]; then
    echo -e "${GREEN}✓${NC} README.md"
else
    echo -e "${RED}✗${NC} README.md not found"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "QUICKSTART.md" ]; then
    echo -e "${GREEN}✓${NC} QUICKSTART.md"
else
    echo -e "${RED}✗${NC} QUICKSTART.md not found"
    ERRORS=$((ERRORS + 1))
fi

# Check scripts
echo -e "\n${YELLOW}Checking scripts...${NC}"
if [ -f "run_tests.sh" ] && [ -x "run_tests.sh" ]; then
    echo -e "${GREEN}✓${NC} run_tests.sh (executable)"
else
    echo -e "${RED}✗${NC} run_tests.sh not found or not executable"
    ERRORS=$((ERRORS + 1))
fi

# Check services are running
echo -e "\n${YELLOW}Checking service health...${NC}"
SERVICES=(
    "8000:Auth"
    "8001:Feed"
    "8002:Content Analysis"
    "8003:Research"
    "8004:OSINT"
    "8005:Notification"
    "8006:Search"
    "8007:Analytics"
)

SERVICE_ERRORS=0
for service in "${SERVICES[@]}"; do
    PORT=$(echo $service | cut -d: -f1)
    NAME=$(echo $service | cut -d: -f2)

    if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1 || \
       curl -s "http://localhost:$PORT/api/v1/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $NAME Service (port $PORT)"
    else
        echo -e "${YELLOW}⚠${NC} $NAME Service (port $PORT) - Not running"
        SERVICE_ERRORS=$((SERVICE_ERRORS + 1))
    fi
done

if [ $SERVICE_ERRORS -gt 0 ]; then
    echo -e "\n${YELLOW}Note: $SERVICE_ERRORS service(s) not running. Start with:${NC}"
    echo -e "${YELLOW}  cd /home/cytrex/news-microservices${NC}"
    echo -e "${YELLOW}  docker-compose up -d${NC}"
fi

# Count test scenarios
echo -e "\n${YELLOW}Analyzing test coverage...${NC}"
TEST_COUNT=$(grep -r "^async def test_" *.py | wc -l)
echo -e "${GREEN}✓${NC} $TEST_COUNT test scenarios found"

# Count lines of code
LOC=$(wc -l *.py load/*.py 2>/dev/null | tail -1 | awk '{print $1}')
echo -e "${GREEN}✓${NC} $LOC lines of test code"

# Final summary
echo -e "\n${BLUE}========================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All validation checks passed!${NC}"
    echo -e "\n${YELLOW}Ready to run tests:${NC}"
    echo -e "  ${BLUE}./run_tests.sh smoke${NC}     # Quick smoke tests"
    echo -e "  ${BLUE}./run_tests.sh all${NC}       # All E2E tests"
    echo -e "  ${BLUE}./run_tests.sh load-k6${NC}   # Load testing"

    if [ $SERVICE_ERRORS -eq 0 ]; then
        echo -e "\n${GREEN}All services are healthy and ready for testing!${NC}"
    else
        echo -e "\n${YELLOW}Start services before running tests:${NC}"
        echo -e "  ${BLUE}cd ../.. && docker-compose up -d${NC}"
    fi
else
    echo -e "${RED}✗ $ERRORS validation error(s) found${NC}"
    echo -e "\n${YELLOW}Please fix errors before running tests${NC}"
fi
echo -e "${BLUE}========================================${NC}\n"

exit $ERRORS
