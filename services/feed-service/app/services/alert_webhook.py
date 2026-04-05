# File: services/feed-service/app/services/alert_webhook.py
"""
Alert Webhook Service for HITL Review Notifications.

Epic 2.3 Task 2.3.6: n8n Webhook for Review Alerts

Sends notifications to n8n webhook when high-risk items (risk_score >= 0.7)
are added to the review queue. Designed for graceful degradation - failures
are logged but don't block the main review submission flow.

Usage:
    from app.services.alert_webhook import get_alert_webhook

    webhook = get_alert_webhook()
    if should_send_alert(risk_score):
        await webhook.send_high_risk_alert(
            item_id=item.id,
            risk_score=risk_score,
            risk_level="HIGH",
            flags=["ai_generated", "legal_language"],
            content_preview=content[:500]
        )
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# Risk threshold for sending alerts
HIGH_RISK_THRESHOLD = 0.7


def should_send_alert(risk_score: float) -> bool:
    """
    Determine if an alert should be sent based on risk score.

    Args:
        risk_score: The calculated risk score (0.0 - 1.0)

    Returns:
        True if risk_score >= 0.7 (HIGH risk threshold)
    """
    return risk_score >= HIGH_RISK_THRESHOLD


class AlertWebhook:
    """
    Webhook service for sending high-risk review alerts to n8n.

    Sends structured JSON payloads to configured webhook URL.
    Handles errors gracefully - failures are logged but don't
    raise exceptions to avoid blocking the main flow.

    Attributes:
        webhook_url: Target n8n webhook URL (None = disabled)
        timeout: HTTP request timeout in seconds

    Example:
        >>> webhook = AlertWebhook("http://n8n:5678/webhook/review-alert")
        >>> await webhook.send_high_risk_alert(
        ...     item_id="uuid-here",
        ...     risk_score=0.85,
        ...     risk_level="HIGH",
        ...     flags=["legal_language", "allegations"],
        ...     content_preview="Breaking news..."
        ... )
    """

    # Maximum length for content preview in payload
    MAX_CONTENT_PREVIEW_LENGTH = 500

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        """
        Initialize the AlertWebhook service.

        Args:
            webhook_url: n8n webhook URL. If None, alerts are disabled.
            timeout: HTTP request timeout in seconds (default: 10.0)
        """
        self.webhook_url = webhook_url
        self.timeout = timeout

    def _build_payload(
        self,
        item_id: str,
        risk_score: float,
        risk_level: str,
        flags: List[str],
        content_preview: str,
    ) -> dict:
        """
        Build the webhook payload.

        Args:
            item_id: UUID of the review item
            risk_score: Risk score (0.0 - 1.0)
            risk_level: Risk level string (LOW, MEDIUM, HIGH)
            flags: List of detected risk flags
            content_preview: Preview of the content (truncated)

        Returns:
            Dict payload for the webhook
        """
        # Truncate content preview if needed
        if len(content_preview) > self.MAX_CONTENT_PREVIEW_LENGTH:
            content_preview = content_preview[: self.MAX_CONTENT_PREVIEW_LENGTH]

        return {
            "alert_type": "high_risk_review_item",
            "item_id": item_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "flags": flags,
            "content_preview": content_preview,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "feed-service-review",
        }

    async def send_high_risk_alert(
        self,
        item_id: str,
        risk_score: float,
        risk_level: str,
        flags: List[str],
        content_preview: str,
    ) -> bool:
        """
        Send a high-risk item alert to the configured webhook.

        This method handles all errors gracefully - it logs failures
        but never raises exceptions to avoid blocking the main flow.

        Args:
            item_id: UUID of the review item
            risk_score: Risk score (0.0 - 1.0)
            risk_level: Risk level string (LOW, MEDIUM, HIGH)
            flags: List of detected risk flags
            content_preview: Preview of the content

        Returns:
            True if the alert was sent successfully, False otherwise
            (including when webhook is disabled)
        """
        # Skip if webhook is not configured
        if not self.webhook_url:
            logger.debug("Review alert webhook not configured, skipping notification")
            return False

        payload = self._build_payload(
            item_id=item_id,
            risk_score=risk_score,
            risk_level=risk_level,
            flags=flags,
            content_preview=content_preview,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                logger.info(
                    f"High-risk review alert sent: item_id={item_id}, "
                    f"risk_score={risk_score}, status_code={response.status_code}"
                )
                return True

        except httpx.TimeoutException:
            logger.warning(
                f"Review alert webhook timeout: url={self.webhook_url}, "
                f"item_id={item_id}"
            )
            return False

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Review alert webhook HTTP error: status={e.response.status_code}, "
                f"url={self.webhook_url}, item_id={item_id}"
            )
            return False

        except Exception as e:
            logger.error(
                f"Failed to send review alert: error={e}, "
                f"url={self.webhook_url}, item_id={item_id}"
            )
            return False


# Singleton instance (lazy initialization)
_alert_webhook: Optional[AlertWebhook] = None


def get_alert_webhook() -> AlertWebhook:
    """
    Get the singleton AlertWebhook instance.

    Uses settings from config for webhook URL and timeout.

    Returns:
        AlertWebhook instance configured from settings
    """
    global _alert_webhook
    if _alert_webhook is None:
        _alert_webhook = AlertWebhook(
            webhook_url=settings.N8N_REVIEW_WEBHOOK_URL,
            timeout=settings.N8N_WEBHOOK_TIMEOUT,
        )
    return _alert_webhook


def reset_alert_webhook() -> None:
    """Reset the singleton instance (useful for testing)."""
    global _alert_webhook
    _alert_webhook = None
