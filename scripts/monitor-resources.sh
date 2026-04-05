#!/bin/bash
# Resource Monitor Script
# Monitors Docker containers for abnormal resource usage
# Can be run via cron or systemd timer
# Usage: ./scripts/monitor-resources.sh [--alert-only] [--json]

set -e

# Thresholds (can be overridden via environment)
PID_THRESHOLD=${PID_THRESHOLD:-100}
MEMORY_PERCENT_THRESHOLD=${MEMORY_PERCENT_THRESHOLD:-10.0}
CPU_PERCENT_THRESHOLD=${CPU_PERCENT_THRESHOLD:-50.0}
MEMORY_GROWTH_THRESHOLD=${MEMORY_GROWTH_THRESHOLD:-10.0}  # % growth per check

# Alert methods
ALERT_METHOD=${ALERT_METHOD:-"log"}  # log, email, webhook, all
LOG_FILE=${LOG_FILE:-"/var/log/docker-monitor/alerts.log"}
WEBHOOK_URL=${WEBHOOK_URL:-""}
EMAIL_TO=${EMAIL_TO:-"admin@example.com"}

# Output format
OUTPUT_FORMAT="human"
ALERT_ONLY=false
JSON_OUTPUT_FILE="/tmp/docker-stats.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --alert-only)
            ALERT_ONLY=true
            shift
            ;;
        --json)
            OUTPUT_FORMAT="json"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Colors (only for human output)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# State file for tracking memory growth
STATE_FILE="/tmp/docker-resource-monitor.state"

# Function to send alert
send_alert() {
    local severity=$1
    local service=$2
    local message=$3

    timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

    case $ALERT_METHOD in
        log)
            # Ensure log directory exists
            mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
            echo "[$timestamp] ALERT [$severity] $service: $message" >> "$LOG_FILE"
            ;;
        email)
            if command -v mail &> /dev/null; then
                echo "[$timestamp] ALERT [$severity] $service: $message" | mail -s "Docker Alert: $service" "$EMAIL_TO"
            else
                echo "[$timestamp] WARNING: mail command not found, logging instead" >> "$LOG_FILE"
                echo "[$timestamp] ALERT [$severity] $service: $message" >> "$LOG_FILE"
            fi
            ;;
        webhook)
            if [ -n "$WEBHOOK_URL" ]; then
                curl -X POST "$WEBHOOK_URL" \
                    -H 'Content-Type: application/json' \
                    -d "{\"text\":\"🚨 [$severity] $service\\n$message\",\"timestamp\":\"$timestamp\"}" \
                    2>/dev/null || echo "[$timestamp] WARNING: Webhook delivery failed" >> "$LOG_FILE"
            else
                echo "[$timestamp] WARNING: WEBHOOK_URL not set, logging instead" >> "$LOG_FILE"
                echo "[$timestamp] ALERT [$severity] $service: $message" >> "$LOG_FILE"
            fi
            ;;
        all)
            send_alert log "$service" "$message"
            send_alert email "$service" "$message"
            send_alert webhook "$service" "$message"
            ;;
    esac
}

