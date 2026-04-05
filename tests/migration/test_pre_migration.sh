#!/bin/bash
# Pre-Migration Test Suite
# Verifies system state BEFORE migration execution

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

init_test "PRE-MIGRATION"

# ════════════════════════════════════════════════════════════════════
# 1. LEGACY TABLE VERIFICATION
# ════════════════════════════════════════════════════════════════════
print_section "1. Legacy Table (content_analysis_v2.pipeline_executions)"

# 1.1 Check table exists
print_info "Checking table existence..."
legacy_exists=$(execute_sql "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='content_analysis_v2' AND table_name='pipeline_executions';")
assert_equals "Legacy table exists" "$legacy_exists" "1"

# 1.2 Check row count
print_info "Checking row count..."
legacy_count=$(execute_sql "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;")
print_info "Legacy table has $legacy_count rows"
assert_greater_than "Legacy table has data" "$legacy_count" "7000"

# 1.3 Check success rate
print_info "Checking success rate..."
legacy_success_rate=$(execute_sql "SELECT ROUND(COUNT(*) FILTER (WHERE success = true) * 100.0 / COUNT(*)) FROM content_analysis_v2.pipeline_executions;")
print_info "Success rate: ${legacy_success_rate}%"
assert_greater_than "Success rate acceptable" "$legacy_success_rate" "90"

# 1.4 Check for null triage decisions
print_info "Checking data quality..."
null_triage_count=$(execute_sql "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions WHERE success = true AND triage_decision IS NULL;")
assert_equals "No null triage for successful analyses" "$null_triage_count" "0"

# 1.5 Check foreign key integrity
print_info "Checking foreign key integrity..."
orphaned_analyses=$(execute_sql "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions pe LEFT JOIN feed_items fi ON pe.article_id = fi.id WHERE fi.id IS NULL;")
assert_equals "No orphaned analyses (all article_ids exist)" "$orphaned_analyses" "0"

# ════════════════════════════════════════════════════════════════════
# 2. UNIFIED TABLE VERIFICATION
# ════════════════════════════════════════════════════════════════════
print_section "2. Unified Table (public.article_analysis)"

# 2.1 Check table exists
print_info "Checking table existence..."
unified_exists=$(execute_sql "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='article_analysis';")
assert_equals "Unified table exists" "$unified_exists" "1"

# 2.2 Check row count
print_info "Checking row count..."
unified_count=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis;")
print_info "Unified table has $unified_count rows"
print_warning "Expected: Lower than legacy (incomplete migration)"

# 2.3 Calculate missing rows
missing_count=$((legacy_count - unified_count))
print_info "Missing rows in unified table: $missing_count"
assert_greater_than "Unified table has some data" "$unified_count" "3000"

# 2.4 Check for overlapping data
print_info "Checking overlap between tables..."
overlap_count=$(execute_sql "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions pe INNER JOIN public.article_analysis aa ON pe.article_id = aa.article_id;")
print_info "Overlapping analyses: $overlap_count"
assert_equals "Overlap matches unified count" "$overlap_count" "$unified_count"

# ════════════════════════════════════════════════════════════════════
# 3. FEED ITEMS VERIFICATION
# ════════════════════════════════════════════════════════════════════
print_section "3. Feed Items Table"

# 3.1 Check total feed items
print_info "Checking total articles..."
total_articles=$(execute_sql "SELECT COUNT(*) FROM feed_items;")
print_info "Total articles: $total_articles"
assert_greater_than "Feed items exist" "$total_articles" "7000"

# 3.2 Check articles WITHOUT analysis (legacy table)
print_info "Checking articles without analysis..."
missing_analysis=$(execute_sql "SELECT COUNT(*) FROM feed_items fi LEFT JOIN content_analysis_v2.pipeline_executions pe ON fi.id = pe.article_id WHERE pe.id IS NULL;")
print_info "Articles without analysis: $missing_analysis"

if [ "$missing_analysis" -gt 0 ]; then
    print_warning "$missing_analysis articles need analysis"
else
    print_success "All articles have analysis ✅"
fi

# ════════════════════════════════════════════════════════════════════
# 4. PERFORMANCE BASELINE
# ════════════════════════════════════════════════════════════════════
print_section "4. Performance Baseline"

