"""OSS Data Models"""
from app.models.proposal import (
    OntologyChangeProposal,
    ChangeType,
    Severity,
    Evidence,
    ImpactAnalysis,
    AnalysisResult
)

__all__ = [
    "OntologyChangeProposal",
    "ChangeType",
    "Severity",
    "Evidence",
    "ImpactAnalysis",
    "AnalysisResult"
]
