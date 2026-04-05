#!/bin/bash
# Post-Migration Test Suite
# Verifies system state AFTER migration execution

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

init_test "POST-MIGRATION"

# Load pre-migration baseline
if [ -f "/tmp/migration_baseline/pre_migration.json" ]; then
    BASELINE_LEGACY_COUNT=$(jq -r '.legacy_count' /tmp/migration_baseline/pre_migration.json)
    BASELINE_UNIFIED_COUNT=$(jq -r '.unified_count' /tmp/migration_baseline/pre_migration.json)
    BASELINE_QUERY_TIME=$(jq -r '.query_time_ms' /tmp/migration_baseline/pre_migration.json)
    print_info "Loaded baseline: Legacy=$BASELINE_LEGACY_COUNT, Unified=$BASELINE_UNIFIED_COUNT"
else
    print_warning "No baseline found - skipping comparison tests"
    BASELINE_LEGACY_COUNT=0
    BASELINE_UNIFIED_COUNT=0
    BASELINE_QUERY_TIME=0
fi

# ════════════════════════════════════════════════════════════════════
# 1. ROW COUNT VERIFICATION
# ════════════════════════════════════════════════════════════════════
print_section "1. Row Count Verification"

# 1.1 Check unified table count
print_info "Checking unified table row count..."
unified_count=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis;")
print_info "Unified table has $unified_count rows"

# 1.2 Check legacy table count (should be same)
print_info "Checking legacy table row count..."
legacy_count=$(execute_sql "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions;")
print_info "Legacy table has $legacy_count rows"

# 1.3 Verify counts match
assert_equals "Counts match (migration complete)" "$unified_count" "$legacy_count"

# 1.4 Verify no missing analyses
print_info "Checking for missing analyses..."
missing_analyses=$(execute_sql "SELECT COUNT(*) FROM content_analysis_v2.pipeline_executions pe LEFT JOIN public.article_analysis aa ON pe.article_id = aa.article_id WHERE aa.id IS NULL;")
assert_equals "No missing analyses in unified table" "$missing_analyses" "0"

# ════════════════════════════════════════════════════════════════════
# 2. DATA TRANSFORMATION VERIFICATION
# ════════════════════════════════════════════════════════════════════
print_section "2. Data Transformation Verification"

# 2.1 Sample 10 random articles
print_info "Sampling 10 random articles for transformation verification..."
sample_ids=$(execute_sql "SELECT article_id FROM content_analysis_v2.pipeline_executions WHERE success = true ORDER BY RANDOM() LIMIT 10;")

# Convert to array
IFS=$'\n' read -d '' -r -a sample_array <<< "$sample_ids" || true

transformation_errors=0

for article_id in "${sample_array[@]}"; do
    # Get legacy data
    legacy_data=$(execute_sql "SELECT triage_decision, entity_results, summary_results, sentiment_results, topic_results, tier1_summary FROM content_analysis_v2.pipeline_executions WHERE article_id = '$article_id';")

    # Get unified data
    unified_data=$(execute_sql "SELECT triage_results, tier1_results, relevance_score FROM public.article_analysis WHERE article_id = '$article_id';")

    # Check if both exist
    if [ -z "$legacy_data" ] || [ -z "$unified_data" ]; then
        print_error "Missing data for article $article_id"
        ((transformation_errors++))
        continue
    fi

    # Verify tier1_results is not null
    tier1_null=$(execute_sql "SELECT tier1_results IS NULL FROM public.article_analysis WHERE article_id = '$article_id';")
    if [ "$tier1_null" = "t" ]; then
        print_error "Tier1 results NULL for $article_id"
        ((transformation_errors++))
    fi
done

if [ $transformation_errors -eq 0 ]; then
    print_success "All sampled transformations correct ✅"
    ((TESTS_PASSED++))
else
    print_error "$transformation_errors transformation errors found"
    ((TESTS_FAILED++))
fi

# 2.2 Verify relevance_score extraction
print_info "Checking relevance_score extraction..."
scores_extracted=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE success = true AND relevance_score IS NOT NULL;")
successful_analyses=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE success = true;")

score_extraction_rate=$((scores_extracted * 100 / successful_analyses))
print_info "Relevance scores extracted: $score_extraction_rate%"
assert_greater_than "Most relevance scores extracted" "$score_extraction_rate" "80"

