# Migration Test Suite

Comprehensive test suite for the dual-table analysis storage migration (Option A: Complete Migration).

## Overview

This test suite verifies the migration from:
- **Legacy table:** `content_analysis_v2.pipeline_executions` (7097 rows)
- **Unified table:** `public.article_analysis` (initially 3364 rows)

**Goal:** Backfill 3733 missing rows and establish unified table as single source of truth.

## Test Scripts

### 1. Pre-Migration Tests (`test_pre_migration.sh`)

**Purpose:** Verify system state BEFORE migration execution.

**Checks:**
- ✅ Legacy table row count (expected: ~7097)
- ✅ Unified table row count (expected: ~3364)
- ✅ Success rate (expected: >90%)
- ✅ Data quality (no null triage, no orphaned analyses)
- ✅ Foreign key integrity
- ✅ Performance baseline (query time measurement)
- ✅ Worker status (analysis-consumer running)

**Usage:**
```bash
cd /home/cytrex/news-microservices
./tests/migration/test_pre_migration.sh
```

**Output:**
- Terminal: Color-coded test results
- File: `/tmp/migration_baseline/pre_migration.json` (metrics)

**Duration:** ~2-3 minutes

---

### 2. Post-Migration Tests (`test_post_migration.sh`)

**Purpose:** Verify system state AFTER migration execution.

**Checks:**
- ✅ Unified table row count matches legacy (expected: 7097 = 7097)
- ✅ No missing analyses (LEFT JOIN check)
- ✅ Data transformation correctness (sample 10 articles)
- ✅ Relevance score extraction (>80% success rate)
- ✅ API performance (<200ms single, <700ms batch)
- ✅ Frontend compatibility (response structure)
- ✅ New analyses working (last 10 min check)
- ✅ Data integrity (no duplicates, no orphans)

**Usage:**
```bash
cd /home/cytrex/news-microservices
./tests/migration/test_post_migration.sh
```

**Output:**
- Terminal: Detailed test results with performance comparison
- File: `/tmp/migration_baseline/post_migration.json` (metrics)

**Duration:** ~3-5 minutes

---

### 3. Rollback Tests (`test_rollback.sh`)

**Purpose:** Verify rollback procedure is documented and executable.

**Checks:**
- ✅ Legacy table exists (or backup available)
- ✅ Database backup present
- ✅ Git status (clean working directory)
- ✅ Rollback procedure documented
- ✅ Dry-run simulation (no actual rollback)
- ✅ Risk assessment
- ✅ Rollback time estimation (~10 minutes)

**Usage:**
```bash
cd /home/cytrex/news-microservices
./tests/migration/test_rollback.sh
```

**Output:**
- Terminal: Rollback procedure documentation
- No files created (simulation only)

**Duration:** ~1-2 minutes

**Note:** This test does NOT execute actual rollback. It only validates the procedure.

---

## Quick Start

### Run All Tests (Sequential)

```bash
cd /home/cytrex/news-microservices

# 1. Pre-migration checks
./tests/migration/test_pre_migration.sh

# 2. [Execute migration here - see migration guide]

# 3. Post-migration verification
./tests/migration/test_post_migration.sh

# 4. Rollback validation (if issues)
./tests/migration/test_rollback.sh
```

### Make Scripts Executable

```bash
chmod +x tests/migration/*.sh
```

### View Test Results

```bash
# Pre-migration baseline
cat /tmp/migration_baseline/pre_migration.json | jq

# Post-migration metrics
cat /tmp/migration_baseline/post_migration.json | jq
```

---

## Test Output Interpretation

### Success Indicators ✅

```
✓ Legacy table exists: 1
✓ Legacy table has data: 7097 > 7000
✓ Success rate acceptable: 97 > 90
✓ No null triage for successful analyses: 0
✓ Counts match (migration complete): 7097 = 7097
✓ Single article response < 200ms: 85 < 200
✅ ALL TESTS PASSED
```

### Failure Indicators ❌

```
✗ Legacy table exists: Expected 1, got 0
✗ Success rate acceptable: Expected > 90, got 85
✗ Counts match (migration complete): Expected 7097, got 6000
❌ TESTS FAILED
```

### Warning Indicators ⚠️

```
⚠️ Migration required: 3733 rows need backfill
⚠️ No database backup found in /tmp/
⚠️ 15 uncommitted changes (commit or stash before rollback)
```

---

## Dependencies

### Required Services

- **Docker:** All services running (`docker compose up -d`)
- **PostgreSQL:** Accessible at `postgres:5432`
- **Feed Service:** API at `localhost:8101`
- **Auth Service:** API at `localhost:8100`

