"""
Proxy Manager Service

Phase 6: Scale

Manages a pool of proxies with:
- Round-robin and weighted rotation strategies
- Health checking and circuit breaking
- Domain affinity (same proxy for same domain)
- Automatic failover
"""
import logging
import time
import random
import hashlib
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.proxy import (
    ProxyConfig,
    ProxyHealth,
    ProxyStatusEnum,
    ProxyPoolStats,
    ProxyRotationConfig,
    ProxyTypeEnum
)

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Manages proxy rotation with health checking and domain affinity.

    Features:
    - Multiple rotation strategies (round_robin, random, weighted)
    - Automatic health checking
    - Circuit breaking for unhealthy proxies
    - Domain affinity to maintain session consistency
    - Automatic failover to healthy proxies
    """

    def __init__(self, config: Optional[ProxyRotationConfig] = None):
        self.config = config or ProxyRotationConfig()
        self._proxies: Dict[str, ProxyConfig] = {}
        self._health: Dict[str, ProxyHealth] = {}
        self._domain_affinity: Dict[str, str] = {}  # domain -> proxy_id
        self._domain_affinity_expires: Dict[str, datetime] = {}
        self._rotation_index: int = 0
        self._last_health_check: Optional[datetime] = None

    def add_proxy(self, proxy: ProxyConfig) -> None:
        """Add a proxy to the pool"""
        self._proxies[proxy.id] = proxy
        self._health[proxy.id] = ProxyHealth(
            proxy_id=proxy.id,
            status=ProxyStatusEnum.UNKNOWN
        )
        logger.info(f"Added proxy: {proxy.id} ({proxy.url_masked})")

    def add_proxies_from_list(self, proxy_list: List[Dict[str, Any]]) -> int:
        """
        Add proxies from a list of dictionaries.

        Args:
            proxy_list: List of proxy configurations

        Returns:
            Number of proxies added
        """
        added = 0
        for idx, p in enumerate(proxy_list):
            try:
                proxy = ProxyConfig(
                    id=p.get("id", f"proxy_{idx}"),
                    host=p["host"],
                    port=p["port"],
                    proxy_type=ProxyTypeEnum(p.get("type", "http")),
                    username=p.get("username"),
                    password=p.get("password"),
                    provider=p.get("provider"),
                    region=p.get("region"),
                    is_residential=p.get("is_residential", False)
                )
                self.add_proxy(proxy)
                added += 1
            except Exception as e:
                logger.warning(f"Failed to add proxy {idx}: {e}")

        return added

    def remove_proxy(self, proxy_id: str) -> bool:
        """Remove a proxy from the pool"""
        if proxy_id in self._proxies:
            del self._proxies[proxy_id]
            del self._health[proxy_id]
            # Clean up domain affinities
            for domain, pid in list(self._domain_affinity.items()):
                if pid == proxy_id:
                    del self._domain_affinity[domain]
                    if domain in self._domain_affinity_expires:
                        del self._domain_affinity_expires[domain]
            logger.info(f"Removed proxy: {proxy_id}")
            return True
        return False

    def get_proxy_for_domain(self, domain: str) -> Optional[ProxyConfig]:
        """
        Get a proxy for the given domain.

        If domain affinity is enabled and a proxy is already assigned,
        returns the same proxy. Otherwise, selects a new proxy.

        Args:
            domain: Target domain

        Returns:
            ProxyConfig or None if no healthy proxies available
        """
        if not self.config.enabled or not self._proxies:
            return None

        # Check if domain is excluded
        if domain in self.config.excluded_domains:
            return None

        # Check domain affinity
        if self.config.domain_affinity:
            if domain in self._domain_affinity:
                proxy_id = self._domain_affinity[domain]
                expires = self._domain_affinity_expires.get(domain)

                # Check if affinity is still valid
                if expires and expires > datetime.utcnow():
                    proxy = self._proxies.get(proxy_id)
                    if proxy and self._is_proxy_usable(proxy_id):
                        return proxy

                # Affinity expired or proxy unhealthy
                del self._domain_affinity[domain]
                if domain in self._domain_affinity_expires:
                    del self._domain_affinity_expires[domain]

        # Select a new proxy
        proxy = self._select_proxy()
        if proxy and self.config.domain_affinity:
            # Establish domain affinity
            self._domain_affinity[domain] = proxy.id
            self._domain_affinity_expires[domain] = datetime.utcnow() + timedelta(
                seconds=self.config.domain_affinity_ttl_seconds
            )

        return proxy

    def _select_proxy(self) -> Optional[ProxyConfig]:
        """Select a proxy based on rotation strategy"""
        healthy_proxies = self._get_healthy_proxies()
        if not healthy_proxies:
            # Try degraded proxies if no healthy ones
            healthy_proxies = self._get_degraded_proxies()
            if not healthy_proxies:
                logger.warning("No usable proxies available")
                return None

        if self.config.strategy == "random":
            return random.choice(healthy_proxies)

        elif self.config.strategy == "weighted":
            # Weight by success rate
            weights = []
            for proxy in healthy_proxies:
                health = self._health.get(proxy.id)
                if health and health.total_requests > 0:
                    weights.append(health.success_rate + 0.1)  # Add small base weight
                else:
                    weights.append(0.5)  # Default weight for unknown

            return random.choices(healthy_proxies, weights=weights, k=1)[0]

        else:  # round_robin (default)
            proxy = healthy_proxies[self._rotation_index % len(healthy_proxies)]
            self._rotation_index += 1
            return proxy

    def _is_proxy_usable(self, proxy_id: str) -> bool:
        """Check if proxy is usable (healthy or degraded)"""
        health = self._health.get(proxy_id)
        if not health:
            return False
        return health.status in (ProxyStatusEnum.HEALTHY, ProxyStatusEnum.DEGRADED, ProxyStatusEnum.UNKNOWN)

    def _get_healthy_proxies(self) -> List[ProxyConfig]:
        """Get list of healthy proxies"""
        return [
            proxy for proxy_id, proxy in self._proxies.items()
            if self._health.get(proxy_id, ProxyHealth(proxy_id=proxy_id)).status == ProxyStatusEnum.HEALTHY
            or self._health.get(proxy_id, ProxyHealth(proxy_id=proxy_id)).status == ProxyStatusEnum.UNKNOWN
        ]

    def _get_degraded_proxies(self) -> List[ProxyConfig]:
        """Get list of degraded proxies"""
        return [
            proxy for proxy_id, proxy in self._proxies.items()
            if self._health.get(proxy_id, ProxyHealth(proxy_id=proxy_id)).status == ProxyStatusEnum.DEGRADED
        ]

    def record_success(
        self,
        proxy_id: str,
        response_time_ms: float
    ) -> None:
        """Record a successful request through a proxy"""
        health = self._health.get(proxy_id)
        if not health:
            return

        health.total_requests += 1
        health.successful_requests += 1
        health.consecutive_failures = 0
        health.last_success_at = datetime.utcnow()
        health.last_response_time_ms = response_time_ms

        # Update average response time
        if health.avg_response_time_ms == 0:
            health.avg_response_time_ms = response_time_ms
        else:
            # Exponential moving average
            health.avg_response_time_ms = (
                health.avg_response_time_ms * 0.8 + response_time_ms * 0.2
            )

        # Update status
        health.status = ProxyStatusEnum.HEALTHY

    def record_failure(
        self,
        proxy_id: str,
        error: Optional[str] = None
    ) -> None:
        """Record a failed request through a proxy"""
        health = self._health.get(proxy_id)
        if not health:
            return

        health.total_requests += 1
        health.failed_requests += 1
        health.consecutive_failures += 1
        health.last_failure_at = datetime.utcnow()
        health.last_error = error

        # Check if circuit should break
        if health.consecutive_failures >= self.config.max_consecutive_failures:
            health.status = ProxyStatusEnum.UNHEALTHY
            logger.warning(
                f"Proxy {proxy_id} marked unhealthy after "
                f"{health.consecutive_failures} consecutive failures"
            )
        elif health.success_rate < 0.5 and health.total_requests >= 10:
            health.status = ProxyStatusEnum.DEGRADED

    def get_health(self, proxy_id: str) -> Optional[ProxyHealth]:
        """Get health status for a proxy"""
        return self._health.get(proxy_id)

    def get_all_health(self) -> Dict[str, ProxyHealth]:
        """Get health status for all proxies"""
        return dict(self._health)

    def get_stats(self) -> ProxyPoolStats:
        """Get pool statistics"""
        stats = ProxyPoolStats(total_proxies=len(self._proxies))

        by_provider: Dict[str, int] = defaultdict(int)
        by_region: Dict[str, int] = defaultdict(int)

        for proxy_id, proxy in self._proxies.items():
            health = self._health.get(proxy_id, ProxyHealth(proxy_id=proxy_id))

            # Count by status
            if health.status == ProxyStatusEnum.HEALTHY:
                stats.healthy_proxies += 1
            elif health.status == ProxyStatusEnum.DEGRADED:
                stats.degraded_proxies += 1
            elif health.status == ProxyStatusEnum.UNHEALTHY:
                stats.unhealthy_proxies += 1
            else:
                stats.unknown_proxies += 1

            # Aggregate metrics
            stats.total_requests += health.total_requests
            stats.total_success += health.successful_requests
            stats.total_failures += health.failed_requests

            # Count by provider/region
            if proxy.provider:
                by_provider[proxy.provider] += 1
            if proxy.region:
                by_region[proxy.region] += 1

        stats.by_provider = dict(by_provider)
        stats.by_region = dict(by_region)

        # Calculate overall success rate
        if stats.total_requests > 0:
            stats.overall_success_rate = stats.total_success / stats.total_requests

        return stats

    def reset_unhealthy_proxies(self) -> int:
        """
        Reset unhealthy proxies to unknown status for retry.

        Called periodically to allow recovery.

        Returns:
            Number of proxies reset
        """
        count = 0
        for proxy_id, health in self._health.items():
            if health.status == ProxyStatusEnum.UNHEALTHY:
                # Check if recovery timeout has passed
                if health.last_failure_at:
                    recovery_time = health.last_failure_at + timedelta(
                        seconds=self.config.recovery_timeout_seconds
                    )
                    if datetime.utcnow() >= recovery_time:
                        health.status = ProxyStatusEnum.UNKNOWN
                        health.consecutive_failures = 0
                        count += 1
                        logger.info(f"Reset proxy {proxy_id} for recovery")

        return count

    def clear_domain_affinity(self, domain: Optional[str] = None) -> int:
        """
        Clear domain affinity cache.

        Args:
            domain: Specific domain to clear, or None for all

        Returns:
            Number of entries cleared
        """
        if domain:
            if domain in self._domain_affinity:
                del self._domain_affinity[domain]
                if domain in self._domain_affinity_expires:
                    del self._domain_affinity_expires[domain]
                return 1
            return 0
        else:
            count = len(self._domain_affinity)
            self._domain_affinity.clear()
            self._domain_affinity_expires.clear()
            return count


# Singleton instance
_proxy_manager: Optional[ProxyManager] = None


def get_proxy_manager() -> ProxyManager:
    """Get singleton proxy manager"""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager
