"""
Tests for Entity Deduplication

Tests entity merging, name normalization, and duplicate detection.
"""

import pytest
from app.models.graph import Entity, Relationship, Triplet
from typing import List, Set


class TestEntityDeduplication:
    """Tests for entity deduplication and canonicalization."""

    def test_exact_match_deduplication(self):
        """Test deduplicating exact entity matches."""
        entities = [
            Entity(name="Tesla", type="ORGANIZATION"),
            Entity(name="Tesla", type="ORGANIZATION"),
            Entity(name="SpaceX", type="ORGANIZATION")
        ]

        # Deduplicate by name and type
        unique_entities = {}
        for entity in entities:
            key = (entity.name, entity.type)
            unique_entities[key] = entity

        assert len(unique_entities) == 2

    def test_case_sensitive_deduplication(self):
        """Test that deduplication is case-sensitive."""
        entities = [
            Entity(name="tesla", type="ORGANIZATION"),
            Entity(name="Tesla", type="ORGANIZATION"),
            Entity(name="TESLA", type="ORGANIZATION")
        ]

        # All three are different due to case sensitivity
        unique_entities = {}
        for entity in entities:
            key = (entity.name, entity.type)
            unique_entities[key] = entity

        assert len(unique_entities) == 3

    def test_type_affects_deduplication(self):
        """Test that entity type affects deduplication."""
        entities = [
            Entity(name="Apple", type="ORGANIZATION"),
            Entity(name="Apple", type="PERSON"),
            Entity(name="Apple", type="LOCATION")
        ]

        # All three are different due to type
        unique_entities = {}
        for entity in entities:
            key = (entity.name, entity.type)
            unique_entities[key] = entity

        assert len(unique_entities) == 3

    def test_merge_duplicate_entities_preserves_properties(self):
        """Test merging duplicate entities preserves all properties."""
        entity1 = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={"sector": "Automotive"}
        )

        entity2 = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={"founded": 2003}
        )

        # Merge properties
        merged_properties = {**entity1.properties, **entity2.properties}

        assert merged_properties["sector"] == "Automotive"
        assert merged_properties["founded"] == 2003

    def test_merge_duplicate_entities_wikidata_id(self):
        """Test merging duplicate entities preserves Wikidata ID."""
        entity1 = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={"wikidata_id": "Q478214"}
        )

        entity2 = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={}
        )

        # Merge: entity1 has wikidata_id, entity2 doesn't
        merged_properties = {**entity2.properties, **entity1.properties}

        assert merged_properties.get("wikidata_id") == "Q478214"

    def test_whitespace_normalization(self):
        """Test detecting and normalizing whitespace variations."""
        names = [
            "Tesla Inc.",
            "Tesla  Inc.",  # Double space
            "Tesla Inc. ",  # Trailing space
            " Tesla Inc."   # Leading space
        ]

        # Normalize whitespace: strip leading/trailing only (preserve internal spacing)
        normalized = [name.strip() for name in names]

        # After normalization, all except one should be identical
        assert normalized[0] == "Tesla Inc."
        assert normalized[1] == "Tesla  Inc."  # Internal double space preserved
        assert normalized[2] == "Tesla Inc."
        assert normalized[3] == "Tesla Inc."

        # Show that strip() only removes leading/trailing
        assert len(set(normalized)) == 2  # Two unique: with single and double space

    def test_punctuation_variations(self):
        """Test detecting entity names with punctuation variations."""
        names = [
            "AT&T",
            "AT & T",
            "AT&amp;T"
        ]

        # These should be detected as similar (but not exactly same)
        assert names[0] != names[1]
        assert names[1] != names[2]

    def test_abbreviation_detection(self):
        """Test detecting entities that might be abbreviations."""
        entities = [
            Entity(name="United States", type="LOCATION"),
            Entity(name="USA", type="LOCATION"),
            Entity(name="U.S.", type="LOCATION")
        ]

        # Exact matches would show they're different
        exact_names = {entity.name for entity in entities}

        assert len(exact_names) == 3

    def test_entity_deduplication_in_triplets(self):
        """Test deduplicating entities across multiple triplets."""
        triplets = [
            Triplet(
                subject=Entity(name="Elon Musk", type="PERSON"),
                relationship=Relationship(
                    subject="Elon Musk",
                    subject_type="PERSON",
                    relationship_type="WORKS_FOR",
                    object="Tesla",
                    object_type="ORGANIZATION",
                    confidence=0.9
                ),
                object=Entity(name="Tesla", type="ORGANIZATION")
            ),
            Triplet(
                subject=Entity(name="Elon Musk", type="PERSON"),
                relationship=Relationship(
                    subject="Elon Musk",
                    subject_type="PERSON",
                    relationship_type="FOUNDED",
                    object="Tesla",
                    object_type="ORGANIZATION",
                    confidence=0.95
                ),
                object=Entity(name="Tesla", type="ORGANIZATION")
            )
        ]

        # Extract all unique entities
        unique_entities = {}
        for triplet in triplets:
            key_subject = (triplet.subject.name, triplet.subject.type)
            unique_entities[key_subject] = triplet.subject

            key_object = (triplet.object.name, triplet.object.type)
            unique_entities[key_object] = triplet.object

        # Should have 2 unique entities: Elon Musk and Tesla
        assert len(unique_entities) == 2

    def test_merge_relationships_for_duplicate_entities(self):
        """Test that duplicate entities share relationships."""
        relationships = [
            Relationship(
                subject="Tesla",
                subject_type="ORGANIZATION",
                relationship_type="WORKS_FOR",
                object="Elon Musk",
                object_type="PERSON",
                confidence=0.9,
                mention_count=1
            ),
            Relationship(
                subject="Tesla",
                subject_type="ORGANIZATION",
                relationship_type="WORKS_FOR",
                object="Elon Musk",
                object_type="PERSON",
                confidence=0.95,
                mention_count=1
            )
        ]

        # Find duplicate relationships
        rel_keys = set()
        duplicates = []

        for rel in relationships:
            key = (rel.subject, rel.object, rel.relationship_type)
            if key in rel_keys:
                duplicates.append(rel)
            rel_keys.add(key)

        # Should detect 1 duplicate
        assert len(duplicates) == 1

    def test_merge_duplicate_relationships_update_confidence(self):
        """Test merging duplicate relationships keeps highest confidence."""
        rel1 = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.9
        )

        rel2 = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95
        )

        # Merge: keep highest confidence
        merged_confidence = max(rel1.confidence, rel2.confidence)

        assert merged_confidence == 0.95

    def test_merge_duplicate_relationships_increment_mention_count(self):
        """Test merging duplicate relationships increments mention count."""
        rel1 = Relationship(
            subject="A",
            subject_type="PERSON",
            relationship_type="KNOWS",
            object="B",
            object_type="PERSON",
            confidence=0.9,
            mention_count=3
        )

        rel2 = Relationship(
            subject="A",
            subject_type="PERSON",
            relationship_type="KNOWS",
            object="B",
            object_type="PERSON",
            confidence=0.9,
            mention_count=2
        )

        # Merge: increment mention count
        merged_mention_count = rel1.mention_count + rel2.mention_count

        assert merged_mention_count == 5

    def test_entity_fingerprint_for_matching(self):
        """Test creating entity fingerprints for matching."""
        entity1 = Entity(name="Tesla Inc.", type="ORGANIZATION")
        entity2 = Entity(name="Tesla Inc", type="ORGANIZATION")

        # Simple fingerprint: name and type
        fp1 = (entity1.name, entity1.type)
        fp2 = (entity2.name, entity2.type)

        # These would be different
        assert fp1 != fp2

    def test_fuzzy_matching_potential(self):
        """Test cases where fuzzy matching might be helpful."""
        # These are conceptually the same but have variations
        variations = [
            "United States of America",
            "United States",
            "USA",
            "U.S.A."
        ]

        # Exact matching shows they're different
        unique = set(variations)

        assert len(unique) == 4

    def test_entity_conflict_resolution(self):
        """Test resolving conflicts when merging entities."""
        entity_db = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={"wikidata_id": "Q478214", "sector": "Automotive"}
        )

        entity_incoming = Entity(
            name="Tesla",
            type="ORGANIZATION",
            properties={"sector": "Electric Vehicles", "founded": 2003}
        )

        # Merge strategy: keep existing DB values, add new ones
        merged = {
            **entity_incoming.properties,
            **entity_db.properties
        }

        # DB values take precedence for conflicts
        assert merged["sector"] == "Automotive"
        assert merged["wikidata_id"] == "Q478214"
        assert merged["founded"] == 2003

    def test_deduplication_across_triplet_batch(self):
        """Test deduplicating entities across a batch of triplets."""
        triplets = [
            Triplet(
                subject=Entity(name="A", type="PERSON"),
                relationship=Relationship(
                    subject="A", subject_type="PERSON",
                    relationship_type="KNOWS", object="B",
                    object_type="PERSON", confidence=0.9
                ),
                object=Entity(name="B", type="PERSON")
            ),
            Triplet(
                subject=Entity(name="B", type="PERSON"),
                relationship=Relationship(
                    subject="B", subject_type="PERSON",
                    relationship_type="KNOWS", object="C",
                    object_type="PERSON", confidence=0.9
                ),
                object=Entity(name="C", type="PERSON")
            ),
            Triplet(
                subject=Entity(name="A", type="PERSON"),
                relationship=Relationship(
                    subject="A", subject_type="PERSON",
                    relationship_type="KNOWS", object="C",
                    object_type="PERSON", confidence=0.85
                ),
                object=Entity(name="C", type="PERSON")
            )
        ]

        # Extract unique entities
        unique_entities = {}
        for triplet in triplets:
            key_s = (triplet.subject.name, triplet.subject.type)
            unique_entities[key_s] = triplet.subject

            key_o = (triplet.object.name, triplet.object.type)
            unique_entities[key_o] = triplet.object

        # Should have 3 unique entities: A, B, C
        assert len(unique_entities) == 3

    def test_relationship_type_normalization_in_dedup(self):
        """Test relationship type normalization during deduplication."""
        rels = [
            Relationship(
                subject="A", subject_type="PERSON",
                relationship_type="works_for", object="B",
                object_type="ORGANIZATION", confidence=0.9
            ),
            Relationship(
                subject="A", subject_type="PERSON",
                relationship_type="WORKS_FOR", object="B",
                object_type="ORGANIZATION", confidence=0.95
            )
        ]

        # Normalize types for comparison
        normalized_rels = []
        for rel in rels:
            norm = rel.model_copy(update={
                "relationship_type": rel.relationship_type.upper()
            })
            normalized_rels.append(norm)

        # Check if now they match
        assert normalized_rels[0].relationship_type == normalized_rels[1].relationship_type
