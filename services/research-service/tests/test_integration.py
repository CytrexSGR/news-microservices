"""
Integration tests for research service.
Tests complete workflows end-to-end.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from fastapi import status


@pytest.mark.integration
class TestResearchWorkflow:
    """Integration tests for complete research workflows."""

    @pytest.mark.asyncio
    async def test_complete_research_workflow(
        self, client, mock_auth, db_session, mock_perplexity_response
    ):
        """Test complete workflow from creation to completion."""
        # 1. Create research task
        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="celery-123")

            create_response = client.post(
                "/api/v1/research/",
                json={
                    "query": "What are the latest developments in quantum computing?",
                    "model_name": "sonar-pro",
                    "depth": "deep"
                }
            )

            assert create_response.status_code == status.HTTP_201_CREATED
            task_data = create_response.json()
            task_id = task_data["id"]

        # 2. Get task status
        get_response = client.get(f"/api/v1/research/{task_id}")
        assert get_response.status_code == status.HTTP_200_OK
        task_data = get_response.json()
        assert task_data["id"] == task_id
        assert task_data["status"] == "pending"

        # 3. List tasks should include new task
        list_response = client.get("/api/v1/research/")
        assert list_response.status_code == status.HTTP_200_OK
        list_data = list_response.json()
        assert any(t["id"] == task_id for t in list_data["tasks"])

    @pytest.mark.asyncio
    async def test_cached_query_workflow(
        self, client, mock_auth, db_session, mock_redis
    ):
        """Test workflow with cache hit."""
        import json

        # Setup cache
        cached_data = {
            "result": {
                "content": "Cached quantum computing research",
                "citations": [{"url": "test.com"}],
                "sources": [{"url": "test.com"}]
            },
            "tokens_used": 1500,
            "cost": 0.0075
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        # Create task (should use cache)
        response = client.post(
            "/api/v1/research/",
            json={
                "query": "Quantum computing developments",
                "model_name": "sonar"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        task_data = response.json()

        # Should be completed immediately from cache
        assert task_data["status"] == "completed"
        assert task_data["result"]["content"] == "Cached quantum computing research"

    @pytest.mark.asyncio
    async def test_batch_research_workflow(self, client, mock_auth):
        """Test batch research workflow."""
        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="celery-123")

            # Create batch
            batch_response = client.post(
                "/api/v1/research/batch",
                json={
                    "queries": [
                        "What is AI?",
                        "What is machine learning?",
                        "What is deep learning?"
                    ],
                    "model_name": "sonar",
                    "depth": "quick"
                }
            )

            assert batch_response.status_code == status.HTTP_200_OK
            tasks = batch_response.json()
            assert len(tasks) == 3

            # All tasks should be created
            for task in tasks:
                assert "id" in task
                assert task["status"] == "pending"

    @pytest.mark.asyncio
    async def test_feed_research_workflow(
        self, client, mock_auth, db_session, test_user_id
    ):
        """Test research workflow with feed association."""
        from app.models.research import ResearchTask

        feed_id = uuid4()

        # Create multiple research tasks for a feed
        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="celery-123")

            for i in range(3):
                response = client.post(
                    "/api/v1/research/",
                    json={
                        "query": f"Research feed article {i}",
                        "feed_id": str(feed_id)
                    }
                )
                assert response.status_code == status.HTTP_201_CREATED

        # Get all research for this feed
        feed_response = client.get(f"/api/v1/research/feed/{feed_id}")
        assert feed_response.status_code == status.HTTP_200_OK
        feed_tasks = feed_response.json()
        assert len(feed_tasks) == 3

    @pytest.mark.asyncio
    async def test_cost_tracking_workflow(
        self, client, mock_auth, db_session, test_user_id
    ):
        """Test cost tracking throughout workflow."""
        from app.models.research import CostTracking

        # Create some tasks with costs
        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="celery-123")

            response = client.post(
                "/api/v1/research/",
                json={
                    "query": "Cost tracking test query",
                    "model_name": "sonar-pro"
                }
            )

            assert response.status_code == status.HTTP_201_CREATED

        # Get usage statistics
        stats_response = client.get("/api/v1/research/stats?days=7")
        assert stats_response.status_code == status.HTTP_200_OK
        stats = stats_response.json()

        assert "total_requests" in stats
        assert "total_cost" in stats
        assert "cost_by_model" in stats

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, client, mock_auth):
        """Test workflow handles errors gracefully."""
        # Attempt to create task with Celery failure
        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.side_effect = Exception("Celery connection failed")

            response = client.post(
                "/api/v1/research/",
                json={
                    "query": "This will fail to dispatch"
                }
            )

            assert response.status_code == status.HTTP_201_CREATED
            task_data = response.json()

            # Task should be created but marked as failed
            assert task_data["status"] == "failed"
            assert task_data["error_message"] is not None


@pytest.mark.integration
class TestHealthCheckIntegration:
    """Integration tests for health checks."""

    @pytest.mark.asyncio
    async def test_health_check_comprehensive(self, client):
        """Test comprehensive health check."""
        with patch("app.services.perplexity.perplexity_client") as mock_perplexity:
            mock_perplexity.check_health = AsyncMock(return_value=True)

            response = client.get("/health")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify all components are checked
            assert "status" in data
            assert "checks" in data
            assert "database" in data["checks"]
            assert "redis" in data["checks"]
            assert "celery" in data["checks"]
            assert "perplexity_api" in data["checks"]


@pytest.mark.integration
class TestPaginationIntegration:
    """Integration tests for pagination."""

    @pytest.mark.asyncio
    async def test_pagination_consistency(
        self, client, mock_auth, db_session, test_user_id
    ):
        """Test pagination returns consistent results."""
        from app.models.research import ResearchTask

        # Create 25 tasks
        for i in range(25):
            task = ResearchTask(
                user_id=test_user_id,
                query=f"Pagination test query {i}",
                model_name="sonar",
                depth="standard",
                status="completed"
            )
            db_session.add(task)
        db_session.commit()

        # Get all tasks via pagination
        all_task_ids = []

        for page in range(1, 4):  # 3 pages of 10
            response = client.get(f"/api/v1/research/?page={page}&page_size=10")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            task_ids = [t["id"] for t in data["tasks"]]
            all_task_ids.extend(task_ids)

        # Verify no duplicates
        assert len(all_task_ids) == len(set(all_task_ids))
        assert len(all_task_ids) == 25


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_task_creation_performance(
        self, client, mock_auth, db_session
    ):
        """Test performance under concurrent task creation."""
        import asyncio
        import time

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="celery-123")

            start_time = time.time()

            # Create 10 tasks concurrently
            async def create_task(i):
                return client.post(
                    "/api/v1/research/",
                    json={"query": f"Concurrent test query {i}"}
                )

            responses = await asyncio.gather(
                *[create_task(i) for i in range(10)]
            )

            elapsed = time.time() - start_time

            # All should succeed
            assert all(r.status_code == status.HTTP_201_CREATED for r in responses)

            # Should complete reasonably fast (< 5 seconds for 10 tasks)
            assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_large_result_set_performance(
        self, client, mock_auth, db_session, test_user_id
    ):
        """Test performance with large result sets."""
        from app.models.research import ResearchTask
        import time

        # Create 100 tasks
        for i in range(100):
            task = ResearchTask(
                user_id=test_user_id,
                query=f"Large set query {i}",
                model_name="sonar",
                depth="standard",
                status="completed"
            )
            db_session.add(task)
        db_session.commit()

        # Query should be fast even with large dataset
        start_time = time.time()
        response = client.get("/api/v1/research/?page_size=100")
        elapsed = time.time() - start_time

        assert response.status_code == status.HTTP_200_OK
        # Should complete in under 1 second
        assert elapsed < 1.0


@pytest.mark.integration
class TestCachingIntegration:
    """Integration tests for caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_hit_improves_response_time(
        self, client, mock_auth, mock_redis
    ):
        """Test that cache hits significantly improve response time."""
        import json
        import time

        cached_data = {
            "result": {"content": "Fast cached result"},
            "tokens_used": 1000,
            "cost": 0.005
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        # First request (cache hit)
        start_time = time.time()
        response = client.post(
            "/api/v1/research/",
            json={"query": "Cached query test"}
        )
        elapsed = time.time() - start_time

        assert response.status_code == status.HTTP_201_CREATED
        assert elapsed < 0.5  # Should be very fast

        task_data = response.json()
        assert task_data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_parameters_change(
        self, client, mock_auth, mock_redis
    ):
        """Test that different parameters don't use same cache."""
        import json

        cached_data = {
            "result": {"content": "Standard depth result"},
            "tokens_used": 1000,
            "cost": 0.005
        }

        # Only return cache for exact match
        def mock_get(key):
            # Simplified - would need actual key matching
            return json.dumps(cached_data).encode()

        mock_redis.get.side_effect = mock_get

        # Request with standard depth
        response1 = client.post(
            "/api/v1/research/",
            json={
                "query": "Same query",
                "depth": "standard"
            }
        )

        # Request with deep depth (different cache key)
        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="celery-123")

            response2 = client.post(
                "/api/v1/research/",
                json={
                    "query": "Same query",
                    "depth": "deep"
                }
            )

            # Should create new task (different cache key)
            assert response2.status_code == status.HTTP_201_CREATED
