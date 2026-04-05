"""
Priority Queue Models

Phase 6: Scale

Defines priority levels and job queue models for prioritized scraping.
"""
from enum import IntEnum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PriorityLevel(IntEnum):
    """
    Scraping job priority levels.

    Higher values = higher priority.
    """
    CRITICAL = 100   # Breaking news, urgent updates
    HIGH = 75        # Important news, time-sensitive
    NORMAL = 50      # Standard articles
    LOW = 25         # Bulk scraping, archives
    BACKGROUND = 10  # Idle processing, prefetch


class ScrapeJobCreate(BaseModel):
    """Request to create a scrape job"""
    url: str = Field(..., description="URL to scrape")
    priority: PriorityLevel = Field(default=PriorityLevel.NORMAL)
    method: str = Field(default="auto", description="Scraping method: auto, newspaper4k, playwright, etc.")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion callback")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job metadata")

    # Scheduling
    delay_seconds: int = Field(default=0, ge=0, description="Delay before processing")
    max_retries: int = Field(default=3, ge=0, le=10)


class ScrapeJob(BaseModel):
    """Scrape job in the queue"""
    id: str = Field(..., description="Unique job identifier")
    url: str
    priority: PriorityLevel
    method: str

    # State
    status: str = Field(default="pending", description="pending, processing, completed, failed")
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = Field(None, description="When to process (after delay)")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Callbacks
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Result (when completed)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class QueueStats(BaseModel):
    """Priority queue statistics"""
    total_jobs: int = Field(default=0)
    pending_jobs: int = Field(default=0)
    processing_jobs: int = Field(default=0)
    completed_jobs: int = Field(default=0)
    failed_jobs: int = Field(default=0)

    # By priority
    by_priority: Dict[str, int] = Field(default_factory=dict)

    # Performance
    avg_wait_time_seconds: float = Field(default=0.0)
    avg_processing_time_seconds: float = Field(default=0.0)
    jobs_per_minute: float = Field(default=0.0)
