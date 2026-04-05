"""JSON schemas for all event types."""

from typing import Any, Dict

# Base payload schemas for each event type
ARTICLE_CREATED_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["article_id", "title", "link", "source_id"],
    "properties": {
        "article_id": {"type": "string", "format": "uuid"},
        "title": {"type": "string", "maxLength": 500},
        "link": {"type": "string", "format": "uri"},
        "guid": {"type": "string"},
        "published_at": {"type": "string", "format": "date-time"},
        "source_id": {"type": "string", "format": "uuid"},
        "source_type": {"type": "string", "enum": ["rss", "api", "scraper"]},
        "content_hash": {"type": "string", "minLength": 64, "maxLength": 64},
        "simhash_fingerprint": {"type": ["integer", "null"]},
        "version": {"type": "integer", "minimum": 1},
        "pub_status": {"type": "string", "enum": ["usable", "withheld", "canceled"]},
    },
}

ARTICLE_UPDATED_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["article_id", "version", "change_type"],
    "properties": {
        "article_id": {"type": "string", "format": "uuid"},
        "version": {"type": "integer", "minimum": 2},
        "previous_version": {"type": "integer", "minimum": 1},
        "change_type": {"type": "string", "enum": ["update", "correction", "withdrawal"]},
        "changed_fields": {"type": "array", "items": {"type": "string"}},
        "pub_status": {"type": "string", "enum": ["usable", "withheld", "canceled"]},
    },
}

ANALYSIS_COMPLETED_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["article_id", "success", "pipeline_version"],
    "properties": {
        "article_id": {"type": "string", "format": "uuid"},
        "success": {"type": "boolean"},
        "pipeline_version": {"type": "string"},
        "tier0": {"type": "object"},
        "tier1": {"type": "object"},
        "tier2": {"type": "object"},
        "embedding": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 384,
            "maxItems": 1536,
        },
        "metrics": {"type": "object"},
    },
}

CLUSTER_CREATED_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["cluster_id", "title", "article_id"],
    "properties": {
        "cluster_id": {"type": "string", "format": "uuid"},
        "title": {"type": "string", "maxLength": 500},
        "article_id": {"type": "string", "format": "uuid"},
        "article_count": {"type": "integer", "minimum": 1},
        "tension_score": {"type": "number", "minimum": 0, "maximum": 10},
        "is_breaking": {"type": "boolean"},
        "primary_entities": {"type": "array"},
    },
}

CLUSTER_UPDATED_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["cluster_id", "article_id", "article_count"],
    "properties": {
        "cluster_id": {"type": "string", "format": "uuid"},
        "article_id": {"type": "string", "format": "uuid"},
        "article_count": {"type": "integer", "minimum": 1},
        "tension_score": {"type": "number", "minimum": 0, "maximum": 10},
        "is_breaking": {"type": "boolean"},
        "primary_entities": {"type": "array"},
        "similarity_score": {"type": "number", "minimum": 0, "maximum": 1},
    },
}

CLUSTER_BURST_DETECTED_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["cluster_id", "title", "growth_rate"],
    "properties": {
        "cluster_id": {"type": "string", "format": "uuid"},
        "title": {"type": "string", "maxLength": 500},
        "article_count": {"type": "integer", "minimum": 1},
        "growth_rate": {"type": "number", "minimum": 0},
        "tension_score": {"type": "number", "minimum": 0, "maximum": 10},
        "detection_method": {"type": "string"},
        "top_entities": {"type": "array", "items": {"type": "string"}},
        "recommended_action": {"type": "string"},
    },
}

# Event type to schema mapping
EVENT_PAYLOAD_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "article.created": ARTICLE_CREATED_SCHEMA,
    "article.updated": ARTICLE_UPDATED_SCHEMA,
    "article.withdrawn": ARTICLE_UPDATED_SCHEMA,
    "analysis.completed": ANALYSIS_COMPLETED_SCHEMA,
    "cluster.created": CLUSTER_CREATED_SCHEMA,
    "cluster.updated": CLUSTER_UPDATED_SCHEMA,
    "cluster.merged": CLUSTER_UPDATED_SCHEMA,
    "cluster.burst_detected": CLUSTER_BURST_DETECTED_SCHEMA,
}