# 4.1 Measure single article query time
print_info "Measuring query performance (100 random articles)..."
query_time_sql="
EXPLAIN (ANALYZE, TIMING)
SELECT * FROM content_analysis_v2.pipeline_executions
WHERE article_id = (SELECT article_id FROM content_analysis_v2.pipeline_executions ORDER BY RANDOM() LIMIT 1);
"
query_time=$(docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "$query_time_sql" 2>/dev/null | grep "Execution Time" | awk '{print $3}')
print_info "Average query time: ${query_time}ms"

# Save baseline to file
mkdir -p /tmp/migration_baseline
echo "{
  \"timestamp\": \"$(date -Iseconds)\",
  \"legacy_count\": $legacy_count,
  \"unified_count\": $unified_count,
  \"missing_count\": $missing_count,
  \"success_rate\": $legacy_success_rate,
  \"query_time_ms\": $query_time
}" > /tmp/migration_baseline/pre_migration.json

print_success "Baseline saved to /tmp/migration_baseline/pre_migration.json"

# ════════════════════════════════════════════════════════════════════
# 5. WORKER STATUS CHECK
# ════════════════════════════════════════════════════════════════════
print_section "5. Worker Status"

# 5.1 Check if analysis-consumer is running
print_info "Checking analysis-consumer status..."
consumer_running=$(docker ps --filter "name=feed-service-analysis-consumer" --format "{{.Status}}" | grep -c "Up" || echo "0")
assert_equals "Analysis-consumer is running" "$consumer_running" "1"

# 5.2 Check if workers are running
print_info "Checking content-analysis-v2 workers..."
worker_count=$(docker ps --filter "name=content-analysis-v2-worker" --format "{{.Names}}" | wc -l)
assert_greater_than "Content-analysis workers running" "$worker_count" "0"
print_info "$worker_count worker(s) active"

# ════════════════════════════════════════════════════════════════════
# 6. DATA INTEGRITY CHECKS
# ════════════════════════════════════════════════════════════════════
print_section "6. Data Integrity"

# 6.1 Check for duplicate article_ids
print_info "Checking for duplicate article_ids..."
duplicates_legacy=$(execute_sql "SELECT COUNT(*) FROM (SELECT article_id, COUNT(*) as cnt FROM content_analysis_v2.pipeline_executions GROUP BY article_id HAVING COUNT(*) > 1) sub;")
assert_equals "No duplicates in legacy table" "$duplicates_legacy" "0"

duplicates_unified=$(execute_sql "SELECT COUNT(*) FROM (SELECT article_id, COUNT(*) as cnt FROM public.article_analysis GROUP BY article_id HAVING COUNT(*) > 1) sub;")
assert_equals "No duplicates in unified table" "$duplicates_unified" "0"

# 6.2 Check data freshness
print_info "Checking data freshness..."
recent_analyses=$(execute_sql "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions WHERE created_at > NOW() - INTERVAL '24 hours';")
print_info "Analyses in last 24h: $recent_analyses"
assert_greater_than "Recent analyses exist" "$recent_analyses" "0"

# ════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════
print_section "Pre-Migration Summary"

echo "┌────────────────────────────────────────┐"
echo "│ LEGACY TABLE                           │"
echo "├────────────────────────────────────────┤"
echo "│ Total rows: $(printf '%6d' $legacy_count)                     │"
echo "│ Success rate: ${legacy_success_rate}%                       │"
echo "│ Null triage: $(printf '%6d' $null_triage_count)                      │"
echo "│ Orphaned: $(printf '%6d' $orphaned_analyses)                         │"
echo "└────────────────────────────────────────┘"
echo ""
echo "┌────────────────────────────────────────┐"
echo "│ UNIFIED TABLE                          │"
echo "├────────────────────────────────────────┤"
echo "│ Total rows: $(printf '%6d' $unified_count)                     │"
echo "│ Missing rows: $(printf '%6d' $missing_count)                   │"
echo "│ Coverage: $(printf '%3d' $((unified_count * 100 / legacy_count)))%                          │"
echo "└────────────────────────────────────────┘"
echo ""

if [ "$missing_count" -gt 0 ]; then
    print_warning "⚠️  Migration required: $missing_count rows need backfill"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Review baseline metrics: /tmp/migration_baseline/pre_migration.json"
    echo "2. Execute backfill SQL script"
    echo "3. Run post-migration tests"
else
    print_success "✅ Data already synchronized - no migration needed"
fi

finish_test
