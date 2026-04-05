# Analytics Service - Composite Index Migration Guide

## Quick Start

```bash
# 1. Enter container
docker compose exec analytics-service bash

# 2. Check current state
alembic current

# 3. Apply migration
alembic upgrade head

# 4. Verify indexes created
psql $DATABASE_URL -c "\d+ analytics_reports"
```

---

## What This Migration Does

Creates **4 composite indexes** to optimize query performance:

1. **`idx_analytics_reports_user_time`**
   - Columns: `(user_id, created_at DESC)`
   - Use case: User report lists sorted by date
   - Expected speedup: **20-100x faster**

2. **`idx_analytics_metrics_service_time_metric`**
   - Columns: `(service, timestamp DESC, metric_name)`
   - Use case: Time-series trend analysis
   - Expected speedup: **10-30x faster**

3. **`idx_analytics_alerts_user_enabled_triggered`**
   - Columns: `(user_id, enabled, last_triggered_at DESC)`
   - Use case: Active alert monitoring
   - Expected speedup: **10-20x faster**

4. **`idx_analytics_dashboards_user_updated`**
   - Columns: `(user_id, updated_at DESC)`
   - Use case: Dashboard list by recent updates
   - Expected speedup: **5-10x faster**

---

## Performance Expectations

### Before Migration
```sql
-- Query: List user reports
SELECT * FROM analytics_reports
WHERE user_id = 'andreas'
ORDER BY created_at DESC
LIMIT 20;

-- Performance:
-- 100K rows: 150-300ms
-- 1M rows:   1500-3000ms
-- Plan: Seq Scan + Sort
```

### After Migration
```sql
-- Same query
SELECT * FROM analytics_reports
WHERE user_id = 'andreas'
ORDER BY created_at DESC
LIMIT 20;

-- Performance:
-- 100K rows: 5-10ms    ✅ 30x faster
-- 1M rows:   8-15ms    ✅ 200x faster
-- Plan: Index Scan using idx_analytics_reports_user_time
```

---

## Deployment Steps

### Development/Staging

```bash
# Enter container
docker compose exec analytics-service bash

# Apply migration
alembic upgrade head

# Test query performance
psql $DATABASE_URL
```

```sql
-- Test 1: Verify index exists
\d+ analytics_reports

-- Test 2: Check query plan (should show "Index Scan")
EXPLAIN ANALYZE
SELECT * FROM analytics_reports
WHERE user_id = 'andreas'
ORDER BY created_at DESC
LIMIT 20;

-- Test 3: Monitor index usage
SELECT indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE tablename = 'analytics_reports';
```

### Production

**⚠️ IMPORTANT**: For tables with **>1M rows**, use concurrent index creation:

```bash
# 1. Edit migration file
# Change: postgresql_concurrently=False
# To:     postgresql_concurrently=True

# 2. Update alembic.ini
# Add: transaction_per_migration = false

# 3. Apply migration (non-blocking)
alembic upgrade head
# Index creation will run in background, no table locks!
```

**Timeline**:
- Small tables (<100K rows): 2-5 seconds
- Medium tables (100K-1M rows): 30-60 seconds
- Large tables (>1M rows): 3-10 minutes

---

## Verification

### 1. Check Indexes Were Created

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename LIKE 'analytics_%'
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

Expected output:
```
indexname                                 | indexdef
-----------------------------------------|------------------
idx_analytics_alerts_user_enabled_triggered | CREATE INDEX ...
idx_analytics_dashboards_user_updated    | CREATE INDEX ...
idx_analytics_metrics_service_time_metric| CREATE INDEX ...
idx_analytics_reports_user_time          | CREATE INDEX ...
```

---

### 2. Verify Query Performance

**Test Script**: `test_index_performance.sql`

