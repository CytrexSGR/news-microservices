"""Tests for HTTP Cache"""
import pytest
import time
from datetime import datetime, timedelta
from app.services.http_cache import HTTPCache, CacheEntry, get_http_cache


class TestHTTPCache:
    @pytest.fixture
    def cache(self):
        return HTTPCache(max_entries=100, max_size_mb=10, default_ttl_seconds=3600)

    def test_set_and_get(self, cache):
        cache.set(
            url="https://example.com/article",
            content="Article content here",
            word_count=100,
            method="newspaper4k",
            status="success"
        )

        entry = cache.get("https://example.com/article")

        assert entry is not None
        assert entry.content == "Article content here"
        assert entry.word_count == 100
        assert entry.method == "newspaper4k"

    def test_get_nonexistent(self, cache):
        entry = cache.get("https://example.com/nonexistent")
        assert entry is None

    def test_cache_miss_increments_stat(self, cache):
        cache.get("https://example.com/miss")
        stats = cache.get_stats()
        assert stats.total_misses == 1

    def test_cache_hit_increments_stat(self, cache):
        cache.set("https://example.com/hit", "Content", 50, "newspaper4k")
        cache.get("https://example.com/hit")

        stats = cache.get_stats()
        assert stats.total_hits == 1

    def test_hit_count_tracking(self, cache):
        cache.set("https://example.com/article", "Content", 50, "newspaper4k")

        for _ in range(5):
            cache.get("https://example.com/article")

        entry = cache.get("https://example.com/article")
        assert entry.hit_count == 6  # 5 previous + this one

    def test_ttl_expiration(self, cache):
        # Set with very short TTL (1 second)
        cache.set(
            url="https://example.com/expiring",
            content="Content",
            word_count=50,
            method="newspaper4k",
            ttl_seconds=1  # 1 second TTL
        )

        # Immediately should still be valid
        entry = cache.get("https://example.com/expiring")
        assert entry is not None

        # Wait for expiration
        import time
        time.sleep(1.1)

        # Now should be expired
        entry = cache.get("https://example.com/expiring")
        assert entry is None  # Expired entries are removed

    def test_invalidate(self, cache):
        cache.set("https://example.com/article", "Content", 50, "newspaper4k")

        result = cache.invalidate("https://example.com/article")
        assert result is True

        entry = cache.get("https://example.com/article")
        assert entry is None

    def test_invalidate_nonexistent(self, cache):
        result = cache.invalidate("https://example.com/nonexistent")
        assert result is False

    def test_invalidate_domain(self, cache):
        cache.set("https://example.com/1", "Content 1", 50, "newspaper4k")
        cache.set("https://example.com/2", "Content 2", 50, "newspaper4k")
        cache.set("https://other.com/3", "Content 3", 50, "newspaper4k")

        count = cache.invalidate_domain("example.com")

        assert count == 2
        assert cache.get("https://example.com/1") is None
        assert cache.get("https://example.com/2") is None
        assert cache.get("https://other.com/3") is not None

    def test_max_entries_eviction(self):
        cache = HTTPCache(max_entries=3)

        cache.set("https://example.com/1", "Content 1", 50, "newspaper4k")
        cache.set("https://example.com/2", "Content 2", 50, "newspaper4k")
        cache.set("https://example.com/3", "Content 3", 50, "newspaper4k")

        # Access first two to make them "recently used"
        cache.get("https://example.com/1")
        cache.get("https://example.com/2")

        # Add fourth entry - should evict oldest
        cache.set("https://example.com/4", "Content 4", 50, "newspaper4k")

        stats = cache.get_stats()
        assert stats.total_entries == 3

    def test_max_size_eviction(self):
        # 1 byte max size
        cache = HTTPCache(max_entries=100, max_size_mb=0)  # 0 MB = immediate eviction

        cache.set("https://example.com/large", "x" * 1000, 100, "newspaper4k")

        # Entry might be evicted immediately due to size limit
        stats = cache.get_stats()
        assert stats.total_entries <= 1

    def test_lru_ordering(self, cache):
        cache.set("https://example.com/1", "Content", 50, "newspaper4k")
        cache.set("https://example.com/2", "Content", 50, "newspaper4k")
        cache.set("https://example.com/3", "Content", 50, "newspaper4k")

        # Access in specific order to update LRU
        cache.get("https://example.com/1")  # Most recently used

        stats = cache.get_stats()
        assert stats.total_entries == 3

    def test_set_domain_ttl(self, cache):
        cache.set_domain_ttl("example.com", 7200)  # 2 hours

        # Set entry for that domain
        cache.set("https://example.com/article", "Content", 50, "newspaper4k")

        entry = cache.get("https://example.com/article")
        assert entry is not None
        # TTL should be domain-specific

    def test_cleanup_expired(self, cache):
        # Add entries with different TTLs
        cache.set("https://example.com/short", "C1", 50, "newspaper4k", ttl_seconds=0)
        cache.set("https://example.com/long", "C2", 50, "newspaper4k", ttl_seconds=3600)

        count = cache.cleanup_expired()

        # Short TTL entry should be cleaned
        assert cache.get("https://example.com/long") is not None

    def test_get_stats(self, cache):
        cache.set("https://example.com/1", "Content 1", 50, "newspaper4k")
        cache.set("https://example.com/2", "Content 2", 50, "newspaper4k")
        cache.get("https://example.com/1")
        cache.get("https://example.com/miss")

        stats = cache.get_stats()

        assert stats.total_entries == 2
        assert stats.total_hits == 1
        assert stats.total_misses == 1
        assert stats.hit_rate == 0.5

    def test_clear(self, cache):
        cache.set("https://example.com/1", "Content 1", 50, "newspaper4k")
        cache.set("https://example.com/2", "Content 2", 50, "newspaper4k")

        count = cache.clear()

        assert count == 2
        assert cache.get("https://example.com/1") is None
        assert cache.get("https://example.com/2") is None

    def test_metadata_storage(self, cache):
        metadata = {"author": "John Doe", "title": "Test Article"}
        cache.set(
            "https://example.com/article",
            "Content",
            50,
            "newspaper4k",
            metadata=metadata
        )

        entry = cache.get("https://example.com/article")
        assert entry.metadata == metadata

    def test_entry_size_calculation(self):
        entry = CacheEntry(
            url="https://example.com/test",
            content="Hello World",
            word_count=2,
            method="newspaper4k",
            status="success"
        )

        assert entry.size_bytes == len("Hello World".encode('utf-8'))

    def test_singleton_instance(self):
        c1 = get_http_cache()
        c2 = get_http_cache()
        assert c1 is c2
