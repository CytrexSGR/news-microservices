"""
Dead Letter Queue API Endpoints

Provides endpoints for managing and monitoring the DLQ.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.services.dlq_handler import get_dlq_handler
from app.models.dlq import (
    DeadLetterEntry,
    DeadLetterUpdate,
    FailureReasonEnum,
    DeadLetterStatusEnum
)

router = APIRouter(prefix="/api/v1/dlq", tags=["Dead Letter Queue"])


@router.get("/stats")
async def get_stats():
    """Get DLQ statistics"""
    handler = get_dlq_handler()
    stats = await handler.get_stats()
    return stats


@router.get("/entries", response_model=List[DeadLetterEntry])
async def list_entries(
    status: Optional[DeadLetterStatusEnum] = None,
    domain: Optional[str] = None,
    failure_reason: Optional[FailureReasonEnum] = None,
    limit: int = Query(default=100, le=1000)
):
    """
    List DLQ entries with optional filters.

    Args:
        status: Filter by status
        domain: Filter by domain
        failure_reason: Filter by failure reason
        limit: Maximum entries to return
    """
    handler = get_dlq_handler()

    if status:
        entries = await handler.get_entries_by_status(status, limit)
    elif domain:
        entries = await handler.get_entries_by_domain(domain, limit)
    elif failure_reason:
        entries = await handler.get_entries_by_failure_reason(failure_reason, limit)
    else:
        entries = await handler.get_entries_by_status(DeadLetterStatusEnum.PENDING, limit)

    return entries


@router.get("/pending", response_model=List[DeadLetterEntry])
async def get_pending_entries(
    domain: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get entries ready for retry"""
    handler = get_dlq_handler()
    return await handler.get_pending_entries(limit, domain)


@router.get("/entries/{entry_id}", response_model=DeadLetterEntry)
async def get_entry(entry_id: int):
    """Get a specific DLQ entry by ID"""
    handler = get_dlq_handler()
    entry = await handler.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.patch("/entries/{entry_id}", response_model=DeadLetterEntry)
async def update_entry(entry_id: int, update: DeadLetterUpdate):
    """Update a DLQ entry"""
    handler = get_dlq_handler()
    entry = await handler.update_entry(entry_id, update)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/entries/{entry_id}/resolve", response_model=DeadLetterEntry)
async def resolve_entry(
    entry_id: int,
    notes: Optional[str] = None
):
    """Mark entry as resolved"""
    handler = get_dlq_handler()
    entry = await handler.mark_resolved(entry_id, notes)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/entries/{entry_id}/manual", response_model=DeadLetterEntry)
async def mark_manual(
    entry_id: int,
    notes: Optional[str] = None
):
    """Mark entry as requiring manual intervention"""
    handler = get_dlq_handler()
    entry = await handler.mark_manual(entry_id, notes)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int):
    """Delete a DLQ entry"""
    handler = get_dlq_handler()
    deleted = await handler.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"deleted": True, "entry_id": entry_id}


@router.post("/cleanup")
async def cleanup_old_entries(days: int = Query(default=30, ge=1, le=365)):
    """Remove resolved/abandoned entries older than specified days"""
    handler = get_dlq_handler()
    removed = await handler.cleanup_old_entries(days)
    return {"removed": removed, "days": days}
