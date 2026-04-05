"""Tests for EventEnvelope class."""

import json
import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from news_intelligence_common.event_envelope import EventEnvelope, EVENT_ENVELOPE_SCHEMA


class TestEventEnvelopeCreation:
    """Test envelope creation."""

    def test_create_minimal_envelope(self) -> None:
        """Should create envelope with required fields only."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={"article_id": "123"},
        )
        assert envelope.event_type == "article.created"
        assert envelope.payload == {"article_id": "123"}

    def test_auto_generates_event_id(self) -> None:
        """event_id should be auto-generated UUID."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={},
        )
        assert envelope.event_id is not None
        assert len(envelope.event_id) == 36  # UUID format

    def test_auto_generates_timestamp(self) -> None:
        """timestamp should be auto-generated ISO format."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={},
        )
        assert envelope.timestamp is not None
        # Should be parseable as ISO datetime
        datetime.fromisoformat(envelope.timestamp.replace("Z", "+00:00"))

    def test_auto_generates_correlation_id(self) -> None:
        """correlation_id should be auto-generated UUID."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={},
        )
        assert envelope.correlation_id is not None
        assert len(envelope.correlation_id) == 36

    def test_default_event_version(self) -> None:
        """event_version should default to 1.0."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={},
        )
        assert envelope.event_version == "1.0"

    def test_default_metadata_empty_dict(self) -> None:
        """metadata should default to empty dict."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={},
        )
        assert envelope.metadata == {}

    def test_causation_id_optional(self) -> None:
        """causation_id should be optional (None)."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={},
        )
        assert envelope.causation_id is None

    def test_custom_values_accepted(self) -> None:
        """Custom values should override defaults."""
        envelope = EventEnvelope(
            event_type="cluster.updated",
            payload={"data": "test"},
            event_id="custom-id",
            event_version="2.0",
            correlation_id="corr-123",
            causation_id="cause-456",
            metadata={"key": "value"},
        )
        assert envelope.event_id == "custom-id"
        assert envelope.event_version == "2.0"
        assert envelope.correlation_id == "corr-123"
        assert envelope.causation_id == "cause-456"
        assert envelope.metadata == {"key": "value"}


class TestEventEnvelopeValidation:
    """Test envelope validation."""

    def test_invalid_event_type_uppercase(self) -> None:
        """Uppercase event_type should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid event_type"):
            EventEnvelope(
                event_type="Article.Created",
                payload={},
            )

    def test_invalid_event_type_no_dot(self) -> None:
        """event_type without dot should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid event_type"):
            EventEnvelope(
                event_type="articlecreated",
                payload={},
            )

    def test_invalid_event_type_spaces(self) -> None:
        """event_type with spaces should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid event_type"):
            EventEnvelope(
                event_type="article .created",
                payload={},
            )

    def test_valid_event_type_with_underscore(self) -> None:
        """event_type with underscore should be valid."""
        envelope = EventEnvelope(
            event_type="cluster.burst_detected",
            payload={},
        )
        assert envelope.event_type == "cluster.burst_detected"

    def test_invalid_event_version_format(self) -> None:
        """Invalid event_version format should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid event_version"):
            EventEnvelope(
                event_type="article.created",
                payload={},
                event_version="v1",
            )

    def test_valid_event_version_format(self) -> None:
        """Valid event_version formats should work."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={},
            event_version="2.5",
        )
        assert envelope.event_version == "2.5"


class TestEventEnvelopeSourceInfo:
    """Test source service information."""

    def test_source_service_from_env(self) -> None:
        """source_service should come from SERVICE_NAME env."""
        with patch.dict(os.environ, {"SERVICE_NAME": "feed-service"}):
            envelope = EventEnvelope(
                event_type="article.created",
                payload={},
            )
            assert envelope.source_service == "feed-service"

    def test_source_service_default(self) -> None:
        """source_service should default to 'unknown'."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove SERVICE_NAME if present
            os.environ.pop("SERVICE_NAME", None)
            envelope = EventEnvelope(
                event_type="article.created",
                payload={},
            )
            assert envelope.source_service == "unknown"

    def test_source_instance_from_env(self) -> None:
        """source_instance should come from HOSTNAME env."""
        with patch.dict(os.environ, {"HOSTNAME": "pod-abc123"}):
            envelope = EventEnvelope(
                event_type="article.created",
                payload={},
            )
            assert envelope.source_instance == "pod-abc123"


class TestEventEnvelopeSerialization:
    """Test serialization."""

    def test_to_dict_returns_dict(self) -> None:
        """to_dict should return dictionary."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={"id": "123"},
        )
        result = envelope.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_all_fields(self) -> None:
        """to_dict should contain all fields."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={"id": "123"},
        )
        result = envelope.to_dict()

        assert "event_id" in result
        assert "event_type" in result
        assert "event_version" in result
        assert "source_service" in result
        assert "source_instance" in result
        assert "timestamp" in result
        assert "correlation_id" in result
        assert "causation_id" in result
        assert "payload" in result
        assert "metadata" in result

    def test_to_dict_json_serializable(self) -> None:
        """to_dict result should be JSON serializable."""
        envelope = EventEnvelope(
            event_type="article.created",
            payload={"nested": {"data": [1, 2, 3]}},
            metadata={"key": "value"},
        )
        result = envelope.to_dict()

        # Should not raise
        json_str = json.dumps(result)
        assert isinstance(json_str, str)


class TestEventEnvelopeSchema:
    """Test JSON schema."""

    def test_schema_is_dict(self) -> None:
        """Schema should be a dictionary."""
        assert isinstance(EVENT_ENVELOPE_SCHEMA, dict)

    def test_schema_has_required_fields(self) -> None:
        """Schema should define required fields."""
        assert "required" in EVENT_ENVELOPE_SCHEMA
        required = EVENT_ENVELOPE_SCHEMA["required"]
        assert "event_id" in required
        assert "event_type" in required
        assert "payload" in required

    def test_schema_has_properties(self) -> None:
        """Schema should define properties."""
        assert "properties" in EVENT_ENVELOPE_SCHEMA
        props = EVENT_ENVELOPE_SCHEMA["properties"]
        assert "event_id" in props
        assert "event_type" in props
        assert "payload" in props
