# Analytics Service Database Migrations

## Overview

This directory contains Alembic migrations for the Analytics Service database schema.

## Migration Naming Convention

```
YYYYMMDD_HHMM_NNN_descriptive_name.py
```

- **YYYYMMDD**: Date of creation
- **HHMM**: Time of creation (24h format)
- **NNN**: Sequential number (001, 002, etc.)
- **descriptive_name**: Short description of the migration

## Current Migrations

### 001 - Composite Indexes (2025-11-24)

**File**: `20251124_1430_001_add_composite_indexes.py`

**Purpose**: Add composite indexes for common query patterns

**Indexes Created**:
1. `idx_analytics_reports_user_time` - User reports sorted by date
2. `idx_analytics_metrics_service_time_metric` - Time-series metric queries
3. `idx_analytics_alerts_user_enabled_triggered` - Active alert monitoring
4. `idx_analytics_dashboards_user_updated` - User dashboard sorting

**Performance Impact**:
- **Query Speed**: 5-50x faster for covered queries
- **Index Creation Time**: 2-5 seconds (100K rows), 30-60 seconds (1M rows)
- **Storage Overhead**: ~5-10% per index
- **Write Performance**: <5% slower inserts

## Running Migrations

### In Docker Container

```bash
# Enter analytics-service container
docker compose exec analytics-service bash

# Run all pending migrations
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Local Development

```bash
cd services/analytics-service

# Ensure DATABASE_URL is set in .env
# Run migrations
alembic upgrade head
```

## Creating New Migrations

### Auto-generate from model changes:

```bash
# From services/analytics-service directory
alembic revision --autogenerate -m "Description of changes"
```

### Manual migration:

```bash
alembic revision -m "Description of changes"
```

Then edit the generated file in `alembic/versions/`.

## Testing Migrations

### Before applying to production:

1. **Test on staging database**:
   ```bash
   # Connect to staging
   alembic upgrade head

   # Verify indexes
   psql -h localhost -U news_user -d news_mcp_staging
   \d+ analytics_reports
   ```

2. **Benchmark performance**:
   ```sql
   -- Before migration
   EXPLAIN ANALYZE
   SELECT * FROM analytics_reports
   WHERE user_id = 'test-user'
   ORDER BY created_at DESC
   LIMIT 20;

   -- After migration (should show "Index Scan using idx_analytics_reports_user_time")
   ```

3. **Check index usage**:
   ```sql
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
   FROM pg_stat_user_indexes
   WHERE tablename LIKE 'analytics_%'
   ORDER BY idx_scan DESC;
   ```

## Rollback Procedures

### Emergency rollback:

```bash
# Downgrade to previous revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade all migrations
alembic downgrade base
```

### Verify rollback:

```sql
-- Check indexes are removed
SELECT indexname FROM pg_indexes
WHERE tablename LIKE 'analytics_%'
AND indexname LIKE 'idx_%';
```

## Performance Monitoring

### Query Performance (Before/After):

```sql
-- Enable query timing
\timing on

-- Test user reports query (most common pattern)
SELECT id, name, status, created_at
FROM analytics_reports
WHERE user_id = 'andreas'
ORDER BY created_at DESC
LIMIT 20;

-- Expected improvement: 100-500ms → 5-10ms
```

### Index Health Check:

```sql
-- Check index bloat
SELECT schemaname, tablename, indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
       idx_scan as index_scans,
       idx_tup_read as tuples_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename LIKE 'analytics_%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Index Usage Statistics:

```sql
-- Monitor index usage over time
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND indexname LIKE 'idx_analytics_%'
ORDER BY idx_scan DESC;
```

## Troubleshooting

### Migration fails with "relation already exists"

```bash
# Check existing indexes
psql -c "\d analytics_reports"

# If index exists, either:
# 1. Skip this migration (mark as applied)
alembic stamp head

# 2. Or drop existing index manually and retry
psql -c "DROP INDEX IF EXISTS idx_analytics_reports_user_time"
alembic upgrade head
```

### Slow index creation on large tables

```bash
# Create indexes concurrently (doesn't lock table)
# Edit migration to use:
op.create_index(..., postgresql_concurrently=True)

# Note: Requires connection outside transaction
# Set in alembic.ini: [alembic] transaction_per_migration = false
```

### Index not being used by queries

```sql
-- Check query plan
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM analytics_reports
WHERE user_id = 'andreas'
ORDER BY created_at DESC;

-- If index not used, might need to:
-- 1. Update table statistics
ANALYZE analytics_reports;

-- 2. Check index bloat/corruption
REINDEX INDEX idx_analytics_reports_user_time;
```

## Best Practices

1. **Always test migrations on staging first**
2. **Create indexes CONCURRENTLY on production** (avoid table locks)
3. **Monitor index usage** after deployment
4. **Document performance improvements** in migration comments
5. **Include rollback procedures** for critical migrations
6. **Backup database** before major schema changes

## Related Documentation

- [Database Optimization Guide](../../../docs/guides/database-optimization.md)
- [Analytics Service README](../README.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
