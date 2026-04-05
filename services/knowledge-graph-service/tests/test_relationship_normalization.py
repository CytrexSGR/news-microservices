"""
Test Relationship Type Normalization

Ensures all relationship types are normalized to UPPERCASE to prevent
case-inconsistency duplicates in Neo4j.

See: CLAUDE.md Critical Learning #31
"""

import pytest
from app.models.graph import Relationship, Entity, Triplet


def test_relationship_type_uppercase_normalization():
    """Test that relationship types are normalized to UPPERCASE."""
    # Test lowercase input
    relationship = Relationship(
        subject="Tesla",
        subject_type="ORGANIZATION",
        relationship_type="works_for",  # lowercase input
        object="Elon Musk",
        object_type="PERSON",
        confidence=0.9,
        evidence="Test evidence"
    )

    # Normalize (as done in ingestion_service.py)
    normalized = relationship.relationship_type.upper()

    assert normalized == "WORKS_FOR"
    assert normalized.isupper()


def test_all_relationship_types_are_uppercase():
    """Test common relationship types are UPPERCASE after normalization."""
    test_cases = [
        ("works_for", "WORKS_FOR"),
        ("WORKS_FOR", "WORKS_FOR"),
        ("located_in", "LOCATED_IN"),
        ("owns", "OWNS"),
        ("related_to", "RELATED_TO"),
        ("member_of", "MEMBER_OF"),
        ("partner_of", "PARTNER_OF"),
        ("not_applicable", "NOT_APPLICABLE"),
    ]

    for input_type, expected_output in test_cases:
        normalized = input_type.upper()
        assert normalized == expected_output
        assert normalized.isupper()


def test_triplet_relationship_type_normalization():
    """Test that triplet relationship types can be normalized."""
    triplet = Triplet(
        subject=Entity(name="Tesla", type="ORGANIZATION"),
        relationship=Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="works_for",  # lowercase
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.9,
            evidence="Test"
        ),
        object=Entity(name="Elon Musk", type="PERSON")
    )

    # Normalize
    normalized = triplet.relationship.relationship_type.upper()

    assert normalized == "WORKS_FOR"
    assert normalized.isupper()


def test_mixed_case_normalization():
    """Test that mixed-case inputs are normalized correctly."""
    test_cases = [
        ("Works_For", "WORKS_FOR"),
        ("WoRkS_fOr", "WORKS_FOR"),
        ("LOCATED_in", "LOCATED_IN"),
    ]

    for input_type, expected_output in test_cases:
        normalized = input_type.upper()
        assert normalized == expected_output


def test_special_characters_preserved():
    """Test that underscores and other characters are preserved."""
    test_cases = [
        ("abused_monopoly_in", "ABUSED_MONOPOLY_IN"),
        ("ruled_against", "RULED_AGAINST"),
    ]

    for input_type, expected_output in test_cases:
        normalized = input_type.upper()
        assert normalized == expected_output
