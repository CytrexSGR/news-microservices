#!/bin/bash
# Disk Usage Monitoring Script
# Purpose: Alert when disk usage exceeds threshold
# Created by: Claude Code (Emergency Recovery 2025-11-18)
# Cron Schedule: Every 6 hours (0 */6 * * *)

THRESHOLD=80
EMAIL="andreas@test.com"
LOG_FILE="/var/log/disk-monitor.log"

# Get current disk usage percentage
USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_INFO=$(df -h / | tail -1)

# Ensure log file exists
touch "$LOG_FILE" 2>/dev/null || LOG_FILE="/tmp/disk-monitor.log"

# Log check
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Disk usage: ${USAGE}%" >> "$LOG_FILE"

# Alert if threshold exceeded
if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ WARNING: Disk usage ${USAGE}% exceeds threshold ${THRESHOLD}%" >> "$LOG_FILE"

    # Console output for cron notification
    echo "⚠️ DISK USAGE ALERT: ${USAGE}% (threshold: ${THRESHOLD}%)"
    echo "Disk: $DISK_INFO"

    # Log Docker stats for analysis
    echo "Docker System DF:" >> "$LOG_FILE"
    docker system df >> "$LOG_FILE" 2>&1

    # Send alert (if mail is configured)
    if command -v mail &> /dev/null; then
        echo "Disk usage on $(hostname) has reached ${USAGE}%

Disk Information:
$DISK_INFO

Docker Usage:
$(docker system df 2>/dev/null || echo 'Docker not available')

Threshold: ${THRESHOLD}%
Time: $(date)

Action Required:
- Run: docker system prune -f
- Check: df -h /
- Monitor: tail -f $LOG_FILE
" | mail -s "⚠️ Disk Usage Alert: ${USAGE}% on $(hostname)" "$EMAIL"
    fi

    exit 1
fi

echo "✅ Disk usage OK: ${USAGE}%" | tee -a "$LOG_FILE"
exit 0
