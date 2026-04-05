#!/bin/bash
# Environment Readiness Check for Week 4 Benchmarks
# Verifies all prerequisites before running performance benchmarks

echo "============================================================"
echo "BENCHMARK ENVIRONMENT READINESS CHECK"
echo "============================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Function to print status
print_status() {
    local status=$1
    local message=$2

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $message"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC} - $message"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC} - $message"
        CHECKS_WARNING=$((CHECKS_WARNING + 1))
    fi
}

echo "🔍 Checking services..."
echo ""

# Check Docker
if command -v docker &> /dev/null; then
    print_status "PASS" "Docker is installed"
else
    print_status "FAIL" "Docker is not installed"
fi

# Check Docker Compose
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    print_status "PASS" "Docker Compose is available"
else
    print_status "FAIL" "Docker Compose is not available"
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "PASS" "Python 3 is installed (version: $PYTHON_VERSION)"
else
    print_status "FAIL" "Python 3 is not installed"
fi

echo ""
echo "🐍 Checking Python dependencies..."
echo ""

# Check required Python packages
check_python_package() {
    local package=$1
    if python3 -c "import $package" 2>/dev/null; then
        print_status "PASS" "Python package '$package' is installed"
    else
        print_status "FAIL" "Python package '$package' is missing (install: pip install $package)"
    fi
}

check_python_package "httpx"
check_python_package "redis"
check_python_package "websockets"

echo ""
echo "🐳 Checking Docker containers..."
echo ""

# Check if services are running
check_container() {
    local name=$1
    local friendly_name=$2

    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        # Check if healthy
        local health=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null)

        if [ "$health" = "healthy" ]; then
            print_status "PASS" "$friendly_name is running and healthy"
        elif [ "$health" = "unhealthy" ]; then
            print_status "WARN" "$friendly_name is running but unhealthy"
        else
            print_status "PASS" "$friendly_name is running (no health check)"
        fi
    else
        print_status "FAIL" "$friendly_name is not running"
    fi
}

check_container "auth-service" "Auth Service"
check_container "prediction-service" "Prediction Service"
check_container "narrative-service" "Narrative Service"
check_container "analytics-service" "Analytics Service"
check_container "scheduler-service" "Scheduler Service"
check_container "fmp-service" "FMP Service"
check_container "scraping-service" "Scraping Service"
check_container "redis" "Redis"
check_container "postgres" "PostgreSQL"

echo ""
echo "🌐 Checking service endpoints..."
echo ""

# Check if services respond to HTTP requests
check_endpoint() {
    local url=$1
    local name=$2

    if curl -s -f "$url/health" > /dev/null 2>&1; then
        print_status "PASS" "$name endpoint is responding ($url)"
    elif curl -s "$url/health" > /dev/null 2>&1; then
        print_status "WARN" "$name endpoint is accessible but returned non-200 status"
    else
        print_status "FAIL" "$name endpoint is not accessible ($url)"
    fi
}

check_endpoint "http://localhost:8100" "Auth Service"
check_endpoint "http://localhost:8116" "Prediction Service"
check_endpoint "http://localhost:8119" "Narrative Service"
check_endpoint "http://localhost:8107" "Analytics Service"
check_endpoint "http://localhost:8108" "Scheduler Service"
check_endpoint "http://localhost:8109" "FMP Service"

echo ""
echo "💾 Checking Redis..."
echo ""

# Check Redis connection
if docker exec redis redis-cli ping 2>&1 | grep -q "PONG"; then
    print_status "PASS" "Redis is responding to commands"
else
    print_status "FAIL" "Redis is not responding"
fi

