"""
Shared contracts and utilities for news-microservices.

This package provides type-safe contracts that ensure consistent
data structures across service boundaries.
"""

from shared.contracts import (
    ResearchTaskRequest,
    FeedSourceAssessmentParams,
    FactCheckParams,
    TrendAnalysisParams,
    validate_research_request,
    build_assessment_request,
)

__all__ = [
    "ResearchTaskRequest",
    "FeedSourceAssessmentParams",
    "FactCheckParams",
    "TrendAnalysisParams",
    "validate_research_request",
    "build_assessment_request",
]
