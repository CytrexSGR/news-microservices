# Alert Response Runbook

## Quick Reference

**Alert Dashboard:** http://localhost:3000/admin/health
**Alert Log:** `/tmp/docker-monitor-alerts.log`
**Systemd Logs:** `journalctl -u docker-monitor.service -n 50`

---

## Alert Types

### 1. HIGH_PID (CRITICAL)

**Trigger:** Container PID count > 100
**Severity:** CRITICAL
**Impact:** Potential resource exhaustion, service instability

**Example:**
```
[2025-11-05 20:50:57 UTC] ALERT [CRITICAL] notification-service: HIGH_PID: 6851 processes (threshold: 100)
```

**Immediate Actions:**

1. **Verify container health:**
   ```bash
   docker ps | grep <service-name>
   docker stats <container-name> --no-stream
   ```

2. **Check for runaway processes:**
   ```bash
   docker exec <container-name> ps aux | wc -l
   ```

3. **Review recent logs:**
   ```bash
   docker logs <container-name> --tail 100
   ```

**Root Cause Analysis:**

**Common Causes:**
- Uvicorn infinite reload loop (missing dependencies)
- Worker process leak (Celery, Gunicorn)
- Zombie processes not reaped
- Fork bomb (malicious or bug)

**Investigation:**
```bash
# Check import errors
docker logs <container-name> | grep ImportError

# Check for reload loops
docker logs <container-name> | grep "Reloading"

# Identify process tree
docker exec <container-name> pstree -p
```

**Resolution:**

**If import error detected:**
```bash
# Fix missing volume mount in docker-compose.yml
# Add: - ./shared:/app/shared
docker compose restart <service-name>
```

**If worker leak:**
```bash
# Restart service
docker compose restart <service-name>

# If persists, rebuild with fixed configuration
docker compose build <service-name>
docker compose up -d <service-name>
```

**Post-Incident:**
- Document root cause in POSTMORTEMS.md
- Add health check if missing
- Review PID limit (currently 512/1024)

---

### 2. HIGH_MEMORY (WARNING)

**Trigger:** Container memory > 10% of total system memory
**Severity:** WARNING
**Impact:** Potential OOM kill, performance degradation

**Example:**
```
[2025-11-05 20:50:57 UTC] ALERT [WARNING] neo4j: HIGH_MEMORY: 9.84% (threshold: 10.0%)
```

**Immediate Actions:**

1. **Check current memory usage:**
   ```bash
   docker stats <container-name> --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
   ```

2. **Identify memory trend:**
   ```bash
   # Monitor over 5 minutes
   watch -n 60 'docker stats <container-name> --no-stream'
   ```

**Root Cause Analysis:**

**Common Causes:**
- Memory leak (gradual increase)
- Large dataset in memory (cache, buffer)
- Machine learning model loaded (entity-canonicalization, content-analysis)
- Inefficient query (ORM N+1)

**Investigation:**
```bash
# Check if memory is growing
grep "<service-name>" /tmp/docker-monitor-alerts.log | grep HIGH_MEMORY

# For Python services, check memory profiler
docker exec <container-name> python -m memory_profiler /app/main.py

# Check cache size (Redis, in-memory)
docker exec redis redis-cli INFO memory
```

**Resolution:**

**If memory leak:**
```bash
# Restart service temporarily
docker compose restart <service-name>

# Long-term: Fix code (use context managers, close connections)
```

**If large model:**
```bash
# entity-canonicalization: Singleton pattern for SentenceTransformer
# (Already implemented as of 2025-10-30)

# Verify singleton is working
docker logs news-entity-canonicalization | grep "SentenceTransformer"
```

**If cache growth:**
```bash
# Redis: Set maxmemory policy
docker exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
docker exec redis redis-cli CONFIG SET maxmemory 512mb
```

**Post-Incident:**
- Profile memory usage with `/application-performance` plugin
- Consider memory limit in docker-compose.yml
- Add memory monitoring dashboard

---

### 3. HIGH_CPU (WARNING)

**Trigger:** Container CPU > 50% average
**Severity:** WARNING
**Impact:** Performance degradation, increased costs

**Example:**
```
[2025-11-05 20:50:57 UTC] ALERT [WARNING] auth-service: HIGH_CPU: 42.4% (threshold: 50.0%)
```

**Immediate Actions:**

1. **Check CPU usage:**
   ```bash
   docker stats <container-name> --no-stream --format "table {{.Name}}\t{{.CPUPerc}}"
   ```

