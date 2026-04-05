"""
Tests for Celery tasks.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from app.workers.tasks import research_task, batch_research_task, cache_cleanup_task
from app.models.research import ResearchTask, ResearchCache


class TestProcessResearchTask:
    """Tests for process_research_task Celery task."""

    def test_process_task_success(self, db_session, test_user_id, mock_perplexity_response):
        """Test successful task processing."""
        # Create pending task
        task = ResearchTask(
            user_id=test_user_id,
            query="What is AI?",
            model_name="sonar",
            depth="standard",
            status="pending"
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        with patch("app.services.perplexity.perplexity_client") as mock_client:
            mock_client.research = AsyncMock(return_value=mock_perplexity_response)

            with patch("app.workers.tasks.SessionLocal", return_value=db_session):
                result = research_task(str(task.id))

                assert result["status"] == "success"
                assert result["task_id"] == str(task.id)

                # Verify task updated
                db_session.refresh(task)
                assert task.status == "completed"
                assert task.result is not None
                assert task.tokens_used > 0
                assert task.completed_at is not None

    def test_process_task_not_found(self, db_session):
        """Test processing nonexistent task."""
        with patch("app.workers.tasks.SessionLocal", return_value=db_session):
            result = research_task("99999")

            assert result["status"] == "error"
            assert "not found" in result["message"]

    def test_process_task_perplexity_error(self, db_session, test_user_id):
        """Test task processing with Perplexity error."""
        task = ResearchTask(
            user_id=test_user_id,
            query="Test query",
            model_name="sonar",
            depth="standard",
            status="pending"
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        with patch("app.services.perplexity.perplexity_client") as mock_client:
            mock_client.research = AsyncMock(side_effect=Exception("API Error"))

            with patch("app.workers.tasks.SessionLocal", return_value=db_session):
                result = research_task(str(task.id))

                assert result["status"] == "error"

                # Verify task marked as failed
                db_session.refresh(task)
                assert task.status == "failed"
                assert task.error_message is not None


class TestBatchResearchTasks:
    """Tests for batch_research_tasks Celery task."""

    def test_batch_tasks_success(self):
        """Test batch task processing."""
        with patch("app.workers.tasks.research_task") as mock_task:
            mock_result = MagicMock()
            mock_result.id = "celery-task-id"
            mock_task.delay.return_value = mock_result

            result = batch_research_task(["1", "2", "3"])

            assert result["task_count"] == 3
            assert len(result["celery_tasks"]) == 3
            assert mock_task.delay.call_count == 3

    def test_batch_tasks_empty_list(self):
        """Test batch with empty task list."""
        result = batch_research_task([])

        assert result["task_count"] == 0
        assert result["celery_tasks"] == []


class TestCleanupExpiredCache:
    """Tests for cleanup_expired_cache Celery task."""

    def test_cleanup_success(self, db_session):
        """Test successful cache cleanup."""
        # Create expired cache entries
        for i in range(5):
            entry = ResearchCache(
                cache_key=f"expired_key_{i}",
                query="Test query",
                model_name="sonar",
                depth="standard",
                result={"content": "Test"},
                tokens_used=1000,
                cost=0.005,
                expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
            )
            db_session.add(entry)

        # Create non-expired entry
        valid_entry = ResearchCache(
            cache_key="valid_key",
            query="Test query",
            model_name="sonar",
            depth="standard",
            result={"content": "Test"},
            tokens_used=1000,
            cost=0.005,
            expires_at=datetime.utcnow() + timedelta(days=7)  # Not expired
        )
        db_session.add(valid_entry)
        db_session.commit()

        with patch("app.workers.tasks.SessionLocal", return_value=db_session):
            result = cache_cleanup_task()

            assert result["deleted"] == 5

            # Verify only expired entries deleted
            remaining = db_session.query(ResearchCache).count()
            assert remaining == 1

    def test_cleanup_no_expired_entries(self, db_session):
        """Test cleanup with no expired entries."""
        # Create only valid entries
        entry = ResearchCache(
            cache_key="valid_key",
            query="Test query",
            model_name="sonar",
            depth="standard",
            result={"content": "Test"},
            tokens_used=1000,
            cost=0.005,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db_session.add(entry)
        db_session.commit()

        with patch("app.workers.tasks.SessionLocal", return_value=db_session):
            result = cache_cleanup_task()

            assert result["deleted"] == 0

    def test_cleanup_error(self, db_session):
        """Test cleanup with database error."""
        with patch("app.workers.tasks.SessionLocal") as mock_session:
            mock_session.return_value.query.side_effect = Exception("DB Error")

            result = cache_cleanup_task()

            assert result["status"] == "error"
            assert "DB Error" in result["message"]


class TestCeleryConfiguration:
    """Tests for Celery configuration."""

    def test_task_names(self):
        """Test that tasks have correct names."""
        assert research_task.name == "research.research_task"
        assert batch_research_task.name == "research.batch_research_task"
        assert cache_cleanup_task.name == "research.cache_cleanup_task"

    def test_task_bindings(self):
        """Test that research_task is bound."""
        assert research_task.request.is_eager or hasattr(research_task, 'bind')