### Required Tools

- `bash` (4.0+)
- `docker`
- `psql` (via docker exec)
- `curl`
- `jq` (JSON parsing)
- `bc` (calculations)

### Check Dependencies

```bash
# Check if all required commands are available
command -v docker >/dev/null 2>&1 || echo "Missing: docker"
command -v curl >/dev/null 2>&1 || echo "Missing: curl"
command -v jq >/dev/null 2>&1 || echo "Missing: jq"
command -v bc >/dev/null 2>&1 || echo "Missing: bc"

# Check if services are running
docker compose ps | grep -E "(postgres|feed-service|auth-service)"
```

---

## Environment Variables

Tests use these environment variables (with defaults):

```bash
# Database
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-news_mcp}"
POSTGRES_USER="${POSTGRES_USER:-news_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-news_pass}"

# API endpoints
FEED_SERVICE_URL="${FEED_SERVICE_URL:-http://localhost:8101}"
AUTH_SERVICE_URL="${AUTH_SERVICE_URL:-http://localhost:8100}"
```

Override if needed:
```bash
export FEED_SERVICE_URL="http://custom-host:8101"
./tests/migration/test_post_migration.sh
```

---

## Troubleshooting

### Test fails: "docker exec postgres: command not found"

**Cause:** PostgreSQL container not running or named differently.

**Fix:**
```bash
# Check container name
docker ps | grep postgres

# If different name, update common.sh or use docker exec <name>
```

### Test fails: "Failed to get auth token"

**Cause:** Auth service not running or credentials incorrect.

**Fix:**
```bash
# Check auth service
docker logs news-microservices-auth-service-1

# Test manually
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}'
```

### Test fails: "Connection refused" (API tests)

**Cause:** Feed service not running or port mapping incorrect.

**Fix:**
```bash
# Check feed service
docker compose ps feed-service

# Check logs
docker logs news-microservices-feed-service-1

# Restart if needed
docker compose restart feed-service
```

### Pre-migration test reports wrong row count

**Cause:** Database has more/less data than expected.

**Fix:** Not a problem - tests adapt to actual counts. Check output for warnings.

---

## Integration with Migration Guide

This test suite is part of the complete migration workflow:

1. **Phase 1: Preparation**
   - Run `test_pre_migration.sh` ← **YOU ARE HERE**
   - Create backup
   - Review baseline metrics

2. **Phase 2: Execution**
   - Stop workers
   - Execute backfill SQL
   - Deploy feed-service updates
   - Restart workers

3. **Phase 3: Verification**
   - Run `test_post_migration.sh` ← **Verify success**
   - Monitor for 24 hours
   - Run `test_post_migration.sh` again after 24h

4. **Phase 4: Cleanup**
   - Deprecate legacy table (if tests pass)
   - Update documentation

**Rollback:** If any test fails, run `test_rollback.sh` for procedure.

---

## Continuous Integration

### Run in CI/CD Pipeline

```yaml
# .github/workflows/test-migration.yml
name: Migration Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker compose up -d
      - name: Pre-migration tests
        run: ./tests/migration/test_pre_migration.sh
      - name: Post-migration tests (if migrated)
        run: ./tests/migration/test_post_migration.sh || true
```

---

## Related Documentation

- **Migration Guide:** `docs/guides/analysis-storage-migration-guide.md`
- **Architecture Decision:** `docs/decisions/ADR-032-dual-table-analysis-architecture.md`
- **Schema Documentation:** `docs/database/analysis-tables-schema.md`
- **Post-Mortem:** `POSTMORTEMS.md` (Incident #8)

---

## Maintenance

### Update Tests After Schema Changes

If database schema changes, update:
1. `lib/common.sh` → SQL queries
2. `test_pre_migration.sh` → Expected values
3. `test_post_migration.sh` → Response structure checks

### Add New Tests

Create new test script:
```bash
cp tests/migration/test_pre_migration.sh tests/migration/test_custom.sh
# Edit test_custom.sh
chmod +x tests/migration/test_custom.sh
```

---

## Support

**Issues?** Check:
1. This README (Troubleshooting section)
2. Docker logs: `docker logs <container-name>`
3. Test output: `/tmp/migration_baseline/*.json`
4. Migration guide: `docs/guides/analysis-storage-migration-guide.md`

**Contact:** Report in project issue tracker or POSTMORTEMS.md

---

**Last Updated:** 2025-10-31
**Version:** 1.0
**Owner:** Backend Team, Database Team
