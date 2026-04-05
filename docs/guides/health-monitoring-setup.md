# Health Monitoring Setup Guide

## Overview

Complete automated health monitoring system with real-time dashboard, alert notifications, and systemd integration.

**Implemented:** 2025-11-05
**Components:**
- Automated monitoring script (15-minute intervals)
- Real-time frontend dashboard
- Alert system (Webhook/Email/Log)
- Enhanced health checks for all services
- PID limits to prevent resource exhaustion

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Systemd Timer                        │
│               (every 15 minutes)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           scripts/monitor-resources.sh                  │
│  - Collects docker stats                                │
│  - Checks thresholds (PID, CPU, Memory)                 │
│  - Exports JSON to /tmp/docker-stats.json               │
│  - Writes alerts to /tmp/docker-monitor-alerts.log      │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────┐
│  Alert Delivery        │   │  Data Export               │
│  - Webhook (Slack)     │   │  - JSON stats file         │
│  - Email (SMTP)        │   │  - Alert log file          │
│  - File logging        │   │                            │
└────────────────────────┘   └───────────┬────────────────┘
                                         │
                                         ▼
                             ┌────────────────────────────┐
                             │  Analytics Service API     │
                             │  GET /api/v1/health/*      │
                             │  - containers              │
                             │  - summary                 │
                             │  - alerts                  │
                             └───────────┬────────────────┘
                                         │
                                         ▼
                             ┌────────────────────────────┐
                             │  Frontend Dashboard        │
                             │  /admin/health             │
                             │  - Auto-refresh (30s)      │
                             │  - Summary cards           │
                             │  - Container grid          │
                             │  - Alert timeline          │
                             └────────────────────────────┘
```

---

## Components

### 1. Monitoring Script

**Location:** `scripts/monitor-resources.sh`

**Features:**
- Collects metrics from all Docker containers
- Threshold-based alerting (configurable via `.env.monitoring`)
- JSON export for API consumption
- Alert logging with severity levels (INFO, WARNING, CRITICAL)
- Memory growth detection

**Default Thresholds:**
- PIDs: 100 processes
- Memory: 10% of total system memory
- CPU: 50% average usage
- Memory Growth: 10% increase per interval

**Execution:**
```bash
# Manual run (with alerts)
./scripts/monitor-resources.sh --alert-only

# View JSON output
cat /tmp/docker-stats.json | jq

# View alert log
tail -f /tmp/docker-monitor-alerts.log
```

### 2. Systemd Integration

**Files:**
- `/etc/systemd/system/docker-monitor.service` - Service definition
- `/etc/systemd/system/docker-monitor.timer` - Scheduling (15-minute intervals)
- `.env.monitoring` - Configuration (alert method, thresholds, credentials)

**Management:**
```bash
# Check timer status
systemctl status docker-monitor.timer

# View recent runs
journalctl -u docker-monitor.service -n 50

# Trigger manual run
sudo systemctl start docker-monitor.service

# Restart timer (after config changes)
sudo systemctl restart docker-monitor.timer
```

**Timer Schedule:**
- First run: 5 minutes after boot
- Interval: Every 15 minutes
- Persistent: Yes (catches up if system was offline)

### 3. Alert Configuration

**File:** `.env.monitoring`

**Alert Methods:**
- `log` - Write to `/tmp/docker-monitor-alerts.log`
- `email` - Send via SMTP
- `webhook` - POST to Slack/Discord/custom endpoint
- `all` - Enable all methods

**Webhook Examples:**

Slack:
```bash
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Discord:
```bash
WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
```

**Email Configuration:**
```bash
EMAIL_TO=admin@example.com
EMAIL_FROM=docker-monitor@news-microservices.local
```

### 4. Enhanced Health Checks

**Location:** `services/*/Dockerfile.dev`, `services/*/healthcheck.sh`

**Pattern:**
```dockerfile
# Copy health check script
COPY healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# Enhanced health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh
```

**Health Check Script:**
```bash
#!/bin/sh
PORT=${PORT:-8000}

# Step 1: Validate critical imports
python3 -c "from app.main import app" 2>/dev/null || exit 1

# Step 2: Check HTTP endpoint
curl -f "http://localhost:${PORT}/health" || exit 1

exit 0
```

**Services with Enhanced Health Checks:**
1. auth-service (8100)
2. notification-service (8105)
3. feed-service (8101)
4. content-analysis-v2 (8114)
5. research-service (8103)
6. osint-service (8104)
7. analytics-service (8107)
8. search-service (8106)
9. scheduler-service (8108)
10. fmp-service (8109)
11. scraping-service
12. knowledge-graph-service (8111)
13. llm-orchestrator-service (8113)

### 5. PID Limits

**Location:** `docker-compose.yml`

**Standard Services:** `pids_limit: 512`
**Worker Services:** `pids_limit: 1024`

**Workers with Higher Limits:**
- analytics-celery-worker
- content-analysis-v2 (3 replicas)
- feed-service-celery-worker
- search-celery-worker

**Purpose:** Prevent PID exhaustion from runaway processes (e.g., infinite reload loops)

### 6. Backend API

**Service:** analytics-service
**Base URL:** `http://localhost:8107/api/v1/health`

**Endpoints:**

#### GET /containers
Returns real-time metrics for all Docker containers.

**Response:**
```json
[
  {
    "name": "news-notification-service",
    "status": "running",
    "health": "healthy",
    "cpu_percent": 0.23,
    "memory_percent": 0.63,
    "memory_usage": "126.4MiB / 19.51GiB",
    "pids": 9,
    "timestamp": "2025-11-05T21:13:20Z"
  }
]
```

#### GET /alerts?limit=20
Returns recent alerts from monitoring log.

**Response:**
```json
[
  {
    "timestamp": "2025-11-05 20:50:57 UTC",
    "severity": "WARNING",
    "service": "neo4j",
    "message": "HIGH_MEMORY: 9.84% (threshold: 10.0%)"
  }
]
```

#### GET /summary
Returns aggregated health metrics.

**Response:**
```json
{
  "total_containers": 29,
  "healthy": 26,
  "unhealthy": 2,
  "no_healthcheck": 1,
  "running": 29,
  "avg_cpu_percent": 1.85,
  "avg_memory_percent": 1.27,
  "total_pids": 442,
  "recent_critical_alerts": 0,
  "recent_warning_alerts": 3,
  "timestamp": "2025-11-05T21:14:00.000000"
}
```

**Volume Mount:** `- /tmp:/host_tmp:ro` (read-only access to stats and alerts)

### 7. Frontend Dashboard

**Route:** `/admin/health`
**Component:** `frontend/src/components/HealthDashboard.tsx`

**Features:**
- **Summary Cards**: Total containers, healthy count, avg CPU, avg memory
- **Container Grid**: Individual service metrics with color-coded health status
  - Green: healthy
  - Red: unhealthy
  - Gray: no health check
- **Alert Timeline**: Recent alerts with severity badges
- **Auto-refresh**: Toggle for 30-second polling (default: ON)
- **Responsive**: 1/2/3 column grid based on screen size

**Access:**
1. Login to frontend: `http://localhost:3000` (or via LAN: `http://<server-ip>:3000`)
2. Navigate to: Admin → System Health
3. Or direct: `http://localhost:3000/admin/health`

**Network Access:**
- **Local:** `http://localhost:3000/admin/health`
- **LAN:** `http://localhost:3000/admin/health` (replace with your server IP)
- API calls use dynamic hostname (`window.location.hostname:8107`)
- Works automatically for both localhost and remote access

**UI Libraries:**
- React 19
- Tailwind CSS
- Lucide Icons
- Vite HMR (hot module replacement)

---

## Quick Start

### First-Time Setup

1. **Verify monitoring script:**
   ```bash
   cd /home/cytrex/news-microservices
   ./scripts/monitor-resources.sh --alert-only
   ```

2. **Check systemd timer:**
   ```bash
   systemctl status docker-monitor.timer
   journalctl -u docker-monitor.service -n 10
   ```

3. **Verify backend API:**
   ```bash
   curl http://localhost:8107/api/v1/health/summary | jq
   ```

4. **Access frontend dashboard:**
   - Navigate to: http://localhost:3000/admin/health
   - Should see all 29 containers with real-time metrics

### Configure Alerts

1. **Edit configuration:**
   ```bash
   nano .env.monitoring
   ```

2. **Set alert method:**
   ```bash
   ALERT_METHOD=webhook  # or: log, email, all
   WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
   ```

3. **Adjust thresholds (optional):**
   ```bash
   PID_THRESHOLD=100
   MEMORY_PERCENT_THRESHOLD=10.0
   CPU_PERCENT_THRESHOLD=50.0
   ```

4. **Restart timer:**
   ```bash
   sudo systemctl restart docker-monitor.timer
   ```

5. **Test alert delivery:**
   ```bash
   ./scripts/monitor-resources.sh --alert-only
   # Check Slack/Discord/Email for test message
   ```

---

## Troubleshooting

### Monitoring Script Issues

**Problem:** Script fails with "docker: command not found"
```bash
# Solution: Ensure Docker is in PATH
which docker
# Should output: /usr/bin/docker
```

**Problem:** Permission denied on /tmp/docker-stats.json
```bash
# Solution: Check file ownership
ls -la /tmp/docker-stats.json
# Should be owned by your user (cytrex)
```

**Problem:** No alerts generated
```bash
# Solution: Check threshold configuration
cat .env.monitoring
# Verify thresholds aren't too high

# Force alert by lowering threshold temporarily
PID_THRESHOLD=10 ./scripts/monitor-resources.sh --alert-only
```

### Backend API Issues

**Problem:** 404 Not Found on /api/v1/health endpoints
```bash
# Solution: Verify analytics-service is running
docker ps | grep analytics-service

# Check router registration
docker logs news-analytics-service | grep health
```

**Problem:** Empty containers list []
```bash
# Solution: Check if JSON file exists and is readable
ls -la /tmp/docker-stats.json
cat /tmp/docker-stats.json | jq

# Verify volume mount in docker-compose.yml
docker inspect news-analytics-service | grep -A5 Mounts
```

**Problem:** CORS error in frontend
```bash
# Solution: Verify CORS settings in analytics-service
# File: services/analytics-service/app/main.py
# Should allow: http://localhost:3000
```

### Frontend Dashboard Issues

**Problem:** Dashboard shows loading spinner indefinitely
```bash
# Check browser console for errors
# Likely causes:
# 1. Backend API not responding (check 8107)
# 2. CORS issue (check network tab)
# 3. Authentication issue (re-login)
```

**Problem:** Dashboard shows stale data
```bash
# Solution: Verify auto-refresh is enabled
# Check "Auto-refresh ON" button in top-right
# Ensure fetchData() is called every 30 seconds
```

**Problem:** Dashboard empty when accessing via LAN (e.g., localhost:3000)
```bash
# Symptom: Only header/summary visible, no container data
# Cause: Dashboard was making API calls to localhost:8107 instead of server IP

# Solution: Already fixed (2025-11-05)
# Dashboard now uses dynamic hostname: window.location.hostname:8107
# Works automatically for both localhost and LAN access

# Verify fix:
# 1. Access via LAN: http://<server-ip>:3000/admin/health
# 2. Check browser console (F12) → Network tab
# 3. API calls should go to: http://<server-ip>:8107/api/v1/health/*
# 4. If still showing localhost, clear browser cache and reload
```

**Problem:** "N/A" health status for all containers
```bash
# Solution: Health checks may not be configured
# Check: docker inspect <container> | grep Healthcheck
# Or: docker ps --format "{{.Names}}\t{{.Status}}"
```

**Problem:** Celery Beat services showing "unhealthy" with high FailingStreak
```bash
# Symptom: news-feed-service-celery-beat or news-analytics-celery-beat marked unhealthy
# Example: FailingStreak: 9,185+ (thousands of failed health checks)

# Root Cause: Celery Beat is a TASK SCHEDULER, not an HTTP server
# - No HTTP endpoint for health checks
# - HTTP-based health check (curl localhost:8000) always fails
# - Services are ACTUALLY RUNNING and sending tasks correctly

# Solution: Disable health check for Celery Beat services
# File: docker-compose.yml
healthcheck:
  disable: true  # Celery Beat has no HTTP endpoint

# Verify service is actually working:
docker logs news-feed-service-celery-beat --tail 20
# Should show: [INFO] Scheduler: Sending due task process-outbox (every 5 seconds)

# Alternative (process-based health check):
# Create healthcheck-celery-beat.sh that checks if process is running
# Note: Not recommended - services work fine without health check
```

### Systemd Timer Issues

**Problem:** Timer shows "inactive (dead)"
```bash
# Solution: Enable and start timer
sudo systemctl enable docker-monitor.timer
sudo systemctl start docker-monitor.timer
```

**Problem:** Timer runs but service fails
```bash
# Check service logs
journalctl -u docker-monitor.service -n 50

# Common issues:
# 1. Missing .env.monitoring file
# 2. Script not executable: chmod +x scripts/monitor-resources.sh
# 3. Wrong working directory in service file
```

**Problem:** Timer doesn't run every 15 minutes
```bash
# Check timer configuration
systemctl cat docker-monitor.timer

# Verify OnUnitActiveSec=15min is set
# Check last trigger time
systemctl status docker-monitor.timer
```

---

## Maintenance

### Weekly Tasks

1. **Review alerts:**
   ```bash
   # Check for patterns
   grep CRITICAL /tmp/docker-monitor-alerts.log | tail -20
   ```

2. **Verify all services healthy:**
   ```bash
   curl -s http://localhost:8107/api/v1/health/summary | \
     jq '{healthy: .healthy, unhealthy: .unhealthy}'
   ```

3. **Check disk usage:**
   ```bash
   du -sh /tmp/docker-monitor-alerts.log
   # If > 10MB, consider rotating logs
   ```

### Monthly Tasks

1. **Review threshold effectiveness:**
   - Are you getting too many/few alerts?
   - Adjust `.env.monitoring` thresholds accordingly

2. **Test alert delivery:**
   ```bash
   # Temporarily lower thresholds to trigger alerts
   PID_THRESHOLD=5 ./scripts/monitor-resources.sh --alert-only
   ```

3. **Update documentation:**
   - Document any new services or configuration changes

### Log Rotation

**Automatic Rotation (Recommended):**

Create `/etc/logrotate.d/docker-monitor`:
```
/tmp/docker-monitor-alerts.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
```

**Manual Rotation:**
```bash
# Archive old logs
mv /tmp/docker-monitor-alerts.log /tmp/docker-monitor-alerts.log.$(date +%Y%m%d)
gzip /tmp/docker-monitor-alerts.log.$(date +%Y%m%d)

# Create new log file
touch /tmp/docker-monitor-alerts.log
```

---

## Testing

### Integration Test Checklist

- [ ] Systemd timer is active and enabled
- [ ] Monitoring script runs successfully
- [ ] JSON stats file is updated every 15 minutes
- [ ] Alert log contains recent entries
- [ ] Backend API returns valid data
- [ ] Frontend dashboard displays all containers
- [ ] Auto-refresh updates data every 30 seconds
- [ ] Health checks pass for all services
- [ ] PID limits are enforced

### Manual Test Commands

```bash
# 1. Test monitoring script
./scripts/monitor-resources.sh --alert-only
echo "Exit code: $?"  # Should be 0

# 2. Verify JSON export
cat /tmp/docker-stats.json | jq length
# Should output: 29 (number of containers)

# 3. Test backend API
curl http://localhost:8107/api/v1/health/containers | jq length
curl http://localhost:8107/api/v1/health/summary | jq .total_containers
curl http://localhost:8107/api/v1/health/alerts | jq length

# 4. Check systemd timer
systemctl list-timers docker-monitor.timer

# 5. Verify health checks
docker ps --format "{{.Names}}\t{{.Status}}" | grep healthy

# 6. Test PID limits
docker inspect news-analytics-service | jq '.[0].HostConfig.PidsLimit'
# Should output: 512
```

---

## Performance Impact

**Resource Usage:**
- Monitoring script: ~0.1% CPU, 10MB RAM (during execution)
- Backend API: +5MB RAM in analytics-service
- Frontend dashboard: +200KB bundle size
- JSON stats file: ~15KB (29 containers)
- Alert log: ~1KB per alert

**Network Impact:**
- API polling: ~30 requests/minute (with auto-refresh enabled)
- Payload size: ~15KB per request
- Total bandwidth: ~450KB/minute = ~27MB/hour

**Storage:**
- Alert log: ~50KB/day (assuming 50 alerts)
- Monthly: ~1.5MB
- With 7-day rotation: ~350KB total

---

## Best Practices

1. **Threshold Tuning:**
   - Start with default thresholds
   - Monitor for 1 week
   - Adjust based on false positives/negatives

2. **Alert Fatigue:**
   - Don't set thresholds too low
   - Use WARNING for non-critical issues
   - Reserve CRITICAL for actual outages

3. **Dashboard Usage:**
   - Use auto-refresh during active monitoring
   - Disable auto-refresh when investigating specific issues
   - Check dashboard daily for system health overview

4. **Health Check Best Practices:**
   - Keep checks fast (< 1 second)
   - Test critical functionality only
   - Don't depend on external services

5. **PID Limits:**
   - Keep standard limit at 512
   - Increase to 1024 only for known workers
   - Monitor PID usage in dashboard

---

## References

- **Monitoring Script:** `scripts/monitor-resources.sh`
- **Backend API:** `services/analytics-service/app/api/routes/health.py`
- **Frontend Component:** `frontend/src/components/HealthDashboard.tsx`
- **Configuration:** `.env.monitoring`
- **Systemd Service:** `/etc/systemd/system/docker-monitor.service`
- **Systemd Timer:** `/etc/systemd/system/docker-monitor.timer`

**Related Documentation:**
- Docker commands: See `docker-compose.yml` for service definitions

---

## See Also

- **[CLAUDE.backend.md - Health Monitoring](../../CLAUDE.backend.md#-health-monitoring--alerting)** - Quick reference and dashboard access
- **[Healthcheck Requirements Guide](./healthcheck-requirements.md)** - Service-level healthcheck implementation (715 lines)
  - Dockerfile requirements and curl installation
  - FastAPI health endpoint patterns
  - Verification and testing procedures
  - Best practices (DO/DON'T)

---

**Last Updated:** 2025-11-05
**Maintainer:** Claude Code
**Status:** Production Ready
