"""
Shared Primitives - System Ontology

Reusable base components for consistent symbolic modeling across all Intelligence modules.

Core Principle: **Define once, use everywhere.**

This module provides 7 core primitives:
1. EntityReference - Universal entity reference
2. RelationshipHint - Graph relationship suggestions
3. TemporalContext - Standardized temporal metadata
4. ConfidenceMetadata - Confidence tracking
5. ActionRecommendation - Actionable intelligence
6. RiskAssessment - Structured risk evaluation
7. GraphTriplet - Standard graph data structure

All primitives are graph-ready with `to_graph_*()` methods for Neo4j ingestion.
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ============================================================================
# 1. EntityReference
# ============================================================================

class EntityReference(BaseModel):
    """
    Universal entity reference primitive.

    Used across ALL Intelligence modules to reference entities consistently.
    Maps directly to Neo4j nodes.

    Examples:
        EntityReference(entity_id="RU", entity_type="COUNTRY", role="aggressor")
        EntityReference(entity_id="EUR_USD", entity_type="FOREX_PAIR", role="monitor_target")
        EntityReference(entity_id="UNRWA", entity_type="ORGANIZATION", role="humanitarian_actor")
    """

    # Core identification (REQUIRED)
    entity_id: str = Field(
        ...,
        description="Unique entity identifier. Use ISO codes where applicable: "
                    "Countries: ISO 3166-1 alpha-2 (e.g., 'RU', 'UA', 'US'). "
                    "Markets: Normalized codes (e.g., 'EUR_USD', 'CRUDE_OIL', 'BTC_USD'). "
                    "Organizations: Canonical names or acronyms (e.g., 'UNRWA', 'NATO', 'UN')."
    )

    entity_type: str = Field(
        ...,
        description="Entity type classification. Common values: "
                    "'COUNTRY', 'ORGANIZATION', 'PERSON', 'LOCATION', 'MARKET', "
                    "'FOREX_PAIR', 'COMMODITY', 'CRYPTO', 'INDEX', 'EVENT', "
                    "'MILITARY_UNIT', 'POLITICAL_ENTITY', 'CIVILIAN_GROUP'. "
                    "Use descriptive strings."
    )

    # Contextual role (OPTIONAL)
    role: Optional[str] = Field(
        None,
        description="Entity role in context. Common values: "
                    "'aggressor', 'defender', 'affected_party', 'neutral', "
                    "'monitor_target', 'threat_source', 'aid_recipient', "
                    "'policy_actor', 'violator', 'witness'. Use descriptive strings."
    )

    # Additional metadata (OPTIONAL)
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence in entity identification/role (0.0-1.0)"
    )

    wikidata_id: Optional[str] = Field(
        None,
        description="Wikidata Q-ID for entity linking (e.g., 'Q30' for United States)"
    )

    aliases: Optional[list[str]] = Field(
        default_factory=list,
        description="Alternative names/identifiers for entity (e.g., ['USA', 'US', 'United States'])"
    )

    metadata: Optional[dict] = Field(
        None,
        description="Additional domain-specific properties (e.g., {'change_percentage': 2.5, 'alignment': 'SUPPORTIVE'})"
    )

    # Graph integration
    def to_graph_node(self) -> dict:
        """Convert to Neo4j node properties."""
        node_props = {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "role": self.role,
            "confidence": self.confidence,
            "wikidata_id": self.wikidata_id,
            "aliases": self.aliases or []
        }
        # Merge metadata if present
        if self.metadata:
            node_props.update(self.metadata)
        return node_props

    def to_graph_label(self) -> str:
        """Get Neo4j node label."""
        # Convert FOREX_PAIR → ForexPair, COUNTRY → Country
        return self.entity_type.replace("_", " ").title().replace(" ", "")


# ============================================================================
# 2. RelationshipHint
# ============================================================================

class RelationshipHint(BaseModel):
    """
    Relationship hint for graph construction.

    Suggests relationships between entities without creating them directly.
    Knowledge Graph Service decides whether to create based on confidence.

    Examples:
        RelationshipHint(
            source=EntityReference(entity_id="RU", entity_type="COUNTRY"),
            relationship_type="ATTACKS",
            target=EntityReference(entity_id="UA", entity_type="COUNTRY"),
            confidence=0.95
        )
    """

    # Relationship endpoints (REQUIRED)
    source: EntityReference = Field(
        ...,
        description="Source entity in relationship (subject)"
    )

    relationship_type: str = Field(
        ...,
        description="Relationship type. Common values: "
                    "'ATTACKS', 'VIOLATES_IHL', 'AFFECTS_REGIONALLY', 'IMPACTS_MARKET', "
                    "'INFLUENCES_POLICY', 'THREATENS', 'OCCURS_AT', 'WORKS_FOR', "
                    "'MEMBER_OF', 'LOCATED_IN', 'BORDERS', 'COOPERATES_WITH'. "
                    "Use descriptive verb phrases in UPPER_SNAKE_CASE."
    )

    target: EntityReference = Field(
        ...,
        description="Target entity in relationship (object)"
    )

    # Relationship metadata (OPTIONAL)
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence in relationship existence (0.0-1.0)"
    )

    properties: Optional[dict] = Field(
        default_factory=dict,
        description="Additional relationship properties (severity, impact, etc.)"
    )

    evidence: Optional[str] = Field(
        None,
        description="Evidence supporting this relationship (short excerpt)"
    )

    bidirectional: bool = Field(
        default=False,
        description="If True, create reverse relationship as well (e.g., BORDERS)"
    )

    # Graph integration
    def to_cypher_params(self) -> dict:
        """Convert to Cypher query parameters."""
        return {
            "source_id": self.source.entity_id,
            "source_type": self.source.entity_type,
            "relationship_type": self.relationship_type,
            "target_id": self.target.entity_id,
            "target_type": self.target.entity_type,
            "confidence": self.confidence,
            "properties": self.properties,
            "evidence": self.evidence
        }


# ============================================================================
# 3. TemporalContext
# ============================================================================

class TemporalContext(BaseModel):
    """
    Temporal context for events, findings, and relationships.

    Provides standardized time tracking across all Intelligence modules.

    Examples:
        TemporalContext(event_timestamp=datetime.utcnow(), duration="SHORT_TERM")
        TemporalContext(valid_from=datetime(2025, 11, 1), valid_to=datetime(2025, 11, 10))
    """

    # Event timing (OPTIONAL - at least one should be provided)
    event_timestamp: Optional[datetime] = Field(
        None,
        description="When the event occurred (for point-in-time events)"
    )

    event_start: Optional[datetime] = Field(
        None,
        description="Start of event (for ongoing/long-duration events)"
    )

    event_end: Optional[datetime] = Field(
        None,
        description="End of event (if known)"
    )

    # Validity period
    valid_from: Optional[datetime] = Field(
        None,
        description="When this finding/relationship became valid"
    )

    valid_to: Optional[datetime] = Field(
        None,
        description="When this finding/relationship expires (if applicable)"
    )

    # Duration estimation
    duration: Optional[str] = Field(
        None,
        description="Estimated duration. Common values: "
                    "'IMMEDIATE', 'SHORT_TERM' (hours-days), 'MEDIUM_TERM' (weeks-months), "
                    "'LONG_TERM' (months-years), 'PERMANENT'. Use descriptive strings."
    )

    # Temporal properties
    is_ongoing: bool = Field(
        default=False,
        description="Is this event/situation currently ongoing?"
    )

    is_historical: bool = Field(
        default=False,
        description="Is this a historical event (vs. current/future)?"
    )

    recurrence: Optional[str] = Field(
        None,
        description="Recurrence pattern if applicable: 'daily', 'weekly', 'sporadic', 'one-time'"
    )

    # Graph integration
    def to_graph_properties(self) -> dict:
        """Convert to Neo4j temporal properties."""
        props = {}
        if self.event_timestamp:
            props["event_timestamp"] = self.event_timestamp.isoformat()
        if self.event_start:
            props["event_start"] = self.event_start.isoformat()
        if self.event_end:
            props["event_end"] = self.event_end.isoformat()
        if self.valid_from:
            props["valid_from"] = self.valid_from.isoformat()
        if self.valid_to:
            props["valid_to"] = self.valid_to.isoformat()
        if self.duration:
            props["duration"] = self.duration
        props["is_ongoing"] = self.is_ongoing
        props["is_historical"] = self.is_historical
        if self.recurrence:
            props["recurrence"] = self.recurrence
        return props


# ============================================================================
# 4. ConfidenceMetadata
# ============================================================================

class ConfidenceMetadata(BaseModel):
    """
    Confidence metadata for findings and relationships.

    Tracks confidence scores, supporting evidence, and validation status.

    Examples:
        ConfidenceMetadata(
            overall_confidence=0.92,
            supporting_agents=["CONFLICT_EVENT_ANALYST", "IHL_SPECIALIST"],
            evidence_count=5
        )
    """

    # Confidence scoring (REQUIRED)
    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0.0-1.0)"
    )

    # Supporting evidence (OPTIONAL)
    supporting_agents: Optional[List[str]] = Field(
        default_factory=list,
        description="List of agents that support this finding (e.g., ['CONFLICT_ANALYST', 'IHL_SPECIALIST'])"
    )

    evidence_count: int = Field(
        default=1,
        ge=1,
        description="Number of supporting evidence pieces"
    )

    source_count: int = Field(
        default=1,
        ge=1,
        description="Number of independent sources"
    )

    # Confidence breakdown (OPTIONAL)
    extraction_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence in entity/data extraction (0.0-1.0)"
    )

    validation_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence after validation checks (0.0-1.0)"
    )

    cross_validation_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence from cross-validation with other sources (0.0-1.0)"
    )

    # Validation status
    is_validated: bool = Field(
        default=False,
        description="Has this been validated by human or automated checks?"
    )

    validation_method: Optional[str] = Field(
        None,
        description="Validation method: 'human', 'automated', 'cross_source', 'none'"
    )

    # Uncertainty quantification
    uncertainty_level: Optional[str] = Field(
        None,
        description="Uncertainty level: 'low', 'moderate', 'high'. Derived from confidence score."
    )

    # Graph integration
    def to_graph_properties(self) -> dict:
        """Convert to Neo4j confidence properties."""
        return {
            "confidence": self.overall_confidence,
            "evidence_count": self.evidence_count,
            "source_count": self.source_count,
            "is_validated": self.is_validated,
            "validation_method": self.validation_method,
            "uncertainty_level": self.uncertainty_level or self._derive_uncertainty()
        }

    def _derive_uncertainty(self) -> str:
        """Derive uncertainty level from confidence score."""
        if self.overall_confidence >= 0.8:
            return "low"
        elif self.overall_confidence >= 0.5:
            return "moderate"
        else:
            return "high"


# ============================================================================
# 5. ActionRecommendation
# ============================================================================

class ActionRecommendation(BaseModel):
    """
    Actionable recommendation derived from intelligence analysis.

    Provides machine-readable action suggestions for downstream systems.

    Examples:
        ActionRecommendation(
            action_type="MONITOR",
            priority="high",
            target_entities=[EntityReference(entity_id="RU", entity_type="COUNTRY")]
        )
    """

    # Action specification (REQUIRED)
    action_type: str = Field(
        ...,
        description="Type of recommended action. Common values: "
                    "'MONITOR', 'INVESTIGATE', 'ALERT', 'ESCALATE', 'DEPLOY_AID', "
                    "'EVACUATE', 'SANCTION', 'INTERVENE', 'NEGOTIATE', 'TRACK_MARKET'. "
                    "Use descriptive verb phrases."
    )

    priority: str = Field(
        ...,
        description="Action priority. Common values: "
                    "'critical', 'high', 'medium', 'low'. Use lowercase strings."
    )

    # Action context (OPTIONAL)
    target_entities: Optional[List[EntityReference]] = Field(
        default_factory=list,
        description="Entities this action applies to"
    )

    timeframe: Optional[str] = Field(
        None,
        description="Recommended timeframe for action. Common values: "
                    "'immediate', 'within_24h', 'within_week', 'ongoing'. Use descriptive strings."
    )

    rationale: Optional[str] = Field(
        None,
        description="Brief rationale for this action (1-2 sentences, machine-readable)"
    )

    expected_outcome: Optional[str] = Field(
        None,
        description="Expected outcome if action is taken"
    )

    # Action metadata
    responsible_party: Optional[str] = Field(
        None,
        description="Who should execute this action: 'military', 'diplomatic', 'humanitarian', 'intelligence'"
    )

    resources_required: Optional[List[str]] = Field(
        default_factory=list,
        description="Resources needed: ['personnel', 'equipment', 'funding', 'authorization']"
    )

    dependencies: Optional[List[str]] = Field(
        default_factory=list,
        description="Dependencies or prerequisites for this action"
    )

    # Graph integration
    def to_graph_node(self) -> dict:
        """Convert to Neo4j action node."""
        return {
            "action_type": self.action_type,
            "priority": self.priority,
            "timeframe": self.timeframe,
            "rationale": self.rationale,
            "expected_outcome": self.expected_outcome,
            "responsible_party": self.responsible_party,
            "resources_required": self.resources_required or [],
            "dependencies": self.dependencies or []
        }


# ============================================================================
# 6. RiskAssessment
# ============================================================================

class RiskAssessment(BaseModel):
    """
    Risk assessment primitive for threat and impact analysis.

    Provides standardized risk scoring across all Intelligence modules.

    Examples:
        RiskAssessment(
            risk_type="CONFLICT_ESCALATION",
            severity=0.85,
            imminence="SHORT_TERM",
            affected_entities=[EntityReference(entity_id="PL", entity_type="COUNTRY")]
        )
    """

    # Risk identification (REQUIRED)
    risk_type: str = Field(
        ...,
        description="Type of risk. Common values: "
                    "'CONFLICT_ESCALATION', 'IHL_VIOLATION', 'HUMANITARIAN_CRISIS', "
                    "'MARKET_VOLATILITY', 'POLICY_SHIFT', 'SECURITY_BREACH', "
                    "'SUPPLY_DISRUPTION', 'REFUGEE_FLOW'. Use descriptive strings."
    )

    severity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Risk severity score (0.0-1.0)"
    )

    # Temporal assessment (OPTIONAL)
    imminence: Optional[str] = Field(
        None,
        description="Risk imminence. Common values: "
                    "'IMMEDIATE', 'SHORT_TERM' (hours-days), 'MEDIUM_TERM' (weeks-months), "
                    "'LONG_TERM' (months-years). Use descriptive strings."
    )

    likelihood: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Likelihood of risk materialization (0.0-1.0)"
    )

    # Impact assessment (OPTIONAL)
    affected_entities: Optional[List[EntityReference]] = Field(
        default_factory=list,
        description="Entities at risk"
    )

    impact_scope: Optional[str] = Field(
        None,
        description="Scope of impact: 'local', 'regional', 'global'"
    )

    estimated_casualties: Optional[int] = Field(
        None,
        ge=0,
        description="Estimated casualties if risk materializes"
    )

    economic_impact_usd: Optional[float] = Field(
        None,
        ge=0.0,
        description="Estimated economic impact in USD"
    )

    # Mitigation (OPTIONAL)
    mitigation_measures: Optional[List[str]] = Field(
        default_factory=list,
        description="Possible mitigation measures"
    )

    residual_risk: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Risk level after mitigation (0.0-1.0)"
    )

    # Graph integration
    def to_graph_node(self) -> dict:
        """Convert to Neo4j risk node."""
        return {
            "risk_type": self.risk_type,
            "severity": self.severity,
            "imminence": self.imminence,
            "likelihood": self.likelihood,
            "impact_scope": self.impact_scope,
            "estimated_casualties": self.estimated_casualties,
            "economic_impact_usd": self.economic_impact_usd,
            "mitigation_measures": self.mitigation_measures or [],
            "residual_risk": self.residual_risk
        }

    def compute_risk_score(self) -> float:
        """Compute overall risk score (severity × likelihood)."""
        if self.likelihood is not None:
            return self.severity * self.likelihood
        return self.severity


# ============================================================================
# 7. GraphTriplet
# ============================================================================

class GraphTriplet(BaseModel):
    """
    (Subject) -[Predicate]-> (Object) graph triplet.

    Standard format for knowledge graph ingestion.

    Examples:
        GraphTriplet(
            subject=EntityReference(entity_id="RU", entity_type="COUNTRY"),
            predicate="ATTACKS",
            object=EntityReference(entity_id="UA", entity_type="COUNTRY"),
            properties={"severity": "CRITICAL"}
        )
    """

    subject: EntityReference = Field(
        ...,
        description="Subject entity (source node)"
    )

    predicate: str = Field(
        ...,
        description="Relationship type (edge label)"
    )

    object: EntityReference = Field(
        ...,
        description="Object entity (target node)"
    )

    properties: dict = Field(
        default_factory=dict,
        description="Relationship properties"
    )

    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Triplet confidence (0.0-1.0)"
    )

    def to_cypher(self) -> str:
        """Generate Cypher MERGE statement."""
        return f"""
        MERGE (s:{self.subject.to_graph_label()} {{entity_id: $subject_id}})
        MERGE (o:{self.object.to_graph_label()} {{entity_id: $object_id}})
        CREATE (s)-[r:{self.predicate} $properties]->(o)
        RETURN id(s) AS subject_id, id(o) AS object_id, id(r) AS rel_id
        """

    def to_cypher_params(self) -> dict:
        """Generate Cypher parameters."""
        return {
            "subject_id": self.subject.entity_id,
            "object_id": self.object.entity_id,
            "properties": {
                **self.properties,
                "confidence": self.confidence
            }
        }