# Function to check single container
check_container() {
    local container=$1

    # Get stats
    stats=$(docker stats --no-stream --format "{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}|{{.MemUsage}}|{{.PIDs}}" "$container" 2>/dev/null || echo "")

    if [ -z "$stats" ]; then
        return 0
    fi

    IFS='|' read -r name cpu_raw mem_percent_raw mem_usage pids <<< "$stats"

    # Remove % signs
    cpu_percent=$(echo "$cpu_raw" | sed 's/%//')
    mem_percent=$(echo "$mem_percent_raw" | sed 's/%//')

    # Parse memory usage (e.g., "127.7MiB / 19.51GiB")
    mem_used=$(echo "$mem_usage" | awk '{print $1}')
    mem_unit=$(echo "$mem_used" | sed 's/[0-9.]//g')
    mem_value=$(echo "$mem_used" | sed 's/[^0-9.]//g')

    # Convert to MB for comparison
    case $mem_unit in
        GiB) mem_mb=$(echo "$mem_value * 1024" | bc) ;;
        MiB) mem_mb=$mem_value ;;
        KiB) mem_mb=$(echo "$mem_value / 1024" | bc) ;;
        *) mem_mb=0 ;;
    esac

    # Check thresholds
    alerts=()

    # PID check
    if [ "$pids" -gt "$PID_THRESHOLD" ]; then
        alerts+=("HIGH_PID_COUNT: $pids (threshold: $PID_THRESHOLD)")
    fi

    # Memory % check
    if (( $(echo "$mem_percent > $MEMORY_PERCENT_THRESHOLD" | bc -l) )); then
        alerts+=("HIGH_MEMORY: ${mem_percent}% (threshold: ${MEMORY_PERCENT_THRESHOLD}%)")
    fi

    # CPU check
    if (( $(echo "$cpu_percent > $CPU_PERCENT_THRESHOLD" | bc -l) )); then
        alerts+=("HIGH_CPU: ${cpu_percent}% (threshold: ${CPU_PERCENT_THRESHOLD}%)")
    fi

    # Memory growth check (compare with previous state)
    if [ -f "$STATE_FILE" ]; then
        prev_mem=$(grep "^${name}|" "$STATE_FILE" | cut -d'|' -f2 || echo "0")
        if [ -n "$prev_mem" ] && [ "$prev_mem" != "0" ]; then
            growth=$(echo "scale=2; (($mem_mb - $prev_mem) / $prev_mem) * 100" | bc)
            if (( $(echo "$growth > $MEMORY_GROWTH_THRESHOLD" | bc -l) )); then
                alerts+=("MEMORY_GROWTH: +${growth}% since last check")
            fi
        fi
    fi

    # Update state
    grep -v "^${name}|" "$STATE_FILE" 2>/dev/null > "${STATE_FILE}.tmp" || true
    echo "${name}|${mem_mb}" >> "${STATE_FILE}.tmp"
    mv "${STATE_FILE}.tmp" "$STATE_FILE"

    # Output
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        if [ ${#alerts[@]} -gt 0 ] || [ "$ALERT_ONLY" = false ]; then
            echo "{"
            echo "  \"container\": \"$name\","
            echo "  \"cpu_percent\": $cpu_percent,"
            echo "  \"memory_percent\": $mem_percent,"
            echo "  \"memory_mb\": $mem_mb,"
            echo "  \"pids\": $pids,"
            echo "  \"alerts\": ["
            for i in "${!alerts[@]}"; do
                echo -n "    \"${alerts[$i]}\""
                [ $i -lt $((${#alerts[@]} - 1)) ] && echo "," || echo ""
            done
            echo "  ]"
            echo "}"
        fi
    else
        if [ ${#alerts[@]} -gt 0 ]; then
            echo -e "${RED}⚠️  ALERT: $name${NC}"
            echo "   CPU: $cpu_percent% | Memory: $mem_percent% ($mem_usage) | PIDs: $pids"
            for alert in "${alerts[@]}"; do
                echo -e "   ${YELLOW}→ $alert${NC}"
                send_alert "WARNING" "$name" "$alert"
            done
            echo ""
        elif [ "$ALERT_ONLY" = false ]; then
            echo -e "${GREEN}✓ $name${NC}"
            echo "   CPU: $cpu_percent% | Memory: $mem_percent% ($mem_usage) | PIDs: $pids"
        fi
    fi
}

# Main monitoring
if [ "$OUTPUT_FORMAT" = "human" ] && [ "$ALERT_ONLY" = false ]; then
    echo "🔍 Docker Resource Monitor"
    echo "=========================="
    echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo ""
    echo "Thresholds:"
    echo "  PIDs: > $PID_THRESHOLD"
    echo "  Memory: > ${MEMORY_PERCENT_THRESHOLD}%"
    echo "  CPU: > ${CPU_PERCENT_THRESHOLD}%"
    echo "  Memory Growth: > ${MEMORY_GROWTH_THRESHOLD}%"
    echo ""
fi

# Check all running containers
containers=$(docker ps --format '{{.Names}}')

for container in $containers; do
    check_container "$container"
done

if [ "$OUTPUT_FORMAT" = "human" ] && [ "$ALERT_ONLY" = false ]; then
    echo ""
    echo "─────────────────────────────────────"
    echo "✅ Monitoring check complete"
    echo ""
    echo "💡 To receive alerts, configure ALERT_METHOD environment variable:"
    echo "   export ALERT_METHOD=webhook"
    echo "   export WEBHOOK_URL=https://your-webhook-url"
fi

# Function to export JSON stats
export_json_stats() {
    local containers=$(docker ps --format "{{.Names}}")
    echo "[" > "$JSON_OUTPUT_FILE"

    first=true
    for container in $containers; do
        stats=$(docker stats --no-stream --format "{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}|{{.MemUsage}}|{{.PIDs}}" "$container" 2>/dev/null || echo "")

        if [ -n "$stats" ]; then
            IFS='|' read -r name cpu mem memusage pids <<< "$stats"

            # Get health status
            health=$(docker inspect "$container" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null || echo "none")
            status=$(docker inspect "$container" --format '{{.State.Status}}' 2>/dev/null || echo "unknown")

            [ "$first" = false ] && echo "," >> "$JSON_OUTPUT_FILE"
            first=false

            cat >> "$JSON_OUTPUT_FILE" << JSONEOF
  {
    "name": "$name",
    "status": "$status",
    "health": "$health",
    "cpu_percent": ${cpu%\%},
    "memory_percent": ${mem%\%},
    "memory_usage": "$memusage",
    "pids": $pids,
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  }
JSONEOF
        fi
    done

    echo "]" >> "$JSON_OUTPUT_FILE"
}

# Always export JSON stats for dashboard
export_json_stats
