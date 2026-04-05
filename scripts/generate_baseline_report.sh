#!/bin/bash
#
# Generate Comprehensive Baseline Report
# Combines code, performance, and system metrics
#

OUTPUT_FILE="reports/baseline-metrics-20251030.md"

cat > "$OUTPUT_FILE" << 'MDEOF'
# Baseline Metrics Report - 2025-10-30

**Purpose:** Pre-refactoring baseline for measuring improvement
**Generated:** $(date)

---

## 📊 Executive Summary

This baseline establishes quantitative metrics before Phase 0 refactoring begins.

### Key Findings

- **Performance:** Auth/Feed services respond in < 10ms (excellent)
- **System Health:** CPU at 19%, Memory at 67% (healthy)
- **Coverage:** Not yet measured (pending)

MDEOF

# Performance Summary
echo "## 1. Performance Metrics" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
latest_perf=$(ls -t reports/metrics/performance/performance-*.md 2>/dev/null | head -1)
if [ -n "$latest_perf" ]; then
  tail -n +5 "$latest_perf" >> "$OUTPUT_FILE"
else
  echo "⚠️ Performance metrics not yet collected" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# System Health
echo "## 2. System Health" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
latest_system=$(ls -t reports/metrics/system/system-*.txt 2>/dev/null | head -1)
if [ -n "$latest_system" ]; then
  cat "$latest_system" >> "$OUTPUT_FILE"
else
  echo "⚠️ System metrics not yet collected" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# Code Coverage Summary
echo "## 3. Code Coverage" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
if [ -f "reports/metrics/code/coverage-summary.txt" ]; then
  cat reports/metrics/code/coverage-summary.txt >> "$OUTPUT_FILE"
else
  echo "⚠️ Code coverage data not yet collected" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  echo "**Note:** Code coverage will be measured per-service basis." >> "$OUTPUT_FILE"
  echo "Services with test suites:" >> "$OUTPUT_FILE"
  echo "- notification-service (12 test files)" >> "$OUTPUT_FILE"
  echo "- entity-canonicalization-service (1 test file)" >> "$OUTPUT_FILE"
  echo "- fmp-service (2 test files)" >> "$OUTPUT_FILE"
  echo "- auth-service (1 test file)" >> "$OUTPUT_FILE"
  echo "- Additional services TBD" >> "$OUTPUT_FILE"
fi
echo "" >> "$OUTPUT_FILE"

# Recommendations
cat >> "$OUTPUT_FILE" << 'MDEOF'

---

## 📈 Tracking Over Time

**Weekly Metrics Collection:**
```bash
# Run full metrics suite
./scripts/collect_performance_metrics.sh
./scripts/collect_system_metrics.sh
./scripts/generate_baseline_report.sh
```

**Compare with baseline:**
```bash
# Compare API performance
diff -u reports/baseline-metrics-20251030.md reports/metrics-$(date +%Y%m%d).md

# Check for regressions
# If response times increased > 20% → investigate
# If coverage decreased → add tests before merging
```

---

## 🎯 Success Metrics for Refactoring

After Phase 5 completion, we should see:

**Code Quality:**
- [ ] Code coverage increased from baseline to > 70%
- [ ] All TODO/FIXME comments resolved (30 tracked)
- [ ] Zero obsolete code remaining

**Performance:**
- [ ] API response times stable or improved (< 10% variance)
- [ ] Database query times optimized (< 100ms for simple queries)
- [ ] No new N+1 query problems introduced

**System Health:**
- [ ] All 25 services healthy (0 unhealthy)
- [ ] Memory usage stable under load
- [ ] No memory leaks detected

---

**Created:** 2025-10-30
**Next Review:** Weekly during refactoring
**Comparison Tool:** `scripts/compare_metrics.sh`
MDEOF

echo ""
echo "✅ Baseline report generated: $OUTPUT_FILE"
cat "$OUTPUT_FILE"
