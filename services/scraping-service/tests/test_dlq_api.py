"""Tests for DLQ API Endpoints"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.models.dlq import (
    DeadLetterEntry,
    DeadLetterStatusEnum,
    FailureReasonEnum
)
from datetime import datetime


class TestDLQAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def sample_entry(self):
        return DeadLetterEntry(
            id=1,
            url="https://example.com/article",
            domain="example.com",
            failure_reason=FailureReasonEnum.TIMEOUT,
            error_message="Connection timed out",
            retry_count=0,
            max_retries=5,
            status=DeadLetterStatusEnum.PENDING,
            created_at=datetime.utcnow()
        )

    def test_get_stats(self, client):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.get_stats = AsyncMock(return_value={
                "total_entries": 10,
                "by_status": {"pending": 5, "resolved": 5},
                "by_failure_reason": {"timeout": 4, "blocked": 6},
                "by_domain": {"example.com": 10}
            })
            mock_handler.return_value = mock_instance

            response = client.get("/api/v1/dlq/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["total_entries"] == 10
            assert "by_status" in data

    def test_list_entries_pending(self, client, sample_entry):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.get_entries_by_status = AsyncMock(return_value=[sample_entry])
            mock_handler.return_value = mock_instance

            response = client.get("/api/v1/dlq/entries")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["url"] == "https://example.com/article"

    def test_list_entries_by_status(self, client, sample_entry):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.get_entries_by_status = AsyncMock(return_value=[sample_entry])
            mock_handler.return_value = mock_instance

            response = client.get("/api/v1/dlq/entries?status=pending")

            assert response.status_code == 200
            mock_instance.get_entries_by_status.assert_called_once()

    def test_list_entries_by_domain(self, client, sample_entry):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.get_entries_by_domain = AsyncMock(return_value=[sample_entry])
            mock_handler.return_value = mock_instance

            response = client.get("/api/v1/dlq/entries?domain=example.com")

            assert response.status_code == 200
            mock_instance.get_entries_by_domain.assert_called_once()

    def test_list_entries_by_failure_reason(self, client, sample_entry):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.get_entries_by_failure_reason = AsyncMock(return_value=[sample_entry])
            mock_handler.return_value = mock_instance

            response = client.get("/api/v1/dlq/entries?failure_reason=timeout")

            assert response.status_code == 200
            mock_instance.get_entries_by_failure_reason.assert_called_once()

    def test_get_pending_entries(self, client, sample_entry):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.get_pending_entries = AsyncMock(return_value=[sample_entry])
            mock_handler.return_value = mock_instance

            response = client.get("/api/v1/dlq/pending")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    def test_get_entry_by_id(self, client, sample_entry):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.get_entry = AsyncMock(return_value=sample_entry)
            mock_handler.return_value = mock_instance

            response = client.get("/api/v1/dlq/entries/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1

    def test_get_entry_not_found(self, client):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.get_entry = AsyncMock(return_value=None)
            mock_handler.return_value = mock_instance

            response = client.get("/api/v1/dlq/entries/999")

            assert response.status_code == 404

    def test_update_entry(self, client, sample_entry):
        updated_entry = DeadLetterEntry(
            id=1,
            url="https://example.com/article",
            domain="example.com",
            failure_reason=FailureReasonEnum.TIMEOUT,
            retry_count=1,
            max_retries=5,
            status=DeadLetterStatusEnum.PROCESSING,
            created_at=datetime.utcnow()
        )

        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.update_entry = AsyncMock(return_value=updated_entry)
            mock_handler.return_value = mock_instance

            response = client.patch(
                "/api/v1/dlq/entries/1",
                json={"status": "processing"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"

    def test_resolve_entry(self, client, sample_entry):
        resolved_entry = DeadLetterEntry(
            id=1,
            url="https://example.com/article",
            domain="example.com",
            failure_reason=FailureReasonEnum.TIMEOUT,
            retry_count=0,
            max_retries=5,
            status=DeadLetterStatusEnum.RESOLVED,
            resolution_notes="Fixed",
            resolved_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )

        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.mark_resolved = AsyncMock(return_value=resolved_entry)
            mock_handler.return_value = mock_instance

            response = client.post("/api/v1/dlq/entries/1/resolve?notes=Fixed")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "resolved"

    def test_mark_manual(self, client, sample_entry):
        manual_entry = DeadLetterEntry(
            id=1,
            url="https://example.com/article",
            domain="example.com",
            failure_reason=FailureReasonEnum.TIMEOUT,
            retry_count=0,
            max_retries=5,
            status=DeadLetterStatusEnum.MANUAL,
            resolution_notes="Needs human review",
            created_at=datetime.utcnow()
        )

        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.mark_manual = AsyncMock(return_value=manual_entry)
            mock_handler.return_value = mock_instance

            response = client.post("/api/v1/dlq/entries/1/manual?notes=Needs%20human%20review")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "manual"

    def test_delete_entry(self, client):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.delete_entry = AsyncMock(return_value=True)
            mock_handler.return_value = mock_instance

            response = client.delete("/api/v1/dlq/entries/1")

            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] is True

    def test_delete_entry_not_found(self, client):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.delete_entry = AsyncMock(return_value=False)
            mock_handler.return_value = mock_instance

            response = client.delete("/api/v1/dlq/entries/999")

            assert response.status_code == 404

    def test_cleanup_old_entries(self, client):
        with patch('app.api.dlq.get_dlq_handler') as mock_handler:
            mock_instance = AsyncMock()
            mock_instance.cleanup_old_entries = AsyncMock(return_value=5)
            mock_handler.return_value = mock_instance

            response = client.post("/api/v1/dlq/cleanup?days=30")

            assert response.status_code == 200
            data = response.json()
            assert data["removed"] == 5
            assert data["days"] == 30
