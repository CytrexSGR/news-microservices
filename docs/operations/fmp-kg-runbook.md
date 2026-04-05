# FMP-KG Integration Operations Runbook

**Service:** Knowledge-Graph Service (FMP Integration)
**Port:** 8111
**Owner:** Platform Engineering
**Last Updated:** 2025-11-16

---

## 1. Service Overview

### Architecture

```
FMP Service (8109) → Knowledge-Graph Service (8111) → Neo4j
     ↓                           ↓
Circuit Breaker          Prometheus Metrics
Rate Limiter            Structured Logging
Retry Logic             Health Checks
```

### Dependencies

| Service | Type | Port | Critical | Fallback |
|---------|------|------|----------|----------|
| FMP Service | HTTP | 8109 | Yes | Circuit Breaker |
| Neo4j | Database | 7687 | Yes | Connection Pool |
| Prometheus | Monitoring | 9090 | No | Metrics buffered |
| Grafana | Visualization | 3000 | No | N/A |

### Key Features

- **Market Sync:** Syncs 40 default assets from FMP → Neo4j
- **Resilience:** Circuit breaker, retry logic, rate limiting
- **Idempotency:** MERGE operations (safe re-runs)
- **Observability:** Full Prometheus metrics, structured logging

---

## 2. Startup Procedures

### Local Development

```bash
# 1. Ensure dependencies are running
docker ps | grep -E '(neo4j|knowledge-graph)'

# 2. If not running, start services
cd /home/cytrex/news-microservices
docker compose up -d neo4j knowledge-graph-service

# 3. Verify startup
docker logs knowledge-graph-service --tail 50

# 4. Check health
curl http://localhost:8111/health/ready

# Expected: {"status":"ready","checks":{"neo4j":"healthy",...}}
```

### Production Deployment

```bash
# 1. Pre-deployment checks
./scripts/pre_deploy_checks.sh knowledge-graph-service

# 2. Deploy new version (rolling update)
kubectl rollout status deployment/knowledge-graph-service
kubectl set image deployment/knowledge-graph-service \
  app=knowledge-graph-service:v1.1.0

# 3. Monitor rollout
kubectl rollout status deployment/knowledge-graph-service

# 4. Verify health
kubectl get pods -l app=knowledge-graph-service
kubectl logs -l app=knowledge-graph-service --tail=100

# 5. Smoke test
curl https://kg-service.example.com/health/ready
```

---

## 3. Shutdown Procedures

### Graceful Shutdown (Local)

```bash
# 1. Stop accepting new requests (optional - drain connections)
# This would be done via load balancer in production

# 2. Wait for in-flight requests (FastAPI handles this)
docker stop knowledge-graph-service --time 30

# 3. Verify shutdown
docker ps | grep knowledge-graph-service
# Should return nothing

# 4. Check logs for clean shutdown
docker logs knowledge-graph-service --tail 20
# Look for: "Shutting down gracefully"
```

### Emergency Shutdown

```bash
# Immediate stop (not recommended)
docker kill knowledge-graph-service

# Cleanup
docker rm knowledge-graph-service
```

### Production Shutdown

```bash
# 1. Scale down to 0 replicas
kubectl scale deployment knowledge-graph-service --replicas=0

# 2. Verify pods terminated
kubectl get pods -l app=knowledge-graph-service

# 3. Or delete deployment entirely
kubectl delete deployment knowledge-graph-service
```

---

## 4. Configuration Management

### Environment Variables

**Required:**
```bash
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secret>

# Service Configuration
SERVICE_NAME=knowledge-graph-service
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Optional:**
```bash
# FMP Integration
FMP_SERVICE_URL=http://fmp-service:8109
FMP_CIRCUIT_BREAKER_THRESHOLD=5
FMP_CIRCUIT_BREAKER_TIMEOUT=30

# Performance
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30
```

### Secrets Management

**Development (docker-compose.yml):**
```yaml
environment:
  NEO4J_PASSWORD: ${NEO4J_PASSWORD:-development}
```

**Production (Kubernetes Secret):**
```bash
# Create secret
kubectl create secret generic kg-service-secrets \
  --from-literal=neo4j-password=<secret> \
  --from-literal=fmp-api-key=<secret>

# Reference in deployment
env:
  - name: NEO4J_PASSWORD
    valueFrom:
      secretKeyRef:
        name: kg-service-secrets
        key: neo4j-password
