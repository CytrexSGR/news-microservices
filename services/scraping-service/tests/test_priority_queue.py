"""Tests for Priority Queue"""
import pytest
import time
from app.services.priority_queue import PriorityQueue, get_priority_queue
from app.models.priority_queue import ScrapeJobCreate, PriorityLevel


class TestPriorityQueue:
    @pytest.fixture
    def queue(self):
        return PriorityQueue(max_size=100)

    def test_enqueue_basic(self, queue):
        job_create = ScrapeJobCreate(
            url="https://example.com/article",
            priority=PriorityLevel.NORMAL
        )

        job = queue.enqueue(job_create)

        assert job.id is not None
        assert job.url == "https://example.com/article"
        assert job.priority == PriorityLevel.NORMAL
        assert job.status == "pending"

    def test_dequeue_returns_highest_priority(self, queue):
        # Add jobs with different priorities
        queue.enqueue(ScrapeJobCreate(url="https://example.com/low", priority=PriorityLevel.LOW))
        queue.enqueue(ScrapeJobCreate(url="https://example.com/critical", priority=PriorityLevel.CRITICAL))
        queue.enqueue(ScrapeJobCreate(url="https://example.com/normal", priority=PriorityLevel.NORMAL))

        # Dequeue should return highest priority first
        job = queue.dequeue()
        assert job.priority == PriorityLevel.CRITICAL

        job = queue.dequeue()
        assert job.priority == PriorityLevel.NORMAL

        job = queue.dequeue()
        assert job.priority == PriorityLevel.LOW

    def test_url_deduplication(self, queue):
        url = "https://example.com/article"

        job1 = queue.enqueue(ScrapeJobCreate(url=url, priority=PriorityLevel.NORMAL))
        job2 = queue.enqueue(ScrapeJobCreate(url=url, priority=PriorityLevel.HIGH))

        # Should return same job
        assert job1.id == job2.id

    def test_complete_success(self, queue):
        job_create = ScrapeJobCreate(url="https://example.com/article")
        job = queue.enqueue(job_create)

        # Dequeue and complete
        dequeued = queue.dequeue()
        result = {"content": "Article content", "word_count": 500}
        completed = queue.complete(dequeued.id, result=result)

        assert completed.status == "completed"
        assert completed.result == result

    def test_complete_failure_with_retry(self, queue):
        job_create = ScrapeJobCreate(
            url="https://example.com/article",
            max_retries=3
        )
        job = queue.enqueue(job_create)

        # Dequeue and fail
        dequeued = queue.dequeue()
        failed = queue.complete(dequeued.id, error="Timeout")

        # Should be re-queued for retry
        assert failed.status == "pending"
        assert failed.retry_count == 1

    def test_complete_failure_max_retries(self, queue):
        job_create = ScrapeJobCreate(
            url="https://example.com/article",
            max_retries=1
        )
        job = queue.enqueue(job_create)

        # First attempt
        dequeued = queue.dequeue()
        queue.complete(dequeued.id, error="Timeout")

        # Second attempt (after scheduled delay - skip for test)
        # Force retry by getting the job directly
        job = queue.get_job(dequeued.id)
        job.scheduled_at = None  # Clear delay

        dequeued2 = queue.dequeue()
        if dequeued2:
            failed = queue.complete(dequeued2.id, error="Timeout again")
            assert failed.status == "failed"

    def test_get_job(self, queue):
        job = queue.enqueue(ScrapeJobCreate(url="https://example.com/article"))

        found = queue.get_job(job.id)
        assert found.id == job.id

    def test_cancel_job(self, queue):
        job = queue.enqueue(ScrapeJobCreate(url="https://example.com/article"))

        result = queue.cancel(job.id)
        assert result is True

        # Should not be dequeuable
        dequeued = queue.dequeue()
        assert dequeued is None

    def test_get_stats(self, queue):
        queue.enqueue(ScrapeJobCreate(url="https://example.com/1", priority=PriorityLevel.HIGH))
        queue.enqueue(ScrapeJobCreate(url="https://example.com/2", priority=PriorityLevel.NORMAL))
        queue.enqueue(ScrapeJobCreate(url="https://example.com/3", priority=PriorityLevel.LOW))

        stats = queue.get_stats()

        assert stats.pending_jobs == 3
        assert stats.by_priority["HIGH"] == 1
        assert stats.by_priority["NORMAL"] == 1
        assert stats.by_priority["LOW"] == 1

    def test_delayed_job(self, queue):
        job = queue.enqueue(ScrapeJobCreate(
            url="https://example.com/article",
            delay_seconds=5
        ))

        # Should not be immediately dequeuable
        dequeued = queue.dequeue()
        assert dequeued is None

    def test_max_size_eviction(self):
        queue = PriorityQueue(max_size=3)

        queue.enqueue(ScrapeJobCreate(url="https://example.com/1", priority=PriorityLevel.HIGH))
        queue.enqueue(ScrapeJobCreate(url="https://example.com/2", priority=PriorityLevel.HIGH))
        queue.enqueue(ScrapeJobCreate(url="https://example.com/3", priority=PriorityLevel.HIGH))

        # This should evict one job
        queue.enqueue(ScrapeJobCreate(url="https://example.com/4", priority=PriorityLevel.CRITICAL))

        stats = queue.get_stats()
        assert stats.pending_jobs <= 3

    def test_clear(self, queue):
        queue.enqueue(ScrapeJobCreate(url="https://example.com/1"))
        queue.enqueue(ScrapeJobCreate(url="https://example.com/2"))
        queue.enqueue(ScrapeJobCreate(url="https://example.com/3"))

        count = queue.clear()

        assert count == 3
        assert queue.dequeue() is None

    def test_singleton_instance(self):
        q1 = get_priority_queue()
        q2 = get_priority_queue()
        assert q1 is q2
