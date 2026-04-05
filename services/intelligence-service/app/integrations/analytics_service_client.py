"""
Analytics Service Integration Client.

Handles communication with analytics-service for sending metrics and retrieving analytics data.

Service: analytics-service (8107)
Base URL: http://analytics-service:8107
"""

import logging
from typing import Optional, Dict, Any
import httpx

from app.core.http_client import ResilientHttpClient, HttpClientFactory

logger = logging.getLogger(__name__)


class AnalyticsServiceClient:
    """
    Client for analytics-service integration.

    Provides methods for:
    - Reporting events and metrics
    - Retrieving analytics data
    - Tracking cluster activity
    """

    def __init__(self, http_client: Optional[ResilientHttpClient] = None):
        """
        Initialize analytics service client.

        Args:
            http_client: ResilientHttpClient instance (or None to use factory)
        """
        self.http_client = http_client or HttpClientFactory.get_client("analytics-service")

    async def report_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Report an event to analytics service.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Response from analytics service
        """
        try:
            path = "/api/v1/events"
            payload = {
                "event_type": event_type,
                "data": event_data,
            }

            async with self.http_client as client:
                response = await client.post(path, json=payload)
                data = response.json()
                logger.debug(f"Reported event: {event_type}")
                return data
        except Exception as e:
            logger.error(f"Failed to report event {event_type}: {e}")
            raise

    async def report_cluster_activity(
        self,
        cluster_id: str,
        activity: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Report cluster activity.

        Args:
            cluster_id: Cluster ID
            activity: Activity details

        Returns:
            Response from analytics service
        """
        try:
            path = f"/api/v1/clusters/{cluster_id}/activity"

            async with self.http_client as client:
                response = await client.post(path, json=activity)
                data = response.json()
                logger.debug(f"Reported cluster activity: {cluster_id}")
                return data
        except Exception as e:
            logger.error(f"Failed to report cluster activity for {cluster_id}: {e}")
            raise

    async def get_metrics(
        self,
        metric_type: str,
        time_range: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get metrics from analytics service.

        Args:
            metric_type: Type of metric
            time_range: Time range in hours (if applicable)

        Returns:
            Metrics data
        """
        try:
            path = f"/api/v1/metrics/{metric_type}"
            params = {}
            if time_range:
                params["hours"] = time_range

            async with self.http_client as client:
                response = await client.get(path, params=params if params else None)
                data = response.json()
                logger.debug(f"Retrieved metrics: {metric_type}")
                return data
        except Exception as e:
            logger.error(f"Failed to get metrics {metric_type}: {e}")
            raise

    async def get_client_stats(self) -> Dict[str, Any]:
        """Get circuit breaker stats for analytics service client"""
        return self.http_client.get_stats()


# Singleton instance
_analytics_service_client: Optional[AnalyticsServiceClient] = None


async def get_analytics_service_client() -> AnalyticsServiceClient:
    """Get or create analytics service client"""
    global _analytics_service_client
    if _analytics_service_client is None:
        _analytics_service_client = AnalyticsServiceClient()
    return _analytics_service_client
