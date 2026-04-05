"""
Ontology Package

Provides canonical entity and relationship types, plus shared primitives for the
news intelligence system's property graph ontology.

Usage:
    >>> from news_mcp_common.ontology import EntityType, EntityReference
    >>>
    >>> # Create entity reference
    >>> entity = EntityReference(
    ...     entity_id="US",
    ...     entity_type=EntityType.COUNTRY,
    ...     name="United States"
    ... )
    >>>
    >>> # Validate entity type
    >>> if EntityType.is_mvo_phase1(entity.entity_type):
    ...     print("MVO Phase 1 entity")

Reference:
    - /home/cytrex/userdocs/system-ontology/ (formal ontology design)
    - /home/cytrex/userdocs/system-ontology/IMPLEMENTATION_PLAN_PHASE1.md

Architecture:
    Three-Layer Property Graph Ontology:
    1. Schema Layer (this package): EntityType, RelationshipType enums
    2. Primitives Layer (this package): EntityReference, RelationshipHint, ConfidenceMetadata
    3. Instance Layer (Neo4j): Actual graph nodes and relationships
"""

from .ontology_schema import (
    EntityType,
    RelationshipType,
    REQUIRED_PROPERTIES,
    RECOMMENDED_PROPERTIES,
    ENTITY_ID_PATTERNS,
)

from .shared_primitives import (
    EntityReference,
    RelationshipHint,
    ConfidenceMetadata,
)

__version__ = "0.1.0"

__all__ = [
    # Schema Layer
    "EntityType",
    "RelationshipType",
    "REQUIRED_PROPERTIES",
    "RECOMMENDED_PROPERTIES",
    "ENTITY_ID_PATTERNS",
    # Primitives Layer
    "EntityReference",
    "RelationshipHint",
    "ConfidenceMetadata",
]
