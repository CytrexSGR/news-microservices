"""
Shared Primitives for Ontology

Defines the core Pydantic models for entity references, relationship hints, and confidence metadata.
These primitives serve as the normalization contract across all microservices.

Reference: /home/cytrex/userdocs/system-ontology/04_SHARED_PRIMITIVES.md

Key Design Principles:
1. EntityReference is the canonicalization contract (required: entity_id, entity_type, name)
2. Machine-readable first (symbolic data), generate human reports on-demand
3. Design-time validation via Pydantic (not runtime checks)
4. Type-specific ID strategies enforced via validators
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import re
from pydantic import BaseModel, Field, field_validator, model_validator
from .ontology_schema import EntityType, RelationshipType, ENTITY_ID_PATTERNS


class EntityReference(BaseModel):
    """
    Universal entity reference primitive.

    This is the canonicalization contract. Every entity MUST have:
    - entity_id: Unique identifier (type-specific format)
    - entity_type: One of EntityType enum values
    - name: Human-readable canonical name

    Reference: 04_SHARED_PRIMITIVES.md (lines 61-155)

    Examples:
        >>> # Country entity
        >>> entity = EntityReference(
        ...     entity_id="US",
        ...     entity_type=EntityType.COUNTRY,
        ...     name="United States"
        ... )

        >>> # Company entity
        >>> entity = EntityReference(
        ...     entity_id="TSLA",
        ...     entity_type=EntityType.COMPANY,
        ...     name="Tesla Inc.",
        ...     wikidata_id="Q478214",
        ...     aliases=["Tesla", "Tesla Motors"]
        ... )
    """

    # REQUIRED PROPERTIES
    entity_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for this entity (type-specific format)",
    )
    entity_type: EntityType = Field(
        ..., description="Entity type from canonical ontology"
    )
    name: str = Field(
        ..., min_length=1, description="Canonical human-readable name"
    )

    # OPTIONAL PROPERTIES
    role: Optional[str] = Field(
        None, description="Role of entity in context (e.g., 'attacker', 'target')"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score for this entity reference"
    )
    wikidata_id: Optional[str] = Field(
        None, description="Wikidata Q-ID for cross-referencing"
    )
    aliases: Optional[List[str]] = Field(
        default_factory=list, description="Alternative names for this entity"
    )
    created_at: Optional[datetime] = Field(
        None, description="When this entity was first seen"
    )
    last_seen: Optional[datetime] = Field(
        None, description="When this entity was last seen"
    )
    source_count: int = Field(
        default=1, ge=1, description="Number of sources mentioning this entity"
    )

    @model_validator(mode='after')
    def validate_entity_id_format(self) -> "EntityReference":
        """
        Validate entity_id format based on entity_type.

        Type-specific validation rules (AI-Driven Learning Strategy):
        - COUNTRY: Must be ISO 3166-1 alpha-2 (2 uppercase letters) - STRICT
        - COMPANY: Flexible format - accepts tickers, Wikidata IDs, or semantic names
        - MARKET: Flexible format - accepts market codes or concept names
        - Others: No format restriction

        Philosophy: Only enforce strict validation where entities are static and canonical
        (countries). For dynamic entities (companies, markets), allow AI to learn semantic
        relationships rather than rejecting based on format.
        """
        if self.entity_type == EntityType.COUNTRY:
            # STRICT: Countries are static, canonical entities
            if not re.match(r"^[A-Z]{2}$", self.entity_id):
                raise ValueError(
                    f"COUNTRY entity_id must be ISO 3166-1 alpha-2. "
                    f"Got: '{self.entity_id}'. Examples: 'RU', 'US', 'UA', 'CN'"
                )

        elif self.entity_type == EntityType.COMPANY:
            # FLEXIBLE: Accept tickers (TSLA), Wikidata (Q12345), or semantic names (OpenAI, Crypto_AG)
            # Allowed: alphanumeric, underscore, hyphen, dot, colon (for prefixed IDs like wikidata:Q12345)
            if not re.match(r"^[a-zA-Z0-9_\-\.:]+$", self.entity_id):
                raise ValueError(
                    f"COMPANY entity_id must be alphanumeric (with _, -, ., : allowed). "
                    f"Got: '{self.entity_id}'. "
                    f"Examples: 'TSLA', 'Q12345', 'OpenAI', 'wikidata:Q478214'"
                )

        elif self.entity_type == EntityType.MARKET:
            # FLEXIBLE: Accept market codes (NASDAQ) or concept names (Crypto, Altcoins)
            if not re.match(r"^[a-zA-Z0-9_\-\.]+$", self.entity_id):
                raise ValueError(
                    f"MARKET entity_id must be alphanumeric (with _, -, . allowed). "
                    f"Got: '{self.entity_id}'. "
                    f"Examples: 'NASDAQ', 'NYSE', 'Crypto', 'Forex_EUR_USD'"
                )

        return self

    @field_validator("wikidata_id")
    @classmethod
    def validate_wikidata_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate Wikidata Q-ID format (Q followed by digits)."""
        if v is not None and not re.match(r"^Q\d+$", v):
            raise ValueError(
                f"wikidata_id must match format 'Q<digits>'. "
                f"Got: '{v}'. Example: 'Q30' (United States)"
            )
        return v

    @model_validator(mode="after")
    def validate_aliases_dedup(self) -> "EntityReference":
        """Ensure canonical name is not duplicated in aliases."""
        if self.aliases and self.name in self.aliases:
            # Remove canonical name from aliases (avoid redundancy)
            self.aliases = [alias for alias in self.aliases if alias != self.name]
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for JSON serialization)."""
        return self.model_dump(exclude_none=True)

    def to_graph_node(self) -> Dict[str, Any]:
        """
        Convert to Neo4j node properties.

        Returns:
            Dictionary suitable for Neo4j CREATE/MERGE statement
        """
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "wikidata_id": self.wikidata_id,
            "aliases": self.aliases or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "source_count": self.source_count,
        }

    def to_graph_label(self) -> str:
        """
        Get Neo4j node label for this entity.

        Returns:
            Node label string (e.g., "Entity:COMPANY")
        """
        return f"Entity:{self.entity_type.value}"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.entity_type.value}:{self.entity_id} ({self.name})"

    def __hash__(self) -> int:
        """Hash based on entity_id and entity_type (for deduplication)."""
        return hash((self.entity_id, self.entity_type))


class RelationshipHint(BaseModel):
    """
    Relationship hint for graph construction.

    Represents a potential relationship between two entities extracted from text.
    OSS Validator will verify before Neo4j write.

    Reference: 04_SHARED_PRIMITIVES.md (lines 256-337)

    Examples:
        >>> # Company impacts stock market
        >>> hint = RelationshipHint(
        ...     source=EntityReference(entity_id="TSLA", entity_type=EntityType.COMPANY, name="Tesla Inc."),
        ...     target=EntityReference(entity_id="NASDAQ", entity_type=EntityType.MARKET, name="NASDAQ"),
        ...     relationship_type=RelationshipType.IMPACTS_STOCK,
        ...     confidence=0.85,
        ...     evidence="Tesla stock price surged 12% on NASDAQ."
        ... )
    """

    source: EntityReference = Field(..., description="Source entity")
    target: EntityReference = Field(..., description="Target entity")
    relationship_type: RelationshipType = Field(
        ..., description="Relationship type from canonical ontology"
    )
    confidence: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Confidence in this relationship"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional relationship properties"
    )
    evidence: Optional[str] = Field(
        None, description="Text evidence supporting this relationship"
    )
    bidirectional: bool = Field(
        default=False,
        description="Whether this relationship is bidirectional (source ↔ target)",
    )

    @model_validator(mode="after")
    def validate_relationship_logic(self) -> "RelationshipHint":
        """Validate relationship makes logical sense."""
        # Example: LOCATED_IN requires source to be physical entity
        if self.relationship_type == RelationshipType.LOCATED_IN:
            valid_source_types = [
                EntityType.COMPANY,
                EntityType.CRITICAL_INFRASTRUCTURE,
                EntityType.WEAPON_SYSTEM,
                EntityType.ORGANIZATION,
                EntityType.PERSON,
            ]
            if self.source.entity_type not in valid_source_types:
                raise ValueError(
                    f"LOCATED_IN relationship requires physical entity as source. "
                    f"Got: {self.source.entity_type.value}"
                )

            valid_target_types = [EntityType.LOCATION, EntityType.COUNTRY]
            if self.target.entity_type not in valid_target_types:
                raise ValueError(
                    f"LOCATED_IN relationship requires location/country as target. "
                    f"Got: {self.target.entity_type.value}"
                )

        return self

    def to_cypher_params(self) -> Dict[str, Any]:
        """
        Convert to Cypher query parameters for Neo4j.

        Returns:
            Dictionary suitable for Neo4j relationship creation
        """
        return {
            "source_id": self.source.entity_id,
            "source_type": self.source.entity_type.value,
            "relationship_type": self.relationship_type.value,
            "target_id": self.target.entity_id,
            "target_type": self.target.entity_type.value,
            "confidence": self.confidence,
            "properties": self.properties,
            "evidence": self.evidence,
            "bidirectional": self.bidirectional,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        arrow = "↔" if self.bidirectional else "→"
        return (
            f"{self.source.name} {arrow} "
            f"[{self.relationship_type.value}] {arrow} "
            f"{self.target.name} "
            f"(confidence: {self.confidence:.2f})"
        )


class ConfidenceMetadata(BaseModel):
    """
    Confidence metadata for findings and relationships.

    Tracks quality metrics across the multi-tier extraction pipeline.

    Reference: 04_SHARED_PRIMITIVES.md (lines 339-415)

    Examples:
        >>> # High-confidence entity extraction
        >>> metadata = ConfidenceMetadata(
        ...     overall_confidence=0.92,
        ...     supporting_agents=["claude-3.5-sonnet", "gpt-4"],
        ...     evidence_count=3,
        ...     source_count=2,
        ...     extraction_confidence=0.95,
        ...     validation_confidence=0.89,
        ...     is_validated=True,
        ...     validation_method="OSS_cross_check"
        ... )
        >>> metadata.derive_uncertainty()
        'low'
    """

    overall_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score"
    )
    supporting_agents: Optional[List[str]] = Field(
        default_factory=list,
        description="List of LLM agents that contributed to this finding",
    )
    evidence_count: int = Field(
        default=1, ge=1, description="Number of pieces of evidence"
    )
    source_count: int = Field(
        default=1, ge=1, description="Number of independent sources"
    )
    extraction_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence from extraction tier"
    )
    validation_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence from validation tier"
    )
    is_validated: bool = Field(
        default=False, description="Whether OSS validation passed"
    )
    validation_method: Optional[str] = Field(
        None, description="Method used for validation (e.g., 'OSS_cross_check')"
    )

    def derive_uncertainty(self) -> str:
        """
        Derive uncertainty level from confidence score.

        Returns:
            "low", "moderate", or "high" uncertainty
        """
        if self.overall_confidence >= 0.8:
            return "low"
        elif self.overall_confidence >= 0.5:
            return "moderate"
        else:
            return "high"

    def should_trigger_review(self, threshold: float = 0.6) -> bool:
        """
        Determine if this finding should trigger human review.

        Args:
            threshold: Minimum confidence to avoid review (default: 0.6)

        Returns:
            True if confidence is below threshold
        """
        return self.overall_confidence < threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for JSON serialization)."""
        result = self.model_dump(exclude_none=True)
        result["uncertainty"] = self.derive_uncertainty()
        return result

    def __str__(self) -> str:
        """Human-readable string representation."""
        uncertainty = self.derive_uncertainty()
        validated = "✓" if self.is_validated else "✗"
        return (
            f"Confidence: {self.overall_confidence:.2f} "
            f"(uncertainty: {uncertainty}, validated: {validated})"
        )
