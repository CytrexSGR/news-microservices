# FMP-KG Integration Troubleshooting Guide

**Service:** Knowledge-Graph Service (FMP Integration)
**Last Updated:** 2025-11-16
**Format:** Symptom → Diagnosis → Resolution

---

## Quick Diagnostic Commands

```bash
# Service Health
curl http://localhost:8111/health/ready

# Recent Logs
docker logs knowledge-graph-service --tail 100

# Metrics Check
curl http://localhost:8111/health/metrics | grep -E '(fmp_sync|circuit_breaker|neo4j_query)'

# Neo4j Connection
docker exec neo4j cypher-shell -u neo4j -p <password> "RETURN 1;"

# Circuit Breaker State
curl http://localhost:8111/health/metrics | grep circuit_breaker_state
```

---

## 1. Market Sync Failures

### 1.1 FMP Service Unavailable

**Symptoms:**
- Sync requests return 503 errors
- Logs show: `FMP Service unavailable`
- Circuit breaker state = 1 (OPEN)

**Diagnosis:**
```bash
# Check FMP Service health
curl http://localhost:8109/health

# Check circuit breaker
curl http://localhost:8111/health/metrics | grep circuit_breaker_state{service=\"fmp_service\"}
```

**Resolution:**

1. **Verify FMP Service is running:**
   ```bash
   docker ps | grep fmp-service

   # If not running
   docker compose up -d fmp-service
   ```

2. **Check FMP Service logs:**
   ```bash
   docker logs fmp-service --tail 50

   # Look for errors, rate limits, or crashes
   ```

3. **Wait for circuit breaker recovery (30s):**
   ```bash
   # Monitor state transition: open → half_open → closed
   watch -n 5 'curl -s http://localhost:8111/health/metrics | grep circuit_breaker_state'
   ```

4. **Manual retry after recovery:**
   ```bash
   curl -X POST http://localhost:8111/api/v1/graph/markets/sync
   ```

**Prevention:**
- Ensure FMP Service has adequate resources
- Monitor FMP Service health
- Consider increasing circuit breaker threshold if transient failures common

### 1.2 Rate Limit Exceeded

**Symptoms:**
- Sync succeeds partially
- Logs show: `FMP API rate limit exceeded`
- HTTP 429 responses from FMP Service

**Diagnosis:**
```bash
# Check rate limit status in logs
docker logs knowledge-graph-service | grep "rate limit"

# View sync results
curl http://localhost:8111/api/v1/graph/markets/sync
# Look for: "status": "partial", "failed": > 0
```

**Resolution:**

1. **Check current usage:**
   ```bash
   # FMP free tier: 250 calls/day
   # Check daily consumption
   curl http://localhost:8109/api/v1/usage/stats
   ```

2. **Reduce sync frequency:**
   ```python
   # Update scheduler (if automated)
   # Change from hourly to every 4 hours
   SYNC_INTERVAL = "0 */4 * * *"  # Every 4 hours
   ```

3. **Sync only critical assets:**
   ```bash
   # Instead of all 40 assets
   curl -X POST http://localhost:8111/api/v1/graph/markets/sync \
     -H "Content-Type: application/json" \
     -d '{"symbols": ["AAPL", "GOOGL", "MSFT", "EURUSD"]}'
   ```

4. **Upgrade FMP plan (if available):**
   - Contact FMP support
   - Upgrade to paid tier (higher limits)

**Prevention:**
- Implement adaptive sync frequency
- Cache frequently accessed data
- Monitor daily usage proactively

### 1.3 Partial Sync Failures

**Symptoms:**
- Some assets sync successfully, others fail
- Logs show individual asset errors
- Status: "partial"

**Diagnosis:**
```bash
# View sync results
curl -X POST http://localhost:8111/api/v1/graph/markets/sync

# Example response:
# {
#   "status": "partial",
#   "total_assets": 40,
#   "synced": 35,
#   "failed": 5,
#   "errors": [
#     {"symbol": "INVALID", "error": "Asset not found"},
#     ...
#   ]
# }
```

**Resolution:**

