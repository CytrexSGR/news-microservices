"""
Unit tests for JobProcessor service.

Tests cover:
- Job processing lifecycle (start/stop)
- Processing pending jobs
- Routing to correct analysis endpoints
- Retry logic with exponential backoff
- Error handling (HTTP errors, timeouts)
- Job status transitions (PENDING → PROCESSING → COMPLETED/FAILED)
- Dead letter queue for permanent failures
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.job_processor import JobProcessor, job_processor
from database.models import AnalysisJobQueue, JobType, JobStatus


# ============================================================================
# Job Processor Lifecycle Tests
# ============================================================================

class TestJobProcessorLifecycle:
    """Test job processor start/stop lifecycle"""

    @pytest.mark.asyncio
    async def test_start_job_processor(self):
        """Test successful job processor start"""
        processor = JobProcessor()

        assert not processor.is_running()

        await processor.start()

        assert processor.is_running()
        assert processor.http_client is not None

        await processor.stop()

    @pytest.mark.asyncio
    async def test_stop_job_processor(self):
        """Test successful job processor stop"""
        processor = JobProcessor()
        await processor.start()

        assert processor.is_running()

        await processor.stop()

        assert not processor.is_running()
        assert processor.http_client is None

    @pytest.mark.asyncio
    async def test_start_already_running(self, caplog):
        """Test starting an already running processor"""
        processor = JobProcessor()
        await processor.start()

        await processor.start()

        assert "already running" in caplog.text
        await processor.stop()

    @pytest.mark.asyncio
    async def test_stop_not_running(self):
        """Test stopping a processor that's not running"""
        processor = JobProcessor()

        # Should not raise error
        await processor.stop()

        assert not processor.is_running()


# ============================================================================
# Job Processing Tests
# ============================================================================

class TestJobProcessing:
    """Test job processing logic"""

    @pytest.mark.asyncio
    async def test_process_pending_jobs_empty_queue(self, db_session, caplog):
        """Test processing when no pending jobs exist"""
        processor = JobProcessor()
        processor._is_running = True

        with patch.object(processor, 'http_client', AsyncMock()):
            await processor._process_jobs()

        assert "No pending jobs" in caplog.text

    @pytest.mark.asyncio
    async def test_process_single_job_success(
        self,
        db_session,
        sample_pending_job,
        mock_http_client
    ):
        """Test successfully processing a single job"""
        processor = JobProcessor()
        processor._is_running = True
        processor.http_client = mock_http_client

        # Mock successful API response
        mock_http_client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {"status": "success", "analysis_id": "test-123"}
            )
        )

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, sample_pending_job)

        # Job should be marked as completed
        db_session.refresh(sample_pending_job)
        assert sample_pending_job.status == JobStatus.COMPLETED
        assert sample_pending_job.completed_at is not None

    @pytest.mark.asyncio
    async def test_process_multiple_jobs(
        self,
        db_session
    ):
        """Test processing multiple jobs in one cycle"""
        # Create multiple pending jobs
        jobs = []
        for i in range(3):
            job = AnalysisJobQueue(
                feed_id=f"feed-{i}",
                article_id=f"article-{i}",
                job_type=JobType.CATEGORIZATION,
                status=JobStatus.PENDING,
                priority=10
            )
            db_session.add(job)
            jobs.append(job)

        db_session.commit()

        processor = JobProcessor()
        processor._is_running = True
        processor._max_concurrent_jobs = 5

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {"status": "success"}
            )
        )
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_jobs()

        # All jobs should be completed
        for job in jobs:
            db_session.refresh(job)
            assert job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_process_jobs_respects_max_concurrent(
        self,
        db_session
    ):
        """Test that max concurrent jobs limit is respected"""
        # Create 10 pending jobs
        for i in range(10):
            job = AnalysisJobQueue(
                feed_id=f"feed-{i}",
                article_id=f"article-{i}",
                job_type=JobType.STANDARD_SENTIMENT,
                status=JobStatus.PENDING,
                priority=5
            )
            db_session.add(job)

        db_session.commit()

        processor = JobProcessor()
        processor._is_running = True
        processor._max_concurrent_jobs = 3  # Limit to 3

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {"status": "success"}
            )
        )
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_jobs()

        # Only 3 jobs should be processed
        completed_jobs = db_session.query(AnalysisJobQueue).filter(
            AnalysisJobQueue.status == JobStatus.COMPLETED
        ).count()

        assert completed_jobs == 3


# ============================================================================
# Job Routing Tests
# ============================================================================

