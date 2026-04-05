#!/bin/bash
#
# Phase 4.4 Hybrid Data Architecture - Production Monitoring Script
#
# Tracks Bybit worker performance, data quality, and system health over 7-day
# observation period. Generates snapshots and alerts on anomalies.
#
# Usage:
#     ./scripts/monitor_hybrid_data_phase44.sh                 # Take snapshot
#     ./scripts/monitor_hybrid_data_phase44.sh --report daily  # Daily report
#     ./scripts/monitor_hybrid_data_phase44.sh --alert         # Check alerts
#
# Author: Phase 4.4 Implementation Team
# Date: 2025-12-01
#

set -e

# Configuration
FMP_SERVICE_URL="http://localhost:8113"
DATABASE_HOST="localhost"
DATABASE_PORT="5432"
DATABASE_NAME="predictions"
DATABASE_USER="postgres"
PGPASSWORD="postgres"
export PGPASSWORD

MONITORING_DIR="/home/cytrex/news-microservices/monitoring/phase44"
mkdir -p "$MONITORING_DIR"

# Alert thresholds
MAX_ERROR_RATE=0.05           # 5% max error rate
MAX_STALE_SECONDS=300         # Max 5 minutes stale data
MIN_SYMBOLS_SYNCING=14        # At least 14/16 symbols
MIN_DATA_QUALITY=90           # Min 90% OI/Funding completeness

