# Migration Runbook: Dual-Table Analysis Storage Consolidation

**Target:** Migrate from dual-table architecture to single unified table (`public.article_analysis`)

**Duration:** 4-6 hours (preparation) + 30-45 minutes (execution) + 24 hours (monitoring)

**Risk Level:** Medium (transaction-wrapped, rollback available, downtime acceptable)

**Operator:** Database Admin + Backend Engineer (2 people recommended)

---

## 📋 Pre-Flight Checklist

**Before starting, verify:**

- [ ] Read [ADR-032: Dual-Table Analysis Architecture](../decisions/ADR-032-dual-table-analysis-architecture.md)
- [ ] Read [Analysis Storage Migration Guide](./analysis-storage-migration-guide.md)
- [ ] All services running: `docker compose ps` (17 services UP)
- [ ] Git working directory clean: `git status`
- [ ] Pre-migration tests passed: `./tests/migration/test_pre_migration.sh`
- [ ] Baseline metrics captured: `cat /tmp/migration_baseline/pre_migration.json`
- [ ] Backup script ready: `scripts/migration/backup_database.sh`
- [ ] Auth credentials available: `andreas@test.com` / `Aug2012#`
- [ ] Terminal multiplexer recommended: `tmux` or `screen`

**Abort if:**
- Pre-migration tests fail with errors (not warnings)
- Legacy table count < 7000 rows (data loss suspected)
- Services not responding to health checks
- Git has uncommitted changes (stash or commit first)

---

## 🎯 Migration Overview

### What We're Doing

```
BEFORE:
┌──────────────────────────────────────────────────────┐
│ content_analysis_v2.pipeline_executions (LEGACY)     │
│ ↑ READ by feed-service (via proxy)                   │
│ ↑ WRITTEN by content-analysis-v2 API                 │
│ 7097 rows                                             │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ public.article_analysis (UNIFIED - ORPHANED!)        │
│ ✗ Never read                                          │
│ ✓ Written by analysis-consumer                       │
│ 3364 rows (47% coverage)                              │
└──────────────────────────────────────────────────────┘

AFTER:
┌──────────────────────────────────────────────────────┐
│ public.article_analysis (UNIFIED - SINGLE SOURCE)    │
│ ✓ READ by feed-service (direct, 2x faster)           │
│ ✓ WRITTEN by analysis-consumer                       │
│ 7097 rows (100% coverage)                             │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ content_analysis_v2.pipeline_executions_deprecated   │
│ (Renamed for safety, will be dropped after 30 days)  │
└──────────────────────────────────────────────────────┘
```

### Timeline

| Phase | Duration | Downtime? |
|-------|----------|-----------|
| 1. Preparation | 4-6h | No |
| 2. Execution | 30-45min | Yes (~5min) |
| 3. Verification | 2-3h | No |
| 4. Monitoring | 24h | No |
| 5. Cleanup | 30min | No |
| **Total** | **~32 hours** | **~5 minutes** |

---

## 🚀 Phase 1: Preparation (4-6 hours)

### Step 1.1: Environment Check

```bash
cd /home/cytrex/news-microservices

# Verify all services running
docker compose ps | grep -E "(Up|running)" | wc -l
# Expected: 17 services

# Verify PostgreSQL accessible
docker exec postgres psql -U news_user -d news_mcp -c "SELECT version();"
# Expected: PostgreSQL 16.x
```

**Decision Point:** If < 17 services running → **Investigate and fix before proceeding**

---

### Step 1.2: Run Pre-Migration Tests

```bash
# Make scripts executable
chmod +x tests/migration/*.sh
chmod +x scripts/migration/*.sh

# Run pre-migration test suite (2-3 minutes)
./tests/migration/test_pre_migration.sh 2>&1 | tee /tmp/pre_migration_output.log

# Check result
echo $?
# Expected: 0 (success)
```

**Verify baseline captured:**
```bash
cat /tmp/migration_baseline/pre_migration.json | jq '.'
```

**Expected output:**
```json
{
  "timestamp": "2025-10-31T...",
  "legacy_count": 7097,
  "unified_count": 3364,
  "missing_count": 3733,
  "success_rate": 97,
  "query_time_ms": 156
}
```

**Decision Point:**
- ✅ All tests passed → **Proceed to Step 1.3**
- ⚠️ Warnings only (e.g., "no backup found") → **Create backup, then proceed**
- ❌ Test failures → **STOP. Investigate errors. Do not proceed.**

