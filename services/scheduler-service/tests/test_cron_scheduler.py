"""
Unit tests for CronScheduler service.

Tests cover:
- Scheduler lifecycle (start/stop)
- Adding jobs (cron, interval, date)
- Job management (pause, resume, remove)
- Error handling (invalid cron expressions, duplicate jobs)
- Job status and info retrieval
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from apscheduler.job import Job

from app.services.cron_scheduler import CronScheduler


class TestCronSchedulerLifecycle:
    """Test scheduler start/stop lifecycle"""

    def test_start_scheduler_success(self):
        """Test successful scheduler start"""
        scheduler = CronScheduler()

        assert not scheduler.is_running()

        scheduler.start()

        assert scheduler.is_running()
        scheduler.stop()

    def test_start_scheduler_already_running(self, caplog):
        """Test starting an already running scheduler"""
        scheduler = CronScheduler()
        scheduler.start()

        # Try starting again
        scheduler.start()

        assert "already running" in caplog.text
        scheduler.stop()

    def test_stop_scheduler_success(self):
        """Test successful scheduler stop"""
        scheduler = CronScheduler()
        scheduler.start()

        assert scheduler.is_running()

        scheduler.stop()

        assert not scheduler.is_running()

    def test_stop_scheduler_not_running(self):
        """Test stopping a scheduler that's not running"""
        scheduler = CronScheduler()

        # Should not raise error
        scheduler.stop()

        assert not scheduler.is_running()


class TestCronSchedulerCronJobs:
    """Test cron-style job scheduling"""

    def test_add_cron_job_hourly(self):
        """Test adding a job that runs every hour"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_cron_job(
            job_id="hourly_job",
            func=test_job,
            cron_expression="0 * * * *",
            name="Hourly Job"
        )

        assert job is not None
        assert job.id == "hourly_job"
        assert job.name == "Hourly Job"
        assert scheduler.get_job("hourly_job") is not None

        scheduler.stop()

    def test_add_cron_job_daily_midnight(self):
        """Test adding a job that runs daily at midnight"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_cron_job(
            job_id="daily_job",
            func=test_job,
            cron_expression="0 0 * * *",
            name="Daily Midnight Job"
        )

        assert job is not None
        assert job.id == "daily_job"
        scheduler.stop()

    def test_add_cron_job_weekly_monday(self):
        """Test adding a job that runs every Monday at 9 AM"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_cron_job(
            job_id="weekly_job",
            func=test_job,
            cron_expression="0 9 * * 1"
        )

        assert job is not None
        scheduler.stop()

    def test_add_cron_job_invalid_expression(self):
        """Test adding a job with invalid cron expression"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        with pytest.raises(ValueError, match="Invalid cron expression"):
            scheduler.add_cron_job(
                job_id="invalid_job",
                func=test_job,
                cron_expression="invalid"
            )

        scheduler.stop()

    def test_add_cron_job_replace_existing(self):
        """Test replacing an existing job"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job_v1():
            pass

        def test_job_v2():
            pass

        # Add first version
        job1 = scheduler.add_cron_job(
            job_id="replaceable_job",
            func=test_job_v1,
            cron_expression="0 * * * *"
        )

        # Replace with second version
        job2 = scheduler.add_cron_job(
            job_id="replaceable_job",
            func=test_job_v2,
            cron_expression="30 * * * *",
            replace_existing=True
        )

        assert job2 is not None
        assert scheduler.get_job("replaceable_job") is not None

        scheduler.stop()

    def test_add_cron_job_with_kwargs(self):
        """Test adding a job with custom kwargs"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job(param1, param2):
            pass

        job = scheduler.add_cron_job(
            job_id="job_with_kwargs",
            func=test_job,
            cron_expression="0 * * * *",
            param1="value1",
            param2="value2"
        )

        assert job is not None
        scheduler.stop()