# Expected symbols
EXPECTED_SYMBOLS=(
    "BTC/USDT:USDT" "ETH/USDT:USDT" "XRP/USDT:USDT" "BNB/USDT:USDT"
    "SOL/USDT:USDT" "TRX/USDT:USDT" "DOGE/USDT:USDT" "ADA/USDT:USDT"
    "AVAX/USDT:USDT" "LINK/USDT:USDT" "DOT/USDT:USDT" "XLM/USDT:USDT"
    "LTC/USDT:USDT" "TON/USDT:USDT" "HBAR/USDT:USDT" "UNI/USDT:USDT"
)

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Fetch Bybit worker status
get_bybit_status() {
    local status_json
    status_json=$(curl -s "$FMP_SERVICE_URL/api/v1/admin/bybit/status" 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$status_json" ]; then
        error "Failed to fetch Bybit worker status"
        return 1
    fi

    echo "$status_json"
}

# Get database statistics
get_database_stats() {
    local timestamp
    timestamp=$(date -u -d '24 hours ago' '+%Y-%m-%d %H:%M:%S')

    # Source distribution (last 24h)
    local source_dist
    source_dist=$(psql -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "
        SELECT
            json_agg(
                json_build_object(
                    'source', source,
                    'count', count,
                    'last_entry', last_entry
                )
            )
        FROM (
            SELECT
                source,
                COUNT(*) as count,
                MAX(timestamp) as last_entry
            FROM analysis_logs
            WHERE timestamp >= '$timestamp'
            GROUP BY source
            ORDER BY count DESC
        ) t
    " 2>/dev/null | tr -d '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Symbol coverage (last 24h, Bybit only)
    local symbol_coverage
    symbol_coverage=$(psql -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "
        SELECT COUNT(DISTINCT symbol)
        FROM analysis_logs
        WHERE timestamp >= '$timestamp' AND source = 'bybit'
    " 2>/dev/null | tr -d ' \n')

    # Data quality (last 24h, Bybit only)
    local data_quality
    data_quality=$(psql -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN market_data->>'open_interest' IS NOT NULL THEN 1 END) as with_oi,
            COUNT(CASE WHEN market_data->>'funding_rate' IS NOT NULL THEN 1 END) as with_funding
        FROM analysis_logs
        WHERE timestamp >= '$timestamp' AND source = 'bybit'
    " 2>/dev/null | tr -d '\n')

    if [ -z "$data_quality" ]; then
        error "Failed to fetch database statistics"
        return 1
    fi

    local total=$(echo "$data_quality" | awk '{print $1}')
    local with_oi=$(echo "$data_quality" | awk '{print $3}')
    local with_funding=$(echo "$data_quality" | awk '{print $5}')

    local oi_pct=0
    local funding_pct=0

    if [ "$total" -gt 0 ]; then
        oi_pct=$(echo "scale=2; $with_oi * 100 / $total" | bc)
        funding_pct=$(echo "scale=2; $with_funding * 100 / $total" | bc)
    fi

    echo "{\"source_distribution\":$source_dist,\"symbol_coverage\":$symbol_coverage,\"total_analyses\":$total,\"oi_completeness_pct\":$oi_pct,\"funding_completeness_pct\":$funding_pct}"
}

# Check for alert conditions
check_alerts() {
    local status_json="$1"
    local db_stats_json="$2"
    local alerts=()

    # Parse JSON (using jq if available, otherwise grep/sed)
    if command -v jq &> /dev/null; then
        local worker_running=$(echo "$status_json" | jq -r '.worker_running')
        local syncs_completed=$(echo "$status_json" | jq -r '.syncs_completed')
        local errors=$(echo "$status_json" | jq -r '.errors')
        local last_sync=$(echo "$status_json" | jq -r '.last_sync')
        local symbols_syncing=$(echo "$db_stats_json" | jq -r '.symbol_coverage')
        local oi_pct=$(echo "$db_stats_json" | jq -r '.oi_completeness_pct')
        local funding_pct=$(echo "$db_stats_json" | jq -r '.funding_completeness_pct')
    else
        # Fallback without jq
        local worker_running=$(echo "$status_json" | grep -oP '"worker_running"\s*:\s*\K(true|false)')
        local syncs_completed=$(echo "$status_json" | grep -oP '"syncs_completed"\s*:\s*\K[0-9]+')
        local errors=$(echo "$status_json" | grep -oP '"errors"\s*:\s*\K[0-9]+')
        local last_sync=$(echo "$status_json" | grep -oP '"last_sync"\s*:\s*"\K[^"]+')
        local symbols_syncing=$(echo "$db_stats_json" | grep -oP '"symbol_coverage"\s*:\s*\K[0-9]+')
        local oi_pct=$(echo "$db_stats_json" | grep -oP '"oi_completeness_pct"\s*:\s*\K[0-9.]+')
        local funding_pct=$(echo "$db_stats_json" | grep -oP '"funding_completeness_pct"\s*:\s*\K[0-9.]+')
    fi

    # Check worker status
    if [ "$worker_running" != "true" ]; then
        alerts+=("🚨 CRITICAL: Bybit worker is not running!")
    fi

    # Check error rate
    if [ "$syncs_completed" -gt 0 ] && [ "$errors" -gt 0 ]; then
        local error_rate=$(echo "scale=4; $errors / $syncs_completed" | bc)
        local threshold_check=$(echo "$error_rate > $MAX_ERROR_RATE" | bc)
        if [ "$threshold_check" -eq 1 ]; then
            local error_pct=$(echo "scale=2; $error_rate * 100" | bc)
            alerts+=("⚠️ WARNING: Error rate ${error_pct}% exceeds threshold")
        fi
    fi

    # Check last sync staleness
    if [ -n "$last_sync" ]; then
        local last_sync_epoch=$(date -d "$last_sync" +%s 2>/dev/null || date -d "${last_sync%.*}" +%s)
        local now_epoch=$(date +%s)
        local stale_seconds=$((now_epoch - last_sync_epoch))

        if [ "$stale_seconds" -gt "$MAX_STALE_SECONDS" ]; then
            alerts+=("⚠️ WARNING: Last sync ${stale_seconds}s ago (threshold: ${MAX_STALE_SECONDS}s)")
        fi
    fi

    # Check symbol coverage
    if [ "$symbols_syncing" -lt "$MIN_SYMBOLS_SYNCING" ]; then
        alerts+=("⚠️ WARNING: Only ${symbols_syncing}/${#EXPECTED_SYMBOLS[@]} symbols syncing")
    fi

    # Check data quality
    local oi_threshold_check=$(echo "$oi_pct < $MIN_DATA_QUALITY" | bc)
    if [ "$oi_threshold_check" -eq 1 ]; then
        alerts+=("⚠️ WARNING: OI data completeness ${oi_pct}% below ${MIN_DATA_QUALITY}% threshold")
    fi

    local funding_threshold_check=$(echo "$funding_pct < $MIN_DATA_QUALITY" | bc)
    if [ "$funding_threshold_check" -eq 1 ]; then
        alerts+=("⚠️ WARNING: Funding rate completeness ${funding_pct}% below ${MIN_DATA_QUALITY}% threshold")
    fi

    # Return alerts as JSON array
    if [ ${#alerts[@]} -eq 0 ]; then
        echo "[]"
    else
        printf '%s\n' "${alerts[@]}" | jq -R . | jq -s .
    fi
}

# Take monitoring snapshot
take_snapshot() {
    info "Taking monitoring snapshot..."

    # Fetch data
    local status_json
    status_json=$(get_bybit_status)
    if [ $? -ne 0 ]; then
        error "Failed to get Bybit status"
        return 1
    fi

    local db_stats_json
    db_stats_json=$(get_database_stats)
    if [ $? -ne 0 ]; then
        error "Failed to get database statistics"
        return 1
    fi

    # Check alerts
    local alerts_json
    alerts_json=$(check_alerts "$status_json" "$db_stats_json")

    # Build snapshot JSON
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%S)
    local snapshot_json=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "bybit_status": $status_json,
  "database_stats": $db_stats_json,
  "alerts": $alerts_json
}
EOF
)

    # Save snapshot
    local snapshot_file="$MONITORING_DIR/snapshot_$(date +%Y%m%d_%H%M%S).json"
    echo "$snapshot_json" > "$snapshot_file"

    success "Snapshot saved: $snapshot_file"

    # Display alerts
    local alert_count=$(echo "$alerts_json" | grep -o '🚨\|⚠️' | wc -l)
    if [ "$alert_count" -gt 0 ]; then
        warning "Found $alert_count alerts:"
        echo "$alerts_json" | jq -r '.[]' 2>/dev/null || echo "$alerts_json"
    else
        success "No alerts - system healthy ✅"
    fi

    return 0
}

# Generate daily report
generate_daily_report() {
    info "Generating daily report..."

    local today=$(date +%Y%m%d)
    local snapshots=("$MONITORING_DIR"/snapshot_${today}_*.json)

    if [ ${#snapshots[@]} -eq 0 ] || [ ! -f "${snapshots[0]}" ]; then
        warning "No snapshots available for today"
        return 1
    fi

    # Get latest snapshot
    local latest_snapshot="${snapshots[-1]}"

    if command -v jq &> /dev/null; then
        local syncs=$(jq -r '.bybit_status.syncs_completed' "$latest_snapshot")
        local errors=$(jq -r '.bybit_status.errors' "$latest_snapshot")
        local uptime=$(jq -r '.bybit_status.uptime_hours' "$latest_snapshot")
        local total_analyses=$(jq -r '.database_stats.total_analyses' "$latest_snapshot")
        local oi_pct=$(jq -r '.database_stats.oi_completeness_pct' "$latest_snapshot")
        local funding_pct=$(jq -r '.database_stats.funding_completeness_pct' "$latest_snapshot")
        local symbols_syncing=$(jq -r '.database_stats.symbol_coverage' "$latest_snapshot")
    else
        error "jq is required for report generation"
        return 1
    fi

    local error_rate=0
    if [ "$syncs" -gt 0 ]; then
        error_rate=$(echo "scale=2; $errors * 100 / $syncs" | bc)
    fi

    # Generate report
    local report_file="$MONITORING_DIR/daily_report_${today}.md"

    cat > "$report_file" <<EOF
# Phase 4.4 Hybrid Data Architecture - Daily Monitoring Report

**Date:** $(date '+%Y-%m-%d')
**Snapshots:** ${#snapshots[@]}

## Bybit Worker Performance
- **Total Syncs:** $syncs
- **Total Errors:** $errors
- **Error Rate:** ${error_rate}%
- **Uptime:** ${uptime} hours

## Data Quality (Last 24h)
- **Total Bybit Analyses:** ${total_analyses}
- **Symbols Syncing:** ${symbols_syncing}/${#EXPECTED_SYMBOLS[@]}
- **OI Completeness:** ${oi_pct}%
- **Funding Completeness:** ${funding_pct}%

## Status
EOF

    # Collect all unique alerts from today's snapshots
    local all_alerts=()
    for snapshot in "${snapshots[@]}"; do
        if [ -f "$snapshot" ]; then
            local alerts=$(jq -r '.alerts[]' "$snapshot" 2>/dev/null)
            if [ -n "$alerts" ]; then
                while IFS= read -r alert; do
                    all_alerts+=("$alert")
                done <<< "$alerts"
            fi
        fi
    done

    # Remove duplicates and display
    if [ ${#all_alerts[@]} -gt 0 ]; then
        local unique_alerts=($(printf '%s\n' "${all_alerts[@]}" | sort -u))
        echo "### Alerts (${#unique_alerts[@]})" >> "$report_file"
        for alert in "${unique_alerts[@]}"; do
            echo "- $alert" >> "$report_file"
        done
    else
        echo "### Status" >> "$report_file"
        echo "✅ No alerts - system healthy" >> "$report_file"
    fi

    echo "" >> "$report_file"
    echo "---" >> "$report_file"
    echo "*Report generated: $(date -u +%Y-%m-%dT%H:%M:%S)*" >> "$report_file"

    success "Daily report saved: $report_file"
    cat "$report_file"

    return 0
}

# Main entry point
main() {
    case "${1:-}" in
        --report)
            if [ "$2" = "daily" ]; then
                generate_daily_report
            else
                error "Unknown report type: $2"
                exit 1
            fi
            ;;
        --alert)
            take_snapshot
            # Exit code reflects alert status (0 = healthy, 1 = alerts found)
            local snapshot_file=$(ls -t "$MONITORING_DIR"/snapshot_*.json 2>/dev/null | head -1)
            if [ -n "$snapshot_file" ] && command -v jq &> /dev/null; then
                local alert_count=$(jq -r '.alerts | length' "$snapshot_file")
                [ "$alert_count" -eq 0 ]
            fi
            ;;
        *)
            take_snapshot
            ;;
    esac
}

main "$@"
