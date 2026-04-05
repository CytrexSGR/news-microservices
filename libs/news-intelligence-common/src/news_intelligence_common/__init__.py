"""
News Intelligence Common Library.

Shared utilities for News Intelligence features:
- SimHasher: Near-duplicate detection via SimHash fingerprinting
- TimeDecayScorer: Time-weighted relevance scoring
- EventEnvelope: Standardized event messaging
- EventValidator: Schema validation for events
- EventPublisherWrapper: Standardized event publishing
"""

__version__ = "0.1.0"

from news_intelligence_common.simhasher import SimHasher
from news_intelligence_common.time_decay import TimeDecayScorer
from news_intelligence_common.event_envelope import EventEnvelope, EVENT_ENVELOPE_SCHEMA
from news_intelligence_common.schemas.validator import EventValidator, validate_event
from news_intelligence_common.schemas.event_schemas import EVENT_PAYLOAD_SCHEMAS
from news_intelligence_common.publisher import EventPublisherWrapper, create_event

__all__ = [
    "SimHasher",
    "TimeDecayScorer",
    "EventEnvelope",
    "EVENT_ENVELOPE_SCHEMA",
    "EventValidator",
    "validate_event",
    "EVENT_PAYLOAD_SCHEMAS",
    "EventPublisherWrapper",
    "create_event",
]
