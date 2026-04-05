"""Tests for Dead Letter Queue Model"""
import pytest
from datetime import datetime
from app.models.dlq import (
    DeadLetterEntry,
    DeadLetterCreate,
    DeadLetterUpdate,
    FailureReasonEnum,
    DeadLetterStatusEnum
)


class TestDeadLetterModel:
    def test_create_dead_letter_entry(self):
        entry = DeadLetterEntry(
            id=1,
            url="https://example.com/article",
            domain="example.com",
            failure_reason=FailureReasonEnum.TIMEOUT,
            error_message="Connection timed out",
            retry_count=3,
            max_retries=5,
            original_payload={"method": "newspaper4k"},
            created_at=datetime.utcnow()
        )

        assert entry.url == "https://example.com/article"
        assert entry.failure_reason == FailureReasonEnum.TIMEOUT
        assert entry.retry_count == 3

    def test_failure_reason_enum_values(self):
        assert FailureReasonEnum.TIMEOUT.value == "timeout"
        assert FailureReasonEnum.BLOCKED.value == "blocked"
        assert FailureReasonEnum.PAYWALL.value == "paywall"
        assert FailureReasonEnum.EXTRACTION_FAILED.value == "extraction_failed"
        assert FailureReasonEnum.RATE_LIMITED.value == "rate_limited"
        assert FailureReasonEnum.CONNECTION_ERROR.value == "connection_error"
        assert FailureReasonEnum.INVALID_CONTENT.value == "invalid_content"
        assert FailureReasonEnum.STRUCTURE_CHANGED.value == "structure_changed"
        assert FailureReasonEnum.UNKNOWN.value == "unknown"

    def test_dead_letter_status_enum_values(self):
        assert DeadLetterStatusEnum.PENDING.value == "pending"
        assert DeadLetterStatusEnum.PROCESSING.value == "processing"
        assert DeadLetterStatusEnum.RESOLVED.value == "resolved"
        assert DeadLetterStatusEnum.ABANDONED.value == "abandoned"
        assert DeadLetterStatusEnum.MANUAL.value == "manual"

    def test_dead_letter_create_schema(self):
        create_data = DeadLetterCreate(
            url="https://news.com/story",
            failure_reason=FailureReasonEnum.BLOCKED,
            error_message="403 Forbidden"
        )

        assert create_data.retry_count == 0  # default
        assert create_data.max_retries == 5  # default

    def test_dead_letter_create_with_payload(self):
        create_data = DeadLetterCreate(
            url="https://news.com/story",
            failure_reason=FailureReasonEnum.TIMEOUT,
            error_message="Timeout after 30s",
            original_payload={"method": "playwright", "stealth": True},
            error_details={"http_status": None, "exception_type": "TimeoutError"}
        )

        assert create_data.original_payload["method"] == "playwright"
        assert create_data.error_details["exception_type"] == "TimeoutError"

    def test_dead_letter_update_schema(self):
        update_data = DeadLetterUpdate(
            status=DeadLetterStatusEnum.RESOLVED,
            resolution_notes="Fixed after site update"
        )

        assert update_data.status == DeadLetterStatusEnum.RESOLVED
        assert update_data.resolution_notes == "Fixed after site update"

    def test_dead_letter_entry_defaults(self):
        entry = DeadLetterEntry(
            id=1,
            url="https://example.com",
            domain="example.com",
            failure_reason=FailureReasonEnum.UNKNOWN,
            retry_count=0,
            max_retries=5,
            created_at=datetime.utcnow()
        )

        assert entry.status == DeadLetterStatusEnum.PENDING
        assert entry.error_details == {}
        assert entry.original_payload == {}
        assert entry.job_id is None

    def test_dead_letter_entry_with_timestamps(self):
        now = datetime.utcnow()
        entry = DeadLetterEntry(
            id=1,
            url="https://example.com",
            domain="example.com",
            failure_reason=FailureReasonEnum.RATE_LIMITED,
            retry_count=2,
            max_retries=5,
            last_retry_at=now,
            next_retry_at=now,
            created_at=now,
            updated_at=now
        )

        assert entry.last_retry_at == now
        assert entry.next_retry_at == now
        assert entry.updated_at == now
