"""HTTP client for Notification service."""

import logging
from typing import Dict, Any, List, Optional

from ..config import settings
from .base import BaseClient, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class NotificationClient(BaseClient):
    """Client for Notification service (Port 8105)."""

    def __init__(self):
        super().__init__(
            name="notification-service",
            base_url=settings.notification_service_url,
            timeout=30.0,
        )

    # =========================================================================
    # Send Notifications
    # =========================================================================

    async def send_notification(
        self,
        user_id: int,
        template_id: str,
        channel: str = "email",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to user.

        Args:
            user_id: Target user ID
            template_id: Notification template ID
            channel: Delivery channel (email, webhook, push)
            data: Template data

        Returns:
            Notification send result with notification_id
        """
        response = await self.post(
            "/api/v1/notifications/send",
            json={
                "user_id": user_id,
                "template_id": template_id,
                "channel": channel,
                "data": data or {},
            }
        )
        response.raise_for_status()
        return response.json()

    async def send_adhoc_notification(
        self,
        user_id: int,
        subject: str,
        body: str,
        channel: str = "email",
    ) -> Dict[str, Any]:
        """
        Send ad-hoc notification without template.

        Args:
            user_id: Target user ID
            subject: Notification subject
            body: Notification body
            channel: Delivery channel

        Returns:
            Notification send result
        """
        response = await self.post(
            "/api/v1/notifications/send/adhoc",
            json={
                "user_id": user_id,
                "subject": subject,
                "body": body,
                "channel": channel,
            }
        )
        response.raise_for_status()
        return response.json()

    async def test_notification(
        self,
        template_id: str,
        channel: str = "email",
    ) -> Dict[str, Any]:
        """
        Send test notification.

        Args:
            template_id: Template to test
            channel: Delivery channel

        Returns:
            Test result
        """
        response = await self.post(
            "/api/v1/notifications/test",
            json={
                "template_id": template_id,
                "channel": channel,
            }
        )
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # History
    # =========================================================================

    async def get_notification_history(
        self,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get notification history.

        Args:
            user_id: Optional user filter
            limit: Max results
            offset: Result offset

        Returns:
            Notification history
        """
        params = {"limit": limit, "offset": offset}
        if user_id:
            params["user_id"] = user_id

        response = await self.get("/api/v1/notifications/history", params=params)
        response.raise_for_status()
        return response.json()

    async def get_notification(self, notification_id: str) -> Dict[str, Any]:
        """
        Get notification details.

        Args:
            notification_id: Notification ID

        Returns:
            Notification details with status
        """
        response = await self.get(f"/api/v1/notifications/{notification_id}")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Templates
    # =========================================================================

    async def list_templates(self) -> Dict[str, Any]:
        """List notification templates."""
        response = await self.get("/api/v1/notifications/templates")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Preferences
    # =========================================================================

    async def get_preferences(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get notification preferences.

        Args:
            user_id: User ID (optional, uses auth if not provided)

        Returns:
            User notification preferences
        """
        params = {}
        if user_id:
            params["user_id"] = user_id

        response = await self.get("/api/v1/notifications/preferences", params=params)
        response.raise_for_status()
        return response.json()

    async def update_preferences(
        self,
        preferences: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update notification preferences.

        Args:
            preferences: Preference settings
            user_id: User ID (optional)

        Returns:
            Updated preferences
        """
        json_body = {"preferences": preferences}
        if user_id:
            json_body["user_id"] = user_id

        response = await self.post("/api/v1/notifications/preferences", json=json_body)
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Admin Operations
    # =========================================================================

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get notification queue statistics."""
        response = await self.get("/api/v1/admin/queue/stats")
        response.raise_for_status()
        return response.json()

    async def list_dlq(self, limit: int = 50) -> Dict[str, Any]:
        """
        List dead letter queue.

        Args:
            limit: Max results

        Returns:
            Failed notifications in DLQ
        """
        response = await self.get(
            "/api/v1/admin/dlq/list",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    async def retry_dlq_notification(self, notification_id: str) -> Dict[str, Any]:
        """
        Retry notification from DLQ.

        Args:
            notification_id: Notification ID to retry

        Returns:
            Retry result
        """
        response = await self.post(f"/api/v1/admin/dlq/retry/{notification_id}")
        response.raise_for_status()
        return response.json()

    async def get_user_rate_limit(self, user_id: int) -> Dict[str, Any]:
        """
        Get user rate limit status.

        Args:
            user_id: User ID

        Returns:
            Rate limit status
        """
        response = await self.get(f"/api/v1/admin/rate-limit/user/{user_id}")
        response.raise_for_status()
        return response.json()

    async def reset_user_rate_limit(self, user_id: int) -> Dict[str, Any]:
        """
        Reset user rate limit.

        Args:
            user_id: User ID

        Returns:
            Reset result
        """
        response = await self.post(f"/api/v1/admin/rate-limit/user/{user_id}/reset")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Health
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check notification service health."""
        response = await self.get("/health")
        response.raise_for_status()
        return response.json()

    async def health_detailed(self) -> Dict[str, Any]:
        """Get detailed health status."""
        response = await self.get("/health/detailed")
        response.raise_for_status()
        return response.json()
