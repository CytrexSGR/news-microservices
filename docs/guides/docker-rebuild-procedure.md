# Docker Complete Rebuild Procedure

**Purpose:** Step-by-step guide for rebuilding all Docker containers after aggressive cleanup or system recovery.

**Last Updated:** 2025-11-17
**Incident Reference:** [POSTMORTEMS.md - Incident #15](../../POSTMORTEMS.md#incident-15-disk-space-crisis--docker-image-rebuild-2025-11-17)

---

## When to Use This Guide

Use this procedure when:
- ✅ All Docker images have been deleted (`docker system prune -af`)
- ✅ System recovery after disk space crisis
- ✅ Major infrastructure changes requiring full rebuild
- ✅ Migration to new server/environment

**DO NOT use for:**
- ❌ Single service updates (use `docker compose build <service>`)
- ❌ Code changes (hot-reload handles this automatically)
- ❌ Minor configuration changes

---

## Prerequisites

### 1. Verify Disk Space

```bash
df -h /
# Required: At least 100GB free for build process
# Recommended: 150GB+ free for safety margin
```

**If disk space < 100GB:** Follow cleanup procedure first (see [Disk Cleanup Guide](#disk-cleanup-before-rebuild))

### 2. Verify Data Volumes

```bash
docker volume ls | grep -E "postgres|neo4j|redis"
# Expected output:
# news-microservices_postgres-data
# news-microservices_neo4j-data
# news-microservices_redis-data
```

**⚠️ WARNING:** If volumes are missing, data loss has occurred. Check backups before proceeding.

### 3. Stop All Running Containers

```bash
cd /home/cytrex/news-microservices
docker compose down
```

---

## Rebuild Order (CRITICAL)

Build services in this **exact order** to respect dependencies:

```
1. Infrastructure (Postgres, Redis, Neo4j, RabbitMQ)
   ↓
2. Auth Service (required by all other services)
   ↓
3. Feed Service + Workers (core data pipeline)
   ↓
4. Content Analysis v3 (depends on feed)
   ↓
5. Support Services (analytics, research, search, notification)
   ↓
6. Scheduler Service (depends on multiple services)
   ↓
7. Frontend (depends on all backend APIs)
```

**Why this order?**
- Infrastructure must be running before any service
- Auth provides JWT validation for all services
- Feed generates events consumed by downstream services
- Scheduler processes entities from content-analysis

---

## Step-by-Step Rebuild

### Phase 1: Infrastructure (No Build Required)

Infrastructure containers use official images (no custom Dockerfiles).

```bash
# Start infrastructure
docker compose up -d postgres redis neo4j rabbitmq

# Wait for health checks
sleep 30

# Verify
docker ps --filter name=postgres --format "{{.Names}}\t{{.Status}}"
docker ps --filter name=redis --format "{{.Names}}\t{{.Status}}"
docker ps --filter name=neo4j --format "{{.Names}}\t{{.Status}}"
docker ps --filter name=rabbitmq --format "{{.Names}}\t{{.Status}}"

# Expected: All show "Up X seconds (healthy)"
```

**If unhealthy:** Wait additional 30-60 seconds. Databases take time to initialize.

---

### Phase 2: Auth Service

```bash
# Build
docker compose build auth-service

# Start
docker compose up -d auth-service

# Wait for healthy
sleep 15

# Verify
docker ps --filter name=auth-service --format "{{.Names}}\t{{.Status}}"
# Expected: Up X seconds (healthy)

# Test endpoint
curl -f http://localhost:8100/health
# Expected: {"status":"healthy","service":"Auth Service",...}
```

**Common Issues:**
- `healthcheck.sh not found`: Check Dockerfile COPY path matches root context
- `Connection refused`: Database not ready yet, wait 30s and retry

---

### Phase 3: Feed Service + Workers

Feed service has **4 containers**:
1. feed-service (API)
2. feed-celery-worker
3. feed-celery-beat
4. feed-service-analysis-consumer

```bash
# Build (single build for all 4)
docker compose build feed-service feed-celery-worker feed-celery-beat feed-service-analysis-consumer

# Start all 4
docker compose up -d feed-service feed-celery-worker feed-celery-beat feed-service-analysis-consumer

# Wait for healthy
sleep 30

# Verify all 4
docker ps --filter name=feed --format "{{.Names}}\t{{.Status}}"
# Expected: 4 containers, all healthy

# Check outbox processing
docker logs news-feed-service --tail 20 | grep "outbox"
# Expected: "Processed X outbox events"

# Check RabbitMQ connections
docker logs news-feed-service --tail 20 | grep "RabbitMQ"
# Expected: "Connected to RabbitMQ"
```

**Common Issues:**
- `build context error`: Ensure context is `.` (root) not `./services/feed-service`
- `shared library not found`: Check `COPY shared/news-mcp-common` path in Dockerfile

---

### Phase 4: Content Analysis v3

**Note:** Content-analysis-v2 was archived on 2025-11-24. Use content-analysis-v3.

```bash
# Build (single build for 3 workers)
docker compose build content-analysis-v3

# Start 3 worker replicas
docker compose up -d content-analysis-v3

# Wait for initialization (workers need time to load AI models)
sleep 60

# Verify all 3 workers
docker ps --filter name=content-analysis-v3 --format "{{.Names}}\t{{.Status}}"
# Expected: 3 workers (content-analysis-v3-consumer-1, -2, -3), all healthy

# Check agent initialization
docker logs news-content-analysis-v3-consumer-1 --tail 50 | grep "initialized"
# Expected: "Analysis consumers initialized successfully"

# Check RabbitMQ listening
docker logs news-content-analysis-v3-consumer-1 --tail 20 | grep "article.created"
# Expected: "Consuming article.created events"
```

**Common Issues:**
- `Timeout during build`: Increase Docker build timeout or check network
- `Worker crashes on startup`: Check memory (needs ~2GB per worker)
- `AI models not loading`: Check volume mounts for model cache

---

### Phase 5: Support Services

Build in parallel (no dependencies between them):

```bash
# Build all support services
docker compose build analytics-service analytics-celery-worker analytics-celery-beat \
  research-service research-celery-worker \
  search-service search-celery-worker \
  notification-service

# Start all
docker compose up -d analytics-service analytics-celery-worker analytics-celery-beat \
  research-service research-celery-worker \
  search-service search-celery-worker \
  notification-service

# Wait for healthy
sleep 30

# Verify
docker ps --filter name=analytics --format "{{.Names}}\t{{.Status}}"
docker ps --filter name=research --format "{{.Names}}\t{{.Status}}"
docker ps --filter name=search --format "{{.Names}}\t{{.Status}}"
docker ps --filter name=notification --format "{{.Names}}\t{{.Status}}"
```

**Expected Warnings (Non-Critical):**
- **Research-Service:** Perplexity API `/models` endpoint 404 (service still works)

---

### Phase 6: Scheduler Service

**⚠️ CRITICAL:** This service has 3 components with different criticality levels:

**Components:**
1. **Feed Monitor** (60s interval) - ⚠️ REDUNDANT (feed-celery-beat already fetches)
2. **Job Processor** (30s interval) - ⚠️ NEVER IMPLEMENTED (no DB tables)
3. **Entity KG Processor** (30s interval) - ✅ CRITICAL (processes entities for Knowledge Graph)

**Decision:** Keep running for Entity KG Processor only.

```bash
# Build
docker compose build scheduler-service

# Start
docker compose up -d scheduler-service

# Wait for first processing cycle
sleep 35

# Verify scheduler is running
docker ps --filter name=scheduler-service --format "{{.Names}}\t{{.Status}}"
# Expected: Up X seconds (healthy)

# Check Entity KG Processor
docker logs news-scheduler-service --tail 30 | grep "Entity KG Processor"
# Expected: "Processing 15 entities in 5 batches"

# Verify entity processing is working
docker logs news-scheduler-service --tail 10 | grep "successfully processed"
# Expected: "15/15 entities successfully processed"
```

**Common Issues:**
- `healthcheck.sh not found`: Check COPY path uses full `services/scheduler-service/healthcheck.sh`
- `No entities processed`: Check if content-analysis-v3 has generated entities first

**Monitor Backlog:**
```bash
# Check unprocessed entity count (entities awaiting KG sync)
# Note: content_analysis_v2 schema was archived 2025-11-24
# Entities are now tracked via article_analysis table
docker exec news-scheduler-service psql -U news_user -d news_mcp -c \
  "SELECT COUNT(*) FROM public.article_analysis
   WHERE kg_synced = false OR kg_synced IS NULL;"

# If count > 0, scheduler will process at 30 entities/minute
```

---

### Phase 7: Frontend

```bash
# Build
docker compose build frontend

# Start
docker compose up -d frontend

# Wait for Vite dev server
sleep 15

# Verify
docker ps --filter name=frontend --format "{{.Names}}\t{{.Status}}"
# Expected: Up X seconds (healthy)

# Test access
curl -f http://localhost:3000
# Expected: HTML response (React app)
```

**Expected Warnings (Non-Critical):**
- **npm audit:** 2 moderate vulnerabilities (deferred, not critical for dev)

---

## Final Verification

### 1. Container Health Check

```bash
# Count healthy containers
docker ps --format "table {{.Names}}\t{{.Status}}" | grep "healthy" | wc -l
# Expected: 35+ containers

# List all unhealthy
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -v "healthy"
# Expected: Only infrastructure (postgres, redis, neo4j) without healthchecks
```

### 2. Service Endpoint Tests

```bash
# Auth
curl -f http://localhost:8100/health
# Expected: {"status":"healthy",...}

# Feed
curl -f http://localhost:8101/health
# Expected: {"status":"healthy",...}

# Content Analysis (via proxy)
curl -f http://localhost:8114/health
# Expected: {"status":"healthy",...}

# Frontend
curl -f http://localhost:3000
# Expected: HTML content

# RabbitMQ UI
curl -f http://localhost:15672
# Expected: RabbitMQ Management UI
```

### 3. Event Flow Test

Test the entire pipeline: Feed → Content Analysis → Scheduler → Knowledge Graph

```bash
# 1. Trigger feed fetch manually
docker exec news-feed-celery-worker celery -A app.celery_app call app.tasks.feed.fetch_all_active

# 2. Check for article.created events in logs
docker logs news-feed-service --tail 50 | grep "article.created"
# Expected: "Published article.created event for article_id=..."

# 3. Verify content-analysis received events
docker logs news-content-analysis-v3-consumer-1 --tail 50 | grep "Received article"
# Expected: "Received article for analysis: article_id=..."

# 4. Verify scheduler processed entities
sleep 60  # Wait for processing cycle
docker logs news-scheduler-service --tail 30 | grep "successfully processed"
# Expected: "X/X entities successfully processed"
```

---

## Disk Cleanup (Before Rebuild)

If disk space < 100GB, clean up before rebuilding:

### Safe Cleanup (Recommended)

```bash
# Remove old images (keep recent)
docker image prune -a --filter "until=168h"  # Older than 1 week

# Remove dangling build cache
docker builder prune --filter "until=168h"

# Check freed space
df -h /
```

### Moderate Cleanup

```bash
# Remove all stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes (⚠️ check before confirming)
docker volume prune -f

# Remove build cache
docker builder prune -a -f

# Check freed space
df -h /
```

### Aggressive Cleanup (⚠️ USE WITH CAUTION)

**⚠️ WARNING:** This will delete ALL images, including running containers' images.

```bash
# ONLY use if disk space critical and data is backed up
docker system prune -af --volumes

# ⚠️ Side effects:
# - Stops all containers
# - Deletes all images (requires full rebuild)
# - Deletes all unused volumes (⚠️ DATA LOSS RISK)
# - Deletes all build cache
```

**ALWAYS verify volumes before aggressive cleanup:**
```bash
# List volumes to preserve
docker volume ls | grep -E "postgres|neo4j|redis"

# If missing, STOP and restore from backup
```

---

## Common Build Issues

### Issue: "failed to calculate checksum: file not found"

**Cause:** Build context mismatch. Dockerfile expects root context (`.`) but service uses service-specific context.

**Fix:**
```yaml
# docker-compose.yml - CORRECT
services:
  my-service:
    build:
      context: .  # Root context
      dockerfile: ./services/my-service/Dockerfile.dev
```

**Dockerfile must use full paths:**
```dockerfile
# CORRECT
COPY services/my-service/healthcheck.sh /usr/local/bin/
COPY services/my-service/app ./app

# WRONG (only works with service-specific context)
COPY healthcheck.sh /usr/local/bin/
COPY app ./app
```

### Issue: "curl: executable file not found in $PATH"

**Cause:** Healthcheck requires `curl` but Dockerfile doesn't install it.

**Fix:**
```dockerfile
# Add curl to system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \  # Required for healthcheck
    && rm -rf /var/lib/apt/lists/*
```

### Issue: Container shows "unhealthy" but service works

**Diagnosis:**
```bash
# Check healthcheck logs
docker inspect <container> --format='{{json .State.Health}}' | python3 -m json.tool

# Look for error in "Output" field
```

**Common causes:**
- Missing binary (`curl`, `wget`)
- Wrong port in healthcheck URL
- Service takes longer than `start_period` to start

**Fix healthcheck timing:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  start_period: 60s  # Increase if service is slow to start
  retries: 3
```

### Issue: Build timeout

**Cause:** Large service (content-analysis-v3) or slow network.

**Fix:**
```bash
# Increase Docker build timeout
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Or build with increased timeout
docker compose build --no-cache --build-arg BUILDKIT_INLINE_CACHE=1
```

---

## Healthcheck Requirements Checklist

Before deploying new services, verify:

- [ ] **System dependencies installed:**
  - [ ] `curl` (for HTTP healthchecks)
  - [ ] OR `wget` (alternative to curl)
  - [ ] OR Python (if using Python-based healthcheck)

- [ ] **Healthcheck configuration:**
  - [ ] `test` command uses available binary
  - [ ] Port matches service port
  - [ ] Endpoint exists and returns 200 OK
  - [ ] `start_period` accounts for initialization time

- [ ] **Build context:**
  - [ ] Context is `.` (root)
  - [ ] Dockerfile uses full paths: `COPY services/SERVICE_NAME/...`
  - [ ] Healthcheck script copied with full path

**Validation:**
```bash
# Test healthcheck manually
docker exec <container> curl -f http://localhost:PORT/health

# Check binary exists
docker exec <container> which curl
# Expected: /usr/bin/curl
```

---

## Monitoring Post-Rebuild

After successful rebuild, monitor for 24 hours:

### 1. Disk Usage Alerts

```bash
# Add to crontab
0 */6 * * * /usr/local/bin/check_disk_usage.sh

# Script should alert if usage > 80%
```

### 2. Container Health Monitoring

```bash
# Daily health check
0 9 * * * docker ps --filter health=unhealthy --format "{{.Names}}" | mail -s "Unhealthy Containers" admin@example.com
```

### 3. Docker Cleanup Automation

```bash
# Weekly cleanup (every Sunday 3 AM)
0 3 * * 0 docker system prune -f --filter "until=168h"
```

### 4. Backup Verification

```bash
# Daily backup check
0 2 * * * /usr/local/bin/verify_backups.sh
```

---

## Rollback Procedure

If rebuild fails catastrophically:

### 1. Restore from Backup

```bash
# Stop all containers
docker compose down

# Restore database volumes
docker volume rm news-microservices_postgres-data
docker run --rm -v news-microservices_postgres-data:/data -v /backup/postgres:/backup alpine sh -c "cd /data && tar xzf /backup/postgres-backup-YYYYMMDD.tar.gz"

# Repeat for neo4j, redis

# Restart
docker compose up -d
```

### 2. Selective Rebuild

Instead of rebuilding all, rebuild only failed services:

```bash
# Identify failed service
docker ps --filter health=unhealthy --format "{{.Names}}"

# Rebuild specific service
docker compose build <service>
docker compose up -d <service>
```

---

## Related Documentation

- [POSTMORTEMS.md - Incident #15](../../POSTMORTEMS.md#incident-15-disk-space-crisis--docker-image-rebuild-2025-11-17)
- [Healthcheck Requirements](./healthcheck-requirements.md)
- [CLAUDE.backend.md](../../CLAUDE.backend.md)

---

**Last Updated:** 2025-11-17
**Verified On:** 2025-11-17 (35 containers successfully rebuilt)