---

### Step 1.3: Create Database Backup

```bash
# Create backup (5-10 minutes for ~500MB database)
docker exec postgres pg_dump -U news_user -d news_mcp -Fc > \
  /tmp/news_mcp_pre_migration_$(date +%Y%m%d_%H%M%S).dump

# Verify backup created
ls -lh /tmp/news_mcp_pre_migration_*.dump
# Expected: ~500MB file

# Test backup integrity (optional but recommended)
docker exec postgres pg_restore --list \
  /tmp/news_mcp_pre_migration_*.dump | head -20
# Expected: List of database objects (no errors)
```

**Backup location:** `/tmp/news_mcp_pre_migration_YYYYMMDD_HHMMSS.dump`

**⚠️ CRITICAL:** Keep this backup for 30 days. It's your rollback lifeline.

---

### Step 1.4: Verify Agent Deliverables

**Check that agents completed their tasks:**

```bash
# 1. Backward-compatible API layer
ls -lh services/feed-service/app/services/analysis_loader.py
# Expected: File exists with unified table read logic

# 2. Load testing suite
ls -lh tests/migration/load_test.sh
# Expected: File exists and is executable

# 3. Deployment scripts
ls -lh scripts/migration/deploy.sh
ls -lh scripts/migration/rollback.sh
ls -lh scripts/migration/health_check.sh
# Expected: All 3 files exist

# 4. Backfill wrapper
ls -lh scripts/migration/execute_backfill.sh
# Expected: File exists and is executable
```

**Decision Point:**
- ✅ All deliverables present → **Proceed to Step 1.5**
- ❌ Missing files → **Wait for agents to complete OR manually create missing scripts**

---

### Step 1.5: Review Backfill SQL

**Human review required** (10-15 minutes):

```bash
# Open backfill SQL in editor
code tests/migration/backfill_unified_table.sql
# OR
cat tests/migration/backfill_unified_table.sql | less
```

**Review checklist:**
- [ ] Transaction wrapped (`BEGIN;` ... `COMMIT;`)
- [ ] Pre-migration verification checks (counts, duplicates)
- [ ] Data transformation logic (tier1_results, tier2_results)
- [ ] Relevance score extraction with type checking
- [ ] Post-migration verification (counts match, no duplicates)
- [ ] `ON CONFLICT (article_id) DO NOTHING` (safety)

**Expected transformation logic:**
```sql
-- Tier 1 results (combine 4 agent results)
CASE
    WHEN pe.entity_results IS NOT NULL
      OR pe.summary_results IS NOT NULL
      OR pe.sentiment_results IS NOT NULL
      OR pe.topic_results IS NOT NULL
    THEN jsonb_build_object(
        'entity_results', COALESCE(pe.entity_results, '{}'::jsonb),
        'summary_results', COALESCE(pe.summary_results, '{}'::jsonb),
        'sentiment_results', COALESCE(pe.sentiment_results, '{}'::jsonb),
        'topic_results', COALESCE(pe.topic_results, '{}'::jsonb)
    )
    ...
END AS tier1_results
```

**Decision Point:**
- ✅ SQL looks correct → **Proceed to Step 1.6**
- ⚠️ Concerns about transformation → **Test on sample data first** (see Appendix A)
- ❌ Errors in SQL → **Fix before proceeding**

---

### Step 1.6: Dry-Run Test (Optional but Recommended)

Test backfill on **3 random articles** to verify transformation logic:

```bash
# Create test version of backfill SQL
cp tests/migration/backfill_unified_table.sql /tmp/test_backfill.sql

# Edit: Change INSERT to only process 3 articles
# Add at line 186 (before ON CONFLICT):
# ) AND pe.article_id IN (
#     SELECT article_id FROM content_analysis_v2.pipeline_executions
#     ORDER BY RANDOM() LIMIT 3
# )

# Run in transaction (will auto-rollback after verification)
docker exec -i postgres psql -U news_user -d news_mcp < /tmp/test_backfill.sql
```

**Expected output:**
```
NOTICE:  ╔════════════════════════════════════════════════════════════╗
NOTICE:  ║  BEFORE BACKFILL - VERIFICATION                            ║
...
NOTICE:  ✓ Backfill complete
NOTICE:  ✅ BACKFILL SUCCESSFUL!
```

