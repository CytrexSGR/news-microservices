"""HTTP clients for backend services."""

from .content_analysis import ContentAnalysisClient
from .entity_canon import EntityCanonClient
from .intelligence import IntelligenceClient
from .narrative import NarrativeClient

# NOTE: OSINTClient removed 2026-01-03 - osint-service was archived (placeholder only)

__all__ = [
    "ContentAnalysisClient",
    "EntityCanonClient",
    "IntelligenceClient",
    "NarrativeClient",
]
