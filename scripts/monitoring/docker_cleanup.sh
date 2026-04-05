#!/bin/bash
# Docker Cleanup Automation Script
# Purpose: Weekly cleanup of old Docker resources
# Created by: Claude Code (Emergency Recovery 2025-11-18)
# Cron Schedule: Every Sunday 3 AM (0 3 * * 0)

LOG_FILE="/var/log/docker-cleanup.log"

# Ensure log file exists
touch "$LOG_FILE" 2>/dev/null || LOG_FILE="/tmp/docker-cleanup.log"

echo "========================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting weekly Docker cleanup" >> "$LOG_FILE"

# Get disk usage before
BEFORE=$(df -h / | tail -1 | awk '{print $5}')

# Cleanup (keeps resources from last 7 days)
echo "Removing old images and containers..." >> "$LOG_FILE"
docker system prune -f --filter "until=168h" >> "$LOG_FILE" 2>&1

# Cleanup dangling volumes (unused volumes)
echo "Removing dangling volumes..." >> "$LOG_FILE"
docker volume prune -f >> "$LOG_FILE" 2>&1

# Cleanup build cache
echo "Removing old build cache..." >> "$LOG_FILE"
docker builder prune -f --filter "until=168h" >> "$LOG_FILE" 2>&1

# Get disk usage after
AFTER=$(df -h / | tail -1 | awk '{print $5}')

echo "Disk usage: $BEFORE → $AFTER" >> "$LOG_FILE"
echo "Docker system df after cleanup:" >> "$LOG_FILE"
docker system df >> "$LOG_FILE" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleanup completed" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Console output
echo "✅ Docker cleanup completed"
echo "Disk usage: $BEFORE → $AFTER"