**Decision Point:**
- ✅ Test successful → **Proceed to Phase 2**
- ❌ Test failed → **Investigate transformation logic, fix, retry**

---

### Step 1.7: Communication

**Notify team:**

```markdown
Subject: Analysis Storage Migration - Starting Execution

Team,

We're proceeding with the dual-table analysis storage migration (ADR-032, Option A).

**Timeline:**
- Execution: [DATE] at [TIME] (~30-45 minutes)
- Expected downtime: ~5 minutes (during backfill)
- Post-verification: Same day (~2-3 hours)
- Monitoring period: 24 hours

**Impact:**
- Analysis pipeline paused during execution
- Article list/detail pages remain functional
- New analyses will resume after restart

**Rollback:** Available if issues detected (10-minute procedure)

**Status updates:** #engineering-alerts channel

Thanks,
[Your Name]
```

---

## ⚡ Phase 2: Execution (30-45 minutes)

**⚠️ POINT OF NO RETURN AFTER STEP 2.4**

### Step 2.1: Stop Analysis Workers

```bash
# Stop analysis-consumer (writes to unified table)
docker compose stop feed-service-analysis-consumer

# Verify stopped
docker ps | grep analysis-consumer
# Expected: No output (container stopped)

# Stop content-analysis-v2 workers (processing pipeline)
docker compose stop content-analysis-v2-worker-1 \
                     content-analysis-v2-worker-2 \
                     content-analysis-v2-worker-3

# Verify all stopped
docker ps | grep content-analysis-v2-worker
# Expected: No output
```

**⏱️ DOWNTIME STARTS HERE**

**Verify no new analyses being created:**
```bash
docker exec postgres psql -U news_user -d news_mcp -c \
  "SELECT MAX(created_at) FROM content_analysis_v2.pipeline_executions;"
# Expected: Timestamp 1-2 minutes ago (no new rows)
```

---

### Step 2.2: Final Row Count Snapshot

```bash
# Capture exact counts before backfill
docker exec postgres psql -U news_user -d news_mcp -t -c \
  "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;" > /tmp/legacy_count_before.txt

docker exec postgres psql -U news_user -d news_mcp -t -c \
  "SELECT COUNT(*) FROM public.article_analysis;" > /tmp/unified_count_before.txt

cat /tmp/legacy_count_before.txt
cat /tmp/unified_count_before.txt

# Expected: 7097 and 3364 (or close to these numbers)
```

---

### Step 2.3: Execute Backfill (2-5 minutes)

**This is the critical step. Transaction-wrapped for safety.**

```bash
# Open second terminal for monitoring (tmux/screen recommended)
# Terminal 2: Watch PostgreSQL activity
watch -n 1 'docker exec postgres psql -U news_user -d news_mcp -c "SELECT COUNT(*) FROM public.article_analysis;"'

# Terminal 1: Execute backfill
time docker exec -i postgres psql -U news_user -d news_mcp < \
  tests/migration/backfill_unified_table.sql 2>&1 | tee /tmp/backfill_output.log

# Expected duration: 2-5 minutes (3733 rows)
```

**Watch for:**
```
NOTICE:  ✓ Pre-migration checks passed
NOTICE:  → Proceeding with backfill of 3733 rows...
NOTICE:  Starting backfill... (this may take 2-5 minutes)
...
NOTICE:  ✓ Backfill complete
NOTICE:  ✅ BACKFILL SUCCESSFUL!
NOTICE:     → All 7097 analyses now in unified table
COMMIT
```

**Decision Point:**
- ✅ Output shows "✅ BACKFILL SUCCESSFUL!" → **Proceed to Step 2.4**
- ⚠️ Warnings but COMMIT successful → **Review warnings, then proceed**
- ❌ ERROR or ROLLBACK → **STOP. Database unchanged. Review /tmp/backfill_output.log**

---

### Step 2.4: Verify Backfill Success

```bash
# Check unified table count
docker exec postgres psql -U news_user -d news_mcp -t -c \
  "SELECT COUNT(*) FROM public.article_analysis;"
# Expected: 7097 (matching legacy table)

# Check for missing analyses
docker exec postgres psql -U news_user -d news_mcp -t -c \
  "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions pe
   LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id
   WHERE aa.id IS NULL;"
# Expected: 0 (no missing rows)

# Check for duplicates
docker exec postgres psql -U news_user -d news_mcp -t -c \
  "SELECT COUNT(*) FROM (
     SELECT article_id, COUNT(*) as cnt
     FROM public.article_analysis
     GROUP BY article_id
     HAVING COUNT(*) > 1
   ) sub;"
# Expected: 0 (no duplicates)
```

