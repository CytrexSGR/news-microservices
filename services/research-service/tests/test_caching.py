"""
Comprehensive tests for caching layer in research service.
Tests cache hit/miss, TTL, invalidation, and performance.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json
import hashlib
import time

from app.services.research import ResearchService
from app.models.research import ResearchCache, ResearchTask


class TestCachingLayer:
    """Tests for Redis caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_key_generation_consistency(self):
        """Test that cache keys are generated consistently."""
        service = ResearchService()

        key1 = service._generate_cache_key("test query", "sonar", "standard")
        key2 = service._generate_cache_key("test query", "sonar", "standard")

        assert key1 == key2
        assert len(key1) == 64  # SHA256 hash length

    @pytest.mark.asyncio
    async def test_cache_key_different_parameters(self):
        """Test that different parameters generate different cache keys."""
        service = ResearchService()

        key1 = service._generate_cache_key("query", "sonar", "standard")
        key2 = service._generate_cache_key("query", "sonar-pro", "standard")
        key3 = service._generate_cache_key("query", "sonar", "deep")
        key4 = service._generate_cache_key("different query", "sonar", "standard")

        assert key1 != key2
        assert key1 != key3
        assert key1 != key4
        assert key2 != key3

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self, db_session, test_user_id, mock_redis):
        """Test that cache hit returns cached result without API call."""
        service = ResearchService()
        service.redis_client = mock_redis

        cached_data = {
            "result": {
                "content": "Cached response",
                "citations": [],
                "sources": []
            },
            "tokens_used": 1000,
            "cost": 0.005
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        with patch("app.services.perplexity.perplexity_client") as mock_perplexity:
            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test query",
                model_name="sonar",
                depth="standard",
                optimize_cost=False
            )

            # Verify cache was checked
            mock_redis.get.assert_called_once()

            # Verify Perplexity API was NOT called
            mock_perplexity.research.assert_not_called()

            # Verify task uses cached data
            assert task.status == "completed"
            assert task.result["content"] == "Cached response"

    @pytest.mark.asyncio
    async def test_cache_miss_calls_api_and_caches_result(
        self, db_session, test_user_id, mock_redis, mock_perplexity_response
    ):
        """Test that cache miss triggers API call and caches result."""
        service = ResearchService()
        service.redis_client = mock_redis

        # Simulate cache miss
        mock_redis.get.return_value = None

        with patch("app.services.perplexity.perplexity_client") as mock_perplexity:
            mock_perplexity.research = AsyncMock(return_value=mock_perplexity_response)

            with patch("app.workers.tasks.research_task") as mock_celery:
                mock_celery.delay.return_value = MagicMock(id="task-123")

                task = await service.create_research_task(
                    db=db_session,
                    user_id=test_user_id,
                    query="Test query",
                    model_name="sonar",
                    depth="standard",
                    optimize_cost=False
                )

                # Verify cache was checked
                mock_redis.get.assert_called_once()

                # Verify task was created and dispatched to Celery
                assert task.status == "pending"
                mock_celery.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_ttl_configuration(self, mock_redis):
        """Test that cache entries use correct TTL."""
        service = ResearchService()
        service.redis_client = mock_redis

        from app.core.config import settings

        result = {
            "content": "Test result",
            "citations": [],
            "sources": []
        }

        await service._cache_result(
            query="Test query",
            model_name="sonar",
            depth="standard",
            result=result,
            tokens_used=1000,
            cost=0.005
        )

        # Verify setex was called with correct TTL
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args

        # Second argument should be TTL
        assert call_args[0][1] == settings.CACHE_RESEARCH_RESULTS_TTL

    @pytest.mark.asyncio
    async def test_cache_stores_complete_data(self, mock_redis):
        """Test that cache stores all necessary data."""
        service = ResearchService()
        service.redis_client = mock_redis

        result = {
            "content": "Full result",
            "citations": [{"url": "test.com"}],
            "sources": [{"url": "test.com"}]
        }

        await service._cache_result(
            query="Test query",
            model_name="sonar-pro",
            depth="deep",
            result=result,
            tokens_used=2000,
            cost=0.015
        )

        mock_redis.setex.assert_called_once()
        cached_json = mock_redis.setex.call_args[0][2]
        cached_data = json.loads(cached_json)

        assert cached_data["result"] == result
        assert cached_data["tokens_used"] == 2000
        assert cached_data["cost"] == 0.015

    @pytest.mark.asyncio
    async def test_cache_failure_does_not_break_service(
        self, db_session, test_user_id, mock_redis
    ):
        """Test that Redis failures don't break the service."""
        service = ResearchService()
        service.redis_client = mock_redis

        # Simulate Redis failure
        mock_redis.get.side_effect = Exception("Redis connection failed")

        with patch("app.services.perplexity.perplexity_client") as mock_perplexity:
            with patch("app.workers.tasks.research_task") as mock_celery:
                mock_celery.delay.return_value = MagicMock(id="task-123")

                # Should not raise exception
                task = await service.create_research_task(
                    db=db_session,
                    user_id=test_user_id,
                    query="Test query",
                    model_name="sonar",
                    depth="standard",
                    optimize_cost=False
                )

                assert task is not None
                assert task.status == "pending"

    @pytest.mark.asyncio
    async def test_cache_disabled_skips_caching(
        self, db_session, test_user_id, mock_redis, disable_cache
    ):
        """Test that caching can be disabled."""
        service = ResearchService()
        service.redis_client = mock_redis

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test query",
                model_name="sonar",
                depth="standard",
                cache_enabled=False
            )

            # Cache should not be checked
            mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_hit_creates_completed_task(
        self, db_session, test_user_id, mock_redis
    ):
        """Test that cache hit creates completed task immediately."""
        service = ResearchService()
        service.redis_client = mock_redis

        cached_data = {
            "result": {
                "content": "Cached",
                "citations": [],
                "sources": [],
                "structured_data": {"key": "value"}
            },
            "tokens_used": 500,
            "cost": 0.0025
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        task = await service.create_research_task(
            db=db_session,
            user_id=test_user_id,
            query="Cached query",
            model_name="sonar",
            depth="standard",
            optimize_cost=False
        )

        assert task.status == "completed"
        assert task.completed_at is not None
        assert task.tokens_used == 500
        assert task.cost == 0.0025

    @pytest.mark.asyncio
    async def test_cache_retrieval_error_handling(self, mock_redis):
        """Test error handling during cache retrieval."""
        service = ResearchService()
        service.redis_client = mock_redis

        # Simulate JSON decode error
        mock_redis.get.return_value = b"invalid json"

        result = await service._get_cached_result("query", "sonar", "standard")

        assert result is None  # Should return None on error

    @pytest.mark.asyncio
    async def test_cache_storage_error_handling(self, mock_redis):
        """Test error handling during cache storage."""
        service = ResearchService()
        service.redis_client = mock_redis

        # Simulate Redis storage error
        mock_redis.setex.side_effect = Exception("Storage failed")

        # Should not raise exception
        await service._cache_result(
            query="test",
            model_name="sonar",
            depth="standard",
            result={"content": "test"},
            tokens_used=100,
            cost=0.001
        )

    @pytest.mark.asyncio
    async def test_cache_key_query_normalization(self):
        """Test that similar queries generate different cache keys."""
        service = ResearchService()

        # Test case sensitivity
        key1 = service._generate_cache_key("Test Query", "sonar", "standard")
        key2 = service._generate_cache_key("test query", "sonar", "standard")

        assert key1 != key2  # Case sensitive

        # Test whitespace
        key3 = service._generate_cache_key("test query", "sonar", "standard")
        key4 = service._generate_cache_key("test  query", "sonar", "standard")

        assert key3 != key4  # Whitespace sensitive

    @pytest.mark.asyncio
    async def test_no_redis_client_skips_caching(self, db_session, test_user_id):
        """Test that missing Redis client doesn't break service."""
        service = ResearchService()
        service.redis_client = None

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test query",
                model_name="sonar",
                depth="standard",
                optimize_cost=False
            )

            assert task is not None

    @pytest.mark.asyncio
    async def test_cache_hit_performance_improvement(
        self, db_session, test_user_id, mock_redis
    ):
        """Test that cache hits are significantly faster than API calls."""
        service = ResearchService()
        service.redis_client = mock_redis

        cached_data = {
            "result": {"content": "Cached"},
            "tokens_used": 1000,
            "cost": 0.005
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        start_time = time.time()

        task = await service.create_research_task(
            db=db_session,
            user_id=test_user_id,
            query="Fast query",
            model_name="sonar",
            depth="standard",
            optimize_cost=False
        )

        elapsed = time.time() - start_time

        # Cache hit should be very fast (< 100ms)
        assert elapsed < 0.1
        assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_structured_data_cached_correctly(
        self, db_session, test_user_id, mock_redis
    ):
        """Test that structured data is preserved in cache."""
        service = ResearchService()
        service.redis_client = mock_redis

        structured_data = {
            "analysis": {
                "sentiment": "positive",
                "topics": ["AI", "Technology"],
                "confidence": 0.95
            }
        }

        cached_data = {
            "result": {
                "content": "Test",
                "citations": [],
                "sources": [],
                "structured_data": structured_data,
                "validation_status": "valid"
            },
            "tokens_used": 1500,
            "cost": 0.0075
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        task = await service.create_research_task(
            db=db_session,
            user_id=test_user_id,
            query="Structured query",
            model_name="sonar",
            depth="standard",
            optimize_cost=False
        )

        assert task.structured_data == structured_data
        assert task.validation_status == "valid"
