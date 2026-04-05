"""
Tests for Relationship Queries

Tests relationship model, query building, and filtering.
"""

import pytest
from datetime import datetime
from app.models.graph import Relationship, Entity, Triplet, GraphEdge


class TestRelationshipCreation:
    """Tests for Relationship model creation."""

    def test_relationship_creation_basic(self):
        """Test basic relationship creation."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95
        )

        assert rel.subject == "Tesla"
        assert rel.subject_type == "ORGANIZATION"
        assert rel.relationship_type == "WORKS_FOR"
        assert rel.object == "Elon Musk"
        assert rel.object_type == "PERSON"
        assert rel.confidence == 0.95

    def test_relationship_confidence_validation(self):
        """Test confidence score validation (0.0-1.0)."""
        # Valid confidence
        rel = Relationship(
            subject="A",
            subject_type="PERSON",
            relationship_type="KNOWS",
            object="B",
            object_type="PERSON",
            confidence=0.5
        )

        assert rel.confidence == 0.5

    def test_relationship_confidence_boundary_zero(self):
        """Test relationship with confidence 0.0."""
        rel = Relationship(
            subject="A",
            subject_type="PERSON",
            relationship_type="KNOWS",
            object="B",
            object_type="PERSON",
            confidence=0.0
        )

        assert rel.confidence == 0.0

    def test_relationship_confidence_boundary_one(self):
        """Test relationship with confidence 1.0."""
        rel = Relationship(
            subject="A",
            subject_type="PERSON",
            relationship_type="KNOWS",
            object="B",
            object_type="PERSON",
            confidence=1.0
        )

        assert rel.confidence == 1.0

    def test_relationship_confidence_invalid_negative(self):
        """Test relationship with invalid negative confidence."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="B",
                object_type="PERSON",
                confidence=-0.1
            )

    def test_relationship_confidence_invalid_over_one(self):
        """Test relationship with invalid confidence > 1.0."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="B",
                object_type="PERSON",
                confidence=1.1
            )

    def test_relationship_with_evidence(self):
        """Test relationship with evidence text."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95,
            evidence="Elon Musk is the CEO of Tesla since 2008"
        )

        assert rel.evidence == "Elon Musk is the CEO of Tesla since 2008"

    def test_relationship_with_source_url(self):
        """Test relationship with source URL."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95,
            source_url="https://example.com/article"
        )

        assert rel.source_url == "https://example.com/article"

    def test_relationship_with_article_id(self):
        """Test relationship with article ID."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95,
            article_id="article-001"
        )

        assert rel.article_id == "article-001"

    def test_relationship_mention_count(self):
        """Test relationship mention count."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95,
            mention_count=5
        )

        assert rel.mention_count == 5

    def test_relationship_mention_count_default(self):
        """Test relationship mention count defaults to 1."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95
        )

        assert rel.mention_count == 1

    def test_relationship_with_sentiment(self):
        """Test relationship with sentiment analysis."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95,
            sentiment_score=0.8,
            sentiment_category="positive",
            sentiment_confidence=0.9
        )

        assert rel.sentiment_score == 0.8
        assert rel.sentiment_category == "positive"
        assert rel.sentiment_confidence == 0.9

    def test_relationship_sentiment_score_negative(self):
        """Test relationship with negative sentiment."""
        rel = Relationship(
            subject="Company",
            subject_type="ORGANIZATION",
            relationship_type="SCANDAL",
            object="Executive",
            object_type="PERSON",
            confidence=0.95,
            sentiment_score=-0.9
        )

        assert rel.sentiment_score == -0.9

    def test_relationship_sentiment_score_neutral(self):
        """Test relationship with neutral sentiment."""
        rel = Relationship(
            subject="A",
            subject_type="PERSON",
            relationship_type="KNOWS",
            object="B",
            object_type="PERSON",
            confidence=0.95,
            sentiment_score=0.0
        )

        assert rel.sentiment_score == 0.0

    def test_relationship_sentiment_optional(self):
        """Test relationship without sentiment (all None)."""
        rel = Relationship(
            subject="A",
            subject_type="PERSON",
            relationship_type="KNOWS",
            object="B",
            object_type="PERSON",
            confidence=0.95
        )

        assert rel.sentiment_score is None
        assert rel.sentiment_category is None
        assert rel.sentiment_confidence is None

    def test_relationship_type_normalization_needed(self):
        """Test relationship type that needs normalization."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="works_for",  # lowercase
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95
        )

        # Type is lowercase as provided
        assert rel.relationship_type == "works_for"
        # But can be normalized
        assert rel.relationship_type.upper() == "WORKS_FOR"

    def test_relationship_all_common_types(self):
        """Test all common relationship types."""
        types = ["WORKS_FOR", "LOCATED_IN", "OWNS", "MEMBER_OF", "PARTNER_OF", "FOUNDED"]

        for rel_type in types:
            rel = Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type=rel_type,
                object="B",
                object_type="ORGANIZATION",
                confidence=0.95
            )
            assert rel.relationship_type == rel_type

    def test_relationship_serialization(self):
        """Test relationship serialization."""
        rel = Relationship(
            subject="Tesla",
            subject_type="ORGANIZATION",
            relationship_type="WORKS_FOR",
            object="Elon Musk",
            object_type="PERSON",
            confidence=0.95,
            evidence="Test evidence"
        )

        data = rel.model_dump()

        assert data["subject"] == "Tesla"
        assert data["object"] == "Elon Musk"
        assert data["confidence"] == 0.95

    def test_relationship_complex_entity_names(self):
        """Test relationship with complex entity names."""
        rel = Relationship(
            subject="Dr. Alan Turing (1912-1954)",
            subject_type="PERSON",
            relationship_type="WORKED_FOR",
            object="Government Communications Headquarters (GCHQ)",
            object_type="ORGANIZATION",
            confidence=0.95
        )

        assert "Dr." in rel.subject
        assert "GCHQ" in rel.object


