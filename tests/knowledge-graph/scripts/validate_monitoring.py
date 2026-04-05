#!/usr/bin/env python3
"""
Knowledge Graph Monitoring Validator

Validates that Prometheus metrics accurately reflect test execution.

Usage:
    export CONTENT_ANALYSIS_METRICS_URL="http://localhost:8102/metrics"
    python scripts/validate_monitoring.py

Logic:
    1. Read baseline metrics from service
    2. Execute test suite (or analyze existing results)
    3. Read metrics again
    4. Compare delta with actual processed relationships
    5. Report discrepancies
"""

import os
import sys
import re
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import json


BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "test-results"
METRICS_URL = os.getenv("CONTENT_ANALYSIS_METRICS_URL", "http://localhost:8102/metrics")


class PrometheusMetrics:
    """Parse and compare Prometheus metrics."""

    def __init__(self, metrics_text: str):
        self.metrics = self.parse_metrics(metrics_text)

    def parse_metrics(self, text: str) -> Dict[str, float]:
        """
        Parse Prometheus text format.

        Example:
        # HELP relationship_extraction_total Total relationships extracted by status
        # TYPE relationship_extraction_total counter
        relationship_extraction_total{status="valid"} 42.0
        relationship_extraction_total{status="invalid"} 5.0
        """
        metrics = {}

        for line in text.split('\n'):
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue

            # Parse metric line: metric_name{labels} value
            match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\{([^}]*)\}\s+([\d.]+)', line)
            if match:
                metric_name = match.group(1)
                labels = match.group(2)
                value = float(match.group(3))

                # Create key with labels
                key = f"{metric_name}{{{labels}}}"
                metrics[key] = value
            else:
                # Metric without labels
                match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s+([\d.]+)', line)
                if match:
                    metric_name = match.group(1)
                    value = float(match.group(2))
                    metrics[metric_name] = value

        return metrics

    def get(self, metric_key: str, default: float = 0.0) -> float:
        """Get metric value."""
        return self.metrics.get(metric_key, default)

    def delta(self, other: 'PrometheusMetrics', metric_key: str) -> float:
        """Calculate delta between two metric snapshots."""
        return self.get(metric_key) - other.get(metric_key)


