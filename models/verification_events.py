"""
Verification Events and DIA Core Models

This module contains all Pydantic models for the DIA (Dynamic Intelligence
Augmentation) system, including:
- Event schemas (verification.required, verification.completed)
- Diagnosis models (ProblemHypothesis)
- Evidence models (EvidencePackage, ToolExecutionResult)

Related: ADR-018 (DIA-Planner & Verifier)
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4


# ============================================================================
# Event Schemas
# ============================================================================

class VerificationRequiredEvent(BaseModel):
    """
    Event published when analysis requires verification.

    Published by: content-analysis-service (UQ Module)
    Consumed by: llm-orchestrator-service (DIA Planner)

    Example:
        {
          "event_id": "123e4567-e89b-12d3-a456-426614174000",
          "event_type": "verification.required",
          "analysis_result_id": "987fcdeb-51a2-43f1-9e8d-123456789abc",
          "article_title": "Tesla Reports Record Q3 Earnings",
          "article_content": "Tesla announced record profits of $5 billion...",
          "uq_confidence_score": 0.45,
          "uncertainty_factors": [
            "Low confidence in claim accuracy",
            "Numerical claim lacks verification"
          ]
        }
    """

    # Identifiers
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(default="verification.required")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Analysis Context
    analysis_result_id: UUID = Field(
        description="ID of the analysis result that requires verification"
    )
    article_id: UUID = Field(
        description="ID of the original article"
    )

    # Original Content
    article_title: str = Field(
        description="Article title for context"
    )
    article_content: str = Field(
        description="Full article text (required for diagnosis)"
    )
    article_url: str = Field(
        description="Source URL"
    )
    article_published_at: datetime = Field(
        description="Publication timestamp"
    )

    # UQ Sensor Output
    uq_confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="UQ confidence score (lower = more uncertain)"
    )
    uncertainty_factors: List[str] = Field(
        description="Uncertainty factors identified by UQ sensor",
        min_items=1
    )

    # Analysis Results (before verification)
    analysis_summary: Optional[str] = Field(
        default=None,
        description="Current analysis summary (may be incorrect)"
    )
    extracted_entities: Optional[List[Dict]] = Field(
        default=None,
        description="Current entities (may contain errors)"
    )
    category_analysis: Optional[Dict] = Field(
        default=None,
        description="Current category/sentiment (may be wrong)"
    )

    # Priority
    priority: str = Field(
        default="medium",
        description="Verification priority based on article importance"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "verification.required",
                "timestamp": "2025-10-24T10:00:00Z",
                "analysis_result_id": "987fcdeb-51a2-43f1-9e8d-123456789abc",
                "article_id": "456789ab-cdef-0123-4567-89abcdef0123",
                "article_title": "Tesla Reports Record Q3 Earnings",
                "article_content": "Tesla announced record profits of $5 billion...",
                "article_url": "https://example.com/tesla-earnings",
                "article_published_at": "2025-10-24T08:00:00Z",
                "uq_confidence_score": 0.45,
                "uncertainty_factors": [
                    "Low confidence in claim accuracy",
                    "Numerical claim lacks verification",
                    "Inconsistent with typical ranges"
                ],
                "analysis_summary": "Tesla achieved record profits in Q3 2024",
                "extracted_entities": [],
                "category_analysis": {"sentiment": "positive"},
                "priority": "high"
            }
        }


class VerificationCompletedEvent(BaseModel):
    """
    Event published when verification is completed.

    Published by: llm-orchestrator-service (DIA Corrector)
    Consumed by: content-analysis-service (to update results)
    """

    # Identifiers
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(default="verification.completed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Links back to request
    original_event_id: UUID = Field(
        description="ID of the original verification.required event"
    )
    analysis_result_id: UUID = Field(
        description="ID of the analysis result that was verified"
    )

    # Verification Results
    hypothesis_confirmed: bool = Field(
        description="Was the problem hypothesis confirmed?"
    )
    corrections_applied: bool = Field(
        description="Were corrections applied to the analysis?"
    )

    # Updated Analysis
    corrected_summary: Optional[str] = Field(
        default=None,
        description="Corrected analysis summary"
    )
    corrected_entities: Optional[List[Dict]] = Field(
        default=None,
        description="Corrected entities"
    )
    corrected_category_analysis: Optional[Dict] = Field(
        default=None,
        description="Corrected category/sentiment"
    )

    # Confidence
    new_uq_confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Updated UQ confidence after verification"
    )

    # Evidence
    source_citations: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Sources used for verification"
    )

    # Metadata
    verification_duration_ms: int = Field(
        description="Time taken for verification (milliseconds)"
    )


# ============================================================================
# Diagnosis Models (Stage 1)
# ============================================================================

class ProblemHypothesis(BaseModel):
    """
    Precise diagnosis of what is uncertain and why.

    Generated by: DIA Planner - Stage 1 (Root Cause Analysis)
    Consumed by: DIA Planner - Stage 2 (Plan Generation)

    Example:
        {
          "primary_concern": "The financial figure '$5 billion' appears to be a factual error",
          "affected_content": "Tesla announced record profits of $5 billion...",
          "hypothesis_type": "factual_error",
          "confidence": 0.85,
          "reasoning": "Historical Tesla quarterly profits typically range $3-4.5B...",
          "verification_approach": "Cross-reference with SEC filings and financial databases"
        }
    """

    primary_concern: str = Field(
        description="The main issue identified (specific and actionable)",
        examples=[
            "The financial figure '$5 billion' in the earnings claim appears to be a factual error",
            "Entity 'John Smith' is ambiguous - could refer to CEO or Board Member",
            "Temporal inconsistency: Event dated 'last week' but article published 3 months ago"
        ]
    )

    affected_content: str = Field(
        description="The specific excerpt from article that is problematic"
    )

    hypothesis_type: str = Field(
        description="Classification of the problem",
        examples=[
            "factual_error",
            "entity_ambiguity",
            "temporal_inconsistency",
            "missing_context",
            "contradictory_claims",
            "source_reliability_issue"
        ]
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description="How confident is this diagnosis (0.0-1.0)"
    )

    reasoning: str = Field(
        description="Why this is considered the root cause"
    )

    verification_approach: str = Field(
        description="High-level approach to verify this hypothesis",
        examples=[
            "Cross-reference with authoritative financial databases",
            "Search for entity clarification in corporate records",
            "Verify event timeline against news archives"
        ]
    )


# ============================================================================
# Evidence Models (Verifier Output)
# ============================================================================

class ToolExecutionResult(BaseModel):
    """
    Result from a single tool execution.

    Example:
        {
          "tool_name": "perplexity_deep_search",
          "tool_parameters": {"query": "Tesla Q3 2024 earnings"},
          "success": true,
          "execution_time_ms": 1200,
          "result_data": {"answer": "...", "sources": [...]},
          "source_citations": ["https://ir.tesla.com/..."],
          "confidence": 0.95
        }
    """

    tool_name: str = Field(description="Tool that was executed")
    tool_parameters: Dict = Field(description="Parameters used")

    success: bool = Field(description="Did tool execute successfully")
    execution_time_ms: int = Field(description="Execution time in milliseconds")

    result_data: Optional[Dict] = Field(
        default=None,
        description="Tool output data (structure varies by tool)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )

    source_citations: List[str] = Field(
        default_factory=list,
        description="Source URLs/references from tool result"
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this evidence (0.0-1.0)"
    )


class EvidencePackage(BaseModel):
    """
    Complete evidence collected during verification.

    Generated by: DIA Verifier
    Consumed by: DIA Corrector

    Example:
        {
          "package_id": "pkg-xyz789",
          "verification_request_id": "a1b2c3d4-...",
          "hypothesis_confirmed": true,
          "confidence_score": 0.97,
          "key_findings": ["Official SEC filing reports $4.194B", "..."],
          "corrected_facts": {
            "Tesla Q3 2024 profit": {
              "original": "$5 billion",
              "corrected": "$4.194 billion",
              "source": "Tesla Q3 2024 Form 10-Q (SEC Filing)"
            }
          }
        }
    """

    # Identifiers
    package_id: UUID = Field(default_factory=uuid4)
    verification_request_id: UUID = Field(
        description="Links back to original verification request"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Original Context
    problem_hypothesis: ProblemHypothesis = Field(
        description="The hypothesis that was tested"
    )
    verification_plan: Dict = Field(
        description="The plan that was executed (VerificationPlan from adversarial_test_case.py)"
    )

    # Execution Results
    tool_executions: List[ToolExecutionResult] = Field(
        description="Results from all tool executions"
    )

    total_execution_time_ms: int = Field(
        description="Total time for all verifications"
    )

    # Evidence Summary
    hypothesis_confirmed: bool = Field(
        description="Was the problem hypothesis confirmed by evidence?"
    )

    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence in collected evidence (0.0-1.0)"
    )

    key_findings: List[str] = Field(
        description="Bullet-point summary of critical findings"
    )

    corrected_facts: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Map of fact_name → {original, corrected, source}",
        examples=[{
            "Tesla Q3 2024 profit": {
                "original": "$5 billion",
                "corrected": "$4.194 billion",
                "source": "Tesla Q3 2024 10-Q SEC Filing",
                "source_url": "https://www.sec.gov/..."
            }
        }]
    )

    source_citations: List[Dict[str, str]] = Field(
        default_factory=list,
        description="All authoritative sources consulted",
        examples=[[
            {
                "source": "Tesla Investor Relations",
                "url": "https://ir.tesla.com/q3-2024-earnings",
                "reliability": "primary"
            }
        ]]
    )

    # Quality Metrics
    verification_quality: Dict[str, float] = Field(
        default_factory=dict,
        description="Quality metrics for this verification",
        examples=[{
            "source_reliability": 0.95,
            "evidence_consistency": 0.92,
            "coverage_completeness": 0.88
        }]
    )


# ============================================================================
# Helper Functions
# ============================================================================

def create_verification_required_event(
    analysis_result_id: UUID,
    article_id: UUID,
    article_title: str,
    article_content: str,
    article_url: str,
    article_published_at: datetime,
    uq_confidence_score: float,
    uncertainty_factors: List[str],
    analysis_summary: Optional[str] = None,
    extracted_entities: Optional[List[Dict]] = None,
    category_analysis: Optional[Dict] = None,
    priority: str = "medium"
) -> VerificationRequiredEvent:
    """
    Helper to create verification.required event.

    Usage:
        event = create_verification_required_event(
            analysis_result_id=result.id,
            article_id=article.id,
            article_title=article.title,
            article_content=article.content,
            article_url=article.url,
            article_published_at=article.published_at,
            uq_confidence_score=0.45,
            uncertainty_factors=["Low confidence in claim accuracy"]
        )
    """
    return VerificationRequiredEvent(
        analysis_result_id=analysis_result_id,
        article_id=article_id,
        article_title=article_title,
        article_content=article_content,
        article_url=article_url,
        article_published_at=article_published_at,
        uq_confidence_score=uq_confidence_score,
        uncertainty_factors=uncertainty_factors,
        analysis_summary=analysis_summary,
        extracted_entities=extracted_entities,
        category_analysis=category_analysis,
        priority=priority
    )


__all__ = [
    "VerificationRequiredEvent",
    "VerificationCompletedEvent",
    "ProblemHypothesis",
    "ToolExecutionResult",
    "EvidencePackage",
    "create_verification_required_event"
]
