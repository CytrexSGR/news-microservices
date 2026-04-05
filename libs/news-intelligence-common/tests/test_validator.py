"""Tests for EventValidator."""

import pytest
from news_intelligence_common.schemas.validator import EventValidator, validate_event


class TestEventValidator:
    """Test event validation."""

    @pytest.fixture
    def validator(self) -> EventValidator:
        """Create validator instance."""
        return EventValidator(strict=False)

    def test_valid_envelope(self, validator: EventValidator) -> None:
        """Valid envelope should pass."""
        data = {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "event_type": "article.created",
            "event_version": "1.0",
            "source_service": "feed-service",
            "timestamp": "2026-01-04T12:00:00Z",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
            "causation_id": None,
            "payload": {"article_id": "test"},
            "metadata": {},
        }
        is_valid, errors = validator.validate_envelope(data)
        assert is_valid
        assert errors == []

    def test_missing_required_field(self, validator: EventValidator) -> None:
        """Missing required field should fail."""
        data = {"event_type": "article.created"}  # Missing event_id, payload
        is_valid, errors = validator.validate_envelope(data)
        assert not is_valid
        assert len(errors) > 0

    def test_valid_article_created_payload(self, validator: EventValidator) -> None:
        """Valid article.created payload should pass."""
        payload = {
            "article_id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test Article",
            "link": "https://example.com/article",
            "source_id": "550e8400-e29b-41d4-a716-446655440001",
        }
        is_valid, errors = validator.validate_payload("article.created", payload)
        assert is_valid
        assert errors == []

    def test_invalid_article_created_payload(self, validator: EventValidator) -> None:
        """Invalid article.created payload should fail."""
        payload = {"title": "Missing required fields"}
        is_valid, errors = validator.validate_payload("article.created", payload)
        assert not is_valid

    def test_unknown_event_type_graceful(self, validator: EventValidator) -> None:
        """Unknown event type should pass gracefully."""
        is_valid, errors = validator.validate_payload("unknown.event", {"data": "test"})
        assert is_valid
        assert errors == []

    def test_strict_mode_raises(self) -> None:
        """Strict mode should raise on invalid data."""
        validator = EventValidator(strict=True)
        with pytest.raises(Exception):
            validator.validate_envelope({"invalid": "data"})

    def test_valid_analysis_completed_payload(self, validator: EventValidator) -> None:
        """Valid analysis.completed payload should pass."""
        payload = {
            "article_id": "550e8400-e29b-41d4-a716-446655440000",
            "success": True,
            "pipeline_version": "1.0.0",
        }
        is_valid, errors = validator.validate_payload("analysis.completed", payload)
        assert is_valid
        assert errors == []

    def test_valid_cluster_created_payload(self, validator: EventValidator) -> None:
        """Valid cluster.created payload should pass."""
        payload = {
            "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Breaking News Cluster",
            "article_id": "550e8400-e29b-41d4-a716-446655440001",
        }
        is_valid, errors = validator.validate_payload("cluster.created", payload)
        assert is_valid
        assert errors == []

    def test_valid_cluster_updated_payload(self, validator: EventValidator) -> None:
        """Valid cluster.updated payload should pass."""
        payload = {
            "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
            "article_id": "550e8400-e29b-41d4-a716-446655440001",
            "article_count": 5,
        }
        is_valid, errors = validator.validate_payload("cluster.updated", payload)
        assert is_valid
        assert errors == []

    def test_valid_cluster_burst_detected_payload(
        self, validator: EventValidator
    ) -> None:
        """Valid cluster.burst_detected payload should pass."""
        payload = {
            "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Breaking: Major Event",
            "growth_rate": 5.5,
        }
        is_valid, errors = validator.validate_payload("cluster.burst_detected", payload)
        assert is_valid
        assert errors == []

    def test_article_updated_requires_change_type(
        self, validator: EventValidator
    ) -> None:
        """article.updated should require change_type field."""
        payload = {
            "article_id": "550e8400-e29b-41d4-a716-446655440000",
            "version": 2,
            # Missing change_type
        }
        is_valid, errors = validator.validate_payload("article.updated", payload)
        assert not is_valid

    def test_full_envelope_and_payload_validation(
        self, validator: EventValidator
    ) -> None:
        """Validate both envelope and payload together."""
        data = {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "event_type": "article.created",
            "event_version": "1.0",
            "source_service": "feed-service",
            "timestamp": "2026-01-04T12:00:00Z",
            "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
            "causation_id": None,
            "payload": {
                "article_id": "550e8400-e29b-41d4-a716-446655440002",
                "title": "Test Article",
                "link": "https://example.com/article",
                "source_id": "550e8400-e29b-41d4-a716-446655440003",
            },
            "metadata": {},
        }
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert errors == []


class TestValidateEventFunction:
    """Test convenience function."""

    def test_validate_event_valid(self) -> None:
        """Valid event should pass."""
        data = {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "event_type": "article.created",
            "event_version": "1.0",
            "source_service": "test",
            "timestamp": "2026-01-04T12:00:00Z",
            "payload": {
                "article_id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "Test",
                "link": "https://example.com",
                "source_id": "550e8400-e29b-41d4-a716-446655440002",
            },
        }
        is_valid, errors = validate_event(data)
        assert is_valid

    def test_validate_event_invalid(self) -> None:
        """Invalid event should fail."""
        data = {"invalid": "data"}
        is_valid, errors = validate_event(data)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_event_strict_raises(self) -> None:
        """Strict mode should raise on invalid event."""
        data = {"invalid": "data"}
        with pytest.raises(Exception):
            validate_event(data, strict=True)


class TestEventSchemasCoverage:
    """Test that all event schemas are properly defined."""

    def test_all_schemas_have_required_fields(self) -> None:
        """All schemas should have required fields defined."""
        from news_intelligence_common.schemas.event_schemas import EVENT_PAYLOAD_SCHEMAS

        for event_type, schema in EVENT_PAYLOAD_SCHEMAS.items():
            assert "type" in schema, f"{event_type} missing 'type'"
            assert schema["type"] == "object", f"{event_type} must be object type"
            assert "required" in schema, f"{event_type} missing 'required'"
            assert "properties" in schema, f"{event_type} missing 'properties'"

    def test_all_required_fields_have_definitions(self) -> None:
        """All required fields should be defined in properties."""
        from news_intelligence_common.schemas.event_schemas import EVENT_PAYLOAD_SCHEMAS

        for event_type, schema in EVENT_PAYLOAD_SCHEMAS.items():
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            for field in required:
                assert field in properties, (
                    f"{event_type}: required field '{field}' not in properties"
                )
