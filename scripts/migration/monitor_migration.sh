#!/bin/bash
# 24h Post-Migration Monitoring Dashboard
# Tracks key metrics after migration to verify success

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_USER="${POSTGRES_USER:-news_user}"
DB_NAME="${POSTGRES_DB:-news_mcp}"
FEED_SERVICE_URL="${FEED_SERVICE_URL:-http://localhost:8101}"
AUTH_SERVICE_URL="${AUTH_SERVICE_URL:-http://localhost:8100}"

# Monitoring interval (default: 2 hours = 7200 seconds)
INTERVAL="${MONITOR_INTERVAL:-7200}"
DURATION="${MONITOR_DURATION:-86400}" # 24 hours

# Alert thresholds
ALERT_ERROR_RATE=0.01        # 1% error rate
ALERT_RESPONSE_TIME=500      # 500ms p95
ALERT_ROW_COUNT_DRIFT=10     # 10 rows difference

# ════════════════════════════════════════════════════════════════════
# Helper Functions
# ════════════════════════════════════════════════════════════════════

execute_sql() {
    docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1" 2>/dev/null | xargs
}

print_header() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  POST-MIGRATION MONITORING DASHBOARD                         ║${NC}"
    echo -e "${CYAN}║  Started: $(date '+%Y-%m-%d %H:%M:%S')                          ║${NC}"
    echo -e "${CYAN}║  Uptime: $(printf '%02d:%02d' $((SECONDS/3600)) $(((SECONDS%3600)/60)))                                                  ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

