#!/usr/bin/env python3
"""
RabbitMQ event-flow smoke verification for News MCP.

Checks that required queues and bindings exist, and that the core routing keys
deliver messages through the `news.events` exchange.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests
from requests import RequestException


EXCHANGE_NAME = "news.events"
DEFAULT_HTTP_PORT = 15672

EXPECTED_BINDINGS: Dict[str, List[str]] = {
    "content-analysis.articles": ["article.created"],
    "search.articles": ["article.created", "article.updated"],
    "research.analysis": ["analysis.completed"],
    "osint.intelligence": ["analysis.completed", "research.completed"],
    "notification.alerts": ["alert.triggered"],
    "analytics.all": ["#"],
}


@dataclass
class CheckResult:
    name: str
    status: str  # pass | warn | fail
    message: Optional[str] = None
    detail: Optional[Dict[str, str]] = None

def check_queue_exists(session: requests.Session, base_url: str, vhost: str, queue: str) -> CheckResult:
    url = f"{base_url}/api/queues/{requests.utils.quote(vhost, safe='')}/{requests.utils.quote(queue, safe='')}"
    try:
        response = session.get(url, timeout=5)
    except RequestException as exc:
        return CheckResult(
            name=f"queue:{queue}",
            status="warn",
            message=f"HTTP error: {exc}",
        )
    if response.status_code == 200:
        return CheckResult(name=f"queue:{queue}", status="pass")
    if response.status_code == 404:
        return CheckResult(name=f"queue:{queue}", status="fail", message="Queue not found")
    return CheckResult(
        name=f"queue:{queue}",
        status="warn",
        message=f"Unexpected status {response.status_code}",
    )


def check_binding_exists(
    session: requests.Session, base_url: str, vhost: str, queue: str, routing_key: str
) -> CheckResult:
    url = (
        f"{base_url}/api/bindings/{requests.utils.quote(vhost, safe='')}"
        f"/e/{requests.utils.quote(EXCHANGE_NAME, safe='')}"
        f"/q/{requests.utils.quote(queue, safe='')}"
    )
    try:
        response = session.get(url, timeout=5)
    except RequestException as exc:
        return CheckResult(
            name=f"binding:{queue}:{routing_key}",
            status="warn",
            message=f"HTTP error: {exc}",
        )
    if response.status_code != 200:
        return CheckResult(
            name=f"binding:{queue}:{routing_key}",
            status="warn",
            message=f"Failed to fetch bindings (status {response.status_code})",
        )

    bindings = response.json()
    if any(b.get("routing_key") == routing_key for b in bindings):
        return CheckResult(name=f"binding:{queue}:{routing_key}", status="pass")

    return CheckResult(
        name=f"binding:{queue}:{routing_key}",
        status="fail",
        message="Binding missing",
    )


def declare_temp_queue(session: requests.Session, base_url: str, vhost: str) -> Tuple[CheckResult, Optional[str]]:
    queue_name = f"smoke.{uuid.uuid4().hex}"
    url = f"{base_url}/api/queues/{requests.utils.quote(vhost, safe='')}/{requests.utils.quote(queue_name, safe='')}"
    try:
        response = session.put(
            url,
            json={
                "auto_delete": True,
                "durable": False,
                "arguments": {},
            },
            timeout=5,
        )
    except RequestException as exc:
        return (
            CheckResult(
                name="queue:create",
                status="warn",
                message=f"HTTP error during queue create: {exc}",
            ),
            None,
        )
    if response.status_code not in (201, 204, 200):
        return (
            CheckResult(
                name="queue:create",
                status="fail",
                message=f"Failed to create temp queue (status {response.status_code})",
            ),
            None,
        )
    return CheckResult(name="queue:create", status="pass"), queue_name


def delete_queue(session: requests.Session, base_url: str, vhost: str, queue_name: str) -> None:
    url = f"{base_url}/api/queues/{requests.utils.quote(vhost, safe='')}/{requests.utils.quote(queue_name, safe='')}"
    session.delete(url, timeout=5)


def verify_routing_key(
    session: requests.Session,
    base_url: str,
    vhost: str,
    routing_key: str,
    payload: Dict[str, str],
) -> CheckResult:
    create_result, queue_name = declare_temp_queue(session, base_url, vhost)
    if queue_name is None:
        return CheckResult(
            name=f"routing:{routing_key}",
            status="fail",
            message=create_result.message,
        )

    try:
        bind_url = (
            f"{base_url}/api/bindings/{requests.utils.quote(vhost, safe='')}/e/"
            f"{requests.utils.quote(EXCHANGE_NAME, safe='')}/q/{requests.utils.quote(queue_name, safe='')}"
        )
        try:
            bind_resp = session.post(
                bind_url,
                json={"routing_key": routing_key},
                timeout=5,
            )
        except RequestException as exc:
            return CheckResult(
                name=f"routing:{routing_key}",
                status="warn",
                message=f"HTTP error during bind: {exc}",
            )
        if bind_resp.status_code not in (201, 204, 200):
            return CheckResult(
                name=f"routing:{routing_key}",
                status="fail",
                message=f"Failed to bind temp queue (status {bind_resp.status_code})",
            )

        publish_url = (
            f"{base_url}/api/exchanges/{requests.utils.quote(vhost, safe='')}/"
            f"{requests.utils.quote(EXCHANGE_NAME, safe='')}/publish"
        )
        try:
            publish_resp = session.post(
                publish_url,
                json={
                    "properties": {},
                    "routing_key": routing_key,
                    "payload": json.dumps(payload),
                    "payload_encoding": "string",
                },
                timeout=5,
            )
        except RequestException as exc:
            return CheckResult(
                name=f"routing:{routing_key}",
                status="warn",
                message=f"HTTP error during publish: {exc}",
            )
        if publish_resp.status_code != 200 or not publish_resp.json().get("routed", False):
            return CheckResult(
                name=f"routing:{routing_key}",
                status="fail",
                message="Publish failed or not routed",
            )

        get_url = (
            f"{base_url}/api/queues/{requests.utils.quote(vhost, safe='')}/"
            f"{requests.utils.quote(queue_name, safe='')}/get"
        )
        deadline = time.time() + 2.0
        while time.time() < deadline:
            try:
                get_resp = session.post(
                    get_url,
                    json={
                        "count": 1,
                        "ackmode": "ack_requeue_false",
                        "encoding": "auto",
                        "truncate": 50000,
                    },
                    timeout=5,
                )
            except RequestException as exc:
                return CheckResult(
                    name=f"routing:{routing_key}",
                    status="warn",
                    message=f"HTTP error during get: {exc}",
                )
            if get_resp.status_code == 200 and get_resp.json():
                return CheckResult(name=f"routing:{routing_key}", status="pass")
            time.sleep(0.1)

        return CheckResult(
            name=f"routing:{routing_key}",
            status="fail",
            message="No message received via exchange",
        )
    except Exception as exc:
        return CheckResult(
            name=f"routing:{routing_key}",
            status="fail",
            message=f"Routing verification error: {exc}",
        )
    finally:
        delete_queue(session, base_url, vhost, queue_name)


def summarise(results: List[CheckResult]) -> Dict[str, int]:
    summary = {"pass": 0, "warn": 0, "fail": 0}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1
    return summary


def overall_status(summary: Dict[str, int]) -> str:
    if summary["fail"] > 0:
        return "fail"
    if summary["warn"] > 0:
        return "warn"
    return "pass"


def build_payload(routing_key: str) -> Dict[str, str]:
    return {
        "event_type": routing_key,
        "event_id": f"smoke-{routing_key}",
        "source": "smoke-test",
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="RabbitMQ event-flow smoke check.")
    parser.add_argument("--output", type=str, help="Optional JSON output path")
    parser.add_argument("--host", default=os.getenv("RABBITMQ_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("RABBITMQ_PORT", "5672")))
    parser.add_argument("--http-port", type=int, default=int(os.getenv("RABBITMQ_HTTP_PORT", str(DEFAULT_HTTP_PORT))))
    parser.add_argument("--user", default=os.getenv("RABBITMQ_USER", "admin"))
    parser.add_argument("--password", default=os.getenv("RABBITMQ_PASS", "rabbit_secret_2024"))
    parser.add_argument("--vhost", default=os.getenv("RABBITMQ_VHOST", "news_mcp"))
    args = parser.parse_args(argv)

    base_http_url = f"http://{args.host}:{args.http_port}"
    session = requests.Session()
    session.auth = (args.user, args.password)

    results: List[CheckResult] = []

    overview_url = f"{base_http_url}/api/overview"
    try:
        session.get(overview_url, timeout=2)
    except RequestException as exc:
        warn_result = CheckResult(name="rabbitmq-connection", status="warn", message=f"HTTP access failed: {exc}")
        results.append(warn_result)
        summary = summarise(results)
        overall = overall_status(summary)
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "timestamp": timestamp,
            "overall_status": overall,
            "summary": summary,
            "checks": [asdict(result) for result in results],
            "exchange": EXCHANGE_NAME,
        }

        print(f"[rabbitmq-smoke] {timestamp} overall={overall} totals={summary}")
        print(f"  - connection: WARN ({warn_result.message})")

        if args.output:
            output_path = os.path.abspath(args.output)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            print(f"[rabbitmq-smoke] wrote {output_path}")

        return 0

    # Queue existence and binding checks
    for queue, routing_keys in EXPECTED_BINDINGS.items():
        results.append(check_queue_exists(session, base_http_url, args.vhost, queue))
        for routing_key in routing_keys:
            results.append(check_binding_exists(session, base_http_url, args.vhost, queue, routing_key))

    # Routing verification using ephemeral queues
    seen_routing_keys = sorted({rk for rks in EXPECTED_BINDINGS.values() for rk in rks})
    for routing_key in seen_routing_keys:
        payload = build_payload(routing_key)
        results.append(verify_routing_key(session, base_http_url, args.vhost, routing_key, payload))

    summary = summarise(results)
    overall = overall_status(summary)
    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "timestamp": timestamp,
        "overall_status": overall,
        "summary": summary,
        "checks": [asdict(result) for result in results],
        "exchange": EXCHANGE_NAME,
    }

    print(f"[rabbitmq-smoke] {timestamp} overall={overall} totals={summary}")
    for result in results:
        if result.status != "pass":
            extra = f" ({result.message})" if result.message else ""
            print(f"  - {result.name}: {result.status.upper()}{extra}")

    if args.output:
        output_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(f"[rabbitmq-smoke] wrote {output_path}")

    return 0 if overall != "fail" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
