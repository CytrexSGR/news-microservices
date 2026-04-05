"""
Common shared primitives and utilities for News Microservices.

This package contains reusable components used across all Intelligence modules.
"""

from .shared_primitives import (
    EntityReference,
    RelationshipHint,
    TemporalContext,
    ConfidenceMetadata,
    ActionRecommendation,
    RiskAssessment,
    GraphTriplet,
)

__all__ = [
    "EntityReference",
    "RelationshipHint",
    "TemporalContext",
    "ConfidenceMetadata",
    "ActionRecommendation",
    "RiskAssessment",
    "GraphTriplet",
]
