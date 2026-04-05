# Docker Healthcheck Requirements & Best Practices

**Purpose:** Standard requirements and patterns for Docker healthchecks across all services.

**Last Updated:** 2025-11-17
**Incident Reference:** [POSTMORTEMS.md - Incident #15](../../POSTMORTEMS.md#incident-15-disk-space-crisis--docker-image-rebuild-2025-11-17)

---

## Overview

Docker healthchecks are **critical** for:
- Container orchestration (Docker knows when service is ready)
- Zero-downtime deployments (don't route traffic to unhealthy containers)
- Automatic recovery (restart unhealthy containers)
- Monitoring and alerting (detect service failures)

**Common Mistake:** Healthcheck configuration exists but required binaries are missing in container.

---

## Standard Healthcheck Pattern

### 1. HTTP Healthcheck (Recommended)

**Use for:** Web services with HTTP APIs (FastAPI, Express, Flask, etc.)

**docker-compose.yml:**
```yaml
services:
  my-service:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${PORT}/health"]
      interval: 30s        # Check every 30 seconds
      timeout: 10s         # Fail if check takes > 10s
      start_period: 10s    # Grace period for service startup
      retries: 3           # Mark unhealthy after 3 consecutive failures
```

**Dockerfile Dependencies:**
```dockerfile
# REQUIRED: Install curl for healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

**FastAPI Health Endpoint:**
```python
# app/main.py
from fastapi import FastAPI, status

app = FastAPI()

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for Docker healthcheck.
    Returns service status and dependencies.
    """
    return {
        "status": "healthy",
        "service": "My Service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        # Optional: Check dependencies
        "database": "connected",  # Check DB connection
        "redis": "connected",     # Check Redis connection
    }
```

**Verification:**
```bash
# Test manually inside container
docker exec <container> curl -f http://localhost:8080/health

# Expected output:
# {"status":"healthy","service":"My Service",...}

# Check healthcheck status
docker inspect <container> --format='{{.State.Health.Status}}'
# Expected: healthy
```

---

### 2. Script-Based Healthcheck

**Use for:** Services without HTTP endpoint or complex health logic.

**docker-compose.yml:**
```yaml
services:
  my-service:
    healthcheck:
      test: ["CMD", "/usr/local/bin/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      start_period: 10s
      retries: 3
```

**Dockerfile:**
```dockerfile
# Copy healthcheck script with full path (root context)
COPY services/my-service/healthcheck.sh /usr/local/bin/healthcheck.sh

# Make executable
RUN chmod +x /usr/local/bin/healthcheck.sh
```

**healthcheck.sh Example:**
```bash
#!/bin/bash
# Healthcheck script for my-service

set -e

# Check if service is running
if ! pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "ERROR: Service process not running"
    exit 1
fi

# Check if port is listening
if ! nc -z localhost 8080; then
    echo "ERROR: Service not listening on port 8080"
    exit 1
fi

# Optional: Check critical dependencies
if ! redis-cli -h redis ping > /dev/null 2>&1; then
    echo "WARNING: Redis connection failed"
    # Don't fail healthcheck for non-critical dependencies
fi

echo "OK: Service is healthy"
exit 0
```

**Required Tools in Dockerfile:**
```dockerfile
RUN apt-get update && apt-get install -y \
    netcat-openbsd \  # For nc (port check)
    procps \          # For pgrep (process check)
    redis-tools \     # For redis-cli (if using Redis)
    && rm -rf /var/lib/apt/lists/*
```

---

### 3. Python-Based Healthcheck

**Use for:** Python services where installing curl/wget is undesirable.

**docker-compose.yml:**
```yaml
services:
  my-service:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()"]
      interval: 30s
      timeout: 10s
      start_period: 10s
      retries: 3
```

**Advantages:**
- ✅ No extra system dependencies (Python already installed)
- ✅ Cross-platform (works on any Python container)

**Disadvantages:**
- ❌ Verbose command in docker-compose.yml
- ❌ Less intuitive than curl/wget
- ❌ Harder to debug (no error messages in healthcheck logs)

**Better Alternative:** Create a simple Python script

**Dockerfile:**
```dockerfile
COPY services/my-service/healthcheck.py /usr/local/bin/healthcheck.py
RUN chmod +x /usr/local/bin/healthcheck.py
```

**healthcheck.py:**
```python
#!/usr/bin/env python3
import sys
import urllib.request

try:
    response = urllib.request.urlopen('http://localhost:8080/health', timeout=5)
    if response.getcode() == 200:
        print("OK: Service is healthy")
        sys.exit(0)
    else:
        print(f"ERROR: Unexpected status code {response.getcode()}")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: Health check failed: {e}")
    sys.exit(1)
```

**docker-compose.yml:**
```yaml
healthcheck:
  test: ["CMD", "python", "/usr/local/bin/healthcheck.py"]
```

---

## Healthcheck Timing Configuration

### Interval

**Purpose:** How often to run healthcheck.

**Recommended:**
- **Fast services:** 30s (default)
- **Slow services:** 60s
- **Critical services:** 15s (more frequent monitoring)

**Example:**
```yaml
interval: 30s  # Check every 30 seconds
```

---

### Timeout

**Purpose:** Maximum time to wait for healthcheck to complete.

**Recommended:**
- **HTTP checks:** 10s
- **Script checks:** 15s
- **Complex checks:** 30s

**Example:**
```yaml
timeout: 10s  # Fail if check takes > 10 seconds
```

**⚠️ Warning:** Too short = false positives. Too long = delayed failure detection.

---

### Start Period

**Purpose:** Grace period before healthchecks count toward failure threshold.

**Recommended:**
- **Fast startup (< 5s):** 10s
- **Normal startup (< 30s):** 30s
- **Slow startup (AI models, large data):** 60s+

**Example:**
```yaml
start_period: 60s  # Allow 60 seconds for startup before enforcing healthcheck
```

**Why this matters:**
- Content-Analysis-v2: Needs 60s to load AI models
- Database services: Needs 30s for initialization
- Simple API services: Needs 10s

---

### Retries

**Purpose:** How many consecutive failures before marking unhealthy.

**Recommended:**
- **Production:** 3 (default, tolerates transient failures)
- **Development:** 3 (same as production for consistency)
- **Critical services:** 5 (more tolerant of transient issues)

**Example:**
```yaml
retries: 3  # Require 3 consecutive failures to mark unhealthy
```

**Calculation:**
```
Time to mark unhealthy = (retries × interval)
With retries=3 and interval=30s: 90 seconds after first failure
```

---

## Service-Specific Configurations

### Fast API Services (Feed, Auth, Analytics)

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:${PORT}/health"]
  interval: 30s
  timeout: 10s
  start_period: 10s   # Fast startup
  retries: 3
```

### AI/ML Services (Content-Analysis-v2)

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:${PORT}/health"]
  interval: 30s
  timeout: 10s
  start_period: 60s   # Models need time to load
  retries: 3
```

### Celery Workers (No HTTP endpoint)

```yaml
healthcheck:
  test: ["CMD", "celery", "-A", "app.celery_app", "inspect", "ping"]
  interval: 60s       # Less frequent (no user traffic)
  timeout: 15s
  start_period: 30s
  retries: 3
```

### Celery Beat (Scheduler)

```yaml
healthcheck:
  test: ["CMD", "/usr/local/bin/healthcheck-celery-beat.sh"]
  interval: 60s
  timeout: 10s
  start_period: 30s
  retries: 3
```

**healthcheck-celery-beat.sh:**
```bash
#!/bin/bash
# Check if celery beat is running
if ! pgrep -f "celery beat" > /dev/null; then
    exit 1
fi

# Check if schedule file exists and is recent (updated in last 5 minutes)
if [ -f /app/celerybeat-schedule ]; then
    if [ $(find /app/celerybeat-schedule -mmin -5) ]; then
        exit 0
    fi
fi

exit 1
```

### Frontend (React/Vite)

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  start_period: 15s   # Vite dev server needs time
  retries: 3
```

---

## Common Issues & Solutions

### Issue: "curl: executable file not found in $PATH"

**Symptom:**
```bash
docker inspect <container> --format='{{json .State.Health}}'
# Output: "exec: 'curl': executable file not found in $PATH"
```

**Cause:** Healthcheck requires `curl` but Dockerfile doesn't install it.

**Fix:**
```dockerfile
# Add curl to system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

**Verification:**
```bash
docker exec <container> which curl
# Expected: /usr/bin/curl
```

---

### Issue: "Connection refused" during healthcheck

**Symptom:**
```bash
docker logs <container> | grep health
# Output: "curl: (7) Failed to connect to localhost port 8080: Connection refused"
```

**Possible Causes:**

1. **Service not yet started:**
   ```yaml
   # Increase start_period
   healthcheck:
     start_period: 30s  # Was: 10s
   ```

2. **Wrong port in healthcheck:**
   ```yaml
   # Fix port mismatch
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8101/health"]  # Not 8080
   ```

3. **Service listening on 127.0.0.1 instead of 0.0.0.0:**
   ```bash
   # Check listening address
   docker exec <container> netstat -tlnp

   # If shows 127.0.0.1:8080, fix service to listen on 0.0.0.0
   # uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

---

### Issue: Healthcheck passes but service doesn't work

**Symptom:** Container shows "healthy" but API requests fail.

**Cause:** Healthcheck endpoint is too simple (doesn't verify dependencies).

**Fix:** Improve health endpoint to check dependencies:

```python
@app.get("/health")
async def health_check():
    health = {
        "status": "healthy",
        "service": "My Service",
        "checks": {}
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check Redis
    try:
        await redis.ping()
        health["checks"]["redis"] = "ok"
    except Exception as e:
        health["checks"]["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check RabbitMQ
    try:
        # Verify connection exists
        if rabbitmq.is_connected:
            health["checks"]["rabbitmq"] = "ok"
        else:
            health["checks"]["rabbitmq"] = "disconnected"
            health["status"] = "degraded"
    except Exception as e:
        health["checks"]["rabbitmq"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Return appropriate status code
    if health["status"] == "degraded":
        raise HTTPException(status_code=503, detail=health)

    return health
```

---

### Issue: Healthcheck script not found

**Symptom:**
```bash
docker inspect <container> --format='{{json .State.Health}}'
# Output: "/usr/local/bin/healthcheck.sh: not found"
```

**Cause:** Build context is root (`.`) but Dockerfile uses relative path.

**Fix:**
```dockerfile
# WRONG (only works with service-specific context)
COPY healthcheck.sh /usr/local/bin/healthcheck.sh

# CORRECT (works with root context)
COPY services/my-service/healthcheck.sh /usr/local/bin/healthcheck.sh
```

**Verification:**
```bash
docker exec <container> ls -la /usr/local/bin/healthcheck.sh
# Expected: -rwxr-xr-x 1 root root ... /usr/local/bin/healthcheck.sh
```

---

## Pre-Deployment Checklist

Before deploying new service, verify:

### 1. System Dependencies

- [ ] `curl` OR `wget` installed (for HTTP healthchecks)
- [ ] `netcat` installed (for port checks in scripts)
- [ ] `procps` installed (for process checks in scripts)
- [ ] Service-specific tools (e.g., `redis-cli`, `psql`)

**Verification:**
```bash
docker exec <container> which curl
docker exec <container> which nc
docker exec <container> which pgrep
```

### 2. Healthcheck Configuration

- [ ] Healthcheck defined in `docker-compose.yml`
- [ ] Port matches service port
- [ ] Endpoint exists (`/health` or `/healthz`)
- [ ] `start_period` accounts for initialization time
- [ ] `interval` appropriate for service criticality
- [ ] `timeout` sufficient for check to complete
- [ ] `retries` set to 3 (or justified if different)

**Verification:**
```bash
# Test healthcheck command manually
docker exec <container> curl -f http://localhost:PORT/health

# Check healthcheck status
docker ps --filter name=<container> --format "{{.Names}}\t{{.Status}}"
# Expected: Up X seconds (healthy)
```

### 3. Build Context

- [ ] Context is `.` (root) in `docker-compose.yml`
- [ ] Dockerfile uses full paths: `COPY services/SERVICE_NAME/...`
- [ ] Healthcheck script copied with full path
- [ ] Healthcheck script is executable (`chmod +x`)

**Verification:**
```bash
# Check build context in docker-compose.yml
grep -A 3 "build:" docker-compose.yml

# Expected:
# build:
#   context: .
#   dockerfile: ./services/my-service/Dockerfile.dev
```

### 4. Health Endpoint Implementation

- [ ] Endpoint returns 200 OK when healthy
- [ ] Response is JSON (recommended)
- [ ] Includes service name and version
- [ ] Checks critical dependencies (DB, cache, queue)
- [ ] Returns 503 Service Unavailable when degraded
- [ ] Doesn't perform expensive operations (< 100ms)

**Verification:**
```bash
# Test endpoint response time
time curl http://localhost:PORT/health
# Expected: < 100ms

# Test response format
curl http://localhost:PORT/health | python3 -m json.tool
# Expected: Valid JSON with status field
```

---

## Monitoring Healthcheck Status

### Real-Time Monitoring

```bash
# List all unhealthy containers
docker ps --filter health=unhealthy --format "{{.Names}}\t{{.Status}}"

# Detailed health status for specific container
docker inspect <container> --format='{{json .State.Health}}' | python3 -m json.tool

# Watch healthcheck logs
docker inspect <container> --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

### Automated Monitoring (Cron)

```bash
# Add to crontab
0 * * * * /usr/local/bin/check_container_health.sh

# check_container_health.sh
#!/bin/bash
UNHEALTHY=$(docker ps --filter health=unhealthy --format "{{.Names}}")

if [ -n "$UNHEALTHY" ]; then
    echo "Unhealthy containers detected: $UNHEALTHY" | \
        mail -s "⚠️ Docker Healthcheck Alert" admin@example.com
fi
```

### Prometheus Metrics (Advanced)

Use **cAdvisor** to export Docker healthcheck metrics to Prometheus:

```yaml
# docker-compose.yml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
```

**Grafana Query:**
```promql
# Container health status (0=healthy, 1=unhealthy)
container_health_status{name=~"news-.*"}
```

---

## Best Practices Summary

### DO ✅

1. **Always install healthcheck dependencies:**
   ```dockerfile
   RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
   ```

2. **Use root build context consistently:**
   ```yaml
   build:
     context: .
     dockerfile: ./services/my-service/Dockerfile.dev
   ```

3. **Check critical dependencies in health endpoint:**
   ```python
   # Verify DB, Redis, RabbitMQ connections
   ```

4. **Set appropriate start_period for service:**
   - Fast services: 10s
   - Normal services: 30s
   - AI/ML services: 60s+

5. **Return proper HTTP status codes:**
   - 200 OK = Healthy
   - 503 Service Unavailable = Degraded/Unhealthy

6. **Monitor healthcheck failures:**
   ```bash
   docker ps --filter health=unhealthy
   ```

### DON'T ❌

1. **Don't skip healthchecks:**
   - "It works on my machine" is not monitoring

2. **Don't use too short timeouts:**
   - False positives cause unnecessary restarts

3. **Don't perform expensive operations in health endpoint:**
   - No database scans, complex calculations
   - Keep response time < 100ms

4. **Don't ignore unhealthy status:**
   - Investigate immediately, don't just restart

5. **Don't use inconsistent build contexts:**
   - Standardize on root context for all services

6. **Don't forget to test healthchecks:**
   - Manually test before deploying

---

## Related Documentation

- [Docker Rebuild Procedure](./docker-rebuild-procedure.md)
- [POSTMORTEMS.md - Incident #15](../../POSTMORTEMS.md#incident-15-disk-space-crisis--docker-image-rebuild-2025-11-17)
- [CLAUDE.backend.md](../../CLAUDE.backend.md)

---

## See Also

- **[CLAUDE.backend.md - Health Monitoring](../../CLAUDE.backend.md#-health-monitoring--alerting)** - Quick reference and dashboard access
- **[Health Monitoring Setup Guide](./health-monitoring-setup.md)** - System-wide monitoring configuration (693 lines)
  - Complete architecture and monitoring flow
  - Systemd integration and scheduling
  - Alert configuration and delivery
  - Frontend dashboard implementation

---

**Last Updated:** 2025-11-17
**Verified On:** 2025-11-17 (35 containers with working healthchecks)