**Decision Point:**
- ✅ All checks pass (7097 rows, 0 missing, 0 duplicates) → **Proceed to Step 2.5**
- ❌ Any check fails → **ROLLBACK IMMEDIATELY** (see Section: Emergency Rollback)

---

### Step 2.5: Deploy feed-service Update

**This switches feed-service to read from unified table.**

```bash
# Check if feed-service code updated (should be done by agent)
git status services/feed-service/app/services/analysis_loader.py
# Expected: Modified (reads from unified table now)

# If not modified, STOP and manually update (see Appendix B)

# Restart feed-service (picks up code changes)
docker compose restart feed-service

# Wait for service to be healthy
sleep 10
docker logs news-microservices-feed-service-1 --tail 20
# Expected: "Application startup complete" (no errors)
```

---

### Step 2.6: Health Check

```bash
# Verify feed-service responds
curl -s http://localhost:8101/health | jq '.'
# Expected: {"status":"healthy"}

# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' | jq -r '.access_token')

# Test single article endpoint
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items?limit=1" | jq '.items[0].pipeline_execution'
# Expected: JSON with triage_results, tier1_results, tier2_results

# Test that data looks correct
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items?limit=1" | \
  jq '.items[0].pipeline_execution | keys'
# Expected: ["created_at", "error_message", "failed_agents", "metrics",
#            "pipeline_version", "relevance_score", "score_breakdown", "success",
#            "tier1_results", "tier2_results", "tier3_results", "triage_results", "updated_at"]
```

**Decision Point:**
- ✅ API healthy, returns correct data → **Proceed to Step 2.7**
- ❌ Errors or malformed data → **ROLLBACK** (see Section: Emergency Rollback)

---

### Step 2.7: Restart Analysis Workers

```bash
# Restart analysis-consumer
docker compose start feed-service-analysis-consumer

# Verify running
docker ps | grep analysis-consumer
# Expected: Container with "Up" status

# Check logs for startup
docker logs feed-service-analysis-consumer --tail 20
# Expected: "Connected to RabbitMQ" (no errors)

# Restart content-analysis-v2 workers
docker compose start content-analysis-v2-worker-1 \
                     content-analysis-v2-worker-2 \
                     content-analysis-v2-worker-3

# Verify all running
docker ps | grep content-analysis-v2-worker | wc -l
# Expected: 3 (all workers up)
```

**⏱️ DOWNTIME ENDS HERE (~5-10 minutes total)**

---

### Step 2.8: Verify End-to-End Pipeline

**Trigger a new analysis to verify entire pipeline works:**

```bash
# Get a feed ID
FEED_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds?limit=1" | jq -r '.feeds[0].id')

# Trigger feed fetch (creates new articles)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/$FEED_ID/fetch"

# Wait 30 seconds for analysis to complete
sleep 30

# Check for new analyses in unified table
docker exec postgres psql -U news_user -d news_mcp -t -c \
  "SELECT COUNT(*) FROM public.article_analysis
   WHERE created_at > NOW() - INTERVAL '2 minutes';"
# Expected: > 0 (new analyses created)
```

**Decision Point:**
- ✅ New analyses appear in unified table → **SUCCESS! Proceed to Phase 3**
- ❌ No new analyses after 5 minutes → **Investigate worker logs, may need rollback**

---

## ✅ Phase 3: Verification (2-3 hours)

### Step 3.1: Run Post-Migration Tests

```bash
# Run full post-migration test suite (3-5 minutes)
./tests/migration/test_post_migration.sh 2>&1 | tee /tmp/post_migration_output.log

# Check result
echo $?
# Expected: 0 (all tests passed)
```

**Expected output:**
```
╔═══════════════════════════════════════╗
║  POST-MIGRATION RESULTS               ║
╠═══════════════════════════════════════╣
║  Tests Passed:    25/25               ║
║  Tests Failed:    0                   ║
╚═══════════════════════════════════════╝

✅ MIGRATION SUCCESSFUL - All checks passed

Next Steps:
1. Monitor system for 24 hours
2. Run test_post_migration.sh again after 24h
3. If stable, deprecate legacy table
4. Update documentation
```