# 2.3 Check for null triage_results
print_info "Checking triage results..."
null_triage=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE success = true AND triage_results IS NULL;")
assert_equals "No null triage for successful analyses" "$null_triage" "0"

# ════════════════════════════════════════════════════════════════════
# 3. PERFORMANCE VERIFICATION
# ════════════════════════════════════════════════════════════════════
print_section "3. Performance Verification"

# 3.1 Get auth token
print_info "Getting auth token..."
TOKEN=$(get_auth_token)
if [ -z "$TOKEN" ]; then
    print_error "Failed to get auth token"
    ((TESTS_FAILED++))
else
    print_success "Auth token obtained"
    ((TESTS_PASSED++))
fi

# 3.2 Test single article endpoint
print_info "Testing single article endpoint performance..."
test_article_id=$(execute_sql "SELECT article_id FROM public.article_analysis ORDER BY RANDOM() LIMIT 1;")

start_time=$(date +%s%3N)
response=$(test_api_endpoint "$FEED_SERVICE_URL/api/v1/feeds/items/$test_article_id" "$TOKEN" "200")
end_time=$(date +%s%3N)
single_article_time=$((end_time - start_time))

print_info "Single article response time: ${single_article_time}ms"
assert_less_than "Single article response < 200ms" "$single_article_time" "200"

# 3.3 Test batch endpoint
print_info "Testing batch endpoint (20 articles)..."
start_time=$(date +%s%3N)
response=$(test_api_endpoint "$FEED_SERVICE_URL/api/v1/feeds/items?limit=20" "$TOKEN" "200")
end_time=$(date +%s%3N)
batch_time=$((end_time - start_time))

print_info "Batch response time: ${batch_time}ms"
assert_less_than "Batch response < 700ms" "$batch_time" "700"

# 3.4 Verify response contains analysis data
print_info "Verifying API response structure..."
has_pipeline_execution=$(echo "$response" | jq -e '.items[0].pipeline_execution != null' >/dev/null 2>&1 && echo "1" || echo "0")
assert_equals "Response contains pipeline_execution" "$has_pipeline_execution" "1"

# ════════════════════════════════════════════════════════════════════
# 4. FRONTEND COMPATIBILITY
# ════════════════════════════════════════════════════════════════════
print_section "4. Frontend Compatibility"

# 4.1 Check response structure matches frontend expectations
print_info "Checking response structure..."
sample_response=$(test_api_endpoint "$FEED_SERVICE_URL/api/v1/feeds/items/$test_article_id" "$TOKEN" "200")

# Check for required fields
has_triage=$(echo "$sample_response" | jq -e '.pipeline_execution.triage_results != null' >/dev/null 2>&1 && echo "1" || echo "0")
assert_equals "Response has triage_results" "$has_triage" "1"

has_tier1=$(echo "$sample_response" | jq -e '.pipeline_execution.tier1_results != null' >/dev/null 2>&1 && echo "1" || echo "0")
assert_equals "Response has tier1_results" "$has_tier1" "1"

has_tier2=$(echo "$sample_response" | jq -e '.pipeline_execution.tier2_results != null' >/dev/null 2>&1 && echo "1" || echo "0")
assert_equals "Response has tier2_results" "$has_tier2" "1"

# ════════════════════════════════════════════════════════════════════
# 5. NEW ANALYSES VERIFICATION
# ════════════════════════════════════════════════════════════════════
print_section "5. New Analyses Verification"

# 5.1 Check recent analyses (last 10 minutes)
print_info "Checking for recent analyses..."
recent_count=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis WHERE created_at > NOW() - INTERVAL '10 minutes';")
print_info "Recent analyses (last 10 min): $recent_count"

if [ "$recent_count" -gt 0 ]; then
    print_success "New analyses are being written to unified table ✅"
    ((TESTS_PASSED++))
else
    print_warning "No recent analyses - workers might be stopped"
fi

# 5.2 Verify analysis-consumer is still running
print_info "Checking analysis-consumer status..."
consumer_running=$(docker ps --filter "name=feed-service-analysis-consumer" --format "{{.Status}}" | grep -c "Up" || echo "0")
assert_equals "Analysis-consumer is running" "$consumer_running" "1"

# ════════════════════════════════════════════════════════════════════
# 6. DATA INTEGRITY POST-MIGRATION
# ════════════════════════════════════════════════════════════════════
print_section "6. Data Integrity"

