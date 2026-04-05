#!/usr/bin/env python3
"""
Update documentation status blocks from reports/status.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = REPO_ROOT / "reports" / "status.json"

MARKER_START = "<!-- AUTO-GENERATED: STATUS -->"
MARKER_END = "<!-- END AUTO-GENERATED: STATUS -->"

TARGET_FILES: Tuple[Path, ...] = (
    REPO_ROOT / "docs" / "PROJECT_STATUS.md",
    REPO_ROOT / "docs" / "SERVICE_IMPLEMENTATION_STATUS.md",
    REPO_ROOT.parent / "userdocs" / "microservices-architecture" / "INDEX.md",
)


def load_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Status file not found: {path}")
    return json.loads(path.read_text())


def summarise_health(health: Dict[str, Any]) -> str:
    summary = health.get("summary", {})
    return f"pass:{summary.get('pass', 0)} warn:{summary.get('warn', 0)} fail:{summary.get('fail', 0)}"


def summarise_tests(tests: Dict[str, Any]) -> str:
    if "totals" in tests:
        totals = tests["totals"]
        return (
            f"{totals.get('tests', 0)} tests, "
            f"{totals.get('failures', 0)} failures, "
            f"{totals.get('errors', 0)} errors, "
            f"time {totals.get('time', 0.0):.2f}s"
        )
    if "suite" in tests:
        suite = tests["suite"]
        return (
            f"{suite.get('tests', 0)} tests, "
            f"{suite.get('failures', 0)} failures, "
            f"{suite.get('errors', 0)} errors, "
            f"time {suite.get('time', 0.0):.2f}s"
        )
    return "keine Testdaten"


def summarise_config(config: Dict[str, Any]) -> str:
    checks = config.get("checks", {})
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for item in checks.values():
        status = item.get("status", "warn")
        counts[status] = counts.get(status, 0) + 1
    return f"pass:{counts['pass']} warn:{counts['warn']} fail:{counts['fail']}"


def summarise_rabbitmq(rabbitmq: Dict[str, Any]) -> str:
    summary = rabbitmq.get("summary", {})
    return f"pass:{summary.get('pass', 0)} warn:{summary.get('warn', 0)} fail:{summary.get('fail', 0)}"


def build_table(status_payload: Dict[str, Any]) -> str:
    sources = status_payload.get("sources", {})
    rows: List[Tuple[str, str, str]] = []

    overall_status = status_payload.get("overall_status", "unknown")
    rows.append(("Overall", overall_status, "Aggregierte Bewertung"))

    if (health := sources.get("health")):
        rows.append(("Health", health.get("overall_status", "unknown"), summarise_health(health)))
    else:
        rows.append(("Health", "unbekannt", "keine Daten"))

    if (tests := sources.get("tests")):
        rows.append(("Tests (Smoke)", tests.get("status", "unknown"), summarise_tests(tests)))
    else:
        rows.append(("Tests (Smoke)", "unbekannt", "keine Daten"))

    if (config := sources.get("config")):
        rows.append(("Secrets/Config", config.get("overall_status", "unknown"), summarise_config(config)))
    else:
        rows.append(("Secrets/Config", "unbekannt", "keine Daten"))

    if (rabbit := sources.get("rabbitmq")):
        rows.append(("RabbitMQ", rabbit.get("overall_status", "unknown"), summarise_rabbitmq(rabbit)))
    else:
        rows.append(("RabbitMQ", "unbekannt", "keine Daten"))

    header = "| Quelle | Status | Details |"
    separator = "| --- | --- | --- |"
    body = [f"| {label} | {status} | {details} |" for label, status, details in rows]
    generated_at = status_payload.get("generated_at") or status_payload.get("timestamp") or ""

    lines = [header, separator, *body, "", f"_Aktualisiert: {generated_at}_"]
    return "\n".join(lines)


def replace_block(content: str, replacement: str) -> str:
    pattern = re.compile(
        rf"{re.escape(MARKER_START)}(.*?){re.escape(MARKER_END)}",
        re.DOTALL,
    )
    new_block = f"{MARKER_START}\n{replacement}\n{MARKER_END}"
    updated, count = pattern.subn(new_block, content)
    if count == 0:
        raise ValueError("Marker block not found in file.")
    return updated


def update_file(path: Path, table: str) -> bool:
    original = path.read_text()
    updated = replace_block(original, table)
    if updated != original:
        path.write_text(updated)
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Update documentation status blocks.")
    parser.add_argument("--status", type=Path, default=STATUS_FILE, help="Path to reports/status.json")
    args = parser.parse_args()

    try:
        payload = load_status(args.status)
    except FileNotFoundError as exc:
        print(f"[update-docs] {exc}", file=sys.stderr)
        return 1

    table = build_table(payload)
    touched = 0
    for target in TARGET_FILES:
        if not target.exists():
            print(f"[update-docs] Skipping missing file: {target}")
            continue
        try:
            changed = update_file(target, table)
            if changed:
                touched += 1
                print(f"[update-docs] Updated {target}")
            else:
                print(f"[update-docs] No changes needed for {target}")
        except ValueError as exc:
            print(f"[update-docs] {target}: {exc}", file=sys.stderr)

    if touched == 0:
        print("[update-docs] No files updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