**Decision Point:**
- ✅ All tests passed → **Proceed to Step 3.2**
- ⚠️ Minor failures (e.g., performance slightly above target) → **Monitor, proceed**
- ❌ Critical failures (e.g., missing data, API errors) → **ROLLBACK**

---

### Step 3.2: Load Testing

```bash
# Run load test suite (10-15 minutes)
./tests/migration/load_test.sh 2>&1 | tee /tmp/load_test_output.log

# Expected: Performance improvements (2-3x faster)
```

**Verify results:**
```bash
cat /tmp/load_test_output.log | grep -A5 "PERFORMANCE COMPARISON"
```

**Expected output:**
```
PERFORMANCE COMPARISON
├─ Single Article (p50):  Before: 156ms → After:  68ms  (2.3x faster)
├─ Single Article (p95):  Before: 234ms → After: 102ms  (2.3x faster)
├─ Batch 20 (p50):        Before: 892ms → After: 376ms  (2.4x faster)
└─ Batch 20 (p95):        Before: 1243ms → After: 512ms (2.4x faster)

✅ Performance improvement verified
```

---

### Step 3.3: Frontend Smoke Test

**Manual verification** (5 minutes):

1. Open browser: http://localhost:3000
2. Login: `andreas@test.com` / `Aug2012#`
3. Navigate to **Article List** page
   - ✅ Articles load without errors
   - ✅ Pipeline execution data visible (relevance scores, sentiment)
4. Click on any article → **Article Detail** page
   - ✅ Full analysis visible (triage, tier1, tier2, tier3)
   - ✅ Entity extraction shows results
   - ✅ Sentiment analysis shows results
5. Check browser console (F12)
   - ✅ No JavaScript errors
   - ✅ No API errors (403/404/500)

**Decision Point:**
- ✅ Frontend works correctly → **Proceed to Step 3.4**
- ❌ Frontend broken or missing data → **ROLLBACK**

---

### Step 3.4: Start 24h Monitoring

```bash
# Start monitoring dashboard in background
nohup ./scripts/migration/monitor_migration.sh > /tmp/migration_monitoring.log 2>&1 &

# Get process ID
echo $! > /tmp/migration_monitor.pid

# Verify monitoring started
tail -f /tmp/migration_monitoring.log
```

**Expected output:**
```
╔═══════════════════════════════════════════════════════════════╗
║  24h POST-MIGRATION MONITORING STARTED                        ║
║  Interval: 7200s (120 minutes)                                ║
║  Duration: 86400s (24 hours)                                  ║
╚═══════════════════════════════════════════════════════════════╝

Iteration: #1
Elapsed: 00:00:00
Remaining: 24:00:00

▶ TABLE ROW COUNTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Legacy table:    7097 rows
  Unified table:   7097 rows
  Drift:              0 rows ✓

▶ HEALTH SCORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Overall health: 100/100 ✓ Excellent
  Issues detected: 0
```

**Monitoring will:**
- Check every 2 hours for 24 hours
- Log to `/tmp/migration_monitoring.csv` for graphing
- Alert if drift > 10 rows, errors detected, or workers stop

---

### Step 3.5: Communication (Success)

```markdown
Subject: Analysis Storage Migration - Phase 2 Complete ✅

Team,

Migration execution completed successfully!

**Results:**
- Unified table: 7,097 analyses (100% coverage)
- Data transformation: Verified (sample check passed)
- API performance: 2.3x faster (156ms → 68ms avg)
- Frontend: Functional (smoke test passed)
- Downtime: 7 minutes (target: <10 minutes)

**Monitoring:**
- 24h monitoring active (updates every 2 hours)
- Health score: 100/100
- Dashboard: /tmp/migration_monitoring.log

**Next Steps:**
- Continue 24h monitoring (auto-alerts enabled)
- Re-run tests after 24h (2025-11-01 at [TIME+24h])
- If stable: Deprecate legacy table (2025-11-02)

**Status:** ✅ Migration successful, monitoring in progress

Thanks,
[Your Name]
```

---

## 📊 Phase 4: 24h Monitoring (Automated)

**Monitoring dashboard is running automatically.**

### Manual Check-ins (Recommended)

**Every 4-6 hours, check:**