class TestJobRouting:
    """Test routing jobs to correct analysis endpoints"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("job_type,expected_endpoint", [
        (JobType.CATEGORIZATION, "/api/v1/internal/analyze/categorization"),
        (JobType.FINANCE_SENTIMENT, "/api/v1/internal/analyze/finance-sentiment"),
        (JobType.GEOPOLITICAL_SENTIMENT, "/api/v1/internal/analyze/geopolitical-sentiment"),
        (JobType.STANDARD_SENTIMENT, "/api/v1/internal/analyze/standard-sentiment"),
        (JobType.OSINT_ANALYSIS, "/api/v1/internal/analyze/osint"),
        (JobType.SUMMARY, "/api/v1/internal/analyze/summary"),
        (JobType.ENTITIES, "/api/v1/internal/analyze/entities"),
        (JobType.TOPICS, "/api/v1/internal/analyze/topics"),
    ])
    async def test_route_to_correct_endpoint(
        self,
        db_session,
        job_type,
        expected_endpoint,
        test_settings
    ):
        """Test that each job type routes to correct endpoint"""
        job = AnalysisJobQueue(
            feed_id="feed-123",
            article_id="article-123",
            job_type=job_type,
            status=JobStatus.PENDING,
            priority=5
        )
        db_session.add(job)
        db_session.commit()

        processor = JobProcessor()
        processor._is_running = True

        mock_client = AsyncMock()
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, job)

        # Verify correct endpoint was called
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert expected_endpoint in call_args[0][0]

    @pytest.mark.asyncio
    async def test_unknown_job_type(self, db_session):
        """Test handling of unknown job type"""
        job = AnalysisJobQueue(
            feed_id="feed-123",
            article_id="article-123",
            job_type="UNKNOWN_TYPE",  # Invalid type
            status=JobStatus.PENDING,
            priority=5
        )
        db_session.add(job)
        db_session.commit()

        processor = JobProcessor()
        processor._is_running = True
        processor.http_client = AsyncMock()

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, job)

        # Job should be marked as failed
        db_session.refresh(job)
        assert job.status == JobStatus.FAILED
        assert "Unknown job type" in job.error_message


# ============================================================================
# Retry Logic Tests
# ============================================================================

class TestRetryLogic:
    """Test retry logic with exponential backoff"""

    @pytest.mark.asyncio
    async def test_job_retry_on_failure(self, db_session):
        """Test that failed job is retried"""
        job = AnalysisJobQueue(
            feed_id="feed-123",
            article_id="article-123",
            job_type=JobType.CATEGORIZATION,
            status=JobStatus.PENDING,
            priority=10,
            max_retries=3,
            retry_count=0
        )
        db_session.add(job)
        db_session.commit()

        processor = JobProcessor()
        processor._is_running = True

        # Mock HTTP client to raise error
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, job)

        # Job should be set back to PENDING with incremented retry count
        db_session.refresh(job)
        assert job.status == JobStatus.PENDING
        assert job.retry_count == 1
        assert job.error_message is not None

    @pytest.mark.asyncio
    async def test_job_max_retries_exceeded(self, db_session):
        """Test that job fails permanently after max retries"""
        job = AnalysisJobQueue(
            feed_id="feed-123",
            article_id="article-123",
            job_type=JobType.CATEGORIZATION,
            status=JobStatus.PENDING,
            priority=10,
            max_retries=3,
            retry_count=2  # Already failed twice
        )
        db_session.add(job)
        db_session.commit()

        processor = JobProcessor()
        processor._is_running = True

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, job)

        # Job should be marked as permanently FAILED
        db_session.refresh(job)
        assert job.status == JobStatus.FAILED
        assert job.retry_count == 3
        assert job.completed_at is not None

    @pytest.mark.asyncio
    async def test_skip_max_retries_exceeded_jobs(self, db_session):
        """Test that jobs with max retries exceeded are skipped"""
        # Create job that has already exceeded max retries
        job = AnalysisJobQueue(
            feed_id="feed-123",
            article_id="article-123",
            job_type=JobType.CATEGORIZATION,
            status=JobStatus.PENDING,
            priority=10,
            max_retries=3,
            retry_count=3  # Already at max
        )
        db_session.add(job)
        db_session.commit()

        processor = JobProcessor()
        processor._is_running = True
        processor.http_client = AsyncMock()

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_jobs()

        # Job should not be processed (status unchanged)
        db_session.refresh(job)
        assert job.status == JobStatus.PENDING  # Not touched


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_http_timeout_error(self, db_session, sample_pending_job):
        """Test handling of HTTP timeout"""
        processor = JobProcessor()
        processor._is_running = True

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, sample_pending_job)

        db_session.refresh(sample_pending_job)
        assert sample_pending_job.retry_count == 1
        assert "timeout" in sample_pending_job.error_message.lower()

    @pytest.mark.asyncio
    async def test_http_404_error(self, db_session, sample_pending_job):
        """Test handling of 404 Not Found"""
        processor = JobProcessor()
        processor._is_running = True

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=mock_response
            )
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, sample_pending_job)

        db_session.refresh(sample_pending_job)
        assert sample_pending_job.retry_count == 1

    @pytest.mark.asyncio
    async def test_http_500_error(self, db_session, sample_pending_job):
        """Test handling of 500 Internal Server Error"""
        processor = JobProcessor()
        processor._is_running = True

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=mock_response
            )
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, sample_pending_job)

        db_session.refresh(sample_pending_job)
        assert sample_pending_job.retry_count == 1

    @pytest.mark.asyncio
    async def test_network_error(self, db_session, sample_pending_job):
        """Test handling of network connection error"""
        processor = JobProcessor()
        processor._is_running = True

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, sample_pending_job)

        db_session.refresh(sample_pending_job)
        assert sample_pending_job.retry_count == 1
        assert "connection" in sample_pending_job.error_message.lower()

    @pytest.mark.asyncio
    async def test_unexpected_exception(self, db_session, sample_pending_job):
        """Test handling of unexpected exception"""
        processor = JobProcessor()
        processor._is_running = True

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Unexpected error"))
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, sample_pending_job)

        db_session.refresh(sample_pending_job)
        assert sample_pending_job.retry_count == 1


# ============================================================================
# Job Status Transition Tests
# ============================================================================

class TestJobStatusTransitions:
    """Test job status state machine"""

    @pytest.mark.asyncio
    async def test_pending_to_processing_transition(self, db_session, sample_pending_job):
        """Test PENDING → PROCESSING transition"""
        assert sample_pending_job.status == JobStatus.PENDING
        assert sample_pending_job.started_at is None

        processor = JobProcessor()
        processor._is_running = True

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {"status": "success"}
            )
        )
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            # Set job to processing first
            sample_pending_job.status = JobStatus.PROCESSING
            sample_pending_job.started_at = datetime.now(timezone.utc)
            db_session.commit()

            await processor._process_single_job(db_session, sample_pending_job)

        db_session.refresh(sample_pending_job)
        assert sample_pending_job.status == JobStatus.COMPLETED
        assert sample_pending_job.started_at is not None

    @pytest.mark.asyncio
    async def test_processing_to_completed_transition(
        self,
        db_session,
        sample_processing_job
    ):
        """Test PROCESSING → COMPLETED transition"""
        assert sample_processing_job.status == JobStatus.PROCESSING
        assert sample_processing_job.completed_at is None

        processor = JobProcessor()
        processor._is_running = True

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {"status": "success"}
            )
        )
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, sample_processing_job)

        db_session.refresh(sample_processing_job)
        assert sample_processing_job.status == JobStatus.COMPLETED
        assert sample_processing_job.completed_at is not None

    @pytest.mark.asyncio
    async def test_processing_to_failed_transition(
        self,
        db_session,
        sample_processing_job
    ):
        """Test PROCESSING → FAILED transition"""
        sample_processing_job.retry_count = 2  # Near max retries

        processor = JobProcessor()
        processor._is_running = True

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Error"))
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_single_job(db_session, sample_processing_job)

        db_session.refresh(sample_processing_job)
        assert sample_processing_job.status == JobStatus.FAILED
        assert sample_processing_job.retry_count == 3
        assert sample_processing_job.completed_at is not None


# ============================================================================
# Priority and Ordering Tests
# ============================================================================

class TestJobPriority:
    """Test job priority and ordering"""

    @pytest.mark.asyncio
    async def test_jobs_processed_by_priority(self, db_session):
        """Test that higher priority jobs are processed first"""
        # Create jobs with different priorities
        low_priority_job = AnalysisJobQueue(
            feed_id="feed-1",
            article_id="article-low",
            job_type=JobType.STANDARD_SENTIMENT,
            status=JobStatus.PENDING,
            priority=1  # Low priority
        )

        high_priority_job = AnalysisJobQueue(
            feed_id="feed-2",
            article_id="article-high",
            job_type=JobType.CATEGORIZATION,
            status=JobStatus.PENDING,
            priority=10  # High priority
        )

        # Add in reverse priority order
        db_session.add(low_priority_job)
        db_session.add(high_priority_job)
        db_session.commit()

        processor = JobProcessor()
        processor._is_running = True
        processor._max_concurrent_jobs = 1  # Process one at a time

        processed_articles = []

        async def track_processing(*args, **kwargs):
            """Track which article is being processed"""
            payload = kwargs.get('json', {})
            article_id = payload.get('article_id')
            processed_articles.append(article_id)
            return MagicMock(
                status_code=200,
                json=lambda: {"status": "success"}
            )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=track_processing)
        processor.http_client = mock_client

        with patch('app.services.job_processor.SessionLocal', return_value=db_session):
            await processor._process_jobs()

        # High priority job should be processed first
        assert processed_articles[0] == "article-high"


# ============================================================================
# Status Reporting Tests
# ============================================================================

class TestJobProcessorStatus:
    """Test status reporting"""

    def test_get_status_not_running(self):
        """Test status when processor is not running"""
        processor = JobProcessor()

        status = processor.get_status()

        assert status["is_running"] is False
        assert "process_interval_seconds" in status
        assert "max_concurrent_jobs" in status

    @pytest.mark.asyncio
    async def test_get_status_running(self):
        """Test status when processor is running"""
        processor = JobProcessor()
        await processor.start()

        status = processor.get_status()

        assert status["is_running"] is True
        assert status["max_concurrent_jobs"] > 0

        await processor.stop()

    def test_is_running_flag(self):
        """Test is_running flag"""
        processor = JobProcessor()

        assert not processor.is_running()
