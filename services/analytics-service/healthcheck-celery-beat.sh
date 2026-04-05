#!/bin/sh
# Health check for Celery Beat scheduler
# Celery Beat has no HTTP endpoint, so we check process status

# Check if celery beat process is running
pgrep -f "celery.*beat" > /dev/null || exit 1

# Optional: Check if beat schedule file exists and is recent
# (indicates that beat is actively scheduling tasks)
if [ -f "/tmp/celerybeat-schedule" ]; then
    # File exists, beat is working
    exit 0
fi

# If no schedule file but process is running, still healthy
# (schedule file may not exist yet on first start)
exit 0
