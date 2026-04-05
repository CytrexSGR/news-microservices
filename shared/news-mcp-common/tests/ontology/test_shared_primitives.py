"""
Tests for shared_primitives.py

Tests EntityReference, RelationshipHint, and ConfidenceMetadata models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from news_mcp_common.ontology import (
    EntityType,
    RelationshipType,
    EntityReference,
    RelationshipHint,
    ConfidenceMetadata,
)


class TestEntityReference:
    """Tests for EntityReference model."""

    def test_minimal_entity_reference(self):
        """Test creating entity reference with required fields only."""
        entity = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States"
        )

        assert entity.entity_id == "US"
        assert entity.entity_type == EntityType.COUNTRY
        assert entity.name == "United States"
        assert entity.source_count == 1  # Default value
        assert entity.aliases == []  # Default empty list
        assert entity.confidence is None
        assert entity.wikidata_id is None

    def test_full_entity_reference(self):
        """Test creating entity reference with all fields."""
        created_at = datetime(2025, 1, 1, 12, 0, 0)
        last_seen = datetime(2025, 1, 2, 12, 0, 0)

        entity = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc.",
            role="subject",
            confidence=0.95,
            wikidata_id="Q478214",
            aliases=["Tesla", "Tesla Motors"],
            created_at=created_at,
            last_seen=last_seen,
            source_count=5
        )

        assert entity.entity_id == "TSLA"
        assert entity.entity_type == EntityType.COMPANY
        assert entity.name == "Tesla Inc."
        assert entity.role == "subject"
        assert entity.confidence == 0.95
        assert entity.wikidata_id == "Q478214"
        assert entity.aliases == ["Tesla", "Tesla Motors"]
        assert entity.created_at == created_at
        assert entity.last_seen == last_seen
        assert entity.source_count == 5

    def test_country_entity_id_validation_success(self):
        """Test valid country entity_id (ISO 3166-1 alpha-2)."""
        entity = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States"
        )
        assert entity.entity_id == "US"

        entity2 = EntityReference(
            entity_id="RU",
            entity_type=EntityType.COUNTRY,
            name="Russia"
        )
        assert entity2.entity_id == "RU"

    def test_country_entity_id_validation_failure(self):
        """Test invalid country entity_id formats."""
        # Too long
        with pytest.raises(ValidationError) as exc_info:
            EntityReference(
                entity_id="USA",
                entity_type=EntityType.COUNTRY,
                name="United States"
            )
        assert "ISO 3166-1 alpha-2" in str(exc_info.value)

        # Lowercase
        with pytest.raises(ValidationError) as exc_info:
            EntityReference(
                entity_id="us",
                entity_type=EntityType.COUNTRY,
                name="United States"
            )
        assert "ISO 3166-1 alpha-2" in str(exc_info.value)

        # Too short
        with pytest.raises(ValidationError) as exc_info:
            EntityReference(
                entity_id="U",
                entity_type=EntityType.COUNTRY,
                name="United States"
            )
        assert "ISO 3166-1 alpha-2" in str(exc_info.value)

    def test_company_entity_id_validation_success(self):
        """Test valid company entity_id (stock ticker)."""
        entity = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc."
        )
        assert entity.entity_id == "TSLA"

        # Single letter ticker
        entity2 = EntityReference(
            entity_id="A",
            entity_type=EntityType.COMPANY,
            name="Agilent Technologies"
        )
        assert entity2.entity_id == "A"

        # 5-letter ticker
        entity3 = EntityReference(
            entity_id="ABCDE",
            entity_type=EntityType.COMPANY,
            name="Example Corp"
        )
        assert entity3.entity_id == "ABCDE"

    def test_company_entity_id_validation_failure(self):
        """Test invalid company entity_id formats."""
        # Too long
        with pytest.raises(ValidationError) as exc_info:
            EntityReference(
                entity_id="ABCDEF",
                entity_type=EntityType.COMPANY,
                name="Example Corp"
            )
        assert "stock ticker" in str(exc_info.value)

        # Lowercase
        with pytest.raises(ValidationError) as exc_info:
            EntityReference(
                entity_id="tsla",
                entity_type=EntityType.COMPANY,
                name="Tesla Inc."
            )
        assert "stock ticker" in str(exc_info.value)

    def test_wikidata_id_validation_success(self):
        """Test valid wikidata_id formats."""
        entity = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States",
            wikidata_id="Q30"
        )
        assert entity.wikidata_id == "Q30"

        entity2 = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc.",
            wikidata_id="Q478214"
        )
        assert entity2.wikidata_id == "Q478214"

    def test_wikidata_id_validation_failure(self):
        """Test invalid wikidata_id formats."""
        with pytest.raises(ValidationError) as exc_info:
            EntityReference(
                entity_id="US",
                entity_type=EntityType.COUNTRY,
                name="United States",
                wikidata_id="30"  # Missing 'Q' prefix
            )
        assert "Q<digits>" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            EntityReference(
                entity_id="US",
                entity_type=EntityType.COUNTRY,
                name="United States",
                wikidata_id="Q"  # Missing digits
            )
        assert "Q<digits>" in str(exc_info.value)

    def test_aliases_deduplication(self):
        """Test that canonical name is removed from aliases."""
        entity = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc.",
            aliases=["Tesla", "Tesla Inc.", "Tesla Motors"]  # Includes canonical name
        )

        # Canonical name should be removed from aliases
        assert "Tesla Inc." not in entity.aliases
        assert "Tesla" in entity.aliases
        assert "Tesla Motors" in entity.aliases

    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence
        entity = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States",
            confidence=0.95
        )
        assert entity.confidence == 0.95

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            EntityReference(
                entity_id="US",
                entity_type=EntityType.COUNTRY,
                name="United States",
                confidence=1.5
            )

        # Invalid confidence (negative)
        with pytest.raises(ValidationError):
            EntityReference(
                entity_id="US",
                entity_type=EntityType.COUNTRY,
                name="United States",
                confidence=-0.1
            )

    def test_to_dict(self):
        """Test conversion to dictionary."""
        entity = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States",
            wikidata_id="Q30",
            aliases=["USA", "United States of America"]
        )

        result = entity.to_dict()

        assert result["entity_id"] == "US"
        assert result["entity_type"] == EntityType.COUNTRY
        assert result["name"] == "United States"
        assert result["wikidata_id"] == "Q30"
        assert result["aliases"] == ["USA", "United States of America"]
        assert "confidence" not in result  # exclude_none=True

    def test_to_graph_node(self):
        """Test conversion to Neo4j node properties."""
        created_at = datetime(2025, 1, 1, 12, 0, 0)

        entity = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States",
            wikidata_id="Q30",
            aliases=["USA"],
            created_at=created_at,
            source_count=3
        )

        result = entity.to_graph_node()

        assert result["entity_id"] == "US"
        assert result["entity_type"] == "COUNTRY"
        assert result["name"] == "United States"
        assert result["wikidata_id"] == "Q30"
        assert result["aliases"] == ["USA"]
        assert result["created_at"] == "2025-01-01T12:00:00"
        assert result["source_count"] == 3

    def test_to_graph_label(self):
        """Test Neo4j node label generation."""
        entity = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States"
        )

        assert entity.to_graph_label() == "Entity:COUNTRY"

        entity2 = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc."
        )

        assert entity2.to_graph_label() == "Entity:COMPANY"

    def test_str_representation(self):
        """Test string representation."""
        entity = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States"
        )

        assert str(entity) == "COUNTRY:US (United States)"

    def test_hash_and_equality(self):
        """Test hashing for deduplication."""
        entity1 = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States"
        )

        entity2 = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States of America"  # Different name, same ID
        )

        # Same hash (based on entity_id and entity_type)
        assert hash(entity1) == hash(entity2)

        # Can be used in sets
        entity_set = {entity1, entity2}
        assert len(entity_set) == 1  # Deduplicated


class TestRelationshipHint:
    """Tests for RelationshipHint model."""

    def test_minimal_relationship_hint(self):
        """Test creating relationship hint with required fields only."""
        source = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc."
        )

        target = EntityReference(
            entity_id="NASDAQ",
            entity_type=EntityType.MARKET,
            name="NASDAQ"
        )

        hint = RelationshipHint(
            source=source,
            target=target,
            relationship_type=RelationshipType.IMPACTS_STOCK
        )

        assert hint.source == source
        assert hint.target == target
        assert hint.relationship_type == RelationshipType.IMPACTS_STOCK
        assert hint.confidence == 0.7  # Default value
        assert hint.properties == {}
        assert hint.evidence is None
        assert hint.bidirectional is False

    def test_full_relationship_hint(self):
        """Test creating relationship hint with all fields."""
        source = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc."
        )

        target = EntityReference(
            entity_id="NASDAQ",
            entity_type=EntityType.MARKET,
            name="NASDAQ"
        )

        hint = RelationshipHint(
            source=source,
            target=target,
            relationship_type=RelationshipType.IMPACTS_STOCK,
            confidence=0.92,
            properties={"impact_magnitude": "high", "timeframe": "immediate"},
            evidence="Tesla stock price surged 12% on NASDAQ after earnings report.",
            bidirectional=False
        )

        assert hint.confidence == 0.92
        assert hint.properties["impact_magnitude"] == "high"
        assert "earnings report" in hint.evidence
        assert hint.bidirectional is False

    def test_located_in_validation_success(self):
        """Test valid LOCATED_IN relationship."""
        source = EntityReference(
            entity_id="TSLA-FACTORY-1",
            entity_type=EntityType.CRITICAL_INFRASTRUCTURE,
            name="Tesla Gigafactory Texas"
        )

        target = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States"
        )

        hint = RelationshipHint(
            source=source,
            target=target,
            relationship_type=RelationshipType.LOCATED_IN
        )

        assert hint.relationship_type == RelationshipType.LOCATED_IN

    def test_located_in_validation_failure_invalid_source(self):
        """Test invalid LOCATED_IN relationship (wrong source type)."""
        source = EntityReference(
            entity_id="NASDAQ",
            entity_type=EntityType.MARKET,  # Markets can't be "located in" places
            name="NASDAQ"
        )

        target = EntityReference(
            entity_id="US",
            entity_type=EntityType.COUNTRY,
            name="United States"
        )

        with pytest.raises(ValidationError) as exc_info:
            RelationshipHint(
                source=source,
                target=target,
                relationship_type=RelationshipType.LOCATED_IN
            )
        assert "physical entity" in str(exc_info.value)

    def test_located_in_validation_failure_invalid_target(self):
        """Test invalid LOCATED_IN relationship (wrong target type)."""
        source = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc."
        )

        target = EntityReference(
            entity_id="NASDAQ",
            entity_type=EntityType.MARKET,  # Markets can't be locations
            name="NASDAQ"
        )

        with pytest.raises(ValidationError) as exc_info:
            RelationshipHint(
                source=source,
                target=target,
                relationship_type=RelationshipType.LOCATED_IN
            )
        assert "location/country" in str(exc_info.value)

    def test_to_cypher_params(self):
        """Test conversion to Cypher query parameters."""
        source = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc."
        )

        target = EntityReference(
            entity_id="NASDAQ",
            entity_type=EntityType.MARKET,
            name="NASDAQ"
        )

        hint = RelationshipHint(
            source=source,
            target=target,
            relationship_type=RelationshipType.IMPACTS_STOCK,
            confidence=0.85,
            properties={"impact": "positive"},
            evidence="Stock surged 12%",
            bidirectional=False
        )

        result = hint.to_cypher_params()

        assert result["source_id"] == "TSLA"
        assert result["source_type"] == "COMPANY"
        assert result["relationship_type"] == "IMPACTS_STOCK"
        assert result["target_id"] == "NASDAQ"
        assert result["target_type"] == "MARKET"
        assert result["confidence"] == 0.85
        assert result["properties"]["impact"] == "positive"
        assert result["evidence"] == "Stock surged 12%"
        assert result["bidirectional"] is False

    def test_str_representation(self):
        """Test string representation."""
        source = EntityReference(
            entity_id="TSLA",
            entity_type=EntityType.COMPANY,
            name="Tesla Inc."
        )

        target = EntityReference(
            entity_id="NASDAQ",
            entity_type=EntityType.MARKET,
            name="NASDAQ"
        )

        # Directional relationship
        hint = RelationshipHint(
            source=source,
            target=target,
            relationship_type=RelationshipType.IMPACTS_STOCK,
            confidence=0.85
        )

        assert "Tesla Inc. → [IMPACTS_STOCK] → NASDAQ" in str(hint)
        assert "0.85" in str(hint)

        # Bidirectional relationship
        hint2 = RelationshipHint(
            source=source,
            target=target,
            relationship_type=RelationshipType.RELATED_TO,
            confidence=0.75,
            bidirectional=True
        )

        assert "Tesla Inc. ↔ [RELATED_TO] ↔ NASDAQ" in str(hint2)


class TestConfidenceMetadata:
    """Tests for ConfidenceMetadata model."""

    def test_minimal_confidence_metadata(self):
        """Test creating confidence metadata with required fields only."""
        metadata = ConfidenceMetadata(overall_confidence=0.85)

        assert metadata.overall_confidence == 0.85
        assert metadata.supporting_agents == []
        assert metadata.evidence_count == 1  # Default
        assert metadata.source_count == 1  # Default
        assert metadata.extraction_confidence is None
        assert metadata.validation_confidence is None
        assert metadata.is_validated is False
        assert metadata.validation_method is None

    def test_full_confidence_metadata(self):
        """Test creating confidence metadata with all fields."""
        metadata = ConfidenceMetadata(
            overall_confidence=0.92,
            supporting_agents=["claude-3.5-sonnet", "gpt-4"],
            evidence_count=3,
            source_count=2,
            extraction_confidence=0.95,
            validation_confidence=0.89,
            is_validated=True,
            validation_method="OSS_cross_check"
        )

        assert metadata.overall_confidence == 0.92
        assert metadata.supporting_agents == ["claude-3.5-sonnet", "gpt-4"]
        assert metadata.evidence_count == 3
        assert metadata.source_count == 2
        assert metadata.extraction_confidence == 0.95
        assert metadata.validation_confidence == 0.89
        assert metadata.is_validated is True
        assert metadata.validation_method == "OSS_cross_check"

    def test_derive_uncertainty_low(self):
        """Test uncertainty derivation for high confidence."""
        metadata = ConfidenceMetadata(overall_confidence=0.92)
        assert metadata.derive_uncertainty() == "low"

        metadata2 = ConfidenceMetadata(overall_confidence=0.80)
        assert metadata2.derive_uncertainty() == "low"

    def test_derive_uncertainty_moderate(self):
        """Test uncertainty derivation for moderate confidence."""
        metadata = ConfidenceMetadata(overall_confidence=0.65)
        assert metadata.derive_uncertainty() == "moderate"

        metadata2 = ConfidenceMetadata(overall_confidence=0.50)
        assert metadata2.derive_uncertainty() == "moderate"

    def test_derive_uncertainty_high(self):
        """Test uncertainty derivation for low confidence."""
        metadata = ConfidenceMetadata(overall_confidence=0.45)
        assert metadata.derive_uncertainty() == "high"

        metadata2 = ConfidenceMetadata(overall_confidence=0.10)
        assert metadata2.derive_uncertainty() == "high"

    def test_should_trigger_review_default_threshold(self):
        """Test review trigger with default threshold (0.6)."""
        # Above threshold - no review
        metadata = ConfidenceMetadata(overall_confidence=0.75)
        assert metadata.should_trigger_review() is False

        # Below threshold - trigger review
        metadata2 = ConfidenceMetadata(overall_confidence=0.45)
        assert metadata2.should_trigger_review() is True

        # At threshold - no review
        metadata3 = ConfidenceMetadata(overall_confidence=0.60)
        assert metadata3.should_trigger_review() is False

    def test_should_trigger_review_custom_threshold(self):
        """Test review trigger with custom threshold."""
        metadata = ConfidenceMetadata(overall_confidence=0.75)

        # Higher threshold
        assert metadata.should_trigger_review(threshold=0.8) is True

        # Lower threshold
        assert metadata.should_trigger_review(threshold=0.5) is False

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = ConfidenceMetadata(
            overall_confidence=0.85,
            supporting_agents=["claude-3.5-sonnet"],
            is_validated=True
        )

        result = metadata.to_dict()

        assert result["overall_confidence"] == 0.85
        assert result["supporting_agents"] == ["claude-3.5-sonnet"]
        assert result["is_validated"] is True
        assert result["uncertainty"] == "low"  # Derived field

    def test_str_representation(self):
        """Test string representation."""
        metadata = ConfidenceMetadata(
            overall_confidence=0.85,
            is_validated=True
        )

        s = str(metadata)
        assert "0.85" in s
        assert "low" in s  # uncertainty
        assert "✓" in s  # validated

        metadata2 = ConfidenceMetadata(
            overall_confidence=0.45,
            is_validated=False
        )

        s2 = str(metadata2)
        assert "0.45" in s2
        assert "high" in s2  # uncertainty
        assert "✗" in s2  # not validated

    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence
        metadata = ConfidenceMetadata(overall_confidence=0.85)
        assert metadata.overall_confidence == 0.85

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            ConfidenceMetadata(overall_confidence=1.5)

        # Invalid confidence (negative)
        with pytest.raises(ValidationError):
            ConfidenceMetadata(overall_confidence=-0.1)

    def test_evidence_count_validation(self):
        """Test evidence count validation."""
        # Valid evidence count
        metadata = ConfidenceMetadata(
            overall_confidence=0.85,
            evidence_count=3
        )
        assert metadata.evidence_count == 3

        # Invalid evidence count (zero)
        with pytest.raises(ValidationError):
            ConfidenceMetadata(
                overall_confidence=0.85,
                evidence_count=0
            )

        # Invalid evidence count (negative)
        with pytest.raises(ValidationError):
            ConfidenceMetadata(
                overall_confidence=0.85,
                evidence_count=-1
            )
