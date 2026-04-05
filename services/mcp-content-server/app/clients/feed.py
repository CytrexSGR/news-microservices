"""Feed service client for MCP Content Server."""

import logging
from typing import Any, Dict, List, Optional

from ..config import settings
from .base import BaseClient

logger = logging.getLogger(__name__)


class FeedClient(BaseClient):
    """Client for feed-service (Port 8101)."""

    def __init__(self):
        super().__init__(
            service_name="feed-service",
            base_url=settings.feed_service_url,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )

    # =========================================================================
    # Feed Management
    # =========================================================================

    async def list_feeds(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        List all RSS feeds.

        Args:
            skip: Number of feeds to skip
            limit: Maximum feeds to return
            is_active: Filter by active status
        """
        params = {"skip": skip, "limit": limit}
        if is_active is not None:
            params["is_active"] = is_active

        return await self.request("GET", "/api/v1/feeds", params=params)

    async def get_feed(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Get feed by ID."""
        return await self.request("GET", f"/api/v1/feeds/{feed_id}")

    async def create_feed(
        self,
        name: str,
        url: str,
        category: Optional[str] = None,
        is_active: bool = True,
    ) -> Dict[str, Any]:
        """Create a new RSS feed."""
        payload = {
            "name": name,
            "url": url,
            "is_active": is_active,
        }
        if category:
            payload["category"] = category

        return await self.request("POST", "/api/v1/feeds", json=payload)

    async def update_feed(
        self,
        feed_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update an existing feed."""
        payload = {}
        if name is not None:
            payload["name"] = name
        if url is not None:
            payload["url"] = url
        if is_active is not None:
            payload["is_active"] = is_active

        return await self.request("PUT", f"/api/v1/feeds/{feed_id}", json=payload)

    async def delete_feed(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Delete a feed."""
        return await self.request("DELETE", f"/api/v1/feeds/{feed_id}")

    async def fetch_feed(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Manually trigger feed fetch."""
        return await self.request("POST", f"/api/v1/feeds/{feed_id}/fetch")

    async def bulk_fetch_feeds(self) -> Dict[str, Any]:
        """Trigger fetch for all active feeds."""
        return await self.request("POST", "/api/v1/feeds/bulk-fetch")

    async def get_feed_stats(self) -> Dict[str, Any]:
        """Get feed statistics."""
        return await self.request("GET", "/api/v1/feeds/stats")

    async def get_feed_health(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Get feed health status."""
        return await self.request("GET", f"/api/v1/feeds/{feed_id}/health")

    async def reset_feed_error(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Reset feed error state."""
        return await self.request("POST", f"/api/v1/feeds/{feed_id}/reset-error")

    # =========================================================================
    # Feed Items
    # =========================================================================

    async def list_feed_items(
        self,
        feed_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List feed items.

        Args:
            feed_id: Filter by feed ID
            skip: Number to skip
            limit: Maximum to return
        """
        if feed_id:
            return await self.request(
                "GET",
                f"/api/v1/feeds/{feed_id}/items",
                params={"skip": skip, "limit": limit},
            )
        else:
            return await self.request(
                "GET",
                "/api/v1/feeds/items",
                params={"skip": skip, "limit": limit},
            )

    async def get_feed_item(
        self,
        item_id: int,
        feed_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get feed item by ID."""
        if feed_id:
            return await self.request(
                "GET",
                f"/api/v1/feeds/{feed_id}/items/{item_id}",
            )
        else:
            return await self.request("GET", f"/api/v1/feeds/items/{item_id}")

    # =========================================================================
    # Feed Quality
    # =========================================================================

    async def get_feed_quality(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Get feed quality assessment."""
        return await self.request("GET", f"/api/v1/feeds/{feed_id}/quality")

    async def get_feed_quality_v2(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Get enhanced feed quality (v2)."""
        return await self.request("GET", f"/api/v1/feeds/{feed_id}/quality-v2")

    async def get_quality_overview(self) -> Dict[str, Any]:
        """Get quality overview for all feeds."""
        return await self.request("GET", "/api/v1/feeds/quality-v2/overview")

    async def assess_feed(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Trigger feed quality assessment."""
        return await self.request("POST", f"/api/v1/feeds/{feed_id}/assess")

    async def pre_assess_feed(
        self,
        url: str,
    ) -> Dict[str, Any]:
        """Pre-assess feed quality before adding."""
        return await self.request(
            "POST",
            "/api/v1/feeds/pre-assess",
            json={"url": url},
        )

    async def get_assessment_history(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Get feed assessment history."""
        return await self.request(
            "GET",
            f"/api/v1/feeds/{feed_id}/assessment-history",
        )

    # =========================================================================
    # Admiralty Codes
    # =========================================================================

    async def get_admiralty_status(self) -> Dict[str, Any]:
        """Get admiralty codes status."""
        return await self.request("GET", "/api/v1/admiralty-codes/status")

    async def get_admiralty_weights(self) -> Dict[str, Any]:
        """Get admiralty weights configuration."""
        return await self.request("GET", "/api/v1/admiralty-codes/weights")

    async def get_admiralty_thresholds(self) -> Dict[str, Any]:
        """Get admiralty thresholds."""
        return await self.request("GET", "/api/v1/admiralty-codes/thresholds")

    # =========================================================================
    # Scheduling
    # =========================================================================

    async def get_scheduling_stats(self) -> Dict[str, Any]:
        """Get feed scheduling statistics."""
        return await self.request("GET", "/api/v1/scheduling/stats")

    async def get_scheduling_timeline(self) -> Dict[str, Any]:
        """Get scheduling timeline."""
        return await self.request("GET", "/api/v1/scheduling/timeline")

    async def get_scheduling_distribution(self) -> Dict[str, Any]:
        """Get scheduling distribution."""
        return await self.request("GET", "/api/v1/scheduling/distribution")

    async def get_scheduling_conflicts(self) -> Dict[str, Any]:
        """Get scheduling conflicts."""
        return await self.request("GET", "/api/v1/scheduling/conflicts")

    async def optimize_scheduling(self) -> Dict[str, Any]:
        """Optimize feed scheduling."""
        return await self.request("POST", "/api/v1/scheduling/optimize")

    async def get_feed_schedule(
        self,
        feed_id: int,
    ) -> Dict[str, Any]:
        """Get feed schedule."""
        return await self.request(
            "GET",
            f"/api/v1/scheduling/feeds/{feed_id}/schedule",
        )
