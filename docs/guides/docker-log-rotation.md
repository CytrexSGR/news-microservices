# Docker Log Rotation Guide

**Last Updated:** 2025-11-24
**Status:** Production Best Practice ✅

## Overview

Docker containers can generate massive log files that fill up disk space. Without log rotation, a single container can accumulate hundreds of gigabytes of logs, causing system-wide failures.

**Real Incident:** On 2025-11-24, knowledge-graph-service accumulated **314GB of logs** from an error loop, bringing the system to 86% disk capacity. See [POSTMORTEMS.md - Incident #24](../../POSTMORTEMS.md#incident-24-docker-log-overflow---346gb-disk-space-crisis-2025-11-24).

## Quick Start

### Global Log Rotation (Recommended)

Add this to the **top** of your `docker-compose.yml`:

```yaml
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"      # Max size per log file
    max-file: "3"        # Number of rotated files
    compress: "true"     # Compress rotated logs
```

Then apply to **every service**:

```yaml
services:
  my-service:
    logging: *default-logging
    image: my-image
    # ... rest of config
```

**Result:** Each container limited to max **30MB of logs** (10MB × 3 files).

## Configuration Options

### max-size

**Description:** Maximum size of a single log file before rotation

**Options:**
- `"1m"` - 1 megabyte
- `"10m"` - 10 megabytes (recommended for most services)
- `"50m"` - 50 megabytes (for high-volume logging)
- `"100m"` - 100 megabytes (for very high-volume logging)

**Recommendation:** Start with `"10m"`. Increase only if you need more history.

### max-file

**Description:** Number of rotated log files to keep

**Options:**
- `"1"` - Keep only current log (10MB total)
- `"3"` - Keep 3 rotated files (30MB total) - **Recommended**
- `"5"` - Keep 5 rotated files (50MB total)
- `"10"` - Keep 10 rotated files (100MB total)

**Recommendation:** `"3"` provides good balance of history vs. disk usage.

### compress

**Description:** Compress rotated log files with gzip

**Options:**
- `"true"` - Compress rotated logs (saves ~70% disk space) - **Recommended**
- `"false"` - No compression

**Recommendation:** Always use `"true"`. Compression is fast and saves significant space.

## Per-Service Configuration

For services with different logging needs:

```yaml
services:
  # High-volume service (e.g., API gateway)
  api-gateway:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
        compress: "true"

  # Low-volume service (e.g., cron job)
  scheduler:
    logging:
      driver: "json-file"
      options:
        max-size: "5m"
        max-file: "2"
        compress: "true"

  # Critical service (keep more history)
  auth-service:
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "10"
        compress: "true"
```

## Applying to Existing Projects

### Manual Method

1. Add `x-logging` anchor at top of `docker-compose.yml`
2. Add `logging: *default-logging` to each service
3. Restart containers: `docker compose down && docker compose up -d`

### Automated Method (Recommended)

Use the provided script:

```bash
# Adds log rotation to all services automatically
python3 scripts/add_log_rotation.py
```

**What it does:**
- Scans `docker-compose.yml` for all service definitions
- Injects `logging: *default-logging` to services without it
- Creates backup at `docker-compose.yml.new`
- Shows summary of changes

## Emergency: Truncating Large Logs

If logs have already filled up disk:

### 1. Find Large Log Files

```bash
# Run comprehensive disk analysis
./scripts/disk_analysis.sh

# Or find manually
sudo find /var/lib/docker/containers -name "*-json.log" -type f -size +1G -exec ls -lh {} \;
```

### 2. Truncate Log Files

```bash
# Truncate specific container (SAFE - doesn't stop container)
sudo truncate -s 0 /var/lib/docker/containers/<container-id>/<container-id>-json.log

# Verify
ls -lh /var/lib/docker/containers/<container-id>/<container-id>-json.log
```

**Safe to do on running containers:** Docker handles truncation gracefully.

### 3. Apply Log Rotation

```bash
# Add log rotation to docker-compose.yml (if not done)
python3 scripts/add_log_rotation.py

# Restart to apply
docker compose down && docker compose up -d
```

## Monitoring

### Check Current Log Sizes

```bash
# Per container
docker ps --format "table {{.Names}}\t{{.Size}}"

# Total Docker disk usage
docker system df

# Container log files
sudo du -h /var/lib/docker/containers/*/  | sort -hr | head -20
```

### Set Up Alerts

**Grafana Dashboard (Recommended):**
- Alert when disk usage > 70%
- Alert when container log size > 20MB
- Alert when log growth rate > 100MB/min

**Cron Job (Simple):**
```bash
# Add to /etc/cron.hourly/check-disk
#!/bin/bash
USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 70 ]; then
    echo "ALERT: Disk usage is ${USAGE}%" | mail -s "Disk Alert" admin@example.com
fi
```

## Best Practices

### 1. Always Configure Log Rotation

**Never rely on Docker's default** (no size limits!)

```yaml
# ❌ WRONG: No log rotation
services:
  my-service:
    image: my-image

# ✅ CORRECT: Log rotation configured
services:
  my-service:
    logging: *default-logging
    image: my-image
```

### 2. Use Global Configuration

**DRY principle:** Define once, apply everywhere

```yaml
# Define at top
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    compress: "true"

# Apply to all services
services:
  service1:
    logging: *default-logging
  service2:
    logging: *default-logging
  service3:
    logging: *default-logging
```

### 3. Adjust for Service Type

**Different services have different needs:**

| Service Type | max-size | max-file | Total Max |
|--------------|----------|----------|-----------|
| Low-volume (cron) | 5m | 2 | 10MB |
| Normal (API) | 10m | 3 | 30MB |
| High-volume (gateway) | 50m | 5 | 250MB |
| Critical (auth) | 20m | 10 | 200MB |

### 4. Monitor Proactively

**Don't wait for disk to fill:**
- Set alerts at 70% disk usage
- Monitor log growth rates
- Review logs regularly

### 5. Fix Root Causes

**Log rotation is damage control, not a fix:**
- Investigate why logs are large
- Fix error loops (see Incident #24)
- Reduce logging verbosity if appropriate
- Add circuit breakers for retries

## Common Issues

### Issue: "Logs still growing too fast"

**Symptoms:** Even with rotation, logs fill up quickly

**Causes:**
1. Error loop (service retrying failed operation)
2. Excessive logging verbosity
3. max-size too large

**Solutions:**
1. Check logs for repeated errors: `docker logs <container> | tail -100`
2. Fix application-level issues (error handling, circuit breakers)
3. Reduce max-size: `"10m"` → `"5m"`
4. Reduce logging level: `INFO` → `WARNING`

### Issue: "Not enough log history"

**Symptoms:** Need more logs for debugging

**Solutions:**
1. Increase max-file: `"3"` → `"5"` or `"10"`
2. Use external logging (ELK, Loki, CloudWatch)
3. For critical services: `max-size: "20m"`, `max-file: "10"` (200MB total)

### Issue: "Logs lost after rotation"

**Symptoms:** Old logs are gone

**Solutions:**
1. This is **expected behavior** - rotation deletes old logs
2. For permanent logs: Use external logging system
3. Or increase max-file to keep more history
4. Or use `docker logs --since` to export before rotation

## External Logging (Advanced)

For production systems, send logs to external service:

### Option 1: Loki (Recommended)

```yaml
x-logging: &loki-logging
  driver: "loki"
  options:
    loki-url: "http://loki:3100/loki/api/v1/push"
    loki-batch-size: "400"
    max-size: "10m"        # Still set limits as fallback
    max-file: "3"
```

### Option 2: Fluentd

```yaml
x-logging: &fluentd-logging
  driver: "fluentd"
  options:
    fluentd-address: "localhost:24224"
    tag: "docker.{{.Name}}"
    max-size: "10m"
    max-file: "3"
```

### Option 3: AWS CloudWatch

```yaml
x-logging: &cloudwatch-logging
  driver: "awslogs"
  options:
    awslogs-region: "us-east-1"
    awslogs-group: "/ecs/my-app"
    awslogs-stream: "{{.Name}}"
    max-size: "10m"
    max-file: "3"
```

**Note:** Always keep local log rotation as fallback!

## Verification

After implementing log rotation:

```bash
# 1. Check config is applied
docker inspect <container> | grep -A 10 LogConfig

# Expected output:
# "LogConfig": {
#   "Type": "json-file",
#   "Config": {
#     "max-size": "10m",
#     "max-file": "3",
#     "compress": "true"
#   }
# }

# 2. Verify rotation is working (wait a few hours)
sudo ls -lh /var/lib/docker/containers/<container-id>/

# Should see:
# <container-id>-json.log       (current, < 10MB)
# <container-id>-json.log.1.gz  (rotated, compressed)
# <container-id>-json.log.2.gz  (rotated, compressed)

# 3. Check disk usage
docker system df
df -h /
```

## References

- [Incident #24: Docker Log Overflow](../../POSTMORTEMS.md#incident-24-docker-log-overflow---346gb-disk-space-crisis-2025-11-24)
- [Docker Logging Documentation](https://docs.docker.com/config/containers/logging/json-file/)
- Script: `scripts/add_log_rotation.py`
- Script: `scripts/disk_analysis.sh`
- Commit: `b82b832` (Log rotation implementation)

## Summary

**Key Takeaways:**

1. ✅ **Always configure log rotation** - Docker's default has NO SIZE LIMITS
2. ✅ **Use global configuration** - Define once with x-logging anchor
3. ✅ **Start with 10m/3 files** - Adjust based on needs
4. ✅ **Enable compression** - Saves ~70% disk space
5. ✅ **Monitor proactively** - Alert at 70% disk usage
6. ✅ **Fix root causes** - Don't just rotate logs from error loops

**One command to check everything:**
```bash
./scripts/disk_analysis.sh
```

**Emergency truncation:**
```bash
sudo truncate -s 0 /var/lib/docker/containers/<container-id>/<container-id>-json.log
```

**Prevent future issues:**
```yaml
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    compress: "true"
```