```

### Configuration Files

**Location:** `services/knowledge-graph-service/app/core/config.py`

**Key Settings:**
```python
class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "knowledge-graph-service"
    API_V1_PREFIX: str = "/api/v1/graph"

    # Neo4j
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "development"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # or "text"
```

---

## 5. Deployment Checklist

### Pre-Deployment

- [ ] Code reviewed and approved
- [ ] Unit tests passing (158 tests, 98%+ coverage)
- [ ] Integration tests passing (10 scenarios)
- [ ] Security audit completed (no critical vulnerabilities)
- [ ] Database migrations prepared (if any)
- [ ] Configuration reviewed (env vars, secrets)
- [ ] Monitoring dashboards updated
- [ ] Runbooks updated

### Deployment Steps

1. **Backup Current State**
   ```bash
   # Neo4j snapshot
   ./scripts/neo4j_snapshot.sh

   # Config backup
   kubectl get configmap kg-service-config -o yaml > backup/config.yaml
   ```

2. **Deploy New Version**
   ```bash
   # Update image tag
   kubectl set image deployment/knowledge-graph-service \
     app=gcr.io/project/kg-service:v1.1.0

   # Or apply updated manifest
   kubectl apply -f k8s/knowledge-graph-service.yaml
   ```

3. **Monitor Rollout**
   ```bash
   # Watch pod status
   kubectl rollout status deployment/knowledge-graph-service

   # Check logs
   kubectl logs -f deployment/knowledge-graph-service
   ```

4. **Smoke Tests**
   ```bash
   # Health check
   curl https://kg-service/health/ready

   # Trigger sync
   curl -X POST https://kg-service/api/v1/graph/markets/sync

   # Verify Neo4j data
   curl https://kg-service/api/v1/graph/markets?limit=10
   ```

5. **Verify Metrics**
   ```bash
   # Check Grafana dashboard
   # → http://grafana/d/fmp-kg-integration

   # Verify no error spike
   # → Error Rate panel should be < 1%
   ```

### Post-Deployment

- [ ] Health checks passing (liveness + readiness)
- [ ] Metrics reporting correctly
- [ ] No error spike in logs
- [ ] SLOs within targets
- [ ] Database queries performing well (P95 < 5ms)
- [ ] Circuit breaker closed
- [ ] Documentation updated

---

## 6. Rollback Procedures

### Automatic Rollback (Kubernetes)

```bash
# Rollback to previous version
kubectl rollout undo deployment/knowledge-graph-service

# Rollback to specific revision
kubectl rollout history deployment/knowledge-graph-service
kubectl rollout undo deployment/knowledge-graph-service --to-revision=3

# Verify rollback
kubectl rollout status deployment/knowledge-graph-service
```

### Manual Rollback (Docker)

```bash
# 1. Stop current version
docker stop knowledge-graph-service

# 2. Start previous version
docker run -d --name knowledge-graph-service \
  --network news-microservices_default \
  -p 8111:8111 \
  knowledge-graph-service:v1.0.0

# 3. Verify
curl http://localhost:8111/health/ready
```

### Database Rollback

```bash
# If schema migration needed
# 1. Identify migration to rollback
alembic history

# 2. Downgrade to previous version
alembic downgrade -1

# 3. Verify
alembic current
```

---

## 7. Common Operational Tasks

### Manual Market Sync

```bash
# Sync all default markets (40 assets)
curl -X POST http://localhost:8111/api/v1/graph/markets/sync

# Sync specific asset types
curl -X POST http://localhost:8111/api/v1/graph/markets/sync \
  -H "Content-Type: application/json" \
  -d '{"asset_types": ["STOCK", "FOREX"]}'

# Sync specific symbols
curl -X POST http://localhost:8111/api/v1/graph/markets/sync \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "GOOGL", "MSFT"]}'

# Force refresh (ignore cache)
curl -X POST http://localhost:8111/api/v1/graph/markets/sync \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": true}'
```

### Query Market Data

```bash
# List all markets
curl http://localhost:8111/api/v1/graph/markets?limit=100

# Get specific market
curl http://localhost:8111/api/v1/graph/markets/AAPL

# Get market statistics
curl http://localhost:8111/api/v1/graph/markets/stats
```

### Check Circuit Breaker Status

```bash
# Via metrics endpoint
curl http://localhost:8111/health/metrics | grep circuit_breaker_state

# Via Grafana dashboard
# → http://grafana/d/fmp-kg-integration
# → Circuit Breaker Status panel
```

### Reset Circuit Breaker (Manual)

```python
# Connect to service container
docker exec -it knowledge-graph-service python

# Execute reset
from app.clients.circuit_breaker import circuit_breaker_registry
circuit_breaker_registry['fmp_service'].reset()
```

### Clear Neo4j Cache

```cypher
// Connect to Neo4j
docker exec -it neo4j cypher-shell -u neo4j -p <password>

