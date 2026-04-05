# Monitoring Setup Guide

This guide explains how to set up resource monitoring and alerts for the News Microservices platform.

**Created:** 2025-11-05
**Purpose:** Prevent resource leaks like Incident #10 (notification-service memory leak)

---

## Quick Start

### 1. Run Manual Check

```bash
# Check all services
./scripts/monitor-resources.sh

# Only show alerts
./scripts/monitor-resources.sh --alert-only

# JSON output (for log parsing)
./scripts/monitor-resources.sh --json
```

### 2. Validate Health Checks

```bash
# Check all services
./scripts/healthcheck-validator.sh

# Check specific service
./scripts/healthcheck-validator.sh notification-service
```

---

## Automated Monitoring

### Option 1: Systemd Timer (Recommended)

**Create timer unit:**

```bash
# /etc/systemd/system/docker-monitor.timer
[Unit]
Description=Docker Resource Monitor Timer
Requires=docker-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Unit=docker-monitor.service

[Install]
WantedBy=timers.target
```

**Create service unit:**

```bash
# /etc/systemd/system/docker-monitor.service
[Unit]
Description=Docker Resource Monitor
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/home/cytrex/news-microservices
ExecStart=/home/cytrex/news-microservices/scripts/monitor-resources.sh --alert-only
StandardOutput=journal
StandardError=journal
Environment="ALERT_METHOD=log"

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable docker-monitor.timer
sudo systemctl start docker-monitor.timer

# Check status
sudo systemctl status docker-monitor.timer
sudo systemctl list-timers docker-monitor
```

### Option 2: Cron Job

```bash
# Edit crontab
crontab -e

# Run every 15 minutes
*/15 * * * * cd /home/cytrex/news-microservices && ./scripts/monitor-resources.sh --alert-only >> /var/log/docker-monitor.log 2>&1
```

---

## Alert Thresholds

Default thresholds in `scripts/monitor-resources.sh`:

| Metric | Threshold | Action |
|--------|-----------|--------|
| PIDs | > 100 | Alert (normal: < 50) |
| Memory % | > 10% | Alert (per service) |
| CPU % | > 50% | Alert (sustained high usage) |
| Memory Growth | > 10% per check | Alert (possible leak) |

**Customizing thresholds:**

```bash
# Edit scripts/monitor-resources.sh
PID_THRESHOLD=150
MEMORY_PERCENT_THRESHOLD=15.0
CPU_PERCENT_THRESHOLD=60.0
MEMORY_GROWTH_THRESHOLD=15.0
```

---

## Alert Methods

### 1. Log Files (Default)

Alerts written to `/var/log/docker-monitor.log`

```bash
# View alerts
tail -f /var/log/docker-monitor.log

# Search for specific service
grep "notification-service" /var/log/docker-monitor.log
```

### 2. Email Alerts

**Setup:**

```bash
# Install mail client
sudo apt install mailutils

# Configure SMTP (example: Gmail)
echo "set smtp=smtp://smtp.gmail.com:587" >> ~/.mailrc
echo "set smtp-use-starttls" >> ~/.mailrc
echo "set smtp-auth=login" >> ~/.mailrc
echo "set smtp-auth-user=your-email@gmail.com" >> ~/.mailrc
echo "set smtp-auth-password=your-app-password" >> ~/.mailrc

# Enable email alerts
export ALERT_METHOD=email
./scripts/monitor-resources.sh
```

### 3. Webhook Alerts (Slack, Discord, etc.)

**Slack webhook:**

```bash
# Get webhook URL from Slack
# https://api.slack.com/messaging/webhooks

export ALERT_METHOD=webhook
export WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

./scripts/monitor-resources.sh --alert-only
```

**Discord webhook:**

```bash
# Get webhook URL from Discord Server Settings -> Integrations

export ALERT_METHOD=webhook
export WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"

./scripts/monitor-resources.sh --alert-only
```

### 4. All Methods

```bash
export ALERT_METHOD=all
export WEBHOOK_URL="https://your-webhook-url"

./scripts/monitor-resources.sh
```

---

## CI/CD Integration

### GitHub Actions

