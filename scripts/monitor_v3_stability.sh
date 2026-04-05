#!/bin/bash
# V3 Stability Monitoring Script
# Usage: ./scripts/monitor_v3_stability.sh [duration_hours]
#
# Monitors content-analysis-v3 service for:
# - Container health status
# - Error rates in logs
# - RabbitMQ queue backlog
# - Memory/CPU usage
# - Event publishing success rate

DURATION_HOURS=${1:-24}
CHECK_INTERVAL_SECONDS=300  # 5 minutes
LOG_FILE="/tmp/v3_stability_monitor_$(date +%Y%m%d_%H%M%S).log"

echo "=== V3 Stability Monitor Started ===" | tee -a "$LOG_FILE"
echo "Duration: ${DURATION_HOURS}h" | tee -a "$LOG_FILE"
echo "Check interval: ${CHECK_INTERVAL_SECONDS}s" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

END_TIME=$(($(date +%s) + DURATION_HOURS * 3600))
CHECK_COUNT=0

while [ $(date +%s) -lt $END_TIME ]; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo "--- Check #$CHECK_COUNT at $TIMESTAMP ---" | tee -a "$LOG_FILE"

    # 1. Container health status
    CONTAINER_STATUS=$(docker inspect news-content-analysis-v3-api --format '{{.State.Health.Status}}' 2>/dev/null || echo "not running")
    echo "Container health: $CONTAINER_STATUS" | tee -a "$LOG_FILE"

    if [ "$CONTAINER_STATUS" != "healthy" ]; then
        echo "❌ WARNING: Container not healthy!" | tee -a "$LOG_FILE"
    fi

    # 2. Error count in last 5 minutes
    ERROR_COUNT=$(docker logs news-content-analysis-v3-api --since 5m 2>&1 | grep -c "ERROR" || echo 0)
    WARNING_COUNT=$(docker logs news-content-analysis-v3-api --since 5m 2>&1 | grep -c "WARNING" || echo 0)
    echo "Errors (last 5min): $ERROR_COUNT" | tee -a "$LOG_FILE"
    echo "Warnings (last 5min): $WARNING_COUNT" | tee -a "$LOG_FILE"

    if [ "$ERROR_COUNT" -gt 10 ]; then
        echo "❌ WARNING: High error rate detected!" | tee -a "$LOG_FILE"
    fi

    # 3. RabbitMQ queue status
    QUEUE_STATS=$(curl -s -u guest:guest http://localhost:15672/api/queues/%2F/analysis_results_queue | jq '{messages, messages_ready, consumers}' 2>/dev/null || echo "{}")
    echo "RabbitMQ queue: $QUEUE_STATS" | tee -a "$LOG_FILE"

    QUEUE_BACKLOG=$(echo "$QUEUE_STATS" | jq '.messages_ready // 0')
    if [ "$QUEUE_BACKLOG" -gt 100 ]; then
        echo "❌ WARNING: Queue backlog detected ($QUEUE_BACKLOG messages)!" | tee -a "$LOG_FILE"
    fi

    # 4. Container resource usage
    RESOURCE_STATS=$(docker stats news-content-analysis-v3-api --no-stream --format "CPU: {{.CPUPerc}}, Memory: {{.MemUsage}}" 2>/dev/null || echo "N/A")
    echo "Resources: $RESOURCE_STATS" | tee -a "$LOG_FILE"

    # 5. Event publishing success (check last 50 log lines)
    PUBLISHED_COUNT=$(docker logs news-content-analysis-v3-api --tail 50 2>&1 | grep -c "✓ Published event" || echo 0)
    FAILED_PUBLISH=$(docker logs news-content-analysis-v3-api --tail 50 2>&1 | grep -c "Failed to publish event" || echo 0)
    echo "Events published (last 50 logs): $PUBLISHED_COUNT" | tee -a "$LOG_FILE"
    echo "Events failed (last 50 logs): $FAILED_PUBLISH" | tee -a "$LOG_FILE"

    if [ "$FAILED_PUBLISH" -gt 5 ]; then
        echo "❌ WARNING: High event publish failure rate!" | tee -a "$LOG_FILE"
    fi

    echo "" | tee -a "$LOG_FILE"

    # Sleep until next check
    REMAINING_TIME=$((END_TIME - $(date +%s)))
    if [ $REMAINING_TIME -gt $CHECK_INTERVAL_SECONDS ]; then
        sleep $CHECK_INTERVAL_SECONDS
    else
        break
    fi
done

echo "=== V3 Stability Monitor Completed ===" | tee -a "$LOG_FILE"
echo "Total checks: $CHECK_COUNT" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"

# Generate summary report
echo "" | tee -a "$LOG_FILE"
echo "=== Summary ===" | tee -a "$LOG_FILE"
TOTAL_ERRORS=$(grep "Errors (last 5min):" "$LOG_FILE" | awk '{sum += $4} END {print sum}')
TOTAL_WARNINGS=$(grep "Warnings (last 5min):" "$LOG_FILE" | awk '{sum += $4} END {print sum}')
CRITICAL_ISSUES=$(grep -c "❌ WARNING" "$LOG_FILE" || echo 0)

echo "Total errors detected: $TOTAL_ERRORS" | tee -a "$LOG_FILE"
echo "Total warnings detected: $TOTAL_WARNINGS" | tee -a "$LOG_FILE"
echo "Critical issues: $CRITICAL_ISSUES" | tee -a "$LOG_FILE"

if [ "$CRITICAL_ISSUES" -eq 0 ]; then
    echo "✅ V3 service appears stable!" | tee -a "$LOG_FILE"
else
    echo "⚠️  V3 service had issues during monitoring period" | tee -a "$LOG_FILE"
fi