# Check Redis memory
REDIS_MEMORY=$(docker exec redis redis-cli INFO memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
if [ ! -z "$REDIS_MEMORY" ]; then
    print_status "PASS" "Redis memory usage: $REDIS_MEMORY"
else
    print_status "WARN" "Cannot determine Redis memory usage"
fi

echo ""
echo "💻 Checking system resources..."
echo ""

# Check available memory
TOTAL_MEM=$(free -g | awk '/^Mem:/ {print $2}')
FREE_MEM=$(free -g | awk '/^Mem:/ {print $4}')

if [ "$FREE_MEM" -ge 2 ]; then
    print_status "PASS" "Sufficient free memory: ${FREE_MEM}GB / ${TOTAL_MEM}GB"
elif [ "$FREE_MEM" -ge 1 ]; then
    print_status "WARN" "Low free memory: ${FREE_MEM}GB / ${TOTAL_MEM}GB (benchmarks may be slow)"
else
    print_status "FAIL" "Insufficient free memory: ${FREE_MEM}GB / ${TOTAL_MEM}GB (need at least 1GB)"
fi

# Check CPU load
CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
CPU_CORES=$(nproc)

if [ ! -z "$CPU_LOAD" ] && [ ! -z "$CPU_CORES" ]; then
    CPU_LOAD_PCT=$(awk "BEGIN {printf \"%.0f\", ($CPU_LOAD / $CPU_CORES) * 100}")

    if [ "$CPU_LOAD_PCT" -lt 50 ]; then
        print_status "PASS" "CPU load is low: ${CPU_LOAD} (${CPU_LOAD_PCT}% of ${CPU_CORES} cores)"
    elif [ "$CPU_LOAD_PCT" -lt 80 ]; then
        print_status "WARN" "CPU load is moderate: ${CPU_LOAD} (${CPU_LOAD_PCT}% of ${CPU_CORES} cores)"
    else
        print_status "FAIL" "CPU load is high: ${CPU_LOAD} (${CPU_LOAD_PCT}% of ${CPU_CORES} cores) - benchmarks may be inaccurate"
    fi
else
    print_status "WARN" "Cannot determine CPU load"
fi

# Check disk space
DISK_FREE=$(df -h / | awk 'NR==2 {print $4}')
DISK_USE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')

if [ "$DISK_USE" -lt 80 ]; then
    print_status "PASS" "Sufficient disk space: $DISK_FREE available (${DISK_USE}% used)"
elif [ "$DISK_USE" -lt 90 ]; then
    print_status "WARN" "Disk space getting low: $DISK_FREE available (${DISK_USE}% used)"
else
    print_status "FAIL" "Disk space critically low: $DISK_FREE available (${DISK_USE}% used)"
fi

echo ""
echo "📂 Checking directories..."
echo ""

# Check report directory
if [ -d "/home/cytrex/news-microservices/reports/performance/week4" ]; then
    print_status "PASS" "Report directory exists"
else
    print_status "WARN" "Report directory does not exist (will be created automatically)"
fi

# Check scripts are executable
if [ -x "/home/cytrex/news-microservices/scripts/benchmarks/run_all_benchmarks.sh" ]; then
    print_status "PASS" "Master benchmark script is executable"
else
    print_status "FAIL" "Master benchmark script is not executable (run: chmod +x scripts/benchmarks/*.sh)"
fi

echo ""
echo "============================================================"
echo "SUMMARY"
echo "============================================================"
echo ""
echo -e "${GREEN}✅ Checks Passed: $CHECKS_PASSED${NC}"
echo -e "${YELLOW}⚠️  Checks Warning: $CHECKS_WARNING${NC}"
echo -e "${RED}❌ Checks Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Environment is ready for benchmarks!${NC}"
    echo ""
    echo "To run all benchmarks:"
    echo "  ./scripts/benchmarks/run_all_benchmarks.sh"
    echo ""
    exit 0
elif [ $CHECKS_FAILED -le 2 ] && [ $CHECKS_PASSED -ge 15 ]; then
    echo -e "${YELLOW}⚠️  Environment is mostly ready, but some issues detected${NC}"
    echo ""
    echo "You can proceed with benchmarks, but results may be affected."
    echo "Review failed checks above and fix if possible."
    echo ""
    exit 0
else
    echo -e "${RED}❌ Environment is not ready for benchmarks${NC}"
    echo ""
    echo "Fix the failed checks above before running benchmarks."
    echo ""
    echo "Common fixes:"
    echo "  - Start services: docker compose up -d"
    echo "  - Install Python deps: pip install httpx redis websockets"
    echo "  - Free up memory: close other applications"
    echo ""
    exit 1
fi
