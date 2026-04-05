"""
Tests for ontology_schema.py

Tests EntityType and RelationshipType enums plus helper methods.
"""

import pytest
from news_mcp_common.ontology import (
    EntityType,
    RelationshipType,
    REQUIRED_PROPERTIES,
    RECOMMENDED_PROPERTIES,
    ENTITY_ID_PATTERNS,
)


class TestEntityType:
    """Tests for EntityType enum."""

    def test_entity_type_values(self):
        """Test that all expected entity types exist."""
        assert EntityType.COMPANY == "COMPANY"
        assert EntityType.CRITICAL_INFRASTRUCTURE == "CRITICAL_INFRASTRUCTURE"
        assert EntityType.WEAPON_SYSTEM == "WEAPON_SYSTEM"
        assert EntityType.COUNTRY == "COUNTRY"
        assert EntityType.ORGANIZATION == "ORGANIZATION"
        assert EntityType.PERSON == "PERSON"
        assert EntityType.LOCATION == "LOCATION"
        assert EntityType.MARKET == "MARKET"
        assert EntityType.UNKNOWN == "UNKNOWN"
        assert EntityType.CONCEPT == "CONCEPT"

    def test_get_mvo_phase1_types(self):
        """Test MVO Phase 1 types list."""
        mvo_types = EntityType.get_mvo_phase1_types()

        # Should include 8 types (excluding UNKNOWN and CONCEPT)
        assert len(mvo_types) == 8

        # Should include core types
        assert EntityType.COMPANY in mvo_types
        assert EntityType.CRITICAL_INFRASTRUCTURE in mvo_types
        assert EntityType.WEAPON_SYSTEM in mvo_types
        assert EntityType.COUNTRY in mvo_types
        assert EntityType.ORGANIZATION in mvo_types
        assert EntityType.PERSON in mvo_types
        assert EntityType.LOCATION in mvo_types
        assert EntityType.MARKET in mvo_types

        # Should NOT include fallback types
        assert EntityType.UNKNOWN not in mvo_types
        assert EntityType.CONCEPT not in mvo_types

    def test_is_mvo_phase1(self):
        """Test MVO Phase 1 membership check."""
        # MVO Phase 1 types
        assert EntityType.is_mvo_phase1(EntityType.COMPANY) is True
        assert EntityType.is_mvo_phase1(EntityType.COUNTRY) is True
        assert EntityType.is_mvo_phase1(EntityType.PERSON) is True

        # Fallback types
        assert EntityType.is_mvo_phase1(EntityType.UNKNOWN) is False
        assert EntityType.is_mvo_phase1(EntityType.CONCEPT) is False

    def test_entity_type_string_conversion(self):
        """Test that entity types can be used as strings."""
        assert str(EntityType.COMPANY) == "COMPANY"
        assert EntityType.COMPANY.value == "COMPANY"