```sql
-- Enable timing
\timing on

-- Test 1: Reports by user (most common query)
SELECT id, name, status, created_at
FROM analytics_reports
WHERE user_id = 'andreas'
ORDER BY created_at DESC
LIMIT 20;
-- Expected: 2-10ms

-- Test 2: Metrics time-series
SELECT metric_name, value, timestamp
FROM analytics_metrics
WHERE service = 'feed-service'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC
LIMIT 100;
-- Expected: 5-20ms

-- Test 3: Active alerts
SELECT id, name, severity, last_triggered_at
FROM analytics_alerts
WHERE user_id = 'andreas'
  AND enabled = true
ORDER BY last_triggered_at DESC;
-- Expected: 2-5ms
```

---

### 3. Monitor Index Usage

```sql
-- Run queries for 5 minutes, then check:
SELECT
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE indexname LIKE 'idx_analytics_%'
ORDER BY idx_scan DESC;
```

**Good Signs**:
- ✅ `idx_scan` increases with each query
- ✅ `idx_tup_read` proportional to result sets
- ✅ Query times match expectations

**Bad Signs**:
- ❌ `idx_scan = 0` after running queries → Index not used
- ❌ Query times unchanged → Check query plan

---

## Rollback

### If Issues Occur

```bash
# Immediate rollback
alembic downgrade -1

# Verify indexes removed
psql $DATABASE_URL -c "\d analytics_reports"
```

### Partial Rollback (Keep Some Indexes)

```sql
-- Drop only problematic index
DROP INDEX IF EXISTS idx_analytics_reports_user_time;

-- Keep others
```

---

## Troubleshooting

### Index Not Being Used

**Problem**: Query still slow after migration

**Solution**:
```sql
-- Update table statistics
ANALYZE analytics_reports;
ANALYZE analytics_metrics;
ANALYZE analytics_alerts;
ANALYZE analytics_dashboards;

-- Check query plan
EXPLAIN ANALYZE
SELECT * FROM analytics_reports
WHERE user_id = 'andreas'
ORDER BY created_at DESC;
```

**Expected plan**:
```
-> Index Scan using idx_analytics_reports_user_time
   Index Cond: (user_id = 'andreas')
```

---

### Index Creation Timeout

**Problem**: Migration takes too long (>10 minutes)

**Solution**:
```bash
# Use concurrent creation (edit migration first)
# Then retry:
alembic upgrade head
```

---

### Disk Space Error

**Problem**: "No space left on device" during index creation

**Calculation**:
```
Required space = Table size × 10-15%
Example: 1GB table → need 100-150MB free
```

**Solution**:
```bash
# Check available space
df -h /var/lib/postgresql

# Free up space or add disk
# Then retry migration
```

---

## Files Created

This migration creates:

1. **Migration Script**:
   - `/services/analytics-service/alembic/versions/20251124_1430_001_add_composite_indexes.py`

2. **Documentation**:
   - `/services/analytics-service/alembic/versions/README.md`
   - `/services/analytics-service/docs/COMPOSITE_INDEX_PERFORMANCE.md`
   - `/services/analytics-service/MIGRATION_GUIDE.md` (this file)

3. **Alembic Infrastructure** (if not exists):
   - `/services/analytics-service/alembic.ini`
   - `/services/analytics-service/alembic/env.py`
   - `/services/analytics-service/alembic/script.py.mako`

---

## Next Steps

After successful migration:

1. **Monitor Performance** (first 24 hours):
   ```bash
   # Watch index usage
   watch -n 5 "psql $DATABASE_URL -c \"
   SELECT indexname, idx_scan
   FROM pg_stat_user_indexes
   WHERE indexname LIKE 'idx_analytics_%'
   ORDER BY idx_scan DESC;
   \""
   ```

2. **Update Dashboards**:
   - Grafana: Add index usage panels
   - Alerts: Set up index bloat monitoring

3. **Document Results**:
   - Record actual performance improvements
   - Note any query plan changes
   - Update capacity planning estimates

---

## Questions?

- **Migration Issues**: Check `alembic/versions/README.md`
- **Performance Analysis**: See `docs/COMPOSITE_INDEX_PERFORMANCE.md`
- **Database Guides**: See `/docs/guides/database-optimization.md`

---

**Created**: 2025-11-24
**Migration Version**: 001
**Status**: Ready for deployment
