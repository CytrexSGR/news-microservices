#!/bin/bash
#
# Knowledge Graph Test Suite - Master Runner
#
# Executes all 4 test phases in sequence:
# 1. run_test_suite.py     - Execute tests against API
# 2. calculate_metrics.py  - Compute precision/recall/F1
# 3. generate_report.py    - Create HTML report
# 4. validate_monitoring.py - Verify Prometheus metrics
#
# Usage:
#   export CONTENT_ANALYSIS_API_URL="http://localhost:8102/api/v1"
#   export AUTH_TOKEN="your-jwt-token"
#   ./scripts/run_all_tests.sh
#

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   KNOWLEDGE GRAPH TEST SUITE - COMPLETE VALIDATION      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check environment
if [ -z "$AUTH_TOKEN" ]; then
    echo "⚠ Warning: AUTH_TOKEN not set"
    read -p "Continue anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo "Configuration:"
echo "  API URL: ${CONTENT_ANALYSIS_API_URL:-http://localhost:8102/api/v1}"
echo "  Base Dir: $BASE_DIR"
echo ""

# Phase 1: Execute Test Suite
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1/4: Executing Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$SCRIPT_DIR/run_test_suite.py"

if [ $? -ne 0 ]; then
    echo "✗ Test suite execution failed"
    exit 1
fi

echo ""
echo "✓ Phase 1 completed"
echo ""

# Phase 2: Calculate Metrics
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 2/4: Calculating Metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$SCRIPT_DIR/calculate_metrics.py"

if [ $? -ne 0 ]; then
    echo "✗ Metrics calculation failed"
    exit 1
fi

echo ""
echo "✓ Phase 2 completed"
echo ""

# Phase 3: Generate HTML Report
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 3/4: Generating HTML Report"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$SCRIPT_DIR/generate_report.py"

if [ $? -ne 0 ]; then
    echo "✗ Report generation failed"
    exit 1
fi

echo ""
echo "✓ Phase 3 completed"
echo ""

# Phase 4: Validate Monitoring (optional - may fail if metrics unavailable)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 4/4: Validating Prometheus Metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$SCRIPT_DIR/validate_monitoring.py" || true  # Don't fail if metrics unavailable

echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              TEST SUITE COMPLETED SUCCESSFULLY           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Results:"
echo "  📊 JSON Report: $BASE_DIR/test-results/summary_report.json"
echo "  📄 HTML Report: $BASE_DIR/test-results/test_report.html"
echo "  📈 Execution Stats: $BASE_DIR/test-results/execution_stats.json"
echo ""
echo "Quick view:"
echo "  Overall Performance:"

# Extract overall metrics using jq if available
if command -v jq &> /dev/null; then
    PRECISION=$(jq -r '.overall.precision * 100 | round' "$BASE_DIR/test-results/summary_report.json" 2>/dev/null || echo "N/A")
    RECALL=$(jq -r '.overall.recall * 100 | round' "$BASE_DIR/test-results/summary_report.json" 2>/dev/null || echo "N/A")
    F1=$(jq -r '.overall.f1 * 100 | round' "$BASE_DIR/test-results/summary_report.json" 2>/dev/null || echo "N/A")

    echo "    Precision: ${PRECISION}%"
    echo "    Recall: ${RECALL}%"
    echo "    F1 Score: ${F1}%"
else
    echo "    (Install 'jq' to see metrics here)"
fi

echo ""
echo "Open HTML report:"
echo "  firefox $BASE_DIR/test-results/test_report.html"
echo ""