// Clear query cache
CALL db.clearQueryCaches();

// Verify
CALL dbms.listQueries();
```

### View Logs

```bash
# Docker
docker logs knowledge-graph-service --tail 100 --follow

# Kubernetes
kubectl logs -f deployment/knowledge-graph-service

# Filter by correlation ID
kubectl logs deployment/knowledge-graph-service | \
  jq 'select(.correlation_id == "550e8400-...")'

# Find errors
kubectl logs deployment/knowledge-graph-service | \
  jq 'select(.level == "ERROR")'
```

---

## 8. Monitoring Dashboards

### Grafana Dashboard

**URL:** `http://grafana/d/fmp-kg-integration`

**Key Panels:**
1. Market Sync Success Rate (7d) - Target: > 95%
2. Average Sync Duration - Target: P95 < 200ms
3. Market Counts - Expected: 40 total, 40 active
4. Circuit Breaker Status - Expected: Closed (Green)
5. Neo4j Query Performance - Target: P95 < 5ms
6. Error Rate - Target: < 1%

### Prometheus Queries

```promql
# Availability (last 1h)
sum(rate(fmp_sync_requests_total{status="success"}[1h])) /
sum(rate(fmp_sync_requests_total[1h]))

# P95 Latency
histogram_quantile(0.95, rate(fmp_sync_duration_seconds_bucket[5m]))

# Error Rate
sum(rate(neo4j_query_errors_total[5m])) /
sum(rate(neo4j_query_duration_seconds_count[5m]))

# Active Markets
sum(fmp_active_markets)
```

---

## 9. Backup and Recovery

### Neo4j Backup

```bash
# Snapshot (requires Neo4j Enterprise or neo4j-admin)
docker exec neo4j neo4j-admin dump \
  --database=neo4j \
  --to=/backups/neo4j-$(date +%Y%m%d-%H%M%S).dump

# Copy to local
docker cp neo4j:/backups/neo4j-20251116.dump ./backups/
```

### Restore from Backup

```bash
# Stop Neo4j
docker stop neo4j

# Restore
docker run --rm \
  -v neo4j_data:/data \
  -v $(pwd)/backups:/backups \
  neo4j:5.13 \
  neo4j-admin load \
    --from=/backups/neo4j-20251116.dump \
    --database=neo4j --force

# Start Neo4j
docker start neo4j

# Verify
docker exec neo4j cypher-shell -u neo4j -p <password> \
  "MATCH (m:MARKET) RETURN count(m) as total;"
```

---

## 10. Troubleshooting Quick Reference

| Symptom | First Check | Quick Fix |
|---------|-------------|-----------|
| Service not starting | Logs, dependencies | `docker compose up -d` |
| Sync failures | Circuit breaker, FMP Service | Check `/health/metrics` |
| Slow queries | Neo4j indexes | `CALL db.indexes()` |
| High error rate | Logs, Neo4j connection | Restart service |
| No metrics | Prometheus scraping | Check `/health/metrics` |

**Full Guide:** [fmp-kg-troubleshooting.md](fmp-kg-troubleshooting.md)

---

## 11. Contacts and Escalation

### On-Call Rotation

- **Primary:** Platform Engineering Team
- **Secondary:** Backend Team
- **Manager:** Engineering Lead

### Escalation Path

1. **L1 (0-15min):** On-call engineer investigates
2. **L2 (15-30min):** Team lead involved if unresolved
3. **L3 (30-60min):** Engineering manager, consider rollback
4. **L4 (60min+):** CTO, customer communication

### Communication Channels

- **Slack:** `#platform-alerts` (automated alerts)
- **Slack:** `#platform-oncall` (incidents)
- **PagerDuty:** Critical alerts only
- **Email:** platform-team@example.com

---

## 12. Maintenance Windows

### Scheduled Maintenance

**Frequency:** Monthly (first Sunday, 02:00-04:00 UTC)

**Activities:**
- Database vacuuming
- Index optimization
- Log rotation
- Dependency updates

**Procedure:**
1. Announce maintenance 48h in advance
2. Scale service to 0 replicas
3. Perform maintenance tasks
4. Scale back to normal
5. Verify health and metrics

### Emergency Maintenance

**Triggers:**
- Critical security vulnerability
- Data corruption
- Cascading failures

**Procedure:**
1. Incident commander declared
2. Service degradation announced
3. Emergency fix applied
4. Post-mortem scheduled within 24h

---

**Document Version:** 1.0
**Maintained By:** Platform Engineering
**Next Review:** 2025-12-16