1. **Identify failing symbols:**
   ```bash
   # Parse sync response
   curl -X POST http://localhost:8111/api/v1/graph/markets/sync | \
     jq '.errors[] | .symbol'
   ```

2. **Check symbol validity:**
   ```bash
   # Verify symbol exists in FMP
   curl "http://localhost:8109/api/v1/metadata/assets?symbols=INVALID"
   ```

3. **Remove invalid symbols from default list:**
   ```python
   # Edit: app/services/fmp_integration/market_sync_service.py
   DEFAULT_SYMBOLS = [
       # Remove or comment out invalid symbols
       # "INVALID",
   ]
   ```

4. **Re-sync after cleanup:**
   ```bash
   curl -X POST http://localhost:8111/api/v1/graph/markets/sync \
     -d '{"force_refresh": true}'
   ```

**Prevention:**
- Validate symbols before adding to default list
- Implement symbol validation endpoint
- Monitor partial sync rate (alert if > 10%)

---

## 2. Neo4j Connection Issues

### 2.1 Connection Refused

**Symptoms:**
- Readiness probe fails
- Logs show: `Neo4j connection refused`
- All requests fail with 503

**Diagnosis:**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Test connection
docker exec neo4j cypher-shell -u neo4j -p <password> "RETURN 1;"

# Check network
docker network inspect news-microservices_default | grep neo4j
```

**Resolution:**

1. **Start Neo4j if not running:**
   ```bash
   docker compose up -d neo4j

   # Wait for startup (can take 30-60s)
   docker logs neo4j --follow
   # Look for: "Started."
   ```

2. **Verify network connectivity:**
   ```bash
   docker exec knowledge-graph-service ping neo4j
   ```

3. **Check credentials:**
   ```bash
   # Verify NEO4J_PASSWORD env var
   docker exec knowledge-graph-service env | grep NEO4J_PASSWORD

   # Test with correct credentials
   docker exec neo4j cypher-shell -u neo4j -p <correct-password>
   ```

4. **Restart KG Service:**
   ```bash
   docker restart knowledge-graph-service
   ```

**Prevention:**
- Use Docker healthchecks for Neo4j
- Implement connection retry logic (already present)
- Monitor Neo4j resource usage

### 2.2 Slow Queries (P95 > 5ms)

**Symptoms:**
- Neo4j query latency alert firing
- P95 latency > 5ms
- User-facing slowness

**Diagnosis:**
```bash
# Check query performance
curl http://localhost:8111/health/metrics | grep neo4j_query_duration_seconds

# View slow queries in Neo4j
docker exec neo4j cypher-shell -u neo4j -p <password> << EOF
CALL dbms.listQueries() YIELD query, elapsedTimeMillis
WHERE elapsedTimeMillis > 5
RETURN query, elapsedTimeMillis
ORDER BY elapsedTimeMillis DESC;
EOF
```

**Resolution:**

1. **Check indexes exist:**
   ```cypher
   CALL db.indexes();

   // Expected indexes:
   // - market_symbol_unique (MARKET.symbol)
   // - market_asset_type_active_idx (MARKET.asset_type, is_active)
   // - market_name_search_idx (MARKET.name - fulltext)
   ```

2. **Rebuild indexes if missing:**
   ```bash
   # Re-run migration
   docker exec neo4j cypher-shell -u neo4j -p <password> \
     < services/knowledge-graph-service/migrations/neo4j/001_market_schema.cypher
   ```

3. **Optimize query patterns:**
   ```cypher
   // ❌ Slow (full scan)
   MATCH (m:MARKET) WHERE m.name CONTAINS 'Apple' RETURN m;

   // ✅ Fast (index lookup)
   MATCH (m:MARKET {symbol: 'AAPL'}) RETURN m;

   // ✅ Fast (fulltext index)
   CALL db.index.fulltext.queryNodes('market_name_search_idx', 'Apple')
   YIELD node RETURN node;
   ```

4. **Check database statistics:**
   ```cypher
   CALL apoc.meta.stats();
   // Look for:
   // - nodeCount: Should be ~40 for default setup
   // - relCount: Varies by sector relationships
   ```

**Prevention:**
- Monitor P95 latency continuously
- Run EXPLAIN on new queries before deploying
- Periodic index maintenance (rebuild quarterly)

### 2.3 Connection Pool Exhaustion

**Symptoms:**
- Intermittent 503 errors
- Logs show: `Connection pool exhausted`
- High concurrent request load

**Diagnosis:**
```bash
# Check active connections
docker exec neo4j cypher-shell -u neo4j -p <password> \
  "CALL dbms.listConnections() YIELD connectionId RETURN count(connectionId);"

