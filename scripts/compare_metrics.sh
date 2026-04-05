#!/bin/bash
#
# Metrics Comparison Tool
# Compare current metrics against baseline
#

if [ $# -lt 2 ]; then
  echo "Usage: $0 <baseline-file> <current-file>"
  echo "Example: $0 reports/baseline-metrics-20251030.md reports/metrics-20251105.md"
  exit 1
fi

BASELINE=$1
CURRENT=$2

if [ ! -f "$BASELINE" ]; then
  echo "Error: Baseline file not found: $BASELINE"
  exit 1
fi

if [ ! -f "$CURRENT" ]; then
  echo "Error: Current file not found: $CURRENT"
  exit 1
fi

echo "=== Metrics Comparison ==="
echo "Baseline: $BASELINE"
echo "Current:  $CURRENT"
echo ""

# Extract API response times from both files
extract_api_times() {
  local file=$1
  grep -A 20 "## API Response Times" "$file" 2>/dev/null | grep "^\- \*\*" | sed 's/- \*\*//g' | sed 's/\*\*://g'
}

echo "## API Response Time Changes"
echo ""

baseline_times=$(extract_api_times "$BASELINE")
current_times=$(extract_api_times "$CURRENT")

if [ -z "$baseline_times" ]; then
  echo "⚠️ No API response times found in baseline file"
  echo ""
fi

if [ -z "$current_times" ]; then
  echo "⚠️ No API response times found in current file"
  echo ""
fi

# Counters
regression_count=0
improvement_count=0
stable_count=0
missing_count=0

# Compare each endpoint
if [ -n "$baseline_times" ] && [ -n "$current_times" ]; then
  while IFS= read -r line; do
    if [ -z "$line" ]; then
      continue
    fi

    endpoint=$(echo "$line" | awk '{print $1}')
    baseline_time=$(echo "$line" | awk '{print $2}' | tr -d 's' | tr -d '(')

    current_line=$(echo "$current_times" | grep "^$endpoint")
    if [ -n "$current_line" ]; then
      current_time=$(echo "$current_line" | awk '{print $2}' | tr -d 's' | tr -d '(')

      # Calculate percentage change
      change=$(echo "scale=2; ($current_time - $baseline_time) / $baseline_time * 100" | bc 2>/dev/null)

      if [ -n "$change" ]; then
        if (( $(echo "$change > 20" | bc -l 2>/dev/null) )); then
          echo "⚠️ $endpoint: ${baseline_time}s → ${current_time}s (+${change}%) REGRESSION"
          regression_count=$((regression_count + 1))
        elif (( $(echo "$change < -10" | bc -l 2>/dev/null) )); then
          echo "✅ $endpoint: ${baseline_time}s → ${current_time}s (${change}%) IMPROVED"
          improvement_count=$((improvement_count + 1))
        else
          echo "➡️  $endpoint: ${baseline_time}s → ${current_time}s (${change}%) STABLE"
          stable_count=$((stable_count + 1))
        fi
      fi
    else
      echo "❓ $endpoint: Missing in current report"
      missing_count=$((missing_count + 1))
    fi
  done <<< "$baseline_times"
fi

echo ""
echo "=== Summary ==="
echo "🔴 Regressions (>20% slower): $regression_count"
echo "🟢 Improvements (>10% faster): $improvement_count"
echo "🟡 Stable (within ±10%): $stable_count"
echo "⚪ Missing from current: $missing_count"
echo ""

# Extract system health metrics
echo "## System Health Changes"
echo ""

extract_cpu() {
  grep "User:" "$1" 2>/dev/null | awk '{print $2}' | tr -d '%' | head -1
}

extract_memory() {
  grep "Used:" "$1" 2>/dev/null | grep "MB" | awk '{print $5}' | tr -d '()%' | head -1
}

baseline_cpu=$(extract_cpu "$BASELINE")
current_cpu=$(extract_cpu "$CURRENT")

baseline_mem=$(extract_memory "$BASELINE")
current_mem=$(extract_memory "$CURRENT")

if [ -n "$baseline_cpu" ] && [ -n "$current_cpu" ]; then
  cpu_change=$(echo "scale=2; $current_cpu - $baseline_cpu" | bc 2>/dev/null)
  if [ -n "$cpu_change" ]; then
    echo "CPU Usage: ${baseline_cpu}% → ${current_cpu}% (${cpu_change}% change)"
  fi
fi

if [ -n "$baseline_mem" ] && [ -n "$current_mem" ]; then
  mem_change=$(echo "scale=2; $current_mem - $baseline_mem" | bc 2>/dev/null)
  if [ -n "$mem_change" ]; then
    echo "Memory Usage: ${baseline_mem}% → ${current_mem}% (${mem_change}% change)"
  fi
fi

echo ""
echo "=== Recommendation ==="
if [ $regression_count -gt 0 ]; then
  echo "⚠️ Performance regressions detected. Investigate before merging."
  exit 1
elif [ $improvement_count -gt 0 ]; then
  echo "✅ Performance improved! Document optimizations in commit message."
  exit 0
else
  echo "➡️ Performance stable. Safe to proceed."
  exit 0
fi
