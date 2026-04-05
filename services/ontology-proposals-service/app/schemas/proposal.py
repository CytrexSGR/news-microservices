"""Pydantic schemas for ontology proposals."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ProposalCreate(BaseModel):
    """Schema for creating a new proposal."""

    proposal_id: str = Field(..., description="Unique proposal identifier")
    change_type: str = Field(..., description="Type of change (NEW_ENTITY, NEW_RELATIONSHIP, etc.)")
    severity: str = Field(..., description="Severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    title: str = Field(..., max_length=500, description="Proposal title")
    description: Optional[str] = Field(None, description="Detailed description")
    definition: Optional[str] = Field(None, description="Formal definition")
    evidence: Optional[Any] = Field(None, description="Supporting evidence (JSONB)")
    pattern_query: Optional[str] = Field(None, description="Query pattern that detected this")
    occurrence_count: Optional[int] = Field(None, description="Number of occurrences")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score (0-1)")
    confidence_factors: Optional[Any] = Field(None, description="Confidence factors (JSONB)")
    validation_checks: Optional[Any] = Field(None, description="Validation results (JSONB)")
    impact_analysis: Optional[Any] = Field(None, description="Impact analysis (JSONB)")
    status: Optional[str] = Field(default="PENDING", description="Proposal status")

    class Config:
        json_schema_extra = {
            "example": {
                "proposal_id": "OSS_20251110_120000_test001",
                "change_type": "NEW_ENTITY",
                "severity": "HIGH",
                "title": "New entity type: TechnologicalInnovation",
                "description": "Detected recurring pattern of technology/innovation mentions...",
                "definition": "Entity representing technological innovations and breakthroughs...",
                "evidence": {
                    "sample_mentions": ["AI breakthrough", "quantum computing"],
                    "article_ids": ["art_001", "art_002"]
                },
                "occurrence_count": 157,
                "confidence": 0.89
            }
        }


class ProposalResponse(BaseModel):
    """Schema for proposal response."""

    success: bool = Field(..., description="Whether operation succeeded")
    proposal_id: str = Field(..., description="Proposal identifier")
    message: Optional[str] = Field(None, description="Optional message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "proposal_id": "OSS_20251110_120000_test001",
                "message": "Proposal created successfully"
            }
        }
