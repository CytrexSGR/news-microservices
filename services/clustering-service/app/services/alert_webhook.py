"""Webhook service for sending burst alerts to n8n.

Sends structured payloads to configured webhook URL for external
alerting via Telegram, Email, Slack, etc.
"""

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

import aiohttp
from prometheus_client import Counter, Histogram

from app.services.burst_detection import BurstSeverity

logger = logging.getLogger(__name__)


# Prometheus metrics
WEBHOOK_SENT = Counter(
    "clustering_webhook_sent_total",
    "Total webhook alerts sent",
    ["severity", "success"]
)

WEBHOOK_LATENCY = Histogram(
    "clustering_webhook_latency_seconds",
    "Webhook request latency",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)


@dataclass
class WebhookPayload:
    """Payload structure for burst alert webhooks.

    Designed for n8n webhook nodes to parse and route
    to appropriate notification channels.
    """
    cluster_id: str
    cluster_title: str
    severity: str
    velocity: int
    window_minutes: int
    top_entities: List[str]
    detected_at: str
    recommended_action: str
    dashboard_url: Optional[str] = None


class AlertWebhookService:
    """
    Service for sending burst alerts via webhook.

    Sends structured JSON payloads to n8n webhook for further
    processing and delivery to Telegram, Email, Slack, etc.

    Attributes:
        webhook_url: Target webhook URL (n8n webhook node)
        timeout: Request timeout in seconds

    Example:
        >>> service = AlertWebhookService("http://n8n:5678/webhook/burst")
        >>> await service.send_alert(
        ...     cluster_id=uuid4(),
        ...     cluster_title="Breaking News",
        ...     severity=BurstSeverity.CRITICAL,
        ...     velocity=25
        ... )
    """

    # Map severity to recommended action
    SEVERITY_ACTIONS = {
        BurstSeverity.LOW: "monitor",
        BurstSeverity.MEDIUM: "review_soon",
        BurstSeverity.HIGH: "review_now",
        BurstSeverity.CRITICAL: "immediate_review",
    }

    def __init__(
        self,
        webhook_url: str,
        timeout: int = 10,
        dashboard_base_url: Optional[str] = None,
    ):
        """
        Initialize webhook service.

        Args:
            webhook_url: Target webhook URL for alerts
            timeout: HTTP request timeout in seconds
            dashboard_base_url: Base URL for dashboard links
        """
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.dashboard_base_url = dashboard_base_url or "http://localhost:3000"

    def build_payload(
        self,
        cluster_id: UUID,
        cluster_title: str,
        severity: BurstSeverity,
        velocity: int,
        window_minutes: int = 5,
        top_entities: Optional[List[str]] = None,
    ) -> WebhookPayload:
        """
        Build webhook payload for burst alert.

        Args:
            cluster_id: UUID of the cluster
            cluster_title: Title of the cluster
            severity: Burst severity level
            velocity: Articles per window
            window_minutes: Detection window size
            top_entities: Top entity names in cluster

        Returns:
            WebhookPayload ready for sending
        """
        return WebhookPayload(
            cluster_id=str(cluster_id),
            cluster_title=cluster_title,
            severity=severity.value,
            velocity=velocity,
            window_minutes=window_minutes,
            top_entities=top_entities or [],
            detected_at=datetime.now(timezone.utc).isoformat(),
            recommended_action=self.SEVERITY_ACTIONS.get(severity, "monitor"),
            dashboard_url=f"{self.dashboard_base_url}/clusters/{cluster_id}",
        )

    async def send_alert(
        self,
        cluster_id: UUID,
        cluster_title: str,
        severity: BurstSeverity,
        velocity: int,
        window_minutes: int = 5,
        top_entities: Optional[List[str]] = None,
    ) -> bool:
        """
        Send burst alert via webhook.

        Builds payload and sends POST request to configured webhook.
        Tracks metrics for success/failure and latency.

        Args:
            cluster_id: UUID of the cluster
            cluster_title: Title of the cluster
            severity: Burst severity level
            velocity: Articles per window
            window_minutes: Detection window size
            top_entities: Top entity names

        Returns:
            True if webhook returned 2xx, False otherwise
        """
        payload = self.build_payload(
            cluster_id=cluster_id,
            cluster_title=cluster_title,
            severity=severity,
            velocity=velocity,
            window_minutes=window_minutes,
            top_entities=top_entities,
        )

        try:
            async with aiohttp.ClientSession() as session:
                with WEBHOOK_LATENCY.time():
                    async with session.post(
                        self.webhook_url,
                        json=asdict(payload),
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        success = 200 <= response.status < 300

                        WEBHOOK_SENT.labels(
                            severity=severity.value,
                            success=str(success).lower()
                        ).inc()

                        if success:
                            logger.info(
                                f"Webhook sent: cluster={cluster_id} "
                                f"severity={severity.value}"
                            )
                        else:
                            logger.warning(
                                f"Webhook failed: status={response.status} "
                                f"cluster={cluster_id}"
                            )

                        return success

        except aiohttp.ClientError as e:
            logger.error(f"Webhook request failed: {e}")
            WEBHOOK_SENT.labels(
                severity=severity.value,
                success="false"
            ).inc()
            return False

        except Exception as e:
            logger.error(f"Unexpected webhook error: {e}")
            WEBHOOK_SENT.labels(
                severity=severity.value,
                success="false"
            ).inc()
            return False
