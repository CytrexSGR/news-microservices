"""
Symbolic Finding Models for Knowledge Graph Ingestion

Shared models from content-analysis-v2 for ingesting structured findings into Neo4j.
These models have built-in `to_graph_triplets()` methods for generating Cypher queries.
"""

from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field, confloat
from enum import Enum


# ============================================================================
# ENUMS (subset from intelligence_synthesis.py)
# ============================================================================

class FindingCategory(str, Enum):
    """Categories for key findings."""
    EVENT_TYPE = "event_type"
    IHL_CONCERN = "ihl_concern"
    REGIONAL_IMPACT = "regional_impact"
    FINANCIAL_IMPACT = "financial_impact"
    POLITICAL_DEVELOPMENT = "political_development"
    SECURITY_THREAT = "security_threat"
    HUMANITARIAN_CRISIS = "humanitarian_crisis"


class PriorityLevel(str, Enum):
    """Priority level for intelligence assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventTypeCode(str, Enum):
    """Event types for military/conflict findings."""
    MISSILE_STRIKE = "MISSILE_STRIKE"
    AIR_STRIKE = "AIR_STRIKE"
    ARTILLERY = "ARTILLERY"
    GROUND_OFFENSIVE = "GROUND_OFFENSIVE"
    DRONE_ATTACK = "DRONE_ATTACK"
    NAVAL_OPERATION = "NAVAL_OPERATION"
    CYBER_ATTACK = "CYBER_ATTACK"
    SABOTAGE = "SABOTAGE"


class TargetTypeCode(str, Enum):
    """Target types for events."""
    INFRASTRUCTURE = "INFRASTRUCTURE"
    CIVILIAN = "CIVILIAN"
    MILITARY = "MILITARY"
    MIXED = "MIXED"
    ENERGY = "ENERGY"
    TRANSPORT = "TRANSPORT"
    COMMUNICATION = "COMMUNICATION"
    GOVERNMENT = "GOVERNMENT"


class SeverityLevel(str, Enum):
    """Severity levels for events and impacts."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActorRole(str, Enum):
    """Roles of actors in events."""
    AGGRESSOR = "aggressor"
    DEFENDER = "defender"
    AFFECTED = "affected"
    OBSERVER = "observer"
    MEDIATOR = "mediator"


class IHLViolationType(str, Enum):
    """Types of IHL violations."""
    CIVILIAN_CASUALTY = "CIVILIAN_CASUALTY"
    INFRASTRUCTURE_ATTACK = "INFRASTRUCTURE_ATTACK"
    PROPORTIONALITY = "PROPORTIONALITY"
    DISTINCTION = "DISTINCTION"
    PROTECTED_ENTITY = "PROTECTED_ENTITY"
    INDISCRIMINATE = "INDISCRIMINATE"
    PRECAUTION = "PRECAUTION"


class ImpactType(str, Enum):
    """Types of regional/global impacts."""
    SECURITY = "SECURITY"
    ECONOMIC = "ECONOMIC"
    DIPLOMATIC = "DIPLOMATIC"
    HUMANITARIAN = "HUMANITARIAN"
    POLITICAL = "POLITICAL"
    ENVIRONMENTAL = "ENVIRONMENTAL"


class StabilityChange(str, Enum):
    """Changes in regional stability."""
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DEGRADING = "DEGRADING"
    CRITICAL = "CRITICAL"


class InstrumentType(str, Enum):
    """Financial instrument types."""
    FOREX = "FOREX"
    COMMODITIES = "COMMODITIES"
    EQUITIES = "EQUITIES"
    CRYPTO = "CRYPTO"
    BONDS = "BONDS"
    DERIVATIVES = "DERIVATIVES"


class Direction(str, Enum):
    """Direction of change/impact."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class VolatilityLevel(str, Enum):
    """Market volatility levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class DurationEstimate(str, Enum):
    """Duration estimates for impacts."""
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    LONG_TERM = "LONG_TERM"


class PoliticalAlignment(str, Enum):
    """Political alignment spectrum."""
    LEFT = "LEFT"
    CENTER_LEFT = "CENTER_LEFT"
    CENTER = "CENTER"
    CENTER_RIGHT = "CENTER_RIGHT"
    RIGHT = "RIGHT"