```bash
# View latest monitoring output
tail -100 /tmp/migration_monitoring.log

# Check health score trend
tail -10 /tmp/migration_monitoring.csv
# Expected: health_score column stays 90-100

# Verify no drift
docker exec postgres psql -U news_user -d news_mcp -t -c \
  "SELECT
     (SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions) as legacy,
     (SELECT COUNT(*) FROM public.article_analysis) as unified,
     ABS((SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions) -
         (SELECT COUNT(*) FROM public.article_analysis)) as drift;"
# Expected: drift = 0 or small (< 10)
```

---

### After 24 Hours

```bash
# Stop monitoring
kill $(cat /tmp/migration_monitor.pid)

# View final report
tail -200 /tmp/migration_monitoring.log | grep -A20 "24h monitoring period complete"

# Re-run post-migration tests
./tests/migration/test_post_migration.sh
```

**Expected: All tests still pass after 24h of production traffic.**

---

## 🧹 Phase 5: Cleanup (After 24h Stable)

### Step 5.1: Deprecate Legacy Table

**⚠️ Only proceed if 24h monitoring shows no issues.**

```bash
# Rename legacy table (preserves data for 30 days)
docker exec postgres psql -U news_user -d news_mcp -c \
  "ALTER TABLE content_analysis_v2.pipeline_executions
   RENAME TO pipeline_executions_deprecated;"

# Verify rename
docker exec postgres psql -U news_user -d news_mcp -c \
  "\dt content_analysis_v2.*"
# Expected: pipeline_executions_deprecated (not pipeline_executions)

# Add comment for future reference
docker exec postgres psql -U news_user -d news_mcp -c \
  "COMMENT ON TABLE content_analysis_v2.pipeline_executions_deprecated IS
   'DEPRECATED 2025-10-31: Replaced by public.article_analysis.
    Safe to drop after 2025-11-30 if no issues.';"
```

---

### Step 5.2: Update Documentation

**6 files to update:**

1. **ARCHITECTURE.md**
   - Remove "Known Issue #4" (dual-table architecture)
   - Update Section 4.3 (Database Architecture) - remove legacy table reference

2. **docs/architecture/analysis-tables-schema.md**
   - Mark legacy table as deprecated
   - Add migration completion date

3. **docs/services/feed-service.md**
   - Update data flow diagram (remove proxy path)
   - Document direct unified table access

4. **docs/services/content-analysis-v2.md**
   - Remove pipeline_executions table documentation
   - Update to reflect unified table only

5. **docs/guides/analysis-storage-migration-guide.md**
   - Add "Migration Completed" banner at top
   - Link to this runbook for execution details

6. **POSTMORTEMS.md**
   - Update Incident #8 with resolution
   - Add "Resolved: 2025-10-31" status

```bash
# Create documentation update checklist
cat > /tmp/doc_update_checklist.txt <<'EOF'
Documentation Update Checklist:
- [ ] ARCHITECTURE.md (remove Known Issue #4)
- [ ] docs/architecture/analysis-tables-schema.md (deprecation notice)
- [ ] docs/services/feed-service.md (data flow update)
- [ ] docs/services/content-analysis-v2.md (unified table only)
- [ ] docs/guides/analysis-storage-migration-guide.md (completion banner)
- [ ] POSTMORTEMS.md (Incident #8 resolution)
EOF

# Work through checklist systematically
```

---

### Step 5.3: Final Communication

```markdown
Subject: Analysis Storage Migration - Complete ✅

Team,

The dual-table analysis storage migration (ADR-032) is now complete!

**Final Results:**
- 24h monitoring: No issues detected
- Health score: 95-100 throughout monitoring period
- Performance: 2.3x improvement sustained
- Legacy table: Deprecated (will be dropped 2025-11-30)

**Changes:**
- All analysis data now in `public.article_analysis` (single source of truth)
- feed-service reads directly (no more proxy)
- API response times improved (156ms → 68ms avg)

**Documentation:**
- ARCHITECTURE.md updated (Known Issue #4 resolved)
- Service docs updated (feed-service, content-analysis-v2)
- Migration guide marked complete

**Backup Retention:**
- Pre-migration backup: /tmp/news_mcp_pre_migration_YYYYMMDD.dump
- Retention: 30 days (until 2025-11-30)
- Deprecated table: 30 days (safe to drop after 2025-11-30)

Thanks to everyone for the smooth execution!

[Your Name]
```

---

## 🚨 Emergency Procedures

### Rollback Procedure (10-15 minutes)