2. **Identify CPU-intensive process:**
   ```bash
   docker exec <container-name> top -bn1
   ```

**Root Cause Analysis:**

**Common Causes:**
- Tight loop (infinite/busy-wait)
- Heavy computation (ML inference, data processing)
- High request rate (traffic spike)
- Inefficient algorithm (O(n²) operations)

**Investigation:**
```bash
# Check request rate
docker logs <container-name> | grep "GET\|POST" | wc -l

# Profile Python code
docker exec <container-name> python -m cProfile /app/main.py

# Check for tight loops
docker logs <container-name> | grep -i "loop\|iteration"
```

**Resolution:**

**If traffic spike:**
```bash
# Scale up workers
docker compose up -d --scale <service-name>=3

# Or add load balancer
```

**If inefficient code:**
```bash
# Profile with /application-performance plugin
# Optimize hot paths
# Add caching for expensive operations
```

**If background job:**
```bash
# Move to Celery task
# Run during off-peak hours
```

**Post-Incident:**
- Use `/application-performance` plugin for profiling
- Add CPU metrics to Grafana
- Review algorithm complexity

---

### 4. MEMORY_GROWTH (WARNING)

**Trigger:** Memory increase > 10% between intervals
**Severity:** WARNING
**Impact:** Eventual OOM kill, requires restart

**Example:**
```
[2025-11-05 20:50:57 UTC] ALERT [WARNING] content-analysis-v2-1: MEMORY_GROWTH: +15.2% growth (threshold: 10.0%)
```

**Immediate Actions:**

1. **Verify growth trend:**
   ```bash
   # Monitor for 30 minutes
   watch -n 300 'docker stats <container-name> --no-stream'
   ```

2. **Check if growth stabilizes:**
   ```bash
   # Compare with threshold
   # If continues growing → leak
   # If stabilizes → normal operation
   ```

**Root Cause Analysis:**

**Common Causes:**
- Memory leak (unclosed connections, circular refs)
- Cache without eviction policy
- Accumulated objects (list append without clear)
- File handles not closed

**Investigation:**
```bash
# Check for open connections
docker exec <container-name> lsof | grep ESTABLISHED | wc -l

# Check for large objects in memory (Python)
docker exec <container-name> python -c "
import gc
objects = gc.get_objects()
print(f'Total objects: {len(objects)}')
"

# Review code for common leak patterns
grep -r "open(" services/<service-name>/ | grep -v "with open"
```

**Resolution:**

**If connection leak:**
```python
# Bad: Connection not closed
conn = psycopg2.connect(...)
cursor = conn.cursor()
cursor.execute("SELECT ...")

# Good: Use context manager
with psycopg2.connect(...) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT ...")
```

**If cache leak:**
```python
# Bad: Unbounded cache
cache = {}
def get_data(key):
    if key not in cache:
        cache[key] = expensive_operation()
    return cache[key]

# Good: Use cachetools with size limit
from cachetools import LRUCache
cache = LRUCache(maxsize=1000)
```

**If object accumulation:**
```python
# Bad: List grows indefinitely
results = []
for item in iterator:
    results.append(process(item))

# Good: Process in batches
batch_size = 100
batch = []
for item in iterator:
    batch.append(item)
    if len(batch) >= batch_size:
        process_batch(batch)
        batch.clear()
```

**Post-Incident:**
- Profile with `memory_profiler`
- Add memory leak tests
- Review all resource acquisition code

---

## General Alert Response Workflow

### Step 1: Acknowledge Alert (1 minute)

1. Check alert dashboard: http://localhost:3000/admin/health
2. Verify alert is real (not false positive)
3. Note severity: CRITICAL vs WARNING

### Step 2: Initial Assessment (5 minutes)

1. **Container Health:**
   ```bash
   docker ps | grep <service-name>
   docker stats <service-name> --no-stream
   ```

2. **Service Functionality:**
   ```bash
   curl http://localhost:<port>/health
   # Should return 200 OK
   ```

3. **Recent Changes:**
   ```bash
   git log --oneline -10
   # Check for recent deploys
   ```

### Step 3: Mitigation (10 minutes)

**Priority: Restore Service**

1. **If service is down:**
   ```bash
   docker compose restart <service-name>
   ```

2. **If unresponsive:**
   ```bash
   docker compose stop <service-name>
   docker compose start <service-name>
   ```