Volume mount validation runs automatically on:
- Pull requests changing `docker-compose.yml` or `requirements.txt`
- Pushes to `master`, `main`, or `feature/**` branches

**Workflow:** `.github/workflows/validate-volume-mounts.yml`

**Manual trigger:**

```bash
# Run validation locally
./.github/workflows/validate-volume-mounts.yml
```

---

## Health Check Enhancements

### Enhanced Dockerfile Health Checks

Services now validate imports before checking HTTP endpoints:

```dockerfile
# Dockerfile.dev
HEALTHCHECK CMD python3 -c "from app.main import app" && curl -f http://localhost:8000/health
```

**Benefits:**
- Catches import errors immediately
- Prevents infinite reload loops
- Fails fast on missing dependencies

### Testing Health Checks

```bash
# Test single service
docker exec news-notification-service /usr/local/bin/healthcheck.sh
echo $?  # 0 = healthy, 1 = unhealthy

# Test all services
for service in $(docker ps --format '{{.Names}}'); do
    echo -n "Testing $service: "
    if docker exec "$service" /usr/local/bin/healthcheck.sh 2>/dev/null; then
        echo "✓ Healthy"
    else
        echo "✗ Unhealthy"
    fi
done
```

---

## Monitoring Best Practices

### 1. Regular Checks

- **Every 15 minutes:** Automated resource monitoring
- **Daily:** Manual review of alerts
- **Weekly:** Health check validation
- **Monthly:** Threshold review and adjustment

### 2. Alert Fatigue Prevention

- Use `--alert-only` to reduce noise
- Adjust thresholds based on service baseline
- Filter repeated alerts (same service, same issue)

### 3. Response Procedures

**High PID Count:**
```bash
# Check service logs
docker logs <service-name> --tail 100

# Check for import errors
docker exec <service-name> python3 -c "from app.main import app"

# Restart if necessary
docker compose restart <service-name>
```

**High Memory Usage:**
```bash
# Check memory growth trend
./scripts/monitor-resources.sh --json | grep <service-name>

# Inspect container
docker stats <service-name>

# Check for leaks
docker exec <service-name> ps aux | wc -l
```

**Missing Volume Mounts:**
```bash
# Validate configuration
./scripts/healthcheck-validator.sh <service-name>

# Check volume mounts
docker inspect <service-name> | grep -A 10 "Mounts"

# Fix in docker-compose.yml
```

---

## Incident Detection Timeline

**Incident #10 (notification-service memory leak) could have been detected earlier:**

| Method | Detection Time |
|--------|---------------|
| Manual check | 5 days (actual) |
| 15min monitoring | ~30 minutes |
| 1hr monitoring | ~2 hours |
| Enhanced health check | Immediate (startup) |
| Volume mount validation | Pre-deployment |

---

## Troubleshooting

### Monitoring Script Issues

**Permission denied:**
```bash
chmod +x ./scripts/monitor-resources.sh
```

**Docker not accessible:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**State file errors:**
```bash
# Reset state
rm /tmp/docker-resource-monitor.state
```

### Health Check Failures

**Import errors:**
```bash
# Check volume mounts
docker inspect <service-name> | grep -A 10 "Mounts"

# Validate shared dependencies
docker exec <service-name> ls -la /app/shared
docker exec <service-name> pip list | grep mcp
```

**Timeout errors:**
```bash
# Increase health check timeout
# In Dockerfile.dev:
HEALTHCHECK --timeout=30s ...
```

---

## Related Documentation

- **Incident Report:** [POSTMORTEMS.md - Incident #10](../../POSTMORTEMS.md)
- **Root Cause Analysis:** `/home/cytrex/userdocs/notification-service-memory-leak-analysis.md`
- **Backend Development:** [CLAUDE.backend.md](../../CLAUDE.backend.md)
- **Docker Guide:** [docker-guide.md](docker-guide.md)

---

## Next Steps

1. ✅ Set up automated monitoring (systemd timer or cron)
2. ✅ Configure alert method (webhook recommended)
3. ✅ Test alerts with threshold breach
4. ⏳ Review alerts weekly, adjust thresholds
5. ⏳ Integrate with existing monitoring (Prometheus, Grafana)

---

**Last Updated:** 2025-11-05
**Maintainer:** DevOps Team