# Check pool size configuration
docker exec knowledge-graph-service env | grep NEO4J_MAX_CONNECTION_POOL_SIZE
```

**Resolution:**

1. **Increase pool size:**
   ```yaml
   # docker-compose.yml
   environment:
     NEO4J_MAX_CONNECTION_POOL_SIZE: 100  # Default: 50
   ```

2. **Restart service:**
   ```bash
   docker compose up -d knowledge-graph-service
   ```

3. **Monitor connection usage:**
   ```bash
   # Add to Prometheus metrics (future enhancement)
   # neo4j_connection_pool_active
   # neo4j_connection_pool_idle
   ```

**Prevention:**
- Size pool based on expected concurrency
- Implement connection pooling monitoring
- Use async/await properly (avoid blocking)

---

## 3. Circuit Breaker Issues

### 3.1 Circuit Breaker Open

**Symptoms:**
- All sync requests fail immediately
- Logs show: `Circuit breaker is OPEN`
- `circuit_breaker_state{service="fmp_service"}` = 1

**Diagnosis:**
```bash
# Check circuit breaker state
curl http://localhost:8111/health/metrics | grep circuit_breaker_state

# Check failure count
docker logs knowledge-graph-service | grep "Circuit breaker" | tail -20
```

**Resolution:**

1. **Identify root cause:**
   ```bash
   # Check FMP Service health
   curl http://localhost:8109/health

   # Check recent errors
   docker logs knowledge-graph-service | grep ERROR | tail -50
   ```

2. **Fix underlying issue:**
   - If FMP Service down: `docker compose up -d fmp-service`
   - If network issue: Check Docker network
   - If rate limit: Wait for quota reset

3. **Wait for automatic recovery (30s timeout):**
   ```bash
   # Monitor state transition
   watch -n 5 'curl -s http://localhost:8111/health/metrics | grep circuit_breaker_state'

   # States: 1 (OPEN) → 2 (HALF_OPEN) → 0 (CLOSED)
   ```

4. **Manual reset (if necessary):**
   ```python
   # Only if auto-recovery fails
   docker exec -it knowledge-graph-service python << EOF
   from app.clients.circuit_breaker import circuit_breaker_registry
   cb = circuit_breaker_registry['fmp_service']
   cb.reset()
   print(f"Circuit breaker reset. State: {cb.state}")
   EOF
   ```

**Prevention:**
- Monitor failure rate proactively
- Tune circuit breaker thresholds (default: 5 failures)
- Implement graceful degradation (cached data)

### 3.2 Circuit Breaker Half-Open (Stuck)

**Symptoms:**
- Circuit breaker stuck in HALF_OPEN for > 5min
- Intermittent failures
- `circuit_breaker_state` = 2

**Diagnosis:**
```bash
# Check state duration
docker logs knowledge-graph-service | grep "Circuit breaker" | grep HALF_OPEN

# Check test request results
docker logs knowledge-graph-service | grep "Circuit breaker test"
```

**Resolution:**

1. **Check if test requests are succeeding:**
   ```bash
   # Manual test request
   curl http://localhost:8109/api/v1/metadata/assets?symbols=AAPL
   ```

2. **If FMP Service healthy, force reset:**
   ```python
   docker exec -it knowledge-graph-service python << EOF
   from app.clients.circuit_breaker import circuit_breaker_registry
   circuit_breaker_registry['fmp_service'].close()
   EOF
   ```

3. **If FMP Service still unhealthy:**
   ```bash
   # Restart FMP Service
   docker restart fmp-service

   # Wait for circuit breaker to close automatically
   ```

**Prevention:**
- Monitor HALF_OPEN duration (alert if > 5min)
- Implement exponential backoff for test requests
- Add metrics for circuit breaker transitions

---

## 4. High Latency (P95 > 200ms)

### 4.1 Sync Operation Slow

**Symptoms:**
- `FMPSyncLatencyHigh` alert firing
- P95 sync duration > 200ms
- User-facing timeout errors

**Diagnosis:**
```bash
# Check P95 latency
curl http://localhost:8111/health/metrics | grep fmp_sync_duration_seconds

