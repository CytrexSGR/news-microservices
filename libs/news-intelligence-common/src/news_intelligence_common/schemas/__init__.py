"""Event schemas package for news-intelligence-common."""

from news_intelligence_common.schemas.event_schemas import (
    ARTICLE_CREATED_SCHEMA,
    ARTICLE_UPDATED_SCHEMA,
    ANALYSIS_COMPLETED_SCHEMA,
    CLUSTER_CREATED_SCHEMA,
    CLUSTER_UPDATED_SCHEMA,
    CLUSTER_BURST_DETECTED_SCHEMA,
    EVENT_PAYLOAD_SCHEMAS,
)
from news_intelligence_common.schemas.validator import (
    EventValidator,
    validate_event,
)

__all__ = [
    "ARTICLE_CREATED_SCHEMA",
    "ARTICLE_UPDATED_SCHEMA",
    "ANALYSIS_COMPLETED_SCHEMA",
    "CLUSTER_CREATED_SCHEMA",
    "CLUSTER_UPDATED_SCHEMA",
    "CLUSTER_BURST_DETECTED_SCHEMA",
    "EVENT_PAYLOAD_SCHEMAS",
    "EventValidator",
    "validate_event",
]
