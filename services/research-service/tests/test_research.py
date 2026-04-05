"""
Tests for research API endpoints.
"""
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch
from datetime import datetime
from uuid import uuid4


class TestCreateResearchTask:
    """Tests for creating research tasks."""

    @pytest.mark.asyncio
    async def test_create_research_task_success(
        self, client, mock_auth, mock_perplexity_client, disable_cost_tracking
    ):
        """Test successful research task creation."""
        response = client.post(
            "/api/v1/research/",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "query": "What are the latest developments in AI?",
                "model_name": "sonar",
                "depth": "standard"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["query"] == "What are the latest developments in AI?"
        assert data["model_name"] == "sonar"
        assert data["depth"] == "standard"
        assert data["status"] == "completed"
        assert "result" in data
        assert data["tokens_used"] > 0

    @pytest.mark.asyncio
    async def test_create_research_task_with_feed_id(
        self, client, mock_auth, mock_perplexity_client, disable_cost_tracking
    ):
        """Test creating research task with feed_id."""
        feed_uuid = str(uuid4())
        response = client.post(
            "/api/v1/research/",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "query": "Research this feed topic",
                "model_name": "sonar",
                "depth": "quick",
                "feed_id": feed_uuid
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["feed_id"] == feed_uuid

    @pytest.mark.asyncio
    async def test_create_research_task_invalid_model(self, client, mock_auth):
        """Test creating task with invalid model."""
        response = client.post(
            "/api/v1/research/",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "query": "Test query",
                "model_name": "invalid-model",
                "depth": "standard"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_research_task_invalid_depth(self, client, mock_auth):
        """Test creating task with invalid depth."""
        response = client.post(
            "/api/v1/research/",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "query": "Test query",
                "model_name": "sonar",
                "depth": "invalid-depth"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_research_task_query_too_short(self, client, mock_auth):
        """Test creating task with too short query."""
        response = client.post(
            "/api/v1/research/",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "query": "Short",
                "model_name": "sonar",
                "depth": "standard"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_research_task_without_auth(self, client):
        """Test creating task without authentication."""
        response = client.post(
            "/api/v1/research/",
            json={
                "query": "Test query for AI research",
                "model_name": "sonar"
            }
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.asyncio
    async def test_create_research_task_perplexity_error(
        self, client, mock_auth, disable_cost_tracking
    ):
        """Test handling Perplexity API errors."""
        with patch("app.services.perplexity.perplexity_client") as mock_client:
            mock_client.research = AsyncMock(side_effect=Exception("API Error"))

            response = client.post(
                "/api/v1/research/",
                headers={"Authorization": "Bearer mock.jwt.token"},
                json={
                    "query": "Test query for error handling",
                    "model_name": "sonar",
                    "depth": "standard"
                }
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["status"] == "failed"
            assert data["error_message"] is not None


class TestGetResearchTask:
    """Tests for getting research tasks."""

    @pytest.mark.asyncio
    async def test_get_research_task_success(
        self, client, mock_auth, sample_research_task
    ):
        """Test getting a specific research task."""
        response = client.get(
            f"/api/v1/research/{sample_research_task.id}",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_research_task.id
        assert data["query"] == sample_research_task.query
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, client, mock_auth):
        """Test getting nonexistent task."""
        response = client.get(
            "/api/v1/research/99999",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_task_without_auth(self, client, sample_research_task):
        """Test getting task without authentication."""
        response = client.get(f"/api/v1/research/{sample_research_task.id}")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestListResearchTasks:
    """Tests for listing research tasks."""

    @pytest.mark.asyncio
    async def test_list_tasks_default(self, client, mock_auth, sample_research_task):
        """Test listing tasks with default parameters."""
        response = client.get(
            "/api/v1/research/",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(
        self, client, mock_auth, sample_research_task
    ):
        """Test listing tasks with status filter."""
        response = client.get(
            "/api/v1/research/?status=completed",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(task["status"] == "completed" for task in data["tasks"])

    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(
        self, client, mock_auth, db_session, test_user_id
    ):
        """Test pagination."""
        # Create multiple tasks
        from app.models.research import ResearchTask
        for i in range(15):
            task = ResearchTask(
                user_id=test_user_id,
                query=f"Test query {i}",
                model_name="sonar",
                depth="standard",
                status="completed"
            )
            db_session.add(task)
        db_session.commit()

        # Get first page
        response = client.get(
            "/api/v1/research/?page=1&page_size=10",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["tasks"]) == 10
        assert data["has_more"] is True

    @pytest.mark.asyncio
    async def test_list_tasks_with_feed_filter(
        self, client, mock_auth, db_session, test_user_id
    ):
        """Test filtering by feed_id."""
        from app.models.research import ResearchTask

        feed_uuid = uuid4()
        task = ResearchTask(
            user_id=test_user_id,
            query="Feed specific query",
            model_name="sonar",
            depth="standard",
            status="completed",
            feed_id=feed_uuid
        )
        db_session.add(task)
        db_session.commit()

        response = client.get(
            f"/api/v1/research/?feed_id={feed_uuid}",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(task["feed_id"] == str(feed_uuid) for task in data["tasks"])


class TestBatchResearchTasks:
    """Tests for batch research task creation."""

    @pytest.mark.asyncio
    async def test_batch_create_success(
        self, client, mock_auth, mock_perplexity_client, disable_cost_tracking
    ):
        """Test batch creating research tasks."""
        response = client.post(
            "/api/v1/research/batch",
            headers={"Authorization": "Bearer mock.jwt.token"},
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

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all(task["status"] == "completed" for task in data)

    @pytest.mark.asyncio
    async def test_batch_create_empty_queries(self, client, mock_auth):
        """Test batch create with empty queries."""
        response = client.post(
            "/api/v1/research/batch",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "queries": [],
                "model_name": "sonar"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestResearchHistory:
    """Tests for research history."""

    @pytest.mark.asyncio
    async def test_get_research_history(
        self, client, mock_auth, sample_research_task
    ):
        """Test getting research history."""
        response = client.get(
            "/api/v1/research/history?days=30",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tasks" in data
        assert "total" in data


class TestUsageStatistics:
    """Tests for usage statistics."""

    @pytest.mark.asyncio
    async def test_get_usage_stats(
        self, client, mock_auth, sample_cost_tracking
    ):
        """Test getting usage statistics."""
        response = client.get(
            "/api/v1/research/stats?days=30",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_requests" in data
        assert "total_tokens" in data
        assert "total_cost" in data
        assert "requests_by_model" in data
        assert "cost_by_model" in data
        assert data["total_requests"] >= 5
