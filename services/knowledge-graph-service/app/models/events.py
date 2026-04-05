"""
Event Models for RabbitMQ Messages

Defines Pydantic models for `relationships.extracted` events.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class EntityInfo(BaseModel):
    """Entity information in a triplet."""

    text: str = Field(..., description="Entity text (name)")
    type: str = Field(..., description="Entity type (PERSON, ORGANIZATION, etc.)")
    wikidata_id: Optional[str] = Field(None, description="Wikidata Q-ID (e.g., Q30 for United States)")


class RelationshipInfo(BaseModel):
    """Relationship information in a triplet."""

    type: str = Field(..., description="Relationship type (WORKS_FOR, LOCATED_IN, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    evidence: Optional[str] = Field(None, description="Evidence text supporting relationship")

    # Sentiment Analysis (2025-10-25)
    sentiment_score: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Sentiment polarity: -1.0 (very negative) to +1.0 (very positive)"
    )
    sentiment_category: Optional[str] = Field(
        None,
        description="Categorical sentiment: positive/negative/neutral"
    )
    sentiment_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence in sentiment assessment"
    )


class RelationshipTriplet(BaseModel):
    """
    (Subject) -[Relationship]-> (Object) triplet from event.

    This is the format published by content-analysis-service.
    """

    subject: EntityInfo
    relationship: RelationshipInfo
    object: EntityInfo


class RelationshipsExtractedPayload(BaseModel):
    """
    Payload for relationships.extracted event.

    Published by content-analysis-service when relationships are extracted.
    """

    article_id: str = Field(..., description="Source article UUID")
    source_url: Optional[str] = Field(None, description="Source article URL")
    triplets: List[RelationshipTriplet] = Field(default_factory=list, description="List of relationship triplets")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When relationships were extracted")
    total_relationships: int = Field(..., description="Total number of relationships extracted")


class RelationshipsExtractedEvent(BaseModel):
    """
    Complete event structure for relationships.extracted.

    This is the message consumed from RabbitMQ.
    """

    event_type: str = Field("relationships.extracted", description="Event type identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    payload: RelationshipsExtractedPayload


# Example event for documentation
EXAMPLE_EVENT = {
    "event_type": "relationships.extracted",
    "timestamp": "2025-10-24T14:00:00Z",
    "payload": {
        "article_id": "197a6e20-5981-410c-bf49-b3552c93b939",
        "source_url": "https://example.com/article",
        "triplets": [
            {
                "subject": {
                    "text": "Philippe Lazzarini",
                    "type": "PERSON"
                },
                "relationship": {
                    "type": "MEMBER_OF",
                    "confidence": 0.9,
                    "evidence": "Philippe Lazzarini is the Commissioner-General of UNRWA."
                },
                "object": {
                    "text": "UNRWA",
                    "type": "ORGANIZATION"
                }
            },
            {
                "subject": {
                    "text": "UNRWA",
                    "type": "ORGANIZATION"
                },
                "relationship": {
                    "type": "LOCATED_IN",
                    "confidence": 0.85,
                    "evidence": "UNRWA operates in Gaza."
                },
                "object": {
                    "text": "Gaza",
                    "type": "LOCATION"
                }
            }
        ],
        "extraction_timestamp": "2025-10-24T14:00:00Z",
        "total_relationships": 2
    }
}
