#!/bin/bash
# Master Benchmark Runner - Week 4 Performance Validation
# Runs all benchmarks sequentially and generates comprehensive report

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPORT_DIR="/home/cytrex/news-microservices/reports/performance/week4"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$REPORT_DIR/benchmark_run_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================================"
echo "WEEK 4 PERFORMANCE VALIDATION BENCHMARK SUITE"
echo "============================================================"
echo "Timestamp: $(date)"
echo "Report directory: $REPORT_DIR"
echo "Log file: $LOG_FILE"
echo "============================================================"
echo ""

# Create report directory
mkdir -p "$REPORT_DIR"

# Initialize log file
{
    echo "============================================================"
    echo "WEEK 4 PERFORMANCE VALIDATION BENCHMARK SUITE"
    echo "============================================================"
    echo "Start time: $(date)"
    echo ""
} > "$LOG_FILE"

# Function to run benchmark and capture results
run_benchmark() {
    local name=$1
    local script=$2
    local description=$3

    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}RUNNING: $name${NC}"
    echo -e "${BLUE}Description: $description${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""

    {
        echo "============================================================"
        echo "BENCHMARK: $name"
        echo "Description: $description"
        echo "Start time: $(date)"
        echo "============================================================"
    } >> "$LOG_FILE"

    # Run the benchmark
    local start_time=$(date +%s)

    if [[ "$script" == *.py ]]; then
        python3 "$SCRIPT_DIR/$script" 2>&1 | tee -a "$LOG_FILE"
    elif [[ "$script" == *.sh ]]; then
        bash "$SCRIPT_DIR/$script" 2>&1 | tee -a "$LOG_FILE"
    fi

    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    {
        echo ""
        echo "End time: $(date)"
        echo "Duration: ${duration}s"
        echo "Exit code: $exit_code"
        echo ""
    } >> "$LOG_FILE"

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ $name completed successfully (${duration}s)${NC}"
    else
        echo -e "${RED}❌ $name failed with exit code $exit_code${NC}"
    fi

    echo ""
    echo -e "${YELLOW}⏸️  Pausing 10 seconds before next benchmark...${NC}"
    echo ""
    sleep 10
}

# Check if services are running
echo "🔍 Checking service health..."
echo ""

check_service() {
    local name=$1
    local url=$2

    if curl -s -f "$url/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ $name is healthy${NC}"
        return 0
    else
        echo -e "  ${RED}❌ $name is not responding${NC}"
        return 1
    fi
}

# Check all required services
SERVICES_OK=true

check_service "Auth Service" "http://localhost:8100" || SERVICES_OK=false
check_service "Prediction Service" "http://localhost:8116" || SERVICES_OK=false
check_service "Narrative Service" "http://localhost:8119" || SERVICES_OK=false
check_service "Analytics Service" "http://localhost:8107" || SERVICES_OK=false
check_service "Scheduler Service" "http://localhost:8108" || SERVICES_OK=false
check_service "FMP Service" "http://localhost:8109" || SERVICES_OK=false

# Check if scraping service container exists
if docker ps --format '{{.Names}}' | grep -q "scraping-service"; then
    echo -e "  ${GREEN}✅ Scraping Service container is running${NC}"
else
    echo -e "  ${YELLOW}⚠️  Scraping Service container not found${NC}"
fi

echo ""

if [ "$SERVICES_OK" = false ]; then
    echo -e "${RED}❌ Some services are not healthy. Start all services before running benchmarks.${NC}"
    echo "Run: docker compose up -d"
    exit 1
fi

echo -e "${GREEN}✅ All services are healthy${NC}"
echo ""
echo -e "${YELLOW}⏸️  Starting benchmarks in 5 seconds...${NC}"
echo ""
sleep 5

# Run all benchmarks
echo "🚀 Starting benchmark suite..."
echo ""

# Week 3 Benchmarks (Critical Performance Claims)
run_benchmark \
    "Prediction Service Cache" \
    "benchmark_prediction_cache.py" \
    "Validates 30-40x speedup claim (5-15ms cached vs 350-450ms uncached)"

run_benchmark \
    "Narrative Service Cache" \
    "benchmark_narrative_cache.py" \
    "Validates 13x better than target claim (3-5ms cached vs 2s target)"

run_benchmark \
    "Analytics WebSocket Stability" \
    "benchmark_websocket_stability.py" \
    "Validates 99.9% stability with 100+ concurrent connections"

run_benchmark \
    "Scheduler Throughput & Metrics" \
    "benchmark_scheduler_throughput.py" \
    "Validates 40+ Prometheus metrics operational and accurate"

# Week 2 Benchmarks
run_benchmark \
    "FMP DCC-GARCH Performance" \
    "benchmark_fmp_dcc_garch.py" \
    "Validates 0.154s execution (6-7x better than <1s target)"

# Long-running benchmark (optional)
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}OPTIONAL: Memory Stability Benchmark (1 hour)${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "This benchmark monitors scraping service memory for 1 hour."
echo "It validates that memory stays < 2GB and doesn't leak."
echo ""
read -p "Run memory stability benchmark? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    run_benchmark \
        "Scraping Service Memory Stability" \
        "benchmark_memory_stability.sh" \
        "Validates memory stable < 2GB with no leaks"
else
    echo "⏭️  Skipping memory stability benchmark"
    echo ""
fi

# Generate summary
echo "============================================================"
echo "BENCHMARK SUITE COMPLETE"
echo "============================================================"
echo ""
echo "📊 Summary:"
echo "  - Prediction Cache: Check log for results"
echo "  - Narrative Cache: Check log for results"
echo "  - WebSocket Stability: Check log for results"
echo "  - Scheduler Metrics: Check log for results"
echo "  - FMP DCC-GARCH: Check log for results"
echo ""
echo "📄 Full results:"
echo "  Log file: $LOG_FILE"
echo "  Report directory: $REPORT_DIR"
echo ""
echo "📝 Next steps:"
echo "  1. Review benchmark results in log file"
echo "  2. Update WEEK4_BENCHMARK_RESULTS.md with findings"
echo "  3. Create performance comparison chart"
echo "  4. Document any claims that need adjustment"
echo ""
echo "✅ All benchmarks completed at $(date)"
echo "============================================================"
