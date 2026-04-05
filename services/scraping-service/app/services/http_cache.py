"""
HTTP Response Cache Service

Phase 6: Scale

Provides caching for scraped content with:
- TTL-based expiration
- LRU eviction policy
- Memory-efficient storage
- Cache statistics
"""
import logging
import hashlib
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cached response entry"""
    url: str
    content: str
    word_count: int
    method: str
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    last_hit_at: Optional[datetime] = None

    @property
    def size_bytes(self) -> int:
        """Approximate size in bytes"""
        return len(self.content.encode('utf-8')) if self.content else 0

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at


@dataclass
class CacheStats:
    """Cache statistics"""
    total_entries: int = 0
    total_size_bytes: int = 0
    total_hits: int = 0
    total_misses: int = 0
    hit_rate: float = 0.0
    oldest_entry_age_seconds: float = 0.0
    avg_entry_age_seconds: float = 0.0


class HTTPCache:
    """
    LRU cache for HTTP responses with TTL.

    Features:
    - TTL-based automatic expiration
    - LRU eviction when max size reached
    - Memory size limits
    - Domain-specific TTLs
    - Cache statistics
    """

    # Default TTLs by content type
    DEFAULT_TTL_SECONDS = 3600  # 1 hour
    NEWS_TTL_SECONDS = 1800     # 30 minutes for news
    STATIC_TTL_SECONDS = 86400  # 24 hours for static content

    def __init__(
        self,
        max_entries: int = 5000,
        max_size_mb: int = 500,
        default_ttl_seconds: int = DEFAULT_TTL_SECONDS
    ):
        self.max_entries = max_entries
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._current_size_bytes = 0
        self._total_hits = 0
        self._total_misses = 0
        self._lock = threading.Lock()

        # Domain-specific TTL overrides
        self._domain_ttls: Dict[str, int] = {}

    def _url_to_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.sha256(url.encode()).hexdigest()[:32]

    def get(self, url: str) -> Optional[CacheEntry]:
        """
        Get cached content for URL.

        Returns None if not cached or expired.
        """
        with self._lock:
            key = self._url_to_key(url)
            entry = self._cache.get(key)

            if entry is None:
                self._total_misses += 1
                return None

            if entry.is_expired:
                # Remove expired entry
                self._remove_entry(key)
                self._total_misses += 1
                return None

            # Update LRU order
            self._cache.move_to_end(key)

            # Update hit stats
            entry.hit_count += 1
            entry.last_hit_at = datetime.utcnow()
            self._total_hits += 1

            logger.debug(f"Cache hit for {url} (hits: {entry.hit_count})")
            return entry

    def set(
        self,
        url: str,
        content: str,
        word_count: int,
        method: str,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None
    ) -> CacheEntry:
        """
        Cache content for URL.

        Args:
            url: Request URL
            content: Scraped content
            word_count: Word count
            method: Scraping method used
            status: Result status
            metadata: Additional metadata
            ttl_seconds: Custom TTL (uses default if not specified)

        Returns:
            Created cache entry
        """
        with self._lock:
            key = self._url_to_key(url)

            # Calculate TTL
            if ttl_seconds is None:
                ttl_seconds = self._get_ttl_for_url(url)

            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds > 0 else None

            entry = CacheEntry(
                url=url,
                content=content,
                word_count=word_count,
                method=method,
                status=status,
                metadata=metadata or {},
                created_at=now,
                expires_at=expires_at
            )

            # Check if replacing existing entry
            if key in self._cache:
                old_entry = self._cache[key]
                self._current_size_bytes -= old_entry.size_bytes

            # Add new entry
            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._current_size_bytes += entry.size_bytes

            # Evict if necessary
            self._evict_if_needed()

            logger.debug(f"Cached {url} ({entry.size_bytes} bytes, TTL: {ttl_seconds}s)")
            return entry

    def _get_ttl_for_url(self, url: str) -> int:
        """Get TTL for URL based on domain"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        # Check domain-specific TTL
        if domain in self._domain_ttls:
            return self._domain_ttls[domain]

        # Use default
        return self.default_ttl_seconds

    def set_domain_ttl(self, domain: str, ttl_seconds: int) -> None:
        """Set custom TTL for a domain"""
        with self._lock:
            self._domain_ttls[domain] = ttl_seconds

    def _evict_if_needed(self) -> None:
        """Evict entries if cache is over limits"""
        # Evict by entry count
        while len(self._cache) > self.max_entries:
            self._remove_oldest()

        # Evict by size
        while self._current_size_bytes > self.max_size_bytes and self._cache:
            self._remove_oldest()

    def _remove_oldest(self) -> None:
        """Remove oldest (least recently used) entry"""
        if not self._cache:
            return

        key, entry = self._cache.popitem(last=False)
        self._current_size_bytes -= entry.size_bytes
        logger.debug(f"Evicted {entry.url} from cache")

    def _remove_entry(self, key: str) -> None:
        """Remove specific entry"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size_bytes -= entry.size_bytes

    def invalidate(self, url: str) -> bool:
        """
        Invalidate cache for URL.

        Returns True if entry was removed.
        """
        with self._lock:
            key = self._url_to_key(url)
            if key in self._cache:
                self._remove_entry(key)
                logger.debug(f"Invalidated cache for {url}")
                return True
            return False

    def invalidate_domain(self, domain: str) -> int:
        """
        Invalidate all entries for a domain.

        Returns number of entries removed.
        """
        from urllib.parse import urlparse

        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                entry_domain = urlparse(entry.url).netloc
                if entry_domain == domain:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self._remove_entry(key)

            logger.info(f"Invalidated {len(keys_to_remove)} entries for domain {domain}")
            return len(keys_to_remove)

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns number of entries removed.
        """
        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                if entry.is_expired:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self._remove_entry(key)

            if keys_to_remove:
                logger.info(f"Cleaned up {len(keys_to_remove)} expired cache entries")

            return len(keys_to_remove)

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._total_hits + self._total_misses
            hit_rate = (
                self._total_hits / total_requests
                if total_requests > 0 else 0.0
            )

            now = datetime.utcnow()
            ages = []
            oldest_age = 0.0

            for entry in self._cache.values():
                age = (now - entry.created_at).total_seconds()
                ages.append(age)
                oldest_age = max(oldest_age, age)

            avg_age = sum(ages) / len(ages) if ages else 0.0

            return CacheStats(
                total_entries=len(self._cache),
                total_size_bytes=self._current_size_bytes,
                total_hits=self._total_hits,
                total_misses=self._total_misses,
                hit_rate=hit_rate,
                oldest_entry_age_seconds=oldest_age,
                avg_entry_age_seconds=avg_age
            )

    def clear(self) -> int:
        """Clear all cache entries"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._current_size_bytes = 0
            logger.info(f"Cleared {count} cache entries")
            return count


# Singleton instance
_http_cache: Optional[HTTPCache] = None


def get_http_cache() -> HTTPCache:
    """Get singleton HTTP cache"""
    global _http_cache
    if _http_cache is None:
        _http_cache = HTTPCache()
    return _http_cache
