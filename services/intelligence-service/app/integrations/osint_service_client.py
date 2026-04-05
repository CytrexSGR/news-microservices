"""
OSINT Service Integration Client.

Handles communication with osint-service for intelligence data and threat monitoring.

Service: osint-service (8104)
Base URL: http://osint-service:8104
"""

import logging
from typing import Optional, Dict, Any
import httpx

from app.core.http_client import ResilientHttpClient, HttpClientFactory

logger = logging.getLogger(__name__)


class OSINTServiceClient:
    """
    Client for osint-service integration.

    Provides methods for:
    - Getting threat intelligence data
    - Retrieving indicators of compromise (IoCs)
    - Getting entity intelligence
    """

    def __init__(self, http_client: Optional[ResilientHttpClient] = None):
        """
        Initialize OSINT service client.

        Args:
            http_client: ResilientHttpClient instance (or None to use factory)
        """
        self.http_client = http_client or HttpClientFactory.get_client("osint-service")

    async def get_threat_intelligence(
        self,
        entity: str,
        entity_type: str = "organization",
    ) -> Dict[str, Any]:
        """
        Get threat intelligence for an entity.

        Args:
            entity: Entity name
            entity_type: Type of entity (organization, person, location, etc.)

        Returns:
            Threat intelligence data
        """
        try:
            path = "/api/v1/intelligence"
            params = {
                "entity": entity,
                "type": entity_type,
            }

            async with self.http_client as client:
                response = await client.get(path, params=params)
                data = response.json()
                logger.debug(f"Retrieved threat intelligence for {entity}")
                return data
        except Exception as e:
            logger.error(f"Failed to get threat intelligence for {entity}: {e}")
            raise

    async def get_indicators(
        self,
        indicator_type: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get indicators of compromise (IoCs).

        Args:
            indicator_type: Type of indicator (ip, domain, hash, etc.)
            severity: Severity level (high, medium, low)

        Returns:
            Indicators data
        """
        try:
            path = "/api/v1/indicators"
            params = {}
            if indicator_type:
                params["type"] = indicator_type
            if severity:
                params["severity"] = severity

            async with self.http_client as client:
                response = await client.get(path, params=params if params else None)
                data = response.json()
                logger.debug(f"Retrieved indicators (type={indicator_type})")
                return data
        except Exception as e:
            logger.error(f"Failed to get indicators: {e}")
            raise

    async def enrich_entity(self, entity: str) -> Dict[str, Any]:
        """
        Enrich entity with additional intelligence data.

        Args:
            entity: Entity name

        Returns:
            Enriched entity data
        """
        try:
            path = f"/api/v1/entities/{entity}/enrich"

            async with self.http_client as client:
                response = await client.get(path)
                data = response.json()
                logger.debug(f"Enriched entity: {entity}")
                return data
        except Exception as e:
            logger.error(f"Failed to enrich entity {entity}: {e}")
            raise

    async def get_client_stats(self) -> Dict[str, Any]:
        """Get circuit breaker stats for OSINT service client"""
        return self.http_client.get_stats()


# Singleton instance
_osint_service_client: Optional[OSINTServiceClient] = None


async def get_osint_service_client() -> OSINTServiceClient:
    """Get or create OSINT service client"""
    global _osint_service_client
    if _osint_service_client is None:
        _osint_service_client = OSINTServiceClient()
    return _osint_service_client
