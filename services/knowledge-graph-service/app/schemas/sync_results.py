"""
Pydantic schemas for market sync operations.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SyncError(BaseModel):
    """Individual sync error detail."""

    symbol: str = Field(..., description="Asset symbol that failed")
    error: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SyncResult(BaseModel):
    """Result of a market sync operation."""

    sync_id: str = Field(..., description="Unique sync operation identifier")
    status: str = Field(..., description="Sync status: completed, partial, failed")

    # Asset-level metrics
    total_assets: int = Field(..., description="Total assets attempted to sync")
    synced: int = Field(..., description="Number of successfully synced assets")
    failed: int = Field(..., description="Number of failed assets")

    # Neo4j operation metrics
    nodes_created: int = Field(default=0, description="Number of MARKET nodes created")
    nodes_updated: int = Field(default=0, description="Number of MARKET nodes updated")
    relationships_created: int = Field(default=0, description="Number of relationships created")
    relationships_updated: int = Field(default=0, description="Number of relationships updated")

    # Performance metrics
    duration_seconds: float = Field(..., description="Sync operation duration")
    fmp_api_calls_used: int = Field(default=1, description="Number of FMP API calls consumed")

    # Error tracking
    errors: List[SyncError] = Field(default_factory=list, description="List of errors encountered")

    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "sync_id": "sync_20251116_103000_a1b2c3d4",
                "status": "completed",
                "total_assets": 40,
                "synced": 40,
                "failed": 0,
                "nodes_created": 15,
                "nodes_updated": 25,
                "relationships_created": 40,
                "relationships_updated": 0,
                "duration_seconds": 2.457,
                "fmp_api_calls_used": 4,
                "errors": [],
                "timestamp": "2025-11-16T10:30:00Z"
            }
        }


class QuoteUpdateResult(BaseModel):
    """Result of quote price update operation."""

    symbols_requested: List[str] = Field(..., description="Symbols requested for update")
    symbols_updated: int = Field(..., description="Number of symbols successfully updated")
    symbols_failed: int = Field(default=0, description="Number of symbols that failed")

    errors: List[SyncError] = Field(default_factory=list, description="Update errors")

    duration_seconds: float = Field(..., description="Update operation duration")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SectorSyncResult(BaseModel):
    """Result of sector initialization/verification."""

    total_sectors: int = Field(..., description="Total number of sectors")
    sectors_created: int = Field(default=0, description="Number of sectors created")
    sectors_verified: int = Field(default=0, description="Number of existing sectors verified")

    sector_codes: List[str] = Field(..., description="List of sector codes in database")

    duration_seconds: float = Field(..., description="Operation duration")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
