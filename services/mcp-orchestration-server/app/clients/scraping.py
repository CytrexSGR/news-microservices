"""Scraping service client for MCP Orchestration Server."""

import logging
from typing import Any, Dict, List, Optional

from ..config import settings
from .base import BaseClient

logger = logging.getLogger(__name__)


class ScrapingClient(BaseClient):
    """Client for scraping-service (Port 8115)."""

    def __init__(self):
        super().__init__(
            service_name="scraping-service",
            base_url=settings.scraping_service_url,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )

    # =========================================================================
    # Monitoring & Health
    # =========================================================================

    async def get_health(self) -> Dict[str, Any]:
        """Get scraping service health status."""
        return await self.request("GET", "/health")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics."""
        return await self.request("GET", "/api/v1/monitoring/metrics")

    async def get_rate_limit_stats(self, key: str) -> Dict[str, Any]:
        """Get rate limit statistics for a specific key."""
        return await self.request("GET", f"/api/v1/monitoring/rate-limits/{key}")

    async def get_active_jobs(self) -> Dict[str, Any]:
        """Get currently active scraping jobs."""
        return await self.request("GET", "/api/v1/monitoring/active-jobs")

    async def reset_stats(self) -> Dict[str, Any]:
        """Reset collected statistics."""
        return await self.request("POST", "/api/v1/monitoring/reset-stats")

    async def get_feed_failures(self, feed_id: str) -> Dict[str, Any]:
        """Get failure count for a specific feed."""
        return await self.request("GET", f"/api/v1/monitoring/failures/{feed_id}")

    # =========================================================================
    # Source Profiles
    # =========================================================================

    async def list_sources(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List source profiles with optional status filter."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return await self.request("GET", "/api/v1/sources/", params=params)

    async def get_source_statistics(self) -> Dict[str, Any]:
        """Get overall source registry statistics."""
        return await self.request("GET", "/api/v1/sources/statistics")

    async def lookup_source(self, url: str) -> Dict[str, Any]:
        """Lookup source profile for a URL."""
        return await self.request("GET", "/api/v1/sources/lookup", params={"url": url})

    async def get_scrape_config(self, url: str) -> Dict[str, Any]:
        """Get scraping configuration for a URL."""
        return await self.request("GET", "/api/v1/sources/config", params={"url": url})

    async def get_source_profile(self, domain: str) -> Dict[str, Any]:
        """Get source profile by domain."""
        return await self.request("GET", f"/api/v1/sources/{domain}")

    async def update_source_profile(
        self,
        domain: str,
        update: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update source profile settings."""
        return await self.request("PATCH", f"/api/v1/sources/{domain}", json=update)

    async def seed_known_sources(self) -> Dict[str, Any]:
        """Seed the registry with known German news sources."""
        return await self.request("POST", "/api/v1/sources/seed")

    async def clear_source_cache(self) -> Dict[str, Any]:
        """Clear the in-memory source profile cache."""
        return await self.request("DELETE", "/api/v1/sources/cache")

    # =========================================================================
    # Dead Letter Queue
    # =========================================================================

    async def get_dlq_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics."""
        return await self.request("GET", "/api/v1/dlq/stats")

    async def list_dlq_entries(
        self,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        failure_reason: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List DLQ entries with optional filters."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        if domain:
            params["domain"] = domain
        if failure_reason:
            params["failure_reason"] = failure_reason
        return await self.request("GET", "/api/v1/dlq/entries", params=params)

    async def get_pending_dlq_entries(
        self,
        domain: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get entries ready for retry."""
        params = {"limit": limit}
        if domain:
            params["domain"] = domain
        return await self.request("GET", "/api/v1/dlq/pending", params=params)

    async def get_dlq_entry(self, entry_id: int) -> Dict[str, Any]:
        """Get a specific DLQ entry."""
        return await self.request("GET", f"/api/v1/dlq/entries/{entry_id}")

    async def resolve_dlq_entry(
        self,
        entry_id: int,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark DLQ entry as resolved."""
        params = {}
        if notes:
            params["notes"] = notes
        return await self.request(
            "POST", f"/api/v1/dlq/entries/{entry_id}/resolve", params=params
        )

    async def mark_dlq_manual(
        self,
        entry_id: int,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark DLQ entry as requiring manual intervention."""
        params = {}
        if notes:
            params["notes"] = notes
        return await self.request(
            "POST", f"/api/v1/dlq/entries/{entry_id}/manual", params=params
        )

    async def delete_dlq_entry(self, entry_id: int) -> Dict[str, Any]:
        """Delete a DLQ entry."""
        return await self.request("DELETE", f"/api/v1/dlq/entries/{entry_id}")

    async def cleanup_dlq(self, days: int = 30) -> Dict[str, Any]:
        """Remove resolved/abandoned entries older than specified days."""
        return await self.request("POST", "/api/v1/dlq/cleanup", params={"days": days})

    # =========================================================================
    # HTTP Cache
    # =========================================================================

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get HTTP cache statistics."""
        return await self.request("GET", "/api/v1/cache/stats")

    async def invalidate_cache(
        self,
        url: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Invalidate cache entries by URL or domain."""
        json_data = {}
        if url:
            json_data["url"] = url
        if domain:
            json_data["domain"] = domain
        return await self.request("POST", "/api/v1/cache/invalidate", json=json_data)

    async def cleanup_cache(self) -> Dict[str, Any]:
        """Remove all expired cache entries."""
        return await self.request("POST", "/api/v1/cache/cleanup")

    async def clear_cache(self) -> Dict[str, Any]:
        """Clear entire cache."""
        return await self.request("POST", "/api/v1/cache/clear")

    async def set_domain_ttl(self, domain: str, ttl_seconds: int) -> Dict[str, Any]:
        """Set custom TTL for a domain."""
        return await self.request(
            "POST",
            "/api/v1/cache/domain-ttl",
            json={"domain": domain, "ttl_seconds": ttl_seconds},
        )

    # =========================================================================
    # Proxy Manager
    # =========================================================================

    async def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy pool statistics."""
        return await self.request("GET", "/api/v1/proxy/stats")

    async def list_proxies(self) -> Dict[str, Any]:
        """List all proxies in the pool."""
        return await self.request("GET", "/api/v1/proxy/list")

    async def add_proxy(
        self,
        proxy_id: str,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        proxy_type: str = "http",
    ) -> Dict[str, Any]:
        """Add a proxy to the pool."""
        json_data = {
            "id": proxy_id,
            "host": host,
            "port": port,
            "proxy_type": proxy_type,
        }
        if username:
            json_data["username"] = username
        if password:
            json_data["password"] = password
        return await self.request("POST", "/api/v1/proxy/add", json=json_data)

    async def remove_proxy(self, proxy_id: str) -> Dict[str, Any]:
        """Remove a proxy from the pool."""
        return await self.request("DELETE", f"/api/v1/proxy/{proxy_id}")

    async def get_proxy_health(self, proxy_id: str) -> Dict[str, Any]:
        """Get health information for a specific proxy."""
        return await self.request("GET", f"/api/v1/proxy/health/{proxy_id}")

    async def reset_unhealthy_proxies(self) -> Dict[str, Any]:
        """Reset unhealthy proxies for retry."""
        return await self.request("POST", "/api/v1/proxy/reset-unhealthy")

    async def clear_domain_affinity(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clear domain affinity mappings."""
        params = {}
        if domain:
            params["domain"] = domain
        return await self.request("POST", "/api/v1/proxy/clear-affinity", params=params)

    # =========================================================================
    # Priority Queue
    # =========================================================================

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get priority queue statistics."""
        return await self.request("GET", "/api/v1/queue/stats")

    async def enqueue_job(
        self,
        url: str,
        priority: str = "NORMAL",
        method: Optional[str] = None,
        max_retries: int = 3,
        delay_seconds: int = 0,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a job to the priority queue."""
        json_data = {
            "url": url,
            "priority": priority,
            "max_retries": max_retries,
            "delay_seconds": delay_seconds,
        }
        if method:
            json_data["method"] = method
        if callback_url:
            json_data["callback_url"] = callback_url
        if metadata:
            json_data["metadata"] = metadata
        return await self.request("POST", "/api/v1/queue/enqueue", json=json_data)

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a specific job."""
        return await self.request("GET", f"/api/v1/queue/job/{job_id}")

    async def cancel_queue_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a pending job."""
        return await self.request("DELETE", f"/api/v1/queue/job/{job_id}")

    async def list_pending_queue_jobs(self, limit: int = 100) -> Dict[str, Any]:
        """List pending jobs in the queue."""
        return await self.request("GET", "/api/v1/queue/pending", params={"limit": limit})

    async def clear_queue(self) -> Dict[str, Any]:
        """Clear all pending jobs from the queue."""
        return await self.request("POST", "/api/v1/queue/clear")

    # =========================================================================
    # Wikipedia
    # =========================================================================

    async def search_wikipedia(
        self,
        query: str,
        language: str = "de",
        limit: int = 10,
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search Wikipedia articles."""
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return await self.request(
            "POST",
            "/api/v1/wikipedia/search",
            json={"query": query, "language": language, "limit": limit},
            headers=headers if headers else None,
        )

    async def get_wikipedia_article(
        self,
        title: str,
        language: str = "de",
        include_infobox: bool = True,
        include_categories: bool = True,
        include_links: bool = True,
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get full Wikipedia article data."""
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return await self.request(
            "POST",
            "/api/v1/wikipedia/article",
            json={
                "title": title,
                "language": language,
                "include_infobox": include_infobox,
                "include_categories": include_categories,
                "include_links": include_links,
            },
            headers=headers if headers else None,
        )

    async def extract_wikipedia_relationships(
        self,
        title: str,
        language: str = "de",
        entity_type: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract relationship candidates from Wikipedia article."""
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        json_data = {"title": title, "language": language}
        if entity_type:
            json_data["entity_type"] = entity_type
        return await self.request(
            "POST",
            "/api/v1/wikipedia/relationships",
            json=json_data,
            headers=headers if headers else None,
        )

    # =========================================================================
    # Direct Scraping
    # =========================================================================

    async def direct_scrape(
        self,
        url: str,
        method: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Scrape a URL directly (synchronous, no queue).

        Args:
            url: The URL to scrape
            method: Scraping method (auto, newspaper4k, playwright, stealth)

        Returns:
            Scraped content with metadata
        """
        json_data = {"url": url}
        if method:
            json_data["method"] = method
        return await self.request("POST", "/api/v1/scrape", json=json_data)
