"""
Comprehensive error handling and edge case tests.
Tests error scenarios, boundary conditions, and resilience.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import httpx
import json

from app.services.research import ResearchService
from app.services.perplexity import PerplexityClient


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_database_connection_loss(self, test_user_id):
        """Test handling of database connection loss."""
        service = ResearchService()

        # Mock database session that fails
        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            await service.create_research_task(
                db=mock_db,
                user_id=test_user_id,
                query="Test query for database failure",
                optimize_cost=False
            )

    @pytest.mark.asyncio
    async def test_perplexity_api_network_error(self):
        """Test handling of network errors from Perplexity API."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.side_effect = httpx.NetworkError("Network unreachable")

            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch.object(client, '_backoff', new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="Max retries exceeded"):
                    await client.research("Test query")

    @pytest.mark.asyncio
    async def test_perplexity_api_malformed_response(self):
        """Test handling of malformed API response."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()

            # Return malformed response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "invalid": "structure"
                # Missing 'choices' and 'usage' fields
            }
            mock_response.raise_for_status = MagicMock()

            mock_post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await client.research("Test query")

            # Should handle gracefully with empty defaults
            assert result["content"] == ""
            assert result["citations"] == []

    @pytest.mark.asyncio
    async def test_cost_tracking_failure_does_not_block_task(
        self, db_session, test_user_id
    ):
        """Test that cost tracking failures don't block task creation."""
        service = ResearchService()

        with patch.object(service, '_track_cost') as mock_track:
            mock_track.side_effect = Exception("Cost tracking failed")

            with patch("app.workers.tasks.research_task") as mock_celery:
                mock_celery.delay.return_value = MagicMock(id="task-123")

                # Should still create task despite tracking failure
                task = await service.create_research_task(
                    db=db_session,
                    user_id=test_user_id,
                    query="Test query despite tracking error",
                    optimize_cost=False
                )

                assert task is not None
                assert task.status == "pending"

    @pytest.mark.asyncio
    async def test_celery_dispatch_failure(self, db_session, test_user_id):
        """Test handling of Celery dispatch failure."""
        service = ResearchService()

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.side_effect = Exception("Celery connection failed")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test query with celery failure",
                optimize_cost=False
            )

            # Task should be created but marked as failed
            assert task is not None
            assert task.status == "failed"
            assert "Celery" in task.error_message

    @pytest.mark.asyncio
    async def test_concurrent_task_creation(self, db_session, test_user_id):
        """Test concurrent task creation doesn't cause issues."""
        service = ResearchService()

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            # Create tasks concurrently
            import asyncio
            tasks = await asyncio.gather(
                service.create_research_task(
                    db=db_session,
                    user_id=test_user_id,
                    query=f"Concurrent query {i}",
                    optimize_cost=False
                )
                for i in range(5)
            )

            assert len(tasks) == 5
            assert all(t.id is not None for t in tasks)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_query_after_strip(self, db_session, test_user_id):
        """Test query that becomes empty after stripping."""
        service = ResearchService()

        # Pydantic should catch this during validation
        with pytest.raises(Exception):  # ValidationError
            await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="          ",  # Only whitespace
                optimize_cost=False
            )

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, db_session, test_user_id):
        """Test query with special characters."""
        service = ResearchService()

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Query with 特殊字符 and émojis 🚀 and symbols <>\"'&",
                optimize_cost=False
            )

            assert task.query == "Query with 特殊字符 and émojis 🚀 and symbols <>\"'&"

    @pytest.mark.asyncio
    async def test_very_long_query_near_limit(self, db_session, test_user_id):
        """Test query at maximum length."""
        service = ResearchService()

        long_query = "a" * 1990 + " valid query"  # Just under 2000

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query=long_query,
                optimize_cost=False
            )

            assert len(task.query) <= 2000

    @pytest.mark.asyncio
    async def test_cost_limit_edge_case(self, db_session, test_user_id):
        """Test cost limit at exact boundary."""
        from app.models.research import CostTracking
        from app.core.config import settings

        # Add cost just below limit
        entry = CostTracking(
            user_id=test_user_id,
            date=datetime.utcnow(),
            model_name="sonar",
            tokens_used=10000,
            cost=settings.MAX_DAILY_COST - 0.01
        )
        db_session.add(entry)
        db_session.commit()

        service = ResearchService()

        # This should still work (just under limit)
        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Edge case query at cost limit",
                optimize_cost=False
            )

            assert task is not None

    @pytest.mark.asyncio
    async def test_zero_cost_result(self, db_session, test_user_id, mock_redis):
        """Test handling of zero-cost cached result."""
        service = ResearchService()
        service.redis_client = mock_redis

        import json
        cached_data = {
            "result": {"content": "Free result"},
            "tokens_used": 0,
            "cost": 0.0
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        task = await service.create_research_task(
            db=db_session,
            user_id=test_user_id,
            query="Zero cost query",
            optimize_cost=False
        )

        assert task.cost == 0.0
        assert task.tokens_used == 0

    @pytest.mark.asyncio
    async def test_null_feed_id_handling(self, db_session, test_user_id):
        """Test handling of None feed_id."""
        service = ResearchService()

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Query without feed",
                feed_id=None,
                legacy_feed_id=None,
                optimize_cost=False
            )

            assert task.feed_id is None
            assert task.legacy_feed_id is None

    @pytest.mark.asyncio
    async def test_duplicate_cache_keys(self):
        """Test that duplicate queries use same cache key."""
        service = ResearchService()

        key1 = service._generate_cache_key("same query", "sonar", "standard")
        key2 = service._generate_cache_key("same query", "sonar", "standard")
        key3 = service._generate_cache_key("same query", "sonar", "standard")

        assert key1 == key2 == key3

    @pytest.mark.asyncio
    async def test_pagination_edge_cases(self, db_session, test_user_id):
        """Test pagination with edge cases."""
        from app.models.research import ResearchTask

        # Create exactly 100 tasks
        for i in range(100):
            task = ResearchTask(
                user_id=test_user_id,
                query=f"Pagination test {i}",
                model_name="sonar",
                depth="standard",
                status="completed"
            )
            db_session.add(task)
        db_session.commit()

        service = ResearchService()

        # Get first page with max page_size
        tasks, total = await service.list_tasks(
            db=db_session,
            user_id=test_user_id,
            skip=0,
            limit=100
        )

        assert len(tasks) == 100
        assert total >= 100

        # Get page beyond available data
        tasks, total = await service.list_tasks(
            db=db_session,
            user_id=test_user_id,
            skip=200,
            limit=50
        )

        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_timestamp_boundary_conditions(self, db_session, test_user_id):
        """Test date/time boundary conditions."""
        from app.models.research import ResearchTask

        # Task created at exact day boundary
        task = ResearchTask(
            user_id=test_user_id,
            query="Boundary timestamp test",
            model_name="sonar",
            depth="standard",
            status="completed",
            created_at=datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        )
        db_session.add(task)
        db_session.commit()

        service = ResearchService()

        stats = await service.get_usage_stats(
            db=db_session,
            user_id=test_user_id,
            days=1
        )

        # Should include task from exact boundary
        assert stats is not None

    @pytest.mark.asyncio
    async def test_unicode_in_citations(self):
        """Test handling of Unicode in citations."""
        client = PerplexityClient()

        citations = [
            {
                "url": "https://例え.jp/article",
                "title": "日本語タイトル",
                "snippet": "これは日本語のスニペットです"
            },
            {
                "url": "https://example.com/article",
                "title": "Título en Español",
                "snippet": "Extracto con acentos: áéíóú"
            }
        ]

        sources = client._extract_sources(citations)

        assert len(sources) == 2
        assert sources[0]["title"] == "日本語タイトル"
        assert sources[1]["title"] == "Título en Español"