class PoliticalPosition(str, Enum):
    """Political position/stance."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class PolicyArea(str, Enum):
    """Policy areas."""
    SANCTIONS = "SANCTIONS"
    DIPLOMACY = "DIPLOMACY"
    DEFENSE = "DEFENSE"
    TRADE = "TRADE"
    AID = "AID"
    ENERGY = "ENERGY"
    CLIMATE = "CLIMATE"


class PolicyDirection(str, Enum):
    """Direction of policy change."""
    TIGHTENING = "TIGHTENING"
    EASING = "EASING"
    NEUTRAL = "NEUTRAL"
    REVERSAL = "REVERSAL"


class ThreatType(str, Enum):
    """Types of security threats."""
    MILITARY = "MILITARY"
    CYBER = "CYBER"
    TERRORISM = "TERRORISM"
    NUCLEAR = "NUCLEAR"
    CHEMICAL = "CHEMICAL"
    BIOLOGICAL = "BIOLOGICAL"
    HYBRID = "HYBRID"


class ImminenceLevel(str, Enum):
    """Imminence of threats."""
    IMMEDIATE = "IMMEDIATE"
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    LONG_TERM = "LONG_TERM"


class CrisisType(str, Enum):
    """Types of humanitarian crises."""
    REFUGEE = "REFUGEE"
    FOOD_INSECURITY = "FOOD_INSECURITY"
    HEALTH = "HEALTH"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DISPLACEMENT = "DISPLACEMENT"
    WATER = "WATER"


class NeedType(str, Enum):
    """Types of urgent needs."""
    MEDICAL = "MEDICAL"
    FOOD = "FOOD"
    SHELTER = "SHELTER"
    WATER = "WATER"
    PROTECTION = "PROTECTION"


# ============================================================================
# SYMBOLIC FINDING MODELS
# ============================================================================

class EventTypeSymbolic(BaseModel):
    """Symbolic representation for event_type findings."""
    event_type: EventTypeCode
    target: TargetTypeCode
    severity: SeverityLevel
    actors: Dict[str, ActorRole]
    location: str
    casualties: Optional[int] = None


class IHLConcernSymbolic(BaseModel):
    """Symbolic representation for ihl_concern findings."""
    ihl_type: IHLViolationType
    violation_level: SeverityLevel
    actors: List[str]
    affected_population: Optional[int] = None
    protected_status: bool


class RegionalImpactSymbolic(BaseModel):
    """Symbolic representation for regional_impact findings."""
    affected_countries: List[str]
    impact_type: str = Field(
        ...,
        description="Type of regional impact. Common values: 'SECURITY', 'ECONOMIC', 'DIPLOMATIC', 'HUMANITARIAN', 'POLITICAL', 'ENVIRONMENTAL'. Use descriptive strings."
    )
    severity: confloat(ge=0.0, le=1.0)
    spillover_risk: confloat(ge=0.0, le=1.0)
    regional_stability: str = Field(
        ...,
        description="Regional stability change. Common values: 'IMPROVING', 'STABLE', 'DEGRADING', 'CRITICAL', 'deteriorating', 'improving'. Use descriptive strings."
    )


class FinancialImpactSymbolic(BaseModel):
    """Symbolic representation for financial_impact findings."""
    markets: Dict[str, float]
    sectors: Dict[str, str] = Field(
        ...,
        description="Sector impacts. Common values: 'positive', 'negative', 'neutral', 'UP', 'DOWN', 'VOLATILE'. Use descriptive strings."
    )
    instruments: List[InstrumentType]
    volatility: VolatilityLevel
    duration: DurationEstimate


class PoliticalStance(BaseModel):
    """Political stance of an actor."""
    alignment: PoliticalAlignment
    position: str = Field(
        ...,
        description="Political position. Common values: 'positive', 'negative', 'neutral', 'supportive', 'opposed'. Use descriptive strings."
    )


class PoliticalDevelopmentSymbolic(BaseModel):
    """Symbolic representation for political_development findings."""
    actors: Dict[str, PoliticalStance]
    policy_area: str = Field(
        ...,
        description="Policy area. Common values: 'SANCTIONS', 'DIPLOMACY', 'DEFENSE', 'TRADE', 'AID', 'ENERGY', 'CLIMATE'. Use descriptive strings."
    )
    direction: str = Field(
        ...,
        description="Policy direction. Common values: 'TIGHTENING', 'EASING', 'NEUTRAL', 'REVERSAL', 'tightening', 'easing'. Use descriptive strings."
    )
    affected_countries: List[str]
    impact_level: SeverityLevel


class SecurityThreatSymbolic(BaseModel):
    """Symbolic representation for security_threat findings."""
    threat_type: str = Field(
        ...,
        description="Type of security threat. Common values: 'MILITARY', 'CYBER', 'TERRORISM', 'NUCLEAR', 'CHEMICAL', 'BIOLOGICAL', 'HYBRID'. Use descriptive strings."
    )
    source: List[str]
    target: List[str]
    severity: confloat(ge=0.0, le=1.0)
    imminence: str = Field(
        ...,
        description="Imminence level. Common values: 'IMMEDIATE', 'SHORT_TERM', 'MEDIUM_TERM', 'LONG_TERM', 'imminent', 'near-term'. Use descriptive strings."
    )
    confidence: confloat(ge=0.0, le=1.0)


class HumanitarianCrisisSymbolic(BaseModel):
    """Symbolic representation for humanitarian_crisis findings."""
    crisis_type: str = Field(
        ...,
        description="Type of humanitarian crisis. Common values: 'REFUGEE', 'FOOD_INSECURITY', 'HEALTH', 'INFRASTRUCTURE', 'DISPLACEMENT', 'WATER'. Use descriptive strings."
    )
    affected_population: int
    location: str
    severity: SeverityLevel
    urgent_needs: List[str] = Field(
        ...,
        description="Urgent needs. Common values: 'MEDICAL', 'FOOD', 'SHELTER', 'WATER', 'PROTECTION'. Use descriptive strings."
    )


# ============================================================================
# KEY FINDING MODEL (for ingestion endpoint)
# ============================================================================

class KeyFinding(BaseModel):
    """A key finding from Intelligence Synthesizer analysis."""
    finding_id: str = Field(..., description="Unique finding ID (F1, F2, etc.)")
    category: FindingCategory = Field(..., description="Finding category")
    confidence: confloat(ge=0.0, le=1.0) = Field(..., description="Confidence in this finding")
    supporting_agents: List[str] = Field(..., description="Agents supporting this finding")
    priority: PriorityLevel = Field(..., description="Priority of this finding")

    # Symbolic representation (REQUIRED - replaces legacy text field)
    symbolic: Union[
        EventTypeSymbolic,
        IHLConcernSymbolic,
        RegionalImpactSymbolic,
        FinancialImpactSymbolic,
        PoliticalDevelopmentSymbolic,
        SecurityThreatSymbolic,
        HumanitarianCrisisSymbolic
    ] = Field(..., description="Structured symbolic representation for knowledge graph")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class IngestFindingsRequest(BaseModel):
    """Request to ingest findings into knowledge graph."""
    article_id: str = Field(..., description="Source article ID")
    findings: List[KeyFinding] = Field(..., description="List of key findings to ingest")


class GraphNodeCreated(BaseModel):
    """Created graph node reference."""
    node_id: str = Field(..., description="Neo4j internal node ID")
    node_type: str = Field(..., description="Node type (LOCATION, EVENT, etc.)")
    name: str = Field(..., description="Node name")


class GraphRelationshipCreated(BaseModel):
    """Created graph relationship reference."""
    relationship_id: str = Field(..., description="Neo4j internal relationship ID")
    relationship_type: str = Field(..., description="Relationship type (ATTACKS, AFFECTS, etc.)")
    source_node: str = Field(..., description="Source node name")
    target_node: str = Field(..., description="Target node name")
    confidence: float = Field(..., description="Confidence score")


class IngestFindingsResponse(BaseModel):
    """Response from findings ingestion."""
    article_id: str = Field(..., description="Source article ID")
    findings_processed: int = Field(..., description="Number of findings processed")
    nodes_created: List[GraphNodeCreated] = Field(..., description="Created nodes")
    relationships_created: List[GraphRelationshipCreated] = Field(..., description="Created relationships")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