class TestCronSchedulerIntervalJobs:
    """Test interval-based job scheduling"""

    def test_add_interval_job_seconds(self):
        """Test adding a job that runs every 30 seconds"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_interval_job(
            job_id="interval_seconds",
            func=test_job,
            seconds=30,
            name="30 Second Job"
        )

        assert job is not None
        assert job.id == "interval_seconds"
        scheduler.stop()

    def test_add_interval_job_minutes(self):
        """Test adding a job that runs every 5 minutes"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_interval_job(
            job_id="interval_minutes",
            func=test_job,
            minutes=5
        )

        assert job is not None
        scheduler.stop()

    def test_add_interval_job_hours(self):
        """Test adding a job that runs every 2 hours"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_interval_job(
            job_id="interval_hours",
            func=test_job,
            hours=2
        )

        assert job is not None
        scheduler.stop()

    def test_add_interval_job_days(self):
        """Test adding a job that runs every day"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_interval_job(
            job_id="interval_days",
            func=test_job,
            days=1
        )

        assert job is not None
        scheduler.stop()

    def test_add_interval_job_combined(self):
        """Test adding a job with combined interval (1 hour 30 minutes)"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_interval_job(
            job_id="interval_combined",
            func=test_job,
            hours=1,
            minutes=30
        )

        assert job is not None
        scheduler.stop()


class TestCronSchedulerDateJobs:
    """Test one-time date-based job scheduling"""

    def test_add_date_job_future(self):
        """Test adding a one-time job in the future"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        run_date = datetime.now(timezone.utc) + timedelta(hours=1)

        job = scheduler.add_date_job(
            job_id="future_job",
            func=test_job,
            run_date=run_date,
            name="Future One-Time Job"
        )

        assert job is not None
        assert job.id == "future_job"
        scheduler.stop()

    def test_add_date_job_with_kwargs(self):
        """Test adding a date job with custom kwargs"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job(message):
            pass

        run_date = datetime.now(timezone.utc) + timedelta(minutes=5)

        job = scheduler.add_date_job(
            job_id="date_job_kwargs",
            func=test_job,
            run_date=run_date,
            message="Hello World"
        )

        assert job is not None
        scheduler.stop()


class TestCronSchedulerJobManagement:
    """Test job management operations"""

    def test_remove_job_success(self):
        """Test removing a job"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        scheduler.add_interval_job(
            job_id="removable_job",
            func=test_job,
            seconds=30
        )

        assert scheduler.get_job("removable_job") is not None

        scheduler.remove_job("removable_job")

        assert scheduler.get_job("removable_job") is None
        scheduler.stop()

    def test_remove_job_not_found(self, caplog):
        """Test removing a non-existent job"""
        scheduler = CronScheduler()
        scheduler.start()

        scheduler.remove_job("nonexistent_job")

        assert "not found" in caplog.text
        scheduler.stop()

    def test_pause_job_success(self):
        """Test pausing a job"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        job = scheduler.add_interval_job(
            job_id="pausable_job",
            func=test_job,
            seconds=30
        )

        scheduler.pause_job("pausable_job")

        # Job should still exist but be paused
        assert scheduler.get_job("pausable_job") is not None
        scheduler.stop()

    def test_resume_job_success(self):
        """Test resuming a paused job"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        scheduler.add_interval_job(
            job_id="resumable_job",
            func=test_job,
            seconds=30
        )

        scheduler.pause_job("resumable_job")
        scheduler.resume_job("resumable_job")

        assert scheduler.get_job("resumable_job") is not None
        scheduler.stop()

    def test_get_all_jobs(self):
        """Test retrieving all jobs"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        scheduler.add_interval_job("job1", test_job, seconds=30)
        scheduler.add_interval_job("job2", test_job, seconds=60)
        scheduler.add_interval_job("job3", test_job, minutes=5)

        all_jobs = scheduler.get_all_jobs()

        assert len(all_jobs) == 3
        assert "job1" in all_jobs
        assert "job2" in all_jobs
        assert "job3" in all_jobs

        scheduler.stop()


class TestCronSchedulerJobInfo:
    """Test job information retrieval"""

    def test_get_job_info_success(self):
        """Test getting job information"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        scheduler.add_interval_job(
            job_id="info_job",
            func=test_job,
            seconds=30,
            name="Test Info Job"
        )

        info = scheduler.get_job_info("info_job")

        assert info is not None
        assert info["id"] == "info_job"
        assert info["name"] == "Test Info Job"
        assert "next_run_time" in info
        assert "trigger" in info
        assert "pending" in info

        scheduler.stop()

    def test_get_job_info_not_found(self):
        """Test getting info for non-existent job"""
        scheduler = CronScheduler()
        scheduler.start()

        info = scheduler.get_job_info("nonexistent_job")

        assert info is None
        scheduler.stop()

    def test_list_jobs(self):
        """Test listing all jobs with info"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        scheduler.add_interval_job("job1", test_job, seconds=30, name="Job 1")
        scheduler.add_interval_job("job2", test_job, minutes=5, name="Job 2")

        jobs_list = scheduler.list_jobs()

        assert len(jobs_list) == 2
        assert all("id" in job for job in jobs_list)
        assert all("name" in job for job in jobs_list)

        scheduler.stop()


class TestCronSchedulerStatus:
    """Test scheduler status reporting"""

    def test_get_status_running(self):
        """Test status when scheduler is running"""
        scheduler = CronScheduler()
        scheduler.start()

        status = scheduler.get_status()

        assert status["is_running"] is True
        assert "total_jobs" in status
        assert "running_jobs" in status

        scheduler.stop()

    def test_get_status_stopped(self):
        """Test status when scheduler is stopped"""
        scheduler = CronScheduler()

        status = scheduler.get_status()

        assert status["is_running"] is False
        assert status["total_jobs"] == 0

    def test_get_status_with_jobs(self):
        """Test status reporting with active jobs"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        scheduler.add_interval_job("job1", test_job, seconds=30)
        scheduler.add_interval_job("job2", test_job, minutes=5)

        status = scheduler.get_status()

        assert status["is_running"] is True
        assert status["total_jobs"] == 2

        scheduler.stop()


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestCronSchedulerEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_cron_expression(self):
        """Test handling empty cron expression"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        with pytest.raises(ValueError):
            scheduler.add_cron_job(
                job_id="empty_cron",
                func=test_job,
                cron_expression=""
            )

        scheduler.stop()

    def test_malformed_cron_expression(self):
        """Test handling malformed cron expression"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        with pytest.raises(ValueError):
            scheduler.add_cron_job(
                job_id="malformed_cron",
                func=test_job,
                cron_expression="* * *"  # Only 3 parts instead of 5
            )

        scheduler.stop()

    def test_interval_job_no_interval(self):
        """Test adding interval job without any interval specified"""
        scheduler = CronScheduler()
        scheduler.start()

        def test_job():
            pass

        # Should use APScheduler default or raise error
        with pytest.raises(Exception):
            scheduler.add_interval_job(
                job_id="no_interval",
                func=test_job
            )

        scheduler.stop()

    def test_multiple_start_stop_cycles(self):
        """Test multiple start/stop cycles"""
        scheduler = CronScheduler()

        for i in range(3):
            scheduler.start()
            assert scheduler.is_running()

            scheduler.stop()
            assert not scheduler.is_running()

    def test_job_execution_count(self):
        """Test that jobs are tracked correctly"""
        scheduler = CronScheduler()
        scheduler.start()

        execution_count = {"count": 0}

        def test_job():
            execution_count["count"] += 1

        scheduler.add_interval_job(
            job_id="counting_job",
            func=test_job,
            seconds=1
        )

        # Let it run for a bit
        import time
        time.sleep(2.5)

        # Should have executed at least 2 times
        assert execution_count["count"] >= 2

        scheduler.stop()