**When to rollback:**
- Backfill verification fails (counts mismatch, duplicates)
- API returns errors or malformed data after deployment
- Frontend broken (missing data, crashes)
- Critical issues detected in first 2 hours

**How to rollback:**

```bash
# 1. Stop analysis workers (prevent new writes)
docker compose stop feed-service-analysis-consumer \
                     content-analysis-v2-worker-1 \
                     content-analysis-v2-worker-2 \
                     content-analysis-v2-worker-3

# 2. Restore legacy table (if renamed)
docker exec postgres psql -U news_user -d news_mcp -c \
  "ALTER TABLE content_analysis_v2.pipeline_executions_deprecated
   RENAME TO pipeline_executions;"

# 3. Revert feed-service code (read from legacy table again)
git diff HEAD services/feed-service/app/services/analysis_loader.py > /tmp/migration_changes.patch
git checkout HEAD -- services/feed-service/app/services/analysis_loader.py

# 4. Restart feed-service
docker compose restart feed-service

# 5. Verify API works
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"andreas@test.com","password":"Aug2012#"}' | jq -r '.access_token')

curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8101/api/v1/feeds/items?limit=1" | jq '.items[0].pipeline_execution'
# Expected: Valid JSON response

# 6. Restart workers
docker compose start feed-service-analysis-consumer \
                     content-analysis-v2-worker-1 \
                     content-analysis-v2-worker-2 \
                     content-analysis-v2-worker-3

# 7. Verify end-to-end
# (Same as Phase 2, Step 2.8)
```

**After rollback:**
- Review `/tmp/backfill_output.log` and `/tmp/post_migration_output.log` for errors
- Document what went wrong in POSTMORTEMS.md
- Fix issues
- Retry migration on another day

---

### Database Restore from Backup (30-60 minutes)

**Only if catastrophic failure (data corruption, unrecoverable state).**

```bash
# 1. Stop all services
docker compose down

# 2. Restore database from backup
docker compose up -d postgres
sleep 10

docker exec -i postgres pg_restore -U news_user -d news_mcp --clean \
  < /tmp/news_mcp_pre_migration_YYYYMMDD_HHMMSS.dump

# 3. Verify restoration
docker exec postgres psql -U news_user -d news_mcp -c \
  "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;"
# Expected: 7097 (pre-migration count)

# 4. Restart all services
docker compose up -d

# 5. Run pre-migration tests to verify clean state
./tests/migration/test_pre_migration.sh
```

---

## 📈 Success Criteria

### Immediate (Phase 2-3)

- ✅ Unified table row count = Legacy table row count (7097)
- ✅ No missing analyses (LEFT JOIN check = 0)
- ✅ No duplicate analyses (duplicate check = 0)
- ✅ API responds < 200ms for single article (target: 2-3x improvement)
- ✅ Frontend functional (article list and detail pages load)
- ✅ New analyses written to unified table (end-to-end pipeline works)

### After 24h (Phase 4)

- ✅ Health score sustained 90-100
- ✅ No data drift (legacy count - unified count < 10)
- ✅ No errors in service logs
- ✅ API performance stable (no regression)
- ✅ Workers operational (analysis-consumer + 3 workers running)

### After 30 days (Phase 5)

- ✅ Legacy table dropped (no longer needed)
- ✅ Documentation updated (6 files)
- ✅ Team trained on new architecture
- ✅ Backup deleted (30-day retention expired)

---

## 📝 Appendix A: Manual Transformation Test

**If you want to verify transformation logic on sample data before full backfill:**

```sql
-- Test transformation on 5 random articles
BEGIN;

-- Create temporary test table
CREATE TEMP TABLE test_unified AS
SELECT
    pe.article_id,
    pe.pipeline_version,
    pe.success,
    pe.triage_decision AS triage_results,

    -- Tier 1 (combined)
    CASE
        WHEN pe.entity_results IS NOT NULL
          OR pe.summary_results IS NOT NULL
          OR pe.sentiment_results IS NOT NULL
          OR pe.topic_results IS NOT NULL
        THEN jsonb_build_object(
            'entity_results', COALESCE(pe.entity_results, '{}'::jsonb),
            'summary_results', COALESCE(pe.summary_results, '{}'::jsonb),
            'sentiment_results', COALESCE(pe.sentiment_results, '{}'::jsonb),
            'topic_results', COALESCE(pe.topic_results, '{}'::jsonb)
        )
        ELSE pe.tier1_summary
    END AS tier1_results,

    -- Relevance score
    CASE
        WHEN pe.triage_decision IS NOT NULL
         AND pe.triage_decision ? 'relevance_score'
         AND jsonb_typeof(pe.triage_decision->'relevance_score') = 'number'
        THEN (pe.triage_decision->>'relevance_score')::DECIMAL(5,2)
        ELSE NULL
    END AS relevance_score

FROM content_analysis_v2.pipeline_executions pe
WHERE pe.success = true
ORDER BY RANDOM()
LIMIT 5;

-- Inspect results
\x
SELECT * FROM test_unified;
\x

-- Compare with original
SELECT
    article_id,
    triage_decision,
    entity_results,
    summary_results
FROM content_analysis_v2.pipeline_executions
WHERE article_id IN (SELECT article_id FROM test_unified);

ROLLBACK;  -- Don't commit test data
```