class TestRateLimitHandling:
    """Tests for rate limit handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_with_retry_after_header(self):
        """Test handling of Retry-After header."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()

            # First call: rate limit with Retry-After
            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {"Retry-After": "2"}

            error = httpx.HTTPStatusError(
                "Rate limit",
                request=MagicMock(),
                response=rate_limit_response
            )

            # Second call: success
            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {
                "choices": [{"message": {"content": "Success", "citations": []}}],
                "usage": {"total_tokens": 500}
            }
            success_response.raise_for_status = MagicMock()

            mock_post.side_effect = [error, success_response]
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch.object(client, '_backoff', new_callable=AsyncMock):
                result = await client.research("Test query")

                assert result["content"] == "Success"

    @pytest.mark.asyncio
    async def test_multiple_consecutive_rate_limits(self):
        """Test handling of multiple consecutive rate limits."""
        client = PerplexityClient()

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()

            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429

            error = httpx.HTTPStatusError(
                "Rate limit",
                request=MagicMock(),
                response=rate_limit_response
            )

            # All retries return rate limit
            mock_post.side_effect = error
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch.object(client, '_backoff', new_callable=AsyncMock):
                with pytest.raises(httpx.HTTPStatusError):
                    await client.research("Test query")


class TestDataIntegrity:
    """Tests for data integrity and consistency."""

    @pytest.mark.asyncio
    async def test_task_creation_rollback_on_error(self, db_session, test_user_id):
        """Test that failed task creation doesn't leave partial data."""
        service = ResearchService()

        with patch("app.workers.tasks.research_task") as mock_celery:
            # Simulate Celery failure after task creation
            mock_celery.delay.side_effect = Exception("Celery error")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test rollback behavior",
                optimize_cost=False
            )

            # Task should exist but be marked as failed
            assert task.status == "failed"
            assert task.error_message is not None

    @pytest.mark.asyncio
    async def test_cache_data_consistency(self, mock_redis):
        """Test that cached data maintains consistency."""
        service = ResearchService()
        service.redis_client = mock_redis

        result = {
            "content": "Test content",
            "citations": [{"url": "test.com"}],
            "sources": [{"url": "test.com"}]
        }

        await service._cache_result(
            query="Test",
            model_name="sonar",
            depth="standard",
            result=result,
            tokens_used=1000,
            cost=0.005
        )

        # Retrieve and verify
        cached_json = mock_redis.setex.call_args[0][2]
        cached_data = json.loads(cached_json)

        assert cached_data["result"] == result
        assert cached_data["tokens_used"] == 1000
        assert cached_data["cost"] == 0.005
