"""
Dead Letter Queue Model

Stores failed scrape jobs for retry or analysis.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class FailureReasonEnum(str, Enum):
    """Categorized failure reasons"""
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    PAYWALL = "paywall"
    EXTRACTION_FAILED = "extraction_failed"
    RATE_LIMITED = "rate_limited"
    CONNECTION_ERROR = "connection_error"
    INVALID_CONTENT = "invalid_content"
    STRUCTURE_CHANGED = "structure_changed"
    UNKNOWN = "unknown"


class DeadLetterStatusEnum(str, Enum):
    """DLQ entry status"""
    PENDING = "pending"        # Waiting for retry
    PROCESSING = "processing"  # Currently being retried
    RESOLVED = "resolved"      # Successfully processed
    ABANDONED = "abandoned"    # Max retries exceeded
    MANUAL = "manual"          # Requires manual intervention


# SQLAlchemy ORM Model
class DeadLetterEntryDB(Base):
    """Database model for dead letter entries"""
    __tablename__ = "dead_letter_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Job identification
    url = Column(String(2048), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    job_id = Column(String(64), nullable=True)  # Original job ID if available

    # Failure information
    failure_reason = Column(SQLEnum(FailureReasonEnum), nullable=False)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, default=dict)  # Stack trace, HTTP status, etc.

    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=5)
    last_retry_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)

    # Status
    status = Column(SQLEnum(DeadLetterStatusEnum), default=DeadLetterStatusEnum.PENDING)

    # Original request
    original_payload = Column(JSON, default=dict)  # Method, headers, etc.

    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Schemas
class DeadLetterCreate(BaseModel):
    """Schema for creating DLQ entry"""
    url: str
    failure_reason: FailureReasonEnum
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = {}
    original_payload: Dict[str, Any] = {}
    retry_count: int = 0
    max_retries: int = 5


class DeadLetterEntry(BaseModel):
    """Full DLQ entry"""
    id: int
    url: str
    domain: str
    job_id: Optional[str] = None
    failure_reason: FailureReasonEnum
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = {}
    retry_count: int
    max_retries: int
    last_retry_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    status: DeadLetterStatusEnum = DeadLetterStatusEnum.PENDING
    original_payload: Dict[str, Any] = {}
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeadLetterUpdate(BaseModel):
    """Schema for updating DLQ entry"""
    status: Optional[DeadLetterStatusEnum] = None
    retry_count: Optional[int] = None
    next_retry_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
