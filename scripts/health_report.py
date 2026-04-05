#!/usr/bin/env python3
"""
Generate consolidated health and smoke status for News MCP services.

The script performs HTTP health checks, lightweight API smoke calls,
and infrastructure command checks. Results are emitted to stdout and,
optionally, persisted as machine-readable JSON for downstream tooling.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT = 8  # seconds


@dataclass
class Check:
    """Definition for an individual health or smoke check."""

    name: str
    target: str
    category: str  # infrastructure | application | monitoring
    check_type: str  # http | command
    expected_status: Optional[int] = None
    method: str = "GET"
    payload: Optional[bytes] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class CheckResult:
    """Result payload for a single check run."""

    name: str
    target: str
    category: str
    check_type: str
    status: str  # pass | warn | fail
    duration_ms: int
    observed_status: Optional[int] = None
    message: Optional[str] = None


def http_check(check: Check) -> CheckResult:
    """Execute an HTTP-based check."""
    start = time.perf_counter()
    status = "fail"
    observed_status: Optional[int] = None
    message: Optional[str] = None

    req = Request(
        check.target,
        method=check.method.upper(),
        headers=check.headers or {},
        data=check.payload,
    )

    try:
        with urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            observed_status = response.getcode()
            if check.expected_status is None or observed_status == check.expected_status:
                status = "pass"
            else:
                status = "warn"
                message = f"Unexpected HTTP status {observed_status}"
    except HTTPError as exc:
        observed_status = exc.code
        status = "warn"
        message = f"HTTP error {exc.code}: {exc.reason}"
    except URLError as exc:
        status = "fail"
        message = f"Connection error: {exc.reason}"
    except Exception as exc:  # pragma: no cover - guard for unforeseen errors
        status = "fail"
        message = f"Unhandled error: {exc}"

    duration_ms = int((time.perf_counter() - start) * 1000)
    return CheckResult(
        name=check.name,
        target=check.target,
        category=check.category,
        check_type=check.check_type,
        status=status,
        duration_ms=duration_ms,
        observed_status=observed_status,
        message=message,
    )


def command_check(check: Check) -> CheckResult:
    """Execute a shell command check."""
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            shlex.split(check.target),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=DEFAULT_TIMEOUT,
            check=False,
            text=True,
        )
        status = "pass" if completed.returncode == 0 else "fail"
        message = None if status == "pass" else completed.stderr.strip() or completed.stdout.strip()
    except subprocess.TimeoutExpired:
        status = "fail"
        message = "Command timed out"
    except FileNotFoundError:
        status = "fail"
        message = "Command not found"
    except Exception as exc:  # pragma: no cover
        status = "fail"
        message = f"Unhandled error: {exc}"

    duration_ms = int((time.perf_counter() - start) * 1000)
    return CheckResult(
        name=check.name,
        target=check.target,
        category=check.category,
        check_type=check.check_type,
        status=status,
        duration_ms=duration_ms,
        message=message,
    )


def run_checks(checks: List[Check]) -> List[CheckResult]:
    """Run all checks and collect results."""
    results: List[CheckResult] = []
    for check in checks:
        if check.check_type == "http":
            results.append(http_check(check))
        else:
            results.append(command_check(check))
    return results


def summarise(results: List[CheckResult]) -> Dict[str, int]:
    """Generate per-status counts."""
    summary = {"pass": 0, "warn": 0, "fail": 0}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1
    return summary


def overall_status(summary: Dict[str, int]) -> str:
    """Derive overall status from counts."""
    if summary["fail"] > 0:
        return "fail"
    if summary["warn"] > 0:
        return "warn"
    return "pass"


def print_table(results: List[CheckResult]) -> None:
    """Pretty-print results in a simple table."""
    headers = ["Status", "Category", "Name", "Target", "Latency"]
    rows = []
    for result in results:
        rows.append([
            result.status.upper(),
            result.category,
            result.name,
            result.target,
            f"{result.duration_ms} ms",
        ])

    col_widths = [max(len(str(col)) for col in column) for column in zip(headers, *rows)]

    def format_row(row: List[str]) -> str:
        return "  ".join(cell.ljust(width) for cell, width in zip(row, col_widths))

    print(format_row(headers))
    print("-" * (sum(col_widths) + 2 * (len(headers) - 1)))
    for row, result in zip(rows, results):
        line = format_row(row)
        if result.message:
            line = f"{line}  ({result.message})"
        print(line)


def ensure_directory(path: Path) -> None:
    """Ensure parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run service health & smoke checks.")
    parser.add_argument("--output", type=Path, help="Write JSON report to path")
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip smoke (OpenAPI) checks and run health probes only.",
    )
    args = parser.parse_args(argv)

    health_checks: List[Check] = [
        # Infrastructure
        Check("postgres", "docker exec news-postgres pg_isready -U news_user -d news_mcp", "infrastructure", "command"),
        Check("redis", "docker exec news-redis redis-cli -a redis_secret_2024 ping", "infrastructure", "command"),
        Check("rabbitmq", "docker exec news-rabbitmq rabbitmq-diagnostics check_running", "infrastructure", "command"),
        Check("minio", "http://localhost:9000/minio/health/live", "infrastructure", "http", expected_status=200),
        # Application health
        Check("auth-health", "http://localhost:8000/health", "application", "http", expected_status=200),
        Check("feed-health", "http://localhost:8001/health", "application", "http", expected_status=200),
        Check("content-analysis-health", "http://localhost:8002/api/v1/health", "application", "http", expected_status=200),
        Check("research-health", "http://localhost:8003/api/v1/health", "application", "http", expected_status=200),
        Check("osint-health", "http://localhost:8004/api/v1/health", "application", "http", expected_status=200),
        Check("notification-health", "http://localhost:8005/health", "application", "http", expected_status=200),
        Check("search-health", "http://localhost:8006/health", "application", "http", expected_status=200),
        Check("analytics-health", "http://localhost:8007/health", "application", "http", expected_status=200),
        # Monitoring / gateway
        Check("traefik-api", "http://localhost:8080/api/overview", "monitoring", "http", expected_status=200),
        Check("prometheus", "http://localhost:9090/-/healthy", "monitoring", "http", expected_status=200),
        Check("grafana", "http://localhost:3001/api/health", "monitoring", "http", expected_status=200),
        Check("loki", "http://localhost:3100/ready", "monitoring", "http", expected_status=200),
    ]

    smoke_checks: List[Check] = [] if args.skip_smoke else [
        Check("auth-openapi", "http://localhost:8000/openapi.json", "application", "http", expected_status=200),
        Check("feed-openapi", "http://localhost:8001/openapi.json", "application", "http", expected_status=200),
        Check("content-analysis-openapi", "http://localhost:8002/openapi.json", "application", "http", expected_status=200),
        Check("research-openapi", "http://localhost:8003/openapi.json", "application", "http", expected_status=200),
        Check("osint-openapi", "http://localhost:8004/openapi.json", "application", "http", expected_status=200),
        Check("notification-openapi", "http://localhost:8005/openapi.json", "application", "http", expected_status=200),
        Check("search-openapi", "http://localhost:8006/openapi.json", "application", "http", expected_status=200),
        Check("analytics-openapi", "http://localhost:8007/openapi.json", "application", "http", expected_status=200),
    ]

    results = run_checks(health_checks + smoke_checks)
    summary = summarise(results)
    overall = overall_status(summary)

    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[health-report] {timestamp} overall={overall} totals={summary}")
    print_table(results)

    report_payload = {
        "timestamp": timestamp,
        "overall_status": overall,
        "summary": summary,
        "results": [asdict(result) for result in results],
    }

    if args.output:
        ensure_directory(args.output)
        args.output.write_text(json.dumps(report_payload, indent=2))

    # Exit code: 0 if all pass, 1 if warn, 2 if fail
    if summary["fail"] > 0:
        return 2
    if summary["warn"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