# View recent sync durations
docker logs knowledge-graph-service | grep "Sync operation" | tail -10 | jq '.duration_ms'
```

**Resolution:**

1. **Check FMP Service latency:**
   ```bash
   time curl http://localhost:8109/api/v1/metadata/assets
   # Should be < 100ms
   ```

2. **Check Neo4j query latency:**
   ```bash
   curl http://localhost:8111/health/metrics | grep neo4j_query_duration_seconds
   # P95 should be < 5ms
   ```

3. **Reduce batch size:**
   ```python
   # Edit: app/services/fmp_integration/market_sync_service.py
   # Sync in smaller batches (10 instead of 40)
   for batch in chunks(symbols, size=10):
       await self.sync_batch(batch)
   ```

4. **Enable parallel processing:**
   ```python
   # Use asyncio.gather for parallel Neo4j writes
   import asyncio

   tasks = [self._sync_single_asset(asset) for asset in metadata]
   await asyncio.gather(*tasks)
   ```

**Prevention:**
- Monitor sync duration continuously
- Implement adaptive batch sizing
- Use caching for frequently accessed data

### 4.2 Database Bottleneck

**Symptoms:**
- Neo4j CPU/memory high
- Slow query performance across all operations

**Diagnosis:**
```bash
# Check Neo4j resource usage
docker stats neo4j

# Check active queries
docker exec neo4j cypher-shell -u neo4j -p <password> "CALL dbms.listQueries();"
```

**Resolution:**

1. **Scale Neo4j resources:**
   ```yaml
   # docker-compose.yml
   services:
     neo4j:
       deploy:
         resources:
           limits:
             cpus: '2.0'  # Increase from 1.0
             memory: 2G   # Increase from 1G
   ```

2. **Optimize queries (see 2.2 Slow Queries)**

3. **Enable query caching:**
   ```bash
   # Neo4j conf
   docker exec neo4j neo4j-admin set-config db.cache.query.enable=true
   ```

**Prevention:**
- Monitor database resources (CPU, memory, disk I/O)
- Implement query result caching (Redis)
- Consider read replicas for high read load

---

## 5. Memory/CPU Issues

### 5.1 High Memory Usage

**Symptoms:**
- Container OOMKilled
- Logs show memory warnings
- Slow performance

**Diagnosis:**
```bash
# Check memory usage
docker stats knowledge-graph-service

# Check Python memory profiling
docker exec knowledge-graph-service python << EOF
import gc
print(f"Objects: {len(gc.get_objects())}")
EOF
```

**Resolution:**

1. **Increase memory limit:**
   ```yaml
   # docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 1G  # Increase from 512M
   ```

2. **Check for memory leaks:**
   ```python
   # Add memory profiling
   from memory_profiler import profile

   @profile
   def sync_markets(...):
       pass
   ```

3. **Restart service:**
   ```bash
   docker restart knowledge-graph-service
   ```

**Prevention:**
- Monitor memory usage trends
- Implement memory leak detection
- Use connection pooling properly

### 5.2 High CPU Usage

**Symptoms:**
- CPU usage > 80%
- Slow response times
- Request timeouts

**Diagnosis:**
```bash
# Check CPU usage
docker stats knowledge-graph-service