---

## 📝 Appendix B: Manual API Layer Update

**If agent didn't complete API layer update, manually edit:**

**File:** `services/feed-service/app/services/analysis_loader.py`

**Change from:**
```python
# OLD: Proxy to content-analysis-v2 API
async def load_analysis(article_id: str) -> Optional[Dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONTENT_ANALYSIS_URL}/api/v1/analyses/{article_id}"
        )
        return response.json() if response.status_code == 200 else None
```

**Change to:**
```python
# NEW: Read directly from unified table
async def load_analysis(article_id: str) -> Optional[Dict]:
    query = """
        SELECT
            article_id,
            pipeline_version,
            success,
            triage_results,
            tier1_results,
            tier2_results,
            tier3_results,
            relevance_score,
            score_breakdown,
            metrics,
            error_message,
            failed_agents,
            created_at,
            updated_at
        FROM public.article_analysis
        WHERE article_id = :article_id
    """

    result = await database.fetch_one(query=query, values={"article_id": article_id})

    if result:
        # Transform to match legacy format for backward compatibility
        return {
            "article_id": result["article_id"],
            "pipeline_version": result["pipeline_version"],
            "success": result["success"],
            "triage_decision": result["triage_results"],
            "entity_results": result["tier1_results"].get("entity_results", {}),
            "summary_results": result["tier1_results"].get("summary_results", {}),
            "sentiment_results": result["tier1_results"].get("sentiment_results", {}),
            "topic_results": result["tier1_results"].get("topic_results", {}),
            "financial_results": result["tier2_results"].get("financial_results", {}),
            "geopolitical_results": result["tier2_results"].get("geopolitical_results", {}),
            "conflict_results": result["tier2_results"].get("conflict_results", {}),
            "bias_results": result["tier2_results"].get("bias_results", {}),
            "intelligence_results": result["tier3_results"],
            "relevance_score": result["relevance_score"],
            "score_breakdown": result["score_breakdown"],
            "metrics": result["metrics"],
            "error_message": result["error_message"],
            "failed_agents": result["failed_agents"],
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
        }

    return None
```

---

## 📞 Contact Information

**Escalation Path:**

| Issue Type | Contact | Availability |
|------------|---------|--------------|
| Database issues | Database Admin | 24/7 |
| API/Backend issues | Backend Engineer | Business hours |
| Frontend issues | Frontend Engineer | Business hours |
| Infrastructure | DevOps | 24/7 (on-call) |

**Communication Channels:**
- Slack: `#engineering-alerts` (real-time updates)
- Email: `engineering@company.com` (status reports)
- On-call: `+49-XXX-XXXXXXX` (emergencies only)

---

## 📚 References

- [ADR-032: Dual-Table Analysis Architecture](../decisions/ADR-032-dual-table-analysis-architecture.md)
- [Analysis Storage Migration Guide](./analysis-storage-migration-guide.md)
- [POSTMORTEMS.md - Incident #8](../../POSTMORTEMS.md#incident-8)
- [Test Suite README](../../tests/migration/README.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-31
**Author:** Database Team + Backend Team
**Review Schedule:** After migration completion

---

## See Also

- **[Migration Protocol](./migration-protocol.md)** - General best practices (499 lines)
  - This runbook implements the protocol described there
  - Use protocol as template for your own migrations
  - Pre-flight checklist and verification procedures
  - Lessons learned from failed migrations

- **[CLAUDE.backend.md - Database Migrations](../../CLAUDE.backend.md#migration-pattern)** - Quick reference for simple migrations

---