3. **If repeatedly failing:**
   ```bash
   # Rollback to last known good version
   git checkout <previous-commit>
   docker compose build <service-name>
   docker compose up -d <service-name>
   ```

### Step 4: Root Cause Analysis (30 minutes)

1. **Collect Evidence:**
   - Container logs: `docker logs <container-name> --tail 500 > /tmp/incident-logs.txt`
   - Metrics: Screenshot from dashboard
   - Timeline: When did alert start?

2. **Reproduce Issue:**
   - Can you trigger alert again?
   - Is it consistent or intermittent?

3. **Identify Root Cause:**
   - Use runbook sections above
   - Check POSTMORTEMS.md for similar incidents

### Step 5: Permanent Fix (varies)

1. **Code Fix:**
   - Create feature branch
   - Implement fix
   - Add test to prevent regression
   - PR review

2. **Configuration Fix:**
   - Update docker-compose.yml
   - Update .env files
   - Document in ADR if architectural change

3. **Infrastructure Fix:**
   - Adjust thresholds in .env.monitoring
   - Add health check if missing
   - Update PID limits

### Step 6: Documentation (15 minutes)

1. **Update POSTMORTEMS.md:**
   - Timeline of events
   - Root cause
   - Resolution
   - Prevention measures

2. **Update Runbooks:**
   - Add new alert type if needed
   - Update investigation steps
   - Add learnings

3. **Notify Team:**
   - Post incident report
   - Share learnings
   - Update monitoring if needed

---

## False Positives

### Threshold Too Low

**Symptom:** Alerts during normal operation

**Solution:**
```bash
# Edit thresholds
nano .env.monitoring

# Increase threshold
PID_THRESHOLD=150  # was: 100
MEMORY_PERCENT_THRESHOLD=15.0  # was: 10.0

# Restart timer
sudo systemctl restart docker-monitor.timer
```

### Baseline Shift

**Symptom:** Alerts after system upgrade

**Solution:**
- Monitor for 1 week to establish new baseline
- Adjust thresholds based on new normal
- Document baseline in monitoring-setup.md

### Burst Activity

**Symptom:** Alerts during known high-activity periods

**Solution:**
- Temporarily disable auto-refresh on dashboard
- Consider time-based threshold adjustments
- Add context to alerts (e.g., "during batch job")

---

## Escalation

### When to Escalate

1. **Service down > 15 minutes**
2. **Data loss suspected**
3. **Security incident (unauthorized access)**
4. **Multiple cascading failures**

### Escalation Contacts

1. **Technical Lead:** Check CODEOWNERS
2. **DevOps:** Check team contacts
3. **On-call Engineer:** Check PagerDuty/OpsGenie

### Escalation Template

```
INCIDENT: [Service Name] - [Issue Type]
SEVERITY: [CRITICAL/HIGH/MEDIUM]
STARTED: [Timestamp]
IMPACT: [User-facing impact]
ACTIONS TAKEN:
- [Action 1]
- [Action 2]
CURRENT STATUS: [Current state]
NEED: [What you need help with]
```

---

## Post-Incident Review (PIR)

**Timing:** Within 48 hours of incident resolution

**Participants:**
- Incident responder
- Service owner
- Technical lead (if escalated)

**Agenda:**
1. Timeline review (5 min)
2. Root cause analysis (10 min)
3. What went well (5 min)
4. What could be improved (10 min)
5. Action items (10 min)

**Deliverables:**
- Updated POSTMORTEMS.md
- Action items in issue tracker
- Updated runbooks
- Training if needed

---

## Quick Commands Reference

```bash
# View all alerts
tail -f /tmp/docker-monitor-alerts.log

# Filter by severity
grep CRITICAL /tmp/docker-monitor-alerts.log

# Filter by service
grep "notification-service" /tmp/docker-monitor-alerts.log

# Count alerts per service
awk -F': ' '{print $1}' /tmp/docker-monitor-alerts.log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn

# Check systemd timer
systemctl status docker-monitor.timer

# Manual monitoring run
./scripts/monitor-resources.sh --alert-only

# API health check
curl http://localhost:8107/api/v1/health/summary | jq

# Container stats
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.PIDs}}"

# Restart all services
docker compose restart

# Rebuild and restart service
docker compose build <service-name> && docker compose up -d <service-name>
```

---

**Last Updated:** 2025-11-05
**Maintainer:** DevOps Team
**Review Frequency:** Quarterly or after major incidents