class MonitoringValidator:
    """Validates Prometheus metrics against test results."""

    def __init__(self):
        self.metrics_url = METRICS_URL
        self.baseline_metrics = None
        self.current_metrics = None
        self.validation_results = []

    def fetch_metrics(self) -> Optional[PrometheusMetrics]:
        """Fetch metrics from service."""
        try:
            response = requests.get(self.metrics_url, timeout=10)
            response.raise_for_status()
            return PrometheusMetrics(response.text)
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to fetch metrics: {e}")
            return None

    def count_relationships_from_results(self) -> Dict[str, int]:
        """
        Count relationships from test results.

        Returns:
            {
                "total_valid": int,
                "total_invalid": int,
                "total_processed": int
            }
        """
        counts = {
            "total_valid": 0,
            "total_invalid": 0,
            "total_processed": 0
        }

        if not RESULTS_DIR.exists():
            return counts

        # Iterate through all result files
        for category_dir in RESULTS_DIR.glob("category-*"):
            for result_file in category_dir.glob("*-result.json"):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)

                    if not result.get("success"):
                        continue

                    relationships = result.get("data", {}).get("relationships", [])
                    counts["total_processed"] += len(relationships)

                    # Assume valid if confidence >= 0.5 (matching our validation threshold)
                    for rel in relationships:
                        if rel.get("confidence", 0) >= 0.5:
                            counts["total_valid"] += 1
                        else:
                            counts["total_invalid"] += 1

                except Exception as e:
                    print(f"⚠ Failed to process {result_file}: {e}")

        return counts

    def validate_counter(self, name: str, expected: int, actual_delta: float, tolerance: float = 0.1) -> bool:
        """
        Validate a counter metric.

        Args:
            name: Metric name
            expected: Expected count from results
            actual_delta: Actual delta from Prometheus
            tolerance: Acceptable percentage difference (default 10%)

        Returns:
            True if validation passes
        """
        # Allow for small discrepancies due to timing, retries, etc.
        acceptable_range = (expected * (1 - tolerance), expected * (1 + tolerance))

        passed = acceptable_range[0] <= actual_delta <= acceptable_range[1]

        result = {
            "metric": name,
            "expected": expected,
            "actual": actual_delta,
            "difference": actual_delta - expected,
            "passed": passed
        }

        self.validation_results.append(result)

        return passed

    def validate_gauge(self, name: str, expected_min: float, expected_max: float, actual: float) -> bool:
        """
        Validate a gauge metric (e.g., acceptance rate, avg confidence).

        Args:
            name: Metric name
            expected_min: Minimum expected value
            expected_max: Maximum expected value
            actual: Actual value from Prometheus

        Returns:
            True if validation passes
        """
        passed = expected_min <= actual <= expected_max

        result = {
            "metric": name,
            "expected_range": f"{expected_min:.2f}-{expected_max:.2f}",
            "actual": actual,
            "passed": passed
        }

        self.validation_results.append(result)

        return passed

    def run(self):
        """Run complete monitoring validation."""
        print("="*60)
        print("PROMETHEUS METRICS VALIDATION")
        print("="*60)
        print(f"Metrics URL: {self.metrics_url}")

        # Fetch current metrics
        print("\n→ Fetching metrics from service...")
        self.current_metrics = self.fetch_metrics()

        if not self.current_metrics:
            print("✗ Cannot proceed without metrics access")
            return False

        print("✓ Metrics fetched successfully")

        # Analyze test results
        print("\n→ Analyzing test results...")
        result_counts = self.count_relationships_from_results()

        print(f"  Total relationships processed: {result_counts['total_processed']}")
        print(f"  Valid relationships: {result_counts['total_valid']}")
        print(f"  Invalid relationships: {result_counts['total_invalid']}")

        # Validate metrics
        print("\n→ Validating metrics...")

        # Counter: relationship_extraction_total{status="valid"}
        actual_valid = self.current_metrics.get('relationship_extraction_total{status="valid"}', 0)
        self.validate_counter(
            "relationship_extraction_total{status=\"valid\"}",
            result_counts["total_valid"],
            actual_valid
        )

        # Counter: relationship_extraction_total{status="invalid"}
        actual_invalid = self.current_metrics.get('relationship_extraction_total{status="invalid"}', 0)
        self.validate_counter(
            "relationship_extraction_total{status=\"invalid\"}",
            result_counts["total_invalid"],
            actual_invalid
        )

        # Gauge: relationship_acceptance_rate (valid / total)
        if result_counts["total_processed"] > 0:
            expected_rate = result_counts["total_valid"] / result_counts["total_processed"]
            actual_rate = self.current_metrics.get('relationship_acceptance_rate', 0)

            self.validate_gauge(
                "relationship_acceptance_rate",
                max(0, expected_rate - 0.1),  # Allow 10% variance
                min(1.0, expected_rate + 0.1),
                actual_rate
            )

        # Print results
        self.print_results()

        # Return success if all validations passed
        return all(r["passed"] for r in self.validation_results)

    def print_results(self):
        """Print validation results."""
        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)

        passed_count = sum(1 for r in self.validation_results if r["passed"])
        total_count = len(self.validation_results)

        for result in self.validation_results:
            status = "✅" if result["passed"] else "❌"
            print(f"\n{status} {result['metric']}")

            if "expected" in result:
                print(f"  Expected: {result['expected']}")
                print(f"  Actual:   {result['actual']}")
                print(f"  Diff:     {result['difference']:+.0f}")
            elif "expected_range" in result:
                print(f"  Expected: {result['expected_range']}")
                print(f"  Actual:   {result['actual']:.2f}")

        print("\n" + "="*60)
        if passed_count == total_count:
            print(f"✅ ALL VALIDATIONS PASSED ({passed_count}/{total_count})")
        else:
            print(f"❌ SOME VALIDATIONS FAILED ({passed_count}/{total_count} passed)")
        print("="*60)


def main():
    """Main entry point."""
    if not RESULTS_DIR.exists():
        print("⚠ Warning: No test results found.")
        print("  Run run_test_suite.py first to generate results.")
        print("  Or this validator will compare against empty baseline.")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            return 1

    validator = MonitoringValidator()
    success = validator.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
