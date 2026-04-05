"""
Tests for Entity Creation in Neo4j

Tests entity node creation, validation, and deduplication.
"""

import pytest
from datetime import datetime
from app.models.graph import Entity, Relationship, Triplet


class TestEntityCreation:
    """Tests for Entity model creation."""

    def test_entity_creation_basic(self):
        """Test basic entity creation."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION"
        )

        assert entity.name == "Tesla"
        assert entity.type == "ORGANIZATION"
        assert entity.properties == {}
        assert entity.created_at is None
        assert entity.last_seen is None

    def test_entity_creation_with_properties(self):
        """Test entity creation with properties."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={
                "wikidata_id": "Q478214",
                "sector": "Automotive",
                "founded": 2003
            }
        )

        assert entity.properties["wikidata_id"] == "Q478214"
        assert entity.properties["sector"] == "Automotive"
        assert entity.properties["founded"] == 2003

    def test_entity_creation_with_timestamps(self):
        """Test entity creation with timestamps."""
        now = datetime.utcnow()
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION",
            created_at=now,
            last_seen=now
        )

        assert entity.created_at == now
        assert entity.last_seen == now

    def test_entity_name_required(self):
        """Test that entity name is required."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Entity(type="ORGANIZATION")

    def test_entity_type_required(self):
        """Test that entity type is required."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Entity(name="Tesla")

    def test_entity_type_person(self):
        """Test PERSON entity type."""
        entity = Entity(
            name="Elon Musk",
            type="PERSON"
        )

        assert entity.type == "PERSON"

    def test_entity_type_organization(self):
        """Test ORGANIZATION entity type."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION"
        )

        assert entity.type == "ORGANIZATION"

    def test_entity_type_location(self):
        """Test LOCATION entity type."""
        entity = Entity(
            name="United States",
            type="LOCATION"
        )

        assert entity.type == "LOCATION"

    def test_entity_type_event(self):
        """Test EVENT entity type."""
        entity = Entity(
            name="Paris Climate Agreement",
            type="EVENT"
        )

        assert entity.type == "EVENT"

    def test_entity_properties_dict(self):
        """Test entity properties are stored as dict."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={"sector": "Automotive", "stock": "TSLA"}
        )

        assert isinstance(entity.properties, dict)
        assert len(entity.properties) == 2

    def test_entity_properties_empty_default(self):
        """Test entity properties default to empty dict."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION"
        )

        assert entity.properties == {}

    def test_entity_with_nested_properties(self):
        """Test entity with nested properties."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={
                "metadata": {
                    "sector": "Automotive",
                    "founded": 2003
                },
                "wikidata_id": "Q478214"
            }
        )

        assert entity.properties["metadata"]["sector"] == "Automotive"

    def test_entity_name_case_sensitive(self):
        """Test that entity names are case-sensitive."""
        entity1 = Entity(name="tesla", type="ORGANIZATION")
        entity2 = Entity(name="Tesla", type="ORGANIZATION")

        assert entity1.name != entity2.name

    def test_entity_type_case_sensitive(self):
        """Test that entity types are case-sensitive."""
        entity1 = Entity(name="Tesla", type="organization")
        entity2 = Entity(name="Tesla", type="ORGANIZATION")

        assert entity1.type != entity2.type

    def test_entity_serialization(self):
        """Test entity serialization to dict."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={"sector": "Automotive"}
        )

        data = entity.model_dump()

        assert data["name"] == "Tesla"
        assert data["type"] == "ORGANIZATION"
        assert data["properties"]["sector"] == "Automotive"

    def test_entity_json_schema(self):
        """Test entity JSON schema."""
        schema = Entity.model_json_schema()

        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "type" in schema["properties"]
        assert "properties" in schema["properties"]

    def test_entity_equality(self):
        """Test entity equality comparison."""
        entity1 = Entity(name="Tesla", type="ORGANIZATION")
        entity2 = Entity(name="Tesla", type="ORGANIZATION")

        # Should be equal if same name and type
        assert entity1.model_dump() == entity2.model_dump()

    def test_entity_inequality_by_name(self):
        """Test entity inequality when names differ."""
        entity1 = Entity(name="Tesla", type="ORGANIZATION")
        entity2 = Entity(name="SpaceX", type="ORGANIZATION")

        assert entity1.model_dump() != entity2.model_dump()

    def test_entity_inequality_by_type(self):
        """Test entity inequality when types differ."""
        entity1 = Entity(name="Tesla", type="ORGANIZATION")
        entity2 = Entity(name="Tesla", type="PERSON")

        assert entity1.model_dump() != entity2.model_dump()

    def test_entity_wikidata_integration(self):
        """Test entity with Wikidata ID."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={"wikidata_id": "Q478214"}
        )

        assert entity.properties["wikidata_id"] == "Q478214"

    def test_entity_timestamp_ordering(self):
        """Test entity timestamp consistency."""
        now = datetime.utcnow()
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION",
            created_at=now,
            last_seen=now
        )

        assert entity.created_at == entity.last_seen

    def test_entity_with_null_timestamps(self):
        """Test entity with null timestamps."""
        entity = Entity(
            name="Tesla",
            type="ORGANIZATION",
            created_at=None,
            last_seen=None
        )

        assert entity.created_at is None
        assert entity.last_seen is None

    def test_entity_complex_name(self):
        """Test entity with complex name."""
        entity = Entity(
            name="Dr. Alan Turing (1912-1954)",
            type="PERSON"
        )

        assert entity.name == "Dr. Alan Turing (1912-1954)"

    def test_entity_special_characters_in_name(self):
        """Test entity with special characters in name."""
        entity = Entity(
            name="O'Brien's Company Inc.",
            type="ORGANIZATION"
        )

        assert entity.name == "O'Brien's Company Inc."

    def test_entity_unicode_name(self):
        """Test entity with unicode characters."""
        entity = Entity(
            name="中国人民銀行",
            type="ORGANIZATION"
        )

        assert entity.name == "中国人民銀行"

    def test_entity_unicode_properties(self):
        """Test entity with unicode properties."""
        entity = Entity(
            name="Tokyo",
            type="LOCATION",
            properties={"country": "日本"}
        )

        assert entity.properties["country"] == "日本"