class TestRelationshipType:
    """Tests for RelationshipType enum."""

    def test_relationship_type_values(self):
        """Test that all expected relationship types exist."""
        assert RelationshipType.DISRUPTS_OPERATIONS == "DISRUPTS_OPERATIONS"
        assert RelationshipType.DISRUPTS_SUPPLY_CHAIN == "DISRUPTS_SUPPLY_CHAIN"
        assert RelationshipType.IMPACTS_STOCK == "IMPACTS_STOCK"
        assert RelationshipType.ATTACKS == "ATTACKS"
        assert RelationshipType.VIOLATES_IHL == "VIOLATES_IHL"
        assert RelationshipType.WORKS_FOR == "WORKS_FOR"
        assert RelationshipType.LOCATED_IN == "LOCATED_IN"
        assert RelationshipType.RELATED_TO == "RELATED_TO"

    def test_get_mvo_phase1_types(self):
        """Test MVO Phase 1 relationship types list."""
        mvo_types = RelationshipType.get_mvo_phase1_types()

        # Should include 7 types (excluding RELATED_TO)
        assert len(mvo_types) == 7

        # Should include core types
        assert RelationshipType.DISRUPTS_OPERATIONS in mvo_types
        assert RelationshipType.DISRUPTS_SUPPLY_CHAIN in mvo_types
        assert RelationshipType.IMPACTS_STOCK in mvo_types
        assert RelationshipType.ATTACKS in mvo_types
        assert RelationshipType.VIOLATES_IHL in mvo_types
        assert RelationshipType.LOCATED_IN in mvo_types
        assert RelationshipType.WORKS_FOR in mvo_types

        # Should NOT include fallback type
        assert RelationshipType.RELATED_TO not in mvo_types

    def test_is_mvo_phase1(self):
        """Test MVO Phase 1 membership check."""
        # MVO Phase 1 types
        assert RelationshipType.is_mvo_phase1(RelationshipType.DISRUPTS_OPERATIONS) is True
        assert RelationshipType.is_mvo_phase1(RelationshipType.ATTACKS) is True
        assert RelationshipType.is_mvo_phase1(RelationshipType.LOCATED_IN) is True

        # Fallback type
        assert RelationshipType.is_mvo_phase1(RelationshipType.RELATED_TO) is False

    def test_get_intelligence_types(self):
        """Test intelligence relationship types list."""
        intel_types = RelationshipType.get_intelligence_types()

        # Should include 5 types
        assert len(intel_types) == 5

        # Intelligence types
        assert RelationshipType.DISRUPTS_OPERATIONS in intel_types
        assert RelationshipType.DISRUPTS_SUPPLY_CHAIN in intel_types
        assert RelationshipType.IMPACTS_STOCK in intel_types
        assert RelationshipType.ATTACKS in intel_types
        assert RelationshipType.VIOLATES_IHL in intel_types

        # Non-intelligence types
        assert RelationshipType.WORKS_FOR not in intel_types
        assert RelationshipType.LOCATED_IN not in intel_types

    def test_is_directional(self):
        """Test directional relationship check."""
        # Directional relationships
        assert RelationshipType.is_directional(RelationshipType.DISRUPTS_OPERATIONS) is True
        assert RelationshipType.is_directional(RelationshipType.ATTACKS) is True
        assert RelationshipType.is_directional(RelationshipType.WORKS_FOR) is True

        # Non-directional relationship (for now, RELATED_TO is not directional)
        # Note: If LOCATED_IN becomes bidirectional, update this test
        assert RelationshipType.is_directional(RelationshipType.LOCATED_IN) is True


class TestConstants:
    """Tests for module-level constants."""

    def test_required_properties(self):
        """Test required properties list."""
        assert "entity_id" in REQUIRED_PROPERTIES
        assert "entity_type" in REQUIRED_PROPERTIES
        assert "name" in REQUIRED_PROPERTIES
        assert len(REQUIRED_PROPERTIES) == 3

    def test_recommended_properties(self):
        """Test recommended properties list."""
        assert "wikidata_id" in RECOMMENDED_PROPERTIES
        assert "aliases" in RECOMMENDED_PROPERTIES
        assert "confidence" in RECOMMENDED_PROPERTIES
        assert "source_count" in RECOMMENDED_PROPERTIES
        assert "created_at" in RECOMMENDED_PROPERTIES
        assert "last_seen" in RECOMMENDED_PROPERTIES
        assert len(RECOMMENDED_PROPERTIES) == 6

    def test_entity_id_patterns(self):
        """Test entity ID regex patterns."""
        import re

        # COUNTRY pattern: ISO 3166-1 alpha-2 (2 uppercase letters)
        country_pattern = ENTITY_ID_PATTERNS[EntityType.COUNTRY]
        assert re.match(country_pattern, "US") is not None
        assert re.match(country_pattern, "RU") is not None
        assert re.match(country_pattern, "UA") is not None
        assert re.match(country_pattern, "USA") is None  # Too long
        assert re.match(country_pattern, "us") is None  # Lowercase

        # COMPANY pattern: Stock ticker (1-5 uppercase letters)
        company_pattern = ENTITY_ID_PATTERNS[EntityType.COMPANY]
        assert re.match(company_pattern, "TSLA") is not None
        assert re.match(company_pattern, "AAPL") is not None
        assert re.match(company_pattern, "A") is not None
        assert re.match(company_pattern, "ABCDE") is not None
        assert re.match(company_pattern, "ABCDEF") is None  # Too long
        assert re.match(company_pattern, "tsla") is None  # Lowercase
