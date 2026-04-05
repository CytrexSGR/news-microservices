"""Tests for Priority Queue API"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.models.priority_queue import ScrapeJob, QueueStats, PriorityLevel


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_queue():
    with patch('app.api.queue.get_priority_queue') as mock:
        queue = MagicMock()
        queue._jobs = {}
        mock.return_value = queue
        yield queue


class TestQueueAPI:
    def test_get_stats(self, client, mock_queue):
        mock_queue.get_stats.return_value = QueueStats(
            total_jobs=100,
            pending_jobs=50,
            processing_jobs=5,
            completed_jobs=40,
            failed_jobs=5,
            by_priority={"HIGH": 10, "NORMAL": 30, "LOW": 10},
            avg_wait_time_seconds=5.0,
            avg_processing_time_seconds=2.5,
            jobs_per_minute=10.0
        )

        response = client.get("/api/v1/queue/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 100
        assert data["pending_jobs"] == 50
        assert data["processing_jobs"] == 5
        assert data["by_priority"]["HIGH"] == 10

    def test_enqueue_job(self, client, mock_queue):
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_job.url = "https://example.com/article"
        mock_job.priority = PriorityLevel.HIGH
        mock_job.status = "pending"
        mock_job.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_queue.enqueue.return_value = mock_job

        response = client.post(
            "/api/v1/queue/enqueue",
            json={
                "url": "https://example.com/article",
                "priority": "HIGH",
                "max_retries": 3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["url"] == "https://example.com/article"
        assert data["priority"] == "HIGH"
        assert data["status"] == "pending"

    def test_enqueue_job_invalid_priority(self, client, mock_queue):
        response = client.post(
            "/api/v1/queue/enqueue",
            json={
                "url": "https://example.com/article",
                "priority": "INVALID"
            }
        )

        assert response.status_code == 400
        assert "Invalid priority" in response.json()["detail"]

    def test_get_job_status(self, client, mock_queue):
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_job.url = "https://example.com/article"
        mock_job.priority = PriorityLevel.NORMAL
        mock_job.status = "processing"
        mock_job.retry_count = 1
        mock_job.max_retries = 3
        mock_job.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_job.started_at = datetime(2024, 1, 1, 12, 1, 0)
        mock_job.completed_at = None
        mock_job.scheduled_at = None
        mock_job.error = None
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/queue/job/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == "processing"
        assert data["retry_count"] == 1

    def test_get_job_status_not_found(self, client, mock_queue):
        mock_queue.get_job.return_value = None

        response = client.get("/api/v1/queue/job/nonexistent")

        assert response.status_code == 404

    def test_cancel_job(self, client, mock_queue):
        mock_queue.cancel.return_value = True

        response = client.delete("/api/v1/queue/job/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_queue.cancel.assert_called_once_with("job-123")

    def test_cancel_job_not_found(self, client, mock_queue):
        mock_queue.cancel.return_value = False

        response = client.delete("/api/v1/queue/job/nonexistent")

        assert response.status_code == 404

    def test_dequeue_job(self, client, mock_queue):
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_job.url = "https://example.com/article"
        mock_job.priority = PriorityLevel.HIGH
        mock_job.method = "auto"
        mock_job.metadata = {"source": "rss"}
        mock_queue.dequeue.return_value = mock_job

        response = client.post("/api/v1/queue/dequeue")

        assert response.status_code == 200
        data = response.json()
        assert data["job"]["id"] == "job-123"
        assert data["job"]["priority"] == "HIGH"

    def test_dequeue_no_jobs(self, client, mock_queue):
        mock_queue.dequeue.return_value = None

        response = client.post("/api/v1/queue/dequeue")

        assert response.status_code == 200
        data = response.json()
        assert data["job"] is None
        assert "No jobs ready" in data["message"]

    def test_complete_job_success(self, client, mock_queue):
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_job.status = "completed"
        mock_job.retry_count = 0
        mock_queue.complete.return_value = mock_job

        response = client.post(
            "/api/v1/queue/complete/job-123",
            params={"success": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "completed"

    def test_complete_job_failure(self, client, mock_queue):
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_job.status = "pending"  # Re-queued for retry
        mock_job.retry_count = 1
        mock_queue.complete.return_value = mock_job

        response = client.post(
            "/api/v1/queue/complete/job-123",
            params={"success": False, "error": "Timeout"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["retry_count"] == 1

    def test_complete_job_not_found(self, client, mock_queue):
        mock_queue.complete.return_value = None

        response = client.post(
            "/api/v1/queue/complete/nonexistent",
            params={"success": True}
        )

        assert response.status_code == 404

    def test_clear_queue(self, client, mock_queue):
        mock_queue.clear.return_value = 25

        response = client.post("/api/v1/queue/clear")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["jobs_cleared"] == 25

    def test_list_pending_jobs(self, client, mock_queue):
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_job.url = "https://example.com/article"
        mock_job.priority = PriorityLevel.HIGH
        mock_job.status = "pending"
        mock_job.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_job.scheduled_at = None

        mock_queue._jobs = {"job-123": mock_job}

        response = client.get("/api/v1/queue/pending")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["jobs"][0]["id"] == "job-123"
