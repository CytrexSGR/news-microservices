"""
Priority Queue API Endpoints

Phase 6: Scale

Provides endpoints for:
- Queue statistics
- Job management
- Queue operations
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.services.priority_queue import get_priority_queue
from app.models.priority_queue import ScrapeJobCreate, PriorityLevel

router = APIRouter(prefix="/api/v1/queue", tags=["queue"])


class QueueStatsResponse(BaseModel):
    """Queue statistics response"""
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    by_priority: Dict[str, int]
    avg_wait_time_seconds: float
    avg_processing_time_seconds: float
    jobs_per_minute: float


class EnqueueRequest(BaseModel):
    """Request to enqueue a scraping job"""
    url: str
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, CRITICAL
    method: Optional[str] = None
    max_retries: int = 3
    delay_seconds: int = 0
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EnqueueResponse(BaseModel):
    """Response from enqueue operation"""
    job_id: str
    url: str
    priority: str
    status: str
    created_at: str


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    url: str
    priority: str
    status: str
    retry_count: int
    max_retries: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    scheduled_at: Optional[str] = None
    error: Optional[str] = None


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats() -> QueueStatsResponse:
    """Get priority queue statistics"""
    queue = get_priority_queue()
    stats = queue.get_stats()

    return QueueStatsResponse(
        total_jobs=stats.total_jobs,
        pending_jobs=stats.pending_jobs,
        processing_jobs=stats.processing_jobs,
        completed_jobs=stats.completed_jobs,
        failed_jobs=stats.failed_jobs,
        by_priority=stats.by_priority,
        avg_wait_time_seconds=stats.avg_wait_time_seconds,
        avg_processing_time_seconds=stats.avg_processing_time_seconds,
        jobs_per_minute=stats.jobs_per_minute
    )


@router.post("/enqueue", response_model=EnqueueResponse)
async def enqueue_job(request: EnqueueRequest) -> EnqueueResponse:
    """Add a job to the priority queue"""
    queue = get_priority_queue()

    # Parse priority
    try:
        priority = PriorityLevel[request.priority.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority: {request.priority}. Use: LOW, NORMAL, HIGH, CRITICAL"
        )

    job_create = ScrapeJobCreate(
        url=request.url,
        priority=priority,
        method=request.method or "auto",
        max_retries=request.max_retries,
        delay_seconds=request.delay_seconds,
        callback_url=request.callback_url,
        metadata=request.metadata or {}
    )

    job = queue.enqueue(job_create)

    return EnqueueResponse(
        job_id=job.id,
        url=job.url,
        priority=job.priority.name,
        status=job.status,
        created_at=job.created_at.isoformat()
    )


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get status of a specific job"""
    queue = get_priority_queue()
    job = queue.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )

    return JobStatusResponse(
        job_id=job.id,
        url=job.url,
        priority=job.priority.name,
        status=job.status,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        scheduled_at=job.scheduled_at.isoformat() if job.scheduled_at else None,
        error=job.error
    )


@router.delete("/job/{job_id}")
async def cancel_job(job_id: str) -> Dict[str, Any]:
    """Cancel a pending job"""
    queue = get_priority_queue()
    success = queue.cancel(job_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found or not cancellable: {job_id}"
        )

    return {
        "success": True,
        "message": f"Cancelled job: {job_id}"
    }


@router.post("/dequeue")
async def dequeue_job() -> Dict[str, Any]:
    """
    Dequeue the next job for processing.

    Returns the highest priority job that is ready (not scheduled for later).
    """
    queue = get_priority_queue()
    job = queue.dequeue()

    if not job:
        return {
            "job": None,
            "message": "No jobs ready for processing"
        }

    return {
        "job": {
            "id": job.id,
            "url": job.url,
            "priority": job.priority.name,
            "method": job.method,
            "metadata": job.metadata
        },
        "message": "Job dequeued for processing"
    }


@router.post("/complete/{job_id}")
async def complete_job(
    job_id: str,
    success: bool = True,
    error: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Mark a job as completed.

    Args:
        job_id: Job ID
        success: Whether the job succeeded
        error: Error message (for failures)
        result: Result data (for success)
    """
    queue = get_priority_queue()

    if success:
        job = queue.complete(job_id, result=result)
    else:
        job = queue.complete(job_id, error=error or "Unknown error")

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )

    return {
        "success": True,
        "job_id": job.id,
        "status": job.status,
        "retry_count": job.retry_count,
        "message": f"Job marked as {job.status}"
    }


@router.post("/clear")
async def clear_queue() -> Dict[str, Any]:
    """Clear all pending jobs from the queue"""
    queue = get_priority_queue()
    count = queue.clear()

    return {
        "success": True,
        "jobs_cleared": count,
        "message": f"Cleared {count} pending jobs"
    }


@router.get("/pending")
async def list_pending_jobs(limit: int = 100) -> Dict[str, Any]:
    """List pending jobs in the queue"""
    queue = get_priority_queue()

    pending = []
    for job in queue._jobs.values():
        if job.status == "pending":
            pending.append({
                "id": job.id,
                "url": job.url,
                "priority": job.priority.name,
                "created_at": job.created_at.isoformat(),
                "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None
            })
            if len(pending) >= limit:
                break

    return {
        "count": len(pending),
        "jobs": pending
    }
