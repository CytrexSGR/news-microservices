#!/usr/bin/env python3
"""
Aggregate health, smoke, and test results into a single status artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from xml.etree import ElementTree


def load_json(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def parse_junit(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    """Parse JUnit XML into a compact summary."""
    if not path or not path.exists():
        return None

    try:
        tree = ElementTree.parse(path)
        root = tree.getroot()
    except ElementTree.ParseError:
        return None

    def attr_int(element: ElementTree.Element, name: str) -> int:
        value = element.attrib.get(name)
        return int(float(value)) if value is not None else 0

    if root.tag == "testsuites":
        totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
        suites = []
        for suite in root.findall("testsuite"):
            suite_summary = {
                "name": suite.attrib.get("name", ""),
                "tests": attr_int(suite, "tests"),
                "failures": attr_int(suite, "failures"),
                "errors": attr_int(suite, "errors"),
                "skipped": attr_int(suite, "skipped"),
                "time": float(suite.attrib.get("time", 0.0)),
            }
            suites.append(suite_summary)
            for key in ("tests", "failures", "errors", "skipped"):
                totals[key] += suite_summary[key]
            totals["time"] += suite_summary["time"]
        status = "pass" if totals["failures"] == 0 and totals["errors"] == 0 else "fail"
        return {"status": status, "totals": totals, "suites": suites}

    if root.tag == "testsuite":
        summary = {
            "name": root.attrib.get("name", ""),
            "tests": attr_int(root, "tests"),
            "failures": attr_int(root, "failures"),
            "errors": attr_int(root, "errors"),
            "skipped": attr_int(root, "skipped"),
            "time": float(root.attrib.get("time", 0.0)),
        }
        status = "pass" if summary["failures"] == 0 and summary["errors"] == 0 else "fail"
        return {"status": status, "suite": summary}

    return None


def combine(
    health: Optional[Dict[str, Any]],
    tests: Optional[Dict[str, Any]],
    config: Optional[Dict[str, Any]],
    rabbitmq: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    payload: Dict[str, Any] = {
        "generated_at": timestamp,
        "sources": {},
    }

    if health:
        payload["sources"]["health"] = health

    if tests:
        payload["sources"]["tests"] = tests

    if config:
        payload["sources"]["config"] = config

    if rabbitmq:
        payload["sources"]["rabbitmq"] = rabbitmq

    overall = "unknown"
    statuses = []
    if health:
        statuses.append(health.get("overall_status", "pass"))
    if tests:
        statuses.append(tests.get("status", "pass"))
    if config:
        statuses.append(config.get("overall_status", "pass"))
    if rabbitmq:
        statuses.append(rabbitmq.get("overall_status", "pass"))

    if statuses:
        if any(status == "fail" for status in statuses):
            overall = "fail"
        elif any(status == "warn" for status in statuses):
            overall = "warn"
        else:
            overall = "pass"

    payload["overall_status"] = overall
    return payload


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate health, smoke, and test reports.")
    parser.add_argument("--health", type=Path, help="Path to health_report JSON output")
    parser.add_argument("--tests", type=Path, help="Path to JUnit XML from pytest smoke run")
    parser.add_argument("--config", type=Path, help="Path to configuration validation JSON output")
    parser.add_argument("--rabbitmq", type=Path, help="Path to RabbitMQ smoke JSON output")
    parser.add_argument("--output", type=Path, required=True, help="Destination JSON file")
    parser.add_argument(
        "--enforce",
        choices=("none", "fail", "warn"),
        default="fail",
        help="Exit with non-zero status when overall status meets threshold. "
             "'fail' (default) exits on overall fail, 'warn' exits on warn or fail, "
             "'none' always exits zero.",
    )
    args = parser.parse_args(argv)

    health = load_json(args.health)
    junit_summary = parse_junit(args.tests)
    config = load_json(args.config)
    rabbitmq = load_json(args.rabbitmq)

    payload = combine(health, junit_summary, config, rabbitmq)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))

    overall = payload["overall_status"]
    print(f"[aggregate-status] wrote {args.output} overall={overall}")

    if args.enforce == "none":
        return 0
    if args.enforce == "fail" and overall == "fail":
        return 2
    if args.enforce == "warn" and overall in {"warn", "fail"}:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
