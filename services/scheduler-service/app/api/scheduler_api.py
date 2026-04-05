"""
Scheduler API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional

from app.core.database import get_db
from app.core.service_auth import get_service_identity, require_any_internal_service
from app.services.feed_monitor import feed_monitor
from app.services.job_processor import job_processor
from app.services.cron_scheduler import cron_scheduler
from app.services.entity_deduplicator import run_deduplication
from database.models import AnalysisJobQueue, JobStatus
from sqlalchemy import func
from datetime import datetime

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.get("/status")
async def get_scheduler_status(
    db: Session = Depends(get_db)
):
    """
    Get scheduler status.

    Returns:
        Scheduler operational status and metrics
    """
    # Get job counts from database
    pending_jobs = db.query(AnalysisJobQueue).filter(
        AnalysisJobQueue.status == JobStatus.PENDING
    ).count()

    processing_jobs = db.query(AnalysisJobQueue).filter(
        AnalysisJobQueue.status == JobStatus.PROCESSING
    ).count()

    # Get feed monitor status
    monitor_status = feed_monitor.get_status()

    # Get job processor status
    processor_status = job_processor.get_status()

    # Get cron scheduler status
    cron_status = cron_scheduler.get_status()

    return {
        "feed_monitor": {
            "is_running": monitor_status["is_running"],
            "check_interval_seconds": monitor_status["check_interval_seconds"],
        },
        "job_processor": {
            "is_running": processor_status["is_running"],
            "process_interval_seconds": processor_status["process_interval_seconds"],
            "max_concurrent_jobs": processor_status["max_concurrent_jobs"],
        },
        "cron_scheduler": {
            "is_running": cron_status["is_running"],
            "total_jobs": cron_status["total_jobs"],
            "running_jobs": cron_status["running_jobs"],
        },
        "queue": {
            "pending_jobs": pending_jobs,
            "processing_jobs": processing_jobs,
        }
    }


@router.get("/jobs/stats")
async def get_job_stats(
    db: Session = Depends(get_db)
):
    """
    Get job queue statistics.

    Returns:
        Job processing metrics
    """
    # Get job counts by status
    total_pending = db.query(AnalysisJobQueue).filter(
        AnalysisJobQueue.status == JobStatus.PENDING
    ).count()

    total_processing = db.query(AnalysisJobQueue).filter(
        AnalysisJobQueue.status == JobStatus.PROCESSING
    ).count()

    total_completed = db.query(AnalysisJobQueue).filter(
        AnalysisJobQueue.status == JobStatus.COMPLETED
    ).count()

    total_failed = db.query(AnalysisJobQueue).filter(
        AnalysisJobQueue.status == JobStatus.FAILED
    ).count()

    # Get job counts by type
    by_type = {}
    type_counts = db.query(
        AnalysisJobQueue.job_type,
        func.count(AnalysisJobQueue.id)
    ).group_by(AnalysisJobQueue.job_type).all()

    for job_type, count in type_counts:
        by_type[job_type] = count

    return {
        "total_pending": total_pending,
        "total_processing": total_processing,
        "total_completed": total_completed,
        "total_failed": total_failed,
        "by_type": by_type
    }


@router.post("/feeds/{feed_id}/check")
async def force_feed_check(
    feed_id: str,
    service: Dict[str, str] = Depends(require_any_internal_service),
    db: Session = Depends(get_db)
):
    """
    Force immediate feed check and analysis.

    Args:
        feed_id: Feed UUID to check

    Returns:
        Check results
    """
    # TODO: Implement feed check logic
    return {
        "status": "triggered",
        "feed_id": feed_id,
        "message": "Feed check scheduled"
    }


@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List analysis jobs with optional filtering.

    Args:
        status: Filter by job status (PENDING, PROCESSING, COMPLETED, FAILED)
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip

    Returns:
        List of jobs
    """
    query = db.query(AnalysisJobQueue)

    if status:
        try:
            job_status = JobStatus[status.upper()]
            query = query.filter(AnalysisJobQueue.status == job_status)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Must be one of: PENDING, PROCESSING, COMPLETED, FAILED"
            )

    total = query.count()
    jobs = query.order_by(
        AnalysisJobQueue.priority.desc(),
        AnalysisJobQueue.created_at.desc()
    ).limit(limit).offset(offset).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": [
            {
                "id": str(job.id),
                "article_id": str(job.article_id),
                "job_type": job.job_type.value,
                "status": job.status.value,
                "priority": job.priority,
                "retry_count": job.retry_count,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message
            }
            for job in jobs
        ]
    }


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    service: Dict[str, str] = Depends(require_any_internal_service),
    db: Session = Depends(get_db)
):
    """
    Retry a failed job.

    Args:
        job_id: Job UUID to retry

    Returns:
        Updated job status
    """
    job = db.query(AnalysisJobQueue).filter(
        AnalysisJobQueue.id == job_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job.status != JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job must be in FAILED status to retry (current: {job.status.value})"
        )

    # Reset job for retry
    job.status = JobStatus.PENDING
    job.retry_count = 0
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    db.commit()

    return {
        "status": "success",
        "message": f"Job {job_id} reset for retry",
        "job": {
            "id": str(job.id),
            "status": job.status.value
        }
    }


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    service: Dict[str, str] = Depends(require_any_internal_service),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending job.

    Args:
        job_id: Job UUID to cancel

    Returns:
        Cancellation confirmation
    """
    job = db.query(AnalysisJobQueue).filter(
        AnalysisJobQueue.id == job_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only cancel PENDING or PROCESSING jobs (current: {job.status.value})"
        )

    # Mark as failed with cancellation message
    job.status = JobStatus.FAILED
    job.error_message = "Cancelled by user request"
    job.completed_at = datetime.now()
    db.commit()

    return {
        "status": "success",
        "message": f"Job {job_id} cancelled",
        "job": {
            "id": str(job.id),
            "status": job.status.value
        }
    }


@router.get("/cron/jobs")
async def list_cron_jobs():
    """
    List all cron scheduled jobs.

    Returns:
        List of cron jobs with their schedules
    """
    jobs = cron_scheduler.list_jobs()
    return {
        "total": len(jobs),
        "jobs": jobs
    }


@router.post("/internal/health/service")
async def internal_health_check(
    service: Dict[str, str] = Depends(get_service_identity)
):
    """
    Internal health check for service-to-service communication.

    Requires service API key authentication.
    """
    return {
        "status": "healthy",
        "authenticated_service": service.get("service_name"),
        "internal_api": "operational"
    }


@router.post("/neo4j/entities/deduplicate")
async def deduplicate_entities(
    dry_run: bool = True
):
    """
    Run entity deduplication on Neo4j Knowledge Graph.

    Finds and merges duplicate entities based on:
    - Case-insensitive name matches
    - Punctuation variations (e.g., "Trump Jr." vs "Trump Jr")

    Args:
        dry_run: If True, only reports what would be merged without actually merging.
                 Default is True for safety.

    Returns:
        Deduplication results including stats before/after and merge operations.

    Examples:
        # Preview what would be merged (safe)
        POST /api/v1/scheduler/neo4j/entities/deduplicate?dry_run=true

        # Actually merge duplicates
        POST /api/v1/scheduler/neo4j/entities/deduplicate?dry_run=false
    """
    try:
        result = await run_deduplication(dry_run=dry_run)
        return {
            "status": "success",
            "dry_run": dry_run,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deduplication failed: {str(e)}"
        )