# Profile CPU usage
docker exec knowledge-graph-service python -m cProfile -s cumtime app/main.py
```

**Resolution:**

1. **Reduce concurrent requests:**
   ```yaml
   # Limit workers
   command: uvicorn app.main:app --host 0.0.0.0 --port 8111 --workers 2
   ```

2. **Optimize hot code paths:**
   - Use async/await properly
   - Avoid blocking I/O
   - Use bulk operations

3. **Scale horizontally:**
   ```bash
   kubectl scale deployment knowledge-graph-service --replicas=3
   ```

**Prevention:**
- Load testing before deployment
- CPU profiling in staging
- Implement auto-scaling

---

## 6. Data Quality Issues

### 6.1 Stale Market Data

**Symptoms:**
- `MarketDataStale` alert firing
- No sync in > 1 hour
- Market prices outdated

**Diagnosis:**
```bash
# Check last sync timestamp
curl http://localhost:8111/health/metrics | grep fmp_sync_requests_total

# Check sync scheduler
docker logs knowledge-graph-service | grep "Scheduled sync"
```

**Resolution:**

1. **Manual trigger sync:**
   ```bash
   curl -X POST http://localhost:8111/api/v1/graph/markets/sync \
     -d '{"force_refresh": true}'
   ```

2. **Verify scheduler configuration:**
   ```python
   # Check: app/workers/sync_scheduler.py
   SYNC_INTERVAL = "0 * * * *"  # Every hour
   ```

3. **Restart scheduler:**
   ```bash
   docker restart knowledge-graph-service
   ```

**Prevention:**
- Monitor sync frequency
- Alert on missing syncs
- Implement backup sync mechanism

### 6.2 Low Active Markets Count

**Symptoms:**
- `ActiveMarketsLow` alert firing
- Active markets < 10 (expected: 40)
- Data completeness issues

**Diagnosis:**
```bash
# Check market counts
curl http://localhost:8111/api/v1/graph/markets/stats

# Query Neo4j directly
docker exec neo4j cypher-shell -u neo4j -p <password> << EOF
MATCH (m:MARKET)
RETURN m.is_active, count(m) as count
GROUP BY m.is_active;
EOF
```

**Resolution:**

1. **Identify inactive markets:**
   ```cypher
   MATCH (m:MARKET {is_active: false})
   RETURN m.symbol, m.name;
   ```

2. **Check activation logic:**
   ```python
   # Verify: app/services/fmp_integration/market_sync_service.py
   # Ensure is_active is set correctly from FMP metadata
   ```

3. **Re-sync with force refresh:**
   ```bash
   curl -X POST http://localhost:8111/api/v1/graph/markets/sync \
     -d '{"force_refresh": true}'
   ```

**Prevention:**
- Monitor active vs inactive ratio
- Validate activation logic in tests
- Alert on unexpected deactivations

---

## 7. Common Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `FMP Service unavailable` | FMP Service down/unreachable | Check FMP Service health, wait for circuit breaker recovery |
| `Neo4j connection refused` | Neo4j not running/network issue | Start Neo4j, verify network connectivity |
| `Circuit breaker is OPEN` | Too many failures to FMP Service | Wait 30s for recovery, fix underlying issue |
| `API rate limit exceeded` | FMP API quota exhausted | Reduce sync frequency, upgrade plan |
| `Connection pool exhausted` | Too many concurrent requests | Increase pool size, optimize queries |
| `Query timeout` | Slow Neo4j query | Check indexes, optimize query |
| `Asset not found` | Invalid symbol in sync list | Remove invalid symbol, validate list |

---

## 8. Escalation Matrix

| Issue Severity | Response Time | Escalation Path |
|----------------|---------------|-----------------|
| P0 - Critical (service down) | Immediate | On-call → Team Lead → Engineering Manager |
| P1 - High (degraded) | 15 minutes | On-call → Team Lead |
| P2 - Medium | 1 hour | On-call (during business hours) |
| P3 - Low | Next business day | Team backlog |

---

## 9. Post-Incident Checklist

After resolving an incident:

- [ ] Document root cause
- [ ] Update runbooks if needed
- [ ] Create follow-up tasks (prevention, monitoring)
- [ ] Post-mortem scheduled (P0/P1 incidents only)
- [ ] Inform stakeholders of resolution
- [ ] Update SLO dashboard if SLO violated
- [ ] Review error budget impact

---

**Document Version:** 1.0
**Maintained By:** Platform Engineering
**Next Review:** 2025-12-16