class TestRelationshipFiltering:
    """Tests for filtering relationships by confidence."""

    def test_filter_relationships_by_confidence_threshold(self):
        """Test filtering relationships by confidence threshold."""
        relationships = [
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="B",
                object_type="PERSON",
                confidence=0.9
            ),
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="C",
                object_type="PERSON",
                confidence=0.4
            ),
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="D",
                object_type="PERSON",
                confidence=0.95
            )
        ]

        # Filter by confidence >= 0.5
        filtered = [r for r in relationships if r.confidence >= 0.5]

        assert len(filtered) == 2
        assert all(r.confidence >= 0.5 for r in filtered)

    def test_filter_high_confidence_relationships(self):
        """Test filtering high confidence relationships."""
        relationships = [
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="B",
                object_type="PERSON",
                confidence=0.99
            ),
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="C",
                object_type="PERSON",
                confidence=0.85
            )
        ]

        high_confidence = [r for r in relationships if r.confidence >= 0.9]

        assert len(high_confidence) == 1
        assert high_confidence[0].confidence == 0.99

    def test_filter_relationships_by_type(self):
        """Test filtering relationships by type."""
        relationships = [
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="WORKS_FOR",
                object="B",
                object_type="ORGANIZATION",
                confidence=0.95
            ),
            Relationship(
                subject="B",
                subject_type="ORGANIZATION",
                relationship_type="LOCATED_IN",
                object="C",
                object_type="LOCATION",
                confidence=0.95
            ),
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="WORKS_FOR",
                object="D",
                object_type="ORGANIZATION",
                confidence=0.95
            )
        ]

        works_for = [r for r in relationships if r.relationship_type == "WORKS_FOR"]

        assert len(works_for) == 2

    def test_sort_relationships_by_confidence(self):
        """Test sorting relationships by confidence."""
        relationships = [
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="B",
                object_type="PERSON",
                confidence=0.5
            ),
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="C",
                object_type="PERSON",
                confidence=0.95
            ),
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="D",
                object_type="PERSON",
                confidence=0.7
            )
        ]

        sorted_rels = sorted(relationships, key=lambda r: r.confidence, reverse=True)

        assert sorted_rels[0].confidence == 0.95
        assert sorted_rels[1].confidence == 0.7
        assert sorted_rels[2].confidence == 0.5

    def test_sort_relationships_by_mention_count(self):
        """Test sorting relationships by mention count."""
        relationships = [
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="B",
                object_type="PERSON",
                confidence=0.95,
                mention_count=1
            ),
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="C",
                object_type="PERSON",
                confidence=0.95,
                mention_count=10
            ),
            Relationship(
                subject="A",
                subject_type="PERSON",
                relationship_type="KNOWS",
                object="D",
                object_type="PERSON",
                confidence=0.95,
                mention_count=5
            )
        ]

        sorted_rels = sorted(relationships, key=lambda r: r.mention_count, reverse=True)

        assert sorted_rels[0].mention_count == 10
        assert sorted_rels[1].mention_count == 5
        assert sorted_rels[2].mention_count == 1
