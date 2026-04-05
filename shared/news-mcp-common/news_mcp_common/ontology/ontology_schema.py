"""
Ontology Schema Definition

Defines the canonical entity and relationship types for the news intelligence system.
This module provides enum-based type safety and validation for the property graph ontology.

Reference: /home/cytrex/userdocs/system-ontology/01_ENTITY_TYPES.md
Reference: /home/cytrex/userdocs/system-ontology/02_RELATIONSHIP_TYPES.md

MVO Phase 1 Focus:
- 8 Entity Types (COMPANY, CRITICAL_INFRASTRUCTURE, WEAPON_SYSTEM, COUNTRY, ORGANIZATION, PERSON, LOCATION, MARKET)
- 8 Relationship Types (DISRUPTS_*, IMPACTS_STOCK, ATTACKS, VIOLATES_IHL, LOCATED_IN, WORKS_FOR, RELATED_TO)
"""

from enum import Enum
from typing import List


class EntityType(str, Enum):
    """
    Canonical entity types from formal ontology (MVO Phase 1).

    Reference: 01_ENTITY_TYPES.md

    Each entity type has specific ID strategies:
    - COUNTRY: ISO 3166-1 alpha-2 (e.g., "US", "RU", "UA")
    - COMPANY: Stock ticker preferred, fallback to normalized name
    - PERSON: Wikidata Q-ID preferred, fallback to normalized name
    - LOCATION: Geonames ID preferred, fallback to lat/lon
    - ORGANIZATION: Wikidata Q-ID preferred, fallback to normalized name
    - CRITICAL_INFRASTRUCTURE: Custom ID based on type + location
    - WEAPON_SYSTEM: NATO/military designation preferred
    - MARKET: Market identifier (e.g., "NASDAQ", "NYSE", "LSE")
    """

    # MVO Phase 1 - Core Entity Types
    COMPANY = "COMPANY"
    CRITICAL_INFRASTRUCTURE = "CRITICAL_INFRASTRUCTURE"
    WEAPON_SYSTEM = "WEAPON_SYSTEM"
    COUNTRY = "COUNTRY"
    ORGANIZATION = "ORGANIZATION"
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    MARKET = "MARKET"

    # Fallback types
    UNKNOWN = "UNKNOWN"
    CONCEPT = "CONCEPT"

    @classmethod
    def get_mvo_phase1_types(cls) -> List["EntityType"]:
        """Get MVO Phase 1 entity types (excludes UNKNOWN and CONCEPT)."""
        return [
            cls.COMPANY,
            cls.CRITICAL_INFRASTRUCTURE,
            cls.WEAPON_SYSTEM,
            cls.COUNTRY,
            cls.ORGANIZATION,
            cls.PERSON,
            cls.LOCATION,
            cls.MARKET,
        ]

    @classmethod
    def is_mvo_phase1(cls, entity_type: "EntityType") -> bool:
        """Check if entity type is part of MVO Phase 1."""
        return entity_type in cls.get_mvo_phase1_types()


class RelationshipType(str, Enum):
    """
    Canonical relationship types from formal ontology (MVO Phase 1).

    Reference: 02_RELATIONSHIP_TYPES.md

    Categories:
    - Intelligence: DISRUPTS_OPERATIONS, DISRUPTS_SUPPLY_CHAIN, IMPACTS_STOCK, ATTACKS, VIOLATES_IHL
    - Social: WORKS_FOR
    - Geographic: LOCATED_IN
    - Generic: RELATED_TO (fallback)
    """

    # Intelligence Relationships (Impact & Threat)
    DISRUPTS_OPERATIONS = "DISRUPTS_OPERATIONS"
    DISRUPTS_SUPPLY_CHAIN = "DISRUPTS_SUPPLY_CHAIN"
    IMPACTS_STOCK = "IMPACTS_STOCK"
    ATTACKS = "ATTACKS"
    VIOLATES_IHL = "VIOLATES_IHL"

    # Social Relationships
    WORKS_FOR = "WORKS_FOR"

    # Geographic Relationships
    LOCATED_IN = "LOCATED_IN"

    # Generic Fallback
    RELATED_TO = "RELATED_TO"

    @classmethod
    def get_mvo_phase1_types(cls) -> List["RelationshipType"]:
        """Get MVO Phase 1 relationship types (excludes RELATED_TO)."""
        return [
            cls.DISRUPTS_OPERATIONS,
            cls.DISRUPTS_SUPPLY_CHAIN,
            cls.IMPACTS_STOCK,
            cls.ATTACKS,
            cls.VIOLATES_IHL,
            cls.LOCATED_IN,
            cls.WORKS_FOR,
        ]

    @classmethod
    def is_mvo_phase1(cls, relationship_type: "RelationshipType") -> bool:
        """Check if relationship type is part of MVO Phase 1."""
        return relationship_type in cls.get_mvo_phase1_types()

    @classmethod
    def get_intelligence_types(cls) -> List["RelationshipType"]:
        """Get intelligence-focused relationship types."""
        return [
            cls.DISRUPTS_OPERATIONS,
            cls.DISRUPTS_SUPPLY_CHAIN,
            cls.IMPACTS_STOCK,
            cls.ATTACKS,
            cls.VIOLATES_IHL,
        ]

    @classmethod
    def is_directional(cls, relationship_type: "RelationshipType") -> bool:
        """Check if relationship type is directional (source → target matters)."""
        # All intelligence relationships are directional
        directional = [
            cls.DISRUPTS_OPERATIONS,
            cls.DISRUPTS_SUPPLY_CHAIN,
            cls.IMPACTS_STOCK,
            cls.ATTACKS,
            cls.VIOLATES_IHL,
            cls.WORKS_FOR,
        ]
        return relationship_type in directional


# Constants for validation

REQUIRED_PROPERTIES: List[str] = [
    "entity_id",
    "entity_type",
    "name",
]
"""Required properties for all EntityReference instances."""

RECOMMENDED_PROPERTIES: List[str] = [
    "wikidata_id",
    "aliases",
    "confidence",
    "source_count",
    "created_at",
    "last_seen",
]
"""Recommended properties for EntityReference instances (improve quality)."""

# Entity ID format patterns (for validation)
ENTITY_ID_PATTERNS = {
    EntityType.COUNTRY: r"^[A-Z]{2}$",  # ISO 3166-1 alpha-2
    EntityType.COMPANY: r"^[A-Z]{1,5}$",  # Stock ticker (1-5 uppercase letters)
    # Additional patterns can be added for other entity types
}
"""Regex patterns for entity_id validation by entity type."""
