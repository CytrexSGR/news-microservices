"""Tests for Dead Letter Queue Handler"""
import pytest
from datetime import datetime, timedelta
from app.services.dlq_handler import DLQHandler, get_dlq_handler
from app.models.dlq import (
    DeadLetterCreate,
    DeadLetterUpdate,
    FailureReasonEnum,
    DeadLetterStatusEnum
)


class TestDLQHandler:
    @pytest.fixture
    def handler(self):
        return DLQHandler()

    @pytest.fixture
    def sample_create_data(self):
        return DeadLetterCreate(
            url="https://example.com/article",
            failure_reason=FailureReasonEnum.TIMEOUT,
            error_message="Connection timed out"
        )

    @pytest.mark.asyncio
    async def test_add_entry(self, handler, sample_create_data):
        entry = await handler.add_entry(sample_create_data)

        assert entry.id == 1
        assert entry.url == sample_create_data.url
        assert entry.domain == "example.com"
        assert entry.failure_reason == FailureReasonEnum.TIMEOUT
        assert entry.status == DeadLetterStatusEnum.PENDING
        assert entry.retry_count == 0
        assert entry.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_add_duplicate_url_increments_retry(self, handler, sample_create_data):
        # First entry
        entry1 = await handler.add_entry(sample_create_data)
        assert entry1.retry_count == 0

        # Same URL again
        entry2 = await handler.add_entry(sample_create_data)
        assert entry2.id == entry1.id  # Same entry
        assert entry2.retry_count == 1  # Incremented

    @pytest.mark.asyncio
    async def test_get_entry_by_id(self, handler, sample_create_data):
        created = await handler.add_entry(sample_create_data)

        entry = await handler.get_entry(created.id)
        assert entry is not None
        assert entry.url == sample_create_data.url

    @pytest.mark.asyncio
    async def test_get_entry_by_url(self, handler, sample_create_data):
        created = await handler.add_entry(sample_create_data)

        entry = await handler.get_entry_by_url(sample_create_data.url)
        assert entry is not None
        assert entry.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_entry(self, handler):
        entry = await handler.get_entry(999)
        assert entry is None

    @pytest.mark.asyncio
    async def test_update_entry(self, handler, sample_create_data):
        created = await handler.add_entry(sample_create_data)

        update = DeadLetterUpdate(
            status=DeadLetterStatusEnum.PROCESSING
        )
        updated = await handler.update_entry(created.id, update)

        assert updated.status == DeadLetterStatusEnum.PROCESSING
        assert updated.updated_at is not None

    @pytest.mark.asyncio
    async def test_mark_resolved(self, handler, sample_create_data):
        created = await handler.add_entry(sample_create_data)

        resolved = await handler.mark_resolved(created.id, "Fixed by update")

        assert resolved.status == DeadLetterStatusEnum.RESOLVED
        assert resolved.resolution_notes == "Fixed by update"
        assert resolved.resolved_at is not None

    @pytest.mark.asyncio
    async def test_mark_processing(self, handler, sample_create_data):
        created = await handler.add_entry(sample_create_data)

        processing = await handler.mark_processing(created.id)

        assert processing.status == DeadLetterStatusEnum.PROCESSING

    @pytest.mark.asyncio
    async def test_mark_manual(self, handler, sample_create_data):
        created = await handler.add_entry(sample_create_data)

        manual = await handler.mark_manual(created.id, "Requires human review")

        assert manual.status == DeadLetterStatusEnum.MANUAL
        assert manual.resolution_notes == "Requires human review"

    @pytest.mark.asyncio
    async def test_get_pending_entries(self, handler):
        # Add entries with different statuses
        entry1 = await handler.add_entry(DeadLetterCreate(
            url="https://example.com/1",
            failure_reason=FailureReasonEnum.TIMEOUT
        ))
        entry2 = await handler.add_entry(DeadLetterCreate(
            url="https://example.com/2",
            failure_reason=FailureReasonEnum.BLOCKED
        ))

        # Mark one as resolved
        await handler.mark_resolved(entry1.id)

        # Get pending (should only be entry2)
        # Note: next_retry_at is in the future, so we need to manually check
        pending = await handler.get_entries_by_status(DeadLetterStatusEnum.PENDING)
        assert len(pending) == 1
        assert pending[0].url == "https://example.com/2"

    @pytest.mark.asyncio
    async def test_get_entries_by_domain(self, handler):
        await handler.add_entry(DeadLetterCreate(
            url="https://example.com/1",
            failure_reason=FailureReasonEnum.TIMEOUT
        ))
        await handler.add_entry(DeadLetterCreate(
            url="https://example.com/2",
            failure_reason=FailureReasonEnum.BLOCKED
        ))
        await handler.add_entry(DeadLetterCreate(
            url="https://other.com/1",
            failure_reason=FailureReasonEnum.TIMEOUT
        ))

        entries = await handler.get_entries_by_domain("example.com")
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_get_entries_by_failure_reason(self, handler):
        await handler.add_entry(DeadLetterCreate(
            url="https://example.com/1",
            failure_reason=FailureReasonEnum.TIMEOUT
        ))
        await handler.add_entry(DeadLetterCreate(
            url="https://example.com/2",
            failure_reason=FailureReasonEnum.TIMEOUT
        ))
        await handler.add_entry(DeadLetterCreate(
            url="https://example.com/3",
            failure_reason=FailureReasonEnum.BLOCKED
        ))

        entries = await handler.get_entries_by_failure_reason(FailureReasonEnum.TIMEOUT)
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_delete_entry(self, handler, sample_create_data):
        created = await handler.add_entry(sample_create_data)

        result = await handler.delete_entry(created.id)
        assert result is True

        entry = await handler.get_entry(created.id)
        assert entry is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entry(self, handler):
        result = await handler.delete_entry(999)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_stats(self, handler):
        await handler.add_entry(DeadLetterCreate(
            url="https://example.com/1",
            failure_reason=FailureReasonEnum.TIMEOUT
        ))
        await handler.add_entry(DeadLetterCreate(
            url="https://example.com/2",
            failure_reason=FailureReasonEnum.BLOCKED
        ))

        stats = await handler.get_stats()

        assert stats["total_entries"] == 2
        assert "by_status" in stats
        assert "by_failure_reason" in stats
        assert "by_domain" in stats
        assert stats["by_status"]["pending"] == 2

    @pytest.mark.asyncio
    async def test_max_retries_abandons_entry(self, handler):
        # Create entry with TIMEOUT which has max 5 retries by default
        # We'll use a URL and keep failing until it's abandoned
        create_data = DeadLetterCreate(
            url="https://example.com/article",
            failure_reason=FailureReasonEnum.PAYWALL,  # max 2 retries
        )

        # First add - pending
        entry = await handler.add_entry(create_data)
        assert entry.status == DeadLetterStatusEnum.PENDING
        assert entry.retry_count == 0

        # Second add - retry 1, still pending
        entry = await handler.add_entry(create_data)
        assert entry.retry_count == 1
        assert entry.status == DeadLetterStatusEnum.PENDING

        # Third add - retry 2, abandoned (2 >= 2)
        entry = await handler.add_entry(create_data)
        assert entry.retry_count == 2
        assert entry.status == DeadLetterStatusEnum.ABANDONED

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, handler):
        """Test that retry delays increase exponentially"""
        entry0 = await handler.add_entry(DeadLetterCreate(
            url="https://example.com/1",
            failure_reason=FailureReasonEnum.TIMEOUT
        ))

        # Base delay is 60 seconds
        time0 = entry0.next_retry_at

        # Simulate retry
        entry1 = await handler.add_entry(DeadLetterCreate(
            url="https://example.com/1",
            failure_reason=FailureReasonEnum.TIMEOUT
        ))
        time1 = entry1.next_retry_at

        # Next delay should be larger (roughly 2x due to exponential backoff)
        # The actual delay includes jitter, so we check it's in reasonable range
        delay0 = (time0 - entry0.created_at).total_seconds() if time0 else 0
        delay1 = (time1 - datetime.utcnow()).total_seconds() if time1 else 0

        # Second delay should be roughly 2x the first (with jitter tolerance)
        assert delay1 > delay0 * 1.5  # At least 1.5x due to jitter

    def test_extract_domain(self, handler):
        assert handler._extract_domain("https://www.example.com/path") == "www.example.com"
        assert handler._extract_domain("http://example.com:8080/path") == "example.com:8080"
        assert handler._extract_domain("invalid-url") == "unknown"

    def test_calculate_next_retry(self, handler):
        now = datetime.utcnow()

        # Retry 0: ~60 seconds
        retry0 = handler._calculate_next_retry(0)
        delay0 = (retry0 - now).total_seconds()
        assert 48 <= delay0 <= 72  # 60 ± 20%

        # Retry 1: ~120 seconds
        retry1 = handler._calculate_next_retry(1)
        delay1 = (retry1 - now).total_seconds()
        assert 96 <= delay1 <= 144  # 120 ± 20%

        # Retry 5: ~1920 seconds (32 minutes)
        retry5 = handler._calculate_next_retry(5)
        delay5 = (retry5 - now).total_seconds()
        assert 1536 <= delay5 <= 2304  # 1920 ± 20%

    def test_singleton_instance(self):
        h1 = get_dlq_handler()
        h2 = get_dlq_handler()
        assert h1 is h2

    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self, handler):
        # This test verifies cleanup logic exists
        # In real scenario, entries would be older
        removed = await handler.cleanup_old_entries(days=30)
        assert removed == 0  # No old entries to remove