get_auth_token() {
    local response=$(curl -s -X POST "$AUTH_SERVICE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"andreas@test.com","password":"Aug2012#"}')
    echo "$response" | jq -r '.access_token // empty'
}

# ════════════════════════════════════════════════════════════════════
# Monitoring Checks
# ════════════════════════════════════════════════════════════════════

check_table_counts() {
    local legacy_count=$(execute_sql "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;")
    local unified_count=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis;")
    local drift=$((legacy_count - unified_count))

    echo -e "${BLUE}▶ TABLE ROW COUNTS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "  Legacy table:  %6d rows\n" "$legacy_count"
    printf "  Unified table: %6d rows\n" "$unified_count"
    printf "  Drift:         %6d rows " "$drift"

    if [ "$drift" -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
    elif [ "$drift" -le "$ALERT_ROW_COUNT_DRIFT" ]; then
        echo -e "${YELLOW}⚠${NC} (within threshold)"
    else
        echo -e "${RED}✗${NC} ALERT: Drift > $ALERT_ROW_COUNT_DRIFT"
        return 1
    fi
    echo ""
}

check_data_quality() {
    local total=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE success = true;")
    local null_triage=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE success = true AND triage_results IS NULL;")
    local null_tier1=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE success = true AND tier1_results IS NULL;")
    local has_relevance=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE success = true AND relevance_score IS NOT NULL;")

    local null_triage_pct=$(echo "scale=2; $null_triage * 100 / $total" | bc)
    local null_tier1_pct=$(echo "scale=2; $null_tier1 * 100 / $total" | bc)
    local relevance_pct=$(echo "scale=2; $has_relevance * 100 / $total" | bc)

    echo -e "${BLUE}▶ DATA QUALITY${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "  Successful analyses:     %6d\n" "$total"
    printf "  Null triage results:     %6d (%5.2f%%) " "$null_triage" "$null_triage_pct"
    [ "$null_triage" -eq 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC}"

    printf "  Null tier1 results:      %6d (%5.2f%%) " "$null_tier1" "$null_tier1_pct"
    [ "$null_tier1" -eq 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC}"

    printf "  Has relevance score:     %6d (%5.2f%%) " "$has_relevance" "$relevance_pct"
    [ "${relevance_pct%.*}" -gt 80 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC}"
    echo ""
}

check_recent_analyses() {
    local last_1h=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE created_at > NOW() - INTERVAL '1 hour';")
    local last_10m=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE created_at > NOW() - INTERVAL '10 minutes';")
    local last_1m=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE created_at > NOW() - INTERVAL '1 minute';")

    echo -e "${BLUE}▶ RECENT ANALYSES${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "  Last hour:   %4d analyses " "$last_1h"
    [ "$last_1h" -gt 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC} (no new analyses)"

    printf "  Last 10 min: %4d analyses\n" "$last_10m"
    printf "  Last 1 min:  %4d analyses " "$last_1m"
    [ "$last_1m" -gt 0 ] && echo -e "${GREEN}✓ Active${NC}" || echo -e "${YELLOW}○ Idle${NC}"
    echo ""
}

check_api_performance() {
    local TOKEN=$(get_auth_token)
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}✗ Failed to get auth token${NC}"
        return 1
    fi

    # Get random article ID
    local article_id=$(execute_sql "SELECT article_id FROM public.article_analysis ORDER BY RANDOM() LIMIT 1;")

    # Test single article endpoint (5 samples)
    local total_time=0
    local samples=5
    for i in $(seq 1 $samples); do
        local start=$(date +%s%3N)
        curl -s -H "Authorization: Bearer $TOKEN" "$FEED_SERVICE_URL/api/v1/feeds/items/$article_id" > /dev/null
        local end=$(date +%s%3N)
        local duration=$((end - start))
        total_time=$((total_time + duration))
    done
    local avg_single=$((total_time / samples))

    # Test batch endpoint (3 samples)
    total_time=0
    samples=3
    for i in $(seq 1 $samples); do
        local start=$(date +%s%3N)
        curl -s -H "Authorization: Bearer $TOKEN" "$FEED_SERVICE_URL/api/v1/feeds/items?limit=20" > /dev/null
        local end=$(date +%s%3N)
        local duration=$((end - start))
        total_time=$((total_time + duration))
    done
    local avg_batch=$((total_time / samples))

    echo -e "${BLUE}▶ API PERFORMANCE${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "  Single article (avg):  %4dms " "$avg_single"
    [ "$avg_single" -lt 200 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC} (target: <200ms)"

    printf "  Batch 20 (avg):        %4dms " "$avg_batch"
    [ "$avg_batch" -lt 700 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC} (target: <700ms)"
    echo ""
}

check_workers_status() {
    local consumer_status=$(docker ps --filter "name=feed-service-analysis-consumer" --format "{{.Status}}" 2>/dev/null | grep -c "Up" || echo "0")
    local worker_count=$(docker ps --filter "name=content-analysis-v2-worker" --format "{{.Names}}" 2>/dev/null | wc -l)

    echo -e "${BLUE}▶ WORKERS STATUS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "  Analysis consumer:     "
    [ "$consumer_status" -eq 1 ] && echo -e "${GREEN}✓ Running${NC}" || echo -e "${RED}✗ Stopped${NC}"

    printf "  Content workers:       %d active " "$worker_count"
    [ "$worker_count" -gt 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"
    echo ""
}

check_errors_in_logs() {
    local feed_errors=$(docker logs --since 1h news-microservices-feed-service-1 2>&1 | grep -i "error" | wc -l || echo "0")
    local worker_errors=$(docker logs --since 1h content-analysis-v2-worker-1 2>&1 | grep -i "error" | wc -l || echo "0")

    echo -e "${BLUE}▶ ERROR LOGS (last 1h)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "  Feed service errors:   %4d " "$feed_errors"
    [ "$feed_errors" -eq 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC}"

    printf "  Worker errors:         %4d " "$worker_errors"
    [ "$worker_errors" -eq 0 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC}"
    echo ""
}

# ════════════════════════════════════════════════════════════════════
# Health Score Calculation
# ════════════════════════════════════════════════════════════════════

calculate_health_score() {
    local score=100
    local issues=0

    # Table drift check
    local drift=$(execute_sql "SELECT ABS((SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions) - (SELECT COUNT(*) FROM public.article_analysis));")
    if [ "$drift" -gt "$ALERT_ROW_COUNT_DRIFT" ]; then
        score=$((score - 20))
        ((issues++))
    fi

    # Recent analyses check
    local recent=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE created_at > NOW() - INTERVAL '1 hour';")
    if [ "$recent" -eq 0 ]; then
        score=$((score - 15))
        ((issues++))
    fi

    # API performance check (rough estimate based on last check)
    # (Would need to store last result for accurate calculation)

    # Worker status check
    local consumer=$(docker ps --filter "name=feed-service-analysis-consumer" --format "{{.Status}}" 2>/dev/null | grep -c "Up" || echo "0")
    if [ "$consumer" -eq 0 ]; then
        score=$((score - 25))
        ((issues++))
    fi

    echo "$score:$issues"
}

# ════════════════════════════════════════════════════════════════════
# Main Monitoring Loop
# ════════════════════════════════════════════════════════════════════

main() {
    local start_time=$(date +%s)
    local iteration=0

    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  24h POST-MIGRATION MONITORING STARTED                        ║${NC}"
    echo -e "${GREEN}║  Interval: ${INTERVAL}s ($(($INTERVAL/60)) minutes)                                  ║${NC}"
    echo -e "${GREEN}║  Duration: ${DURATION}s (24 hours)                                 ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
    echo ""
    sleep 3

    while true; do
        ((iteration++))
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        # Exit after duration
        if [ "$elapsed" -ge "$DURATION" ]; then
            echo -e "${GREEN}✅ 24h monitoring period complete${NC}"
            echo ""
            echo "📊 Final Status:"
            check_table_counts
            check_data_quality
            echo ""
            echo "Migration monitoring completed successfully."
            exit 0
        fi

        print_header

        echo -e "${CYAN}Iteration: #$iteration${NC}"
        echo -e "${CYAN}Elapsed: $(printf '%02d:%02d:%02d' $((elapsed/3600)) $(((elapsed%3600)/60)) $((elapsed%60)))${NC}"
        echo -e "${CYAN}Remaining: $(printf '%02d:%02d:%02d' $(((DURATION-elapsed)/3600)) $((((DURATION-elapsed)%3600)/60)) $(((DURATION-elapsed)%60)))${NC}"
        echo ""

        # Run all checks
        check_table_counts
        check_data_quality
        check_recent_analyses
        check_api_performance
        check_workers_status
        check_errors_in_logs

        # Calculate health score
        local health_result=$(calculate_health_score)
        local health_score=$(echo "$health_result" | cut -d: -f1)
        local issue_count=$(echo "$health_result" | cut -d: -f2)

        echo -e "${BLUE}▶ HEALTH SCORE${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        printf "  Overall health: %3d/100 " "$health_score"

        if [ "$health_score" -ge 90 ]; then
            echo -e "${GREEN}✓ Excellent${NC}"
        elif [ "$health_score" -ge 70 ]; then
            echo -e "${YELLOW}⚠ Good${NC}"
        elif [ "$health_score" -ge 50 ]; then
            echo -e "${YELLOW}⚠ Fair${NC}"
        else
            echo -e "${RED}✗ Poor${NC}"
        fi

        printf "  Issues detected: %d\n" "$issue_count"
        echo ""

        # Log to file
        echo "$(date -Iseconds),${health_score},${issue_count}" >> /tmp/migration_monitoring.csv

        # Next check in...
        echo -e "${CYAN}Next check in $(($INTERVAL/60)) minutes...${NC}"
        echo ""

        sleep "$INTERVAL"
    done
}

# ════════════════════════════════════════════════════════════════════
# Entry Point
# ════════════════════════════════════════════════════════════════════

# Initialize CSV log
if [ ! -f /tmp/migration_monitoring.csv ]; then
    echo "timestamp,health_score,issues" > /tmp/migration_monitoring.csv
fi

main "$@"
