"""
Webhook Notifier Service for analytics-service.

Sends burst alerts to n8n webhook for Twitter publishing.
"""

import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class WebhookNotifier:
    """
    Sends burst alerts to n8n webhook for Twitter publishing.
    """

    def __init__(
        self,
        webhook_url: str = None,
        timeout: float = 10.0
    ):
        """
        Initialize webhook notifier.

        Args:
            webhook_url: n8n webhook URL (defaults to internal n8n)
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url or "http://n8n:5678/webhook/burst-alert"
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def notify_burst(
        self,
        burst: Dict[str, Any],
        articles: List[Dict[str, Any]]
    ) -> bool:
        """
        Send burst alert to n8n webhook.

        Args:
            burst: Burst detection result
            articles: Related articles (top 5)

        Returns:
            True if notification sent successfully
        """
        payload = {
            "burst_detected": True,
            "entity": burst.get("entity"),
            "level": burst.get("level"),
            "spike_factor": burst.get("spike_factor"),
            "start_time": burst.get("start_time"),
            "end_time": burst.get("end_time"),
            "mention_count": burst.get("mention_count"),
            "articles": articles[:5],  # Top 5 relevant articles
            "timestamp": datetime.utcnow().isoformat(),
            "source": "analytics-service"
        }

        try:
            client = await self._get_client()
            response = await client.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            logger.info(
                "Burst alert sent to n8n",
                entity=burst.get("entity"),
                level=burst.get("level"),
                status_code=response.status_code
            )
            return True

        except httpx.TimeoutException:
            logger.error(
                "Webhook timeout",
                url=self.webhook_url,
                entity=burst.get("entity")
            )
            return False

        except httpx.HTTPStatusError as e:
            logger.error(
                "Webhook HTTP error",
                url=self.webhook_url,
                status_code=e.response.status_code,
                entity=burst.get("entity")
            )
            return False

        except Exception as e:
            logger.error(
                "Failed to send burst alert",
                error=str(e),
                url=self.webhook_url,
                entity=burst.get("entity")
            )
            return False

    async def notify_contrarian_alert(
        self,
        alert: Dict[str, Any]
    ) -> bool:
        """
        Send contrarian alert to n8n webhook.

        Args:
            alert: Contrarian alert data

        Returns:
            True if notification sent successfully
        """
        webhook_url = self.webhook_url.replace("burst-alert", "contrarian-alert")

        payload = {
            "contrarian_alert": True,
            "entity": alert.get("entity"),
            "alert_type": alert.get("alert_type"),
            "z_score": alert.get("z_score"),
            "current_sentiment": alert.get("current_sentiment"),
            "historical_mean": alert.get("historical_mean"),
            "message": alert.get("message"),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "analytics-service"
        }

        try:
            client = await self._get_client()
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            logger.info(
                "Contrarian alert sent to n8n",
                entity=alert.get("entity"),
                alert_type=alert.get("alert_type"),
                z_score=alert.get("z_score")
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to send contrarian alert",
                error=str(e),
                entity=alert.get("entity")
            )
            return False

    async def notify_momentum_turnaround(
        self,
        momentum: Dict[str, Any]
    ) -> bool:
        """
        Send momentum turnaround alert to n8n webhook.

        Args:
            momentum: Momentum result data

        Returns:
            True if notification sent successfully
        """
        webhook_url = self.webhook_url.replace("burst-alert", "momentum-alert")

        payload = {
            "momentum_alert": True,
            "entity": momentum.get("entity"),
            "signal": momentum.get("signal"),
            "momentum": momentum.get("momentum"),
            "current_sentiment": momentum.get("current_sentiment"),
            "trend_direction": momentum.get("trend_direction"),
            "confidence": momentum.get("confidence"),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "analytics-service"
        }

        try:
            client = await self._get_client()
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            logger.info(
                "Momentum alert sent to n8n",
                entity=momentum.get("entity"),
                signal=momentum.get("signal"),
                momentum=momentum.get("momentum")
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to send momentum alert",
                error=str(e),
                entity=momentum.get("entity")
            )
            return False


# Singleton instance
webhook_notifier = WebhookNotifier()