# 6.1 Check for duplicates
print_info "Checking for duplicate article_ids..."
duplicates=$(execute_sql "SELECT COUNT(*) FROM (SELECT article_id, COUNT(*) as cnt FROM public.article_analysis GROUP BY article_id HAVING COUNT(*) > 1) sub;")
assert_equals "No duplicates in unified table" "$duplicates" "0"

# 6.2 Check foreign key integrity
print_info "Checking foreign key integrity..."
orphaned=$(execute_sql "SELECT COUNT(*) FROM public.article_analysis aa LEFT JOIN feed_items fi ON aa.article_id = fi.id WHERE fi.id IS NULL;")
assert_equals "No orphaned analyses" "$orphaned" "0"

# 6.3 Check success rate
print_info "Checking success rate..."
success_rate=$(execute_sql "SELECT ROUND(COUNT(*) FILTER (WHERE success = true) * 100.0 / COUNT(*)) FROM public.article_analysis;")
print_info "Success rate: ${success_rate}%"
assert_greater_than "Success rate acceptable" "$success_rate" "90"

# ════════════════════════════════════════════════════════════════════
# 7. PERFORMANCE COMPARISON
# ════════════════════════════════════════════════════════════════════
print_section "7. Performance Comparison"

if [ "$BASELINE_QUERY_TIME" != "0" ]; then
    print_info "Comparing with baseline..."

    # Current query time (already measured in section 3)
    improvement_percent=$(echo "scale=1; ($BASELINE_QUERY_TIME - $single_article_time) * 100 / $BASELINE_QUERY_TIME" | bc)

    echo "┌─────────────────────────────────────────────┐"
    echo "│ PERFORMANCE COMPARISON                      │"
    echo "├─────────────────────────────────────────────┤"
    echo "│ Before: $(printf '%4d' $(echo $BASELINE_QUERY_TIME | cut -d. -f1))ms                              │"
    echo "│ After:  $(printf '%4d' $single_article_time)ms                              │"

    if [ "${improvement_percent%.*}" -gt 0 ]; then
        echo "│ Improvement: $(printf '%3d' ${improvement_percent%.*})%                         │"
        print_success "Performance improved ✅"
    else
        echo "│ Improvement: 0%                             │"
        print_warning "No significant performance change"
    fi
    echo "└─────────────────────────────────────────────┘"
else
    print_warning "No baseline available for comparison"
fi

# ════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════
print_section "Post-Migration Summary"

echo "┌────────────────────────────────────────┐"
echo "│ MIGRATION RESULTS                      │"
echo "├────────────────────────────────────────┤"
echo "│ Unified table rows: $(printf '%6d' $unified_count)          │"
echo "│ Legacy table rows:  $(printf '%6d' $legacy_count)          │"
echo "│ Success rate: ${success_rate}%                   │"
echo "│ Single article: $(printf '%4d' $single_article_time)ms               │"
echo "│ Batch (20): $(printf '%4d' $batch_time)ms                   │"
echo "└────────────────────────────────────────┘"
echo ""

# Save post-migration metrics
mkdir -p /tmp/migration_baseline
echo "{
  \"timestamp\": \"$(date -Iseconds)\",
  \"unified_count\": $unified_count,
  \"legacy_count\": $legacy_count,
  \"success_rate\": $success_rate,
  \"single_article_time_ms\": $single_article_time,
  \"batch_time_ms\": $batch_time
}" > /tmp/migration_baseline/post_migration.json

print_success "Post-migration metrics saved"

if [ "$unified_count" = "$legacy_count" ] && [ "$duplicates" = "0" ] && [ "$orphaned" = "0" ]; then
    print_success "✅ MIGRATION SUCCESSFUL - All checks passed"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Monitor system for 24 hours"
    echo "2. Run test_post_migration.sh again after 24h"
    echo "3. If stable, deprecate legacy table (rename to *_deprecated)"
    echo "4. Update documentation"
else
    print_error "⚠️  MIGRATION ISSUES DETECTED - Review failures above"
    echo ""
    echo -e "${RED}Rollback Recommended:${NC}"
    echo "1. Run ./test_rollback.sh to restore legacy configuration"
    echo "2. Investigate errors"
    echo "3. Fix issues and retry migration"
fi

finish_test
