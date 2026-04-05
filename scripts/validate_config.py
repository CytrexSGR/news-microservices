#!/usr/bin/env python3
"""
Validate critical secrets and configuration before running the stack.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


PLACEHOLDER_PATTERNS = [
    re.compile(r"your[-_]?"),
    re.compile(r"example"),
    re.compile(r"changeme", re.IGNORECASE),
    re.compile(r"replace[-_]?me", re.IGNORECASE),
]

CRITICAL_KEYS = {
    "OPENAI_API_KEY": "Content Analysis LLM",
    "ANTHROPIC_API_KEY": "Anthropic LLM",
    "PERPLEXITY_API_KEY": "Research LLM",
    "SMTP_PASSWORD": "Notification SMTP password",
    "SMTP_USERNAME": "Notification SMTP username",
    "JWT_SECRET_KEY": "JWT symmetric secret",
    "RABBITMQ_DEFAULT_PASS": "RabbitMQ default password",
    "MINIO_ROOT_PASSWORD": "MinIO admin password",
}


def parse_env(path: Path) -> Dict[str, str]:
    """Parse a simple dotenv-style file."""
    values: Dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def looks_like_placeholder(value: str) -> bool:
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(value):
            return True
    return False


def validate(values: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """Validate critical keys and return per-key diagnostics."""
    diagnostics: Dict[str, Dict[str, str]] = {}
    for key, description in CRITICAL_KEYS.items():
        value = values.get(key)
        if not value:
            diagnostics[key] = {
                "status": "fail",
                "message": "Missing value",
                "description": description,
            }
        elif looks_like_placeholder(value):
            diagnostics[key] = {
                "status": "warn",
                "message": "Placeholder value detected",
                "description": description,
            }
        else:
            diagnostics[key] = {
                "status": "pass",
                "message": "Configured",
                "description": description,
            }
    return diagnostics


def overall_status(diagnostics: Dict[str, Dict[str, str]]) -> str:
    statuses = [item["status"] for item in diagnostics.values()]
    if any(status == "fail" for status in statuses):
        return "fail"
    if any(status == "warn" for status in statuses):
        return "warn"
    return "pass"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate required secrets in .env")
    parser.add_argument("--env", type=Path, default=Path(".env"), help="Path to .env file")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args(argv)

    values = parse_env(args.env)
    diagnostics = validate(values)
    status = overall_status(diagnostics)

    env_timestamp = None
    if args.env.exists():
        env_timestamp = datetime.fromtimestamp(
            args.env.resolve().stat().st_mtime,
            tz=timezone.utc,
        ).isoformat()

    payload = {
        "timestamp": env_timestamp,
        "overall_status": status,
        "checks": diagnostics,
        "env_path": str(args.env.resolve()) if args.env.exists() else str(args.env),
    }

    summary_counts = {"pass": 0, "warn": 0, "fail": 0}
    for result in diagnostics.values():
        summary_counts[result["status"]] += 1

    print(
        f"[config-validate] env={args.env} status={status} "
        f"pass={summary_counts['pass']} warn={summary_counts['warn']} fail={summary_counts['fail']}"
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2))
        print(f"[config-validate] wrote {args.output}")

    return 0 if status != "fail" else 1


if __name__ == "__main__":
    sys.exit(main())
