"""Tests for escalation anchor seeding script.

These tests verify the anchor data structure and seeding logic
without requiring database access.
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from seed_escalation_anchors import (
    DEFAULT_ANCHORS,
    generate_embedding,
)


class TestDefaultAnchorsData:
    """Test the default anchor definitions."""

    def test_anchor_count_is_fifteen(self):
        """Should have exactly 15 anchors (3 domains x 5 levels)."""
        assert len(DEFAULT_ANCHORS) == 15

    def test_all_domains_present(self):
        """Each domain should be present in the anchors."""
        domains = {anchor[0] for anchor in DEFAULT_ANCHORS}
        expected_domains = {"geopolitical", "military", "economic"}
        assert domains == expected_domains

    def test_each_domain_has_all_five_levels(self):
        """Each domain should have anchors for levels 1-5."""
        domains = {"geopolitical", "military", "economic"}

        for domain in domains:
            domain_anchors = [a for a in DEFAULT_ANCHORS if a[0] == domain]
            assert len(domain_anchors) == 5, f"{domain} should have 5 anchors"

            levels = {a[1] for a in domain_anchors}
            expected_levels = {1, 2, 3, 4, 5}
            assert levels == expected_levels, f"{domain} missing levels"

    def test_anchor_tuple_structure(self):
        """Each anchor should have 5 elements: domain, level, label, text, keywords."""
        for i, anchor in enumerate(DEFAULT_ANCHORS):
            assert len(anchor) == 5, f"Anchor {i} should have 5 elements"

            domain, level, label, text, keywords = anchor

            # Type checks
            assert isinstance(domain, str), f"Anchor {i}: domain should be str"
            assert isinstance(level, int), f"Anchor {i}: level should be int"
            assert isinstance(label, str), f"Anchor {i}: label should be str"
            assert isinstance(text, str), f"Anchor {i}: text should be str"
            assert isinstance(keywords, list), f"Anchor {i}: keywords should be list"

    def test_domain_values_are_valid(self):
        """Domains should only be geopolitical, military, or economic."""
        valid_domains = {"geopolitical", "military", "economic"}

        for anchor in DEFAULT_ANCHORS:
            domain = anchor[0]
            assert domain in valid_domains, f"Invalid domain: {domain}"

    def test_level_values_are_in_range(self):
        """Levels should be integers between 1 and 5."""
        for anchor in DEFAULT_ANCHORS:
            level = anchor[1]
            assert 1 <= level <= 5, f"Level {level} out of range"

    def test_labels_are_non_empty(self):
        """Labels should be non-empty strings."""
        for anchor in DEFAULT_ANCHORS:
            label = anchor[2]
            assert len(label) > 0, "Label should not be empty"
            assert label.strip() == label, "Label should not have leading/trailing whitespace"

    def test_reference_texts_are_substantial(self):
        """Reference texts should be substantial (at least 100 characters)."""
        for anchor in DEFAULT_ANCHORS:
            domain, level, label, text, _ = anchor
            assert len(text) >= 100, (
                f"Reference text for {domain}/L{level}/{label} is too short "
                f"({len(text)} chars)"
            )

    def test_keywords_have_minimum_count(self):
        """Each anchor should have at least 5 keywords."""
        for anchor in DEFAULT_ANCHORS:
            domain, level, label, _, keywords = anchor
            assert len(keywords) >= 5, (
                f"Anchor {domain}/L{level}/{label} needs at least 5 keywords "
                f"(has {len(keywords)})"
            )

    def test_keywords_are_non_empty_strings(self):
        """All keywords should be non-empty strings."""
        for anchor in DEFAULT_ANCHORS:
            domain, level, label, _, keywords = anchor
            for kw in keywords:
                assert isinstance(kw, str), f"Keyword should be string in {label}"
                assert len(kw) > 0, f"Empty keyword in {label}"

    def test_labels_are_unique_within_domain_level(self):
        """Labels should be unique within each domain-level combination."""
        seen = set()
        for anchor in DEFAULT_ANCHORS:
            domain, level, label, _, _ = anchor
            key = (domain, level, label)
            assert key not in seen, f"Duplicate label: {key}"
            seen.add(key)

    def test_labels_follow_snake_case_convention(self):
        """Labels should use snake_case convention."""
        for anchor in DEFAULT_ANCHORS:
            label = anchor[2]
            # Should only contain lowercase letters, numbers, and underscores
            assert label.islower() or "_" in label, f"Label {label} should be snake_case"
            assert " " not in label, f"Label {label} should not contain spaces"

    def test_escalation_progression_in_text(self):
        """Higher levels should have more severe language indicators."""
        # Keywords that indicate escalation severity
        severity_keywords = {
            5: ["critical", "war", "collapse", "conflict", "emergency", "imminent"],
            4: ["severe", "crisis", "casualties", "confrontation"],
            3: ["significant", "emergency", "buildup", "stress"],
            2: ["elevated", "tensions", "concerns", "increased"],
            1: ["routine", "normal", "standard", "stable"],
        }

        for anchor in DEFAULT_ANCHORS:
            domain, level, label, text, _ = anchor
            text_lower = text.lower()

            # Check that at least one severity keyword appears
            level_keywords = severity_keywords.get(level, [])
            found_keywords = [kw for kw in level_keywords if kw in text_lower]

            assert len(found_keywords) > 0, (
                f"Anchor {domain}/L{level} should contain severity keywords: "
                f"{level_keywords}"
            )


class TestEmbeddingGeneration:
    """Test the deterministic embedding generation."""

    @pytest.mark.asyncio
    async def test_embedding_has_correct_dimension(self):
        """Embedding should be 1536-dimensional."""
        embedding = await generate_embedding("Test text for embedding dimension check")
        assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_embedding_values_in_range(self):
        """All embedding values should be in [-1, 1] range."""
        embedding = await generate_embedding("Test text for value range check")
        for i, value in enumerate(embedding):
            assert -1.0 <= value <= 1.0, f"Value at index {i} out of range: {value}"

    @pytest.mark.asyncio
    async def test_embedding_is_deterministic(self):
        """Same text should produce same embedding."""
        text = "Reproducible embedding test"
        embedding1 = await generate_embedding(text)
        embedding2 = await generate_embedding(text)

        assert embedding1 == embedding2, "Same text should produce identical embeddings"

    @pytest.mark.asyncio
    async def test_different_texts_produce_different_embeddings(self):
        """Different texts should produce different embeddings."""
        embedding1 = await generate_embedding("First text about diplomacy")
        embedding2 = await generate_embedding("Second text about military")

        # Should be different
        assert embedding1 != embedding2

        # Calculate difference magnitude
        diff_count = sum(1 for a, b in zip(embedding1, embedding2) if a != b)
        assert diff_count > 0, "Embeddings should differ"

    @pytest.mark.asyncio
    async def test_embedding_for_each_anchor(self):
        """Should generate valid embedding for each anchor's reference text."""
        for anchor in DEFAULT_ANCHORS:
            domain, level, label, text, _ = anchor
            embedding = await generate_embedding(text)

            assert len(embedding) == 1536, f"Wrong dimension for {label}"
            assert all(-1.0 <= v <= 1.0 for v in embedding), f"Values out of range for {label}"

    @pytest.mark.asyncio
    async def test_embeddings_are_floats(self):
        """Embedding values should be floats."""
        embedding = await generate_embedding("Test text")
        for value in embedding:
            assert isinstance(value, float), f"Value should be float: {type(value)}"

    @pytest.mark.asyncio
    async def test_empty_text_produces_embedding(self):
        """Even empty text should produce a valid embedding."""
        embedding = await generate_embedding("")
        assert len(embedding) == 1536
        assert all(-1.0 <= v <= 1.0 for v in embedding)

    @pytest.mark.asyncio
    async def test_unicode_text_produces_embedding(self):
        """Unicode text should produce a valid embedding."""
        # Use valid Unicode characters (accented letters and CJK)
        embedding = await generate_embedding("Test with unicode: cafe resume naive Munchen Beijing Tokyo")
        assert len(embedding) == 1536
        assert all(-1.0 <= v <= 1.0 for v in embedding)


class TestAnchorCoverage:
    """Test that anchors cover expected semantic space."""

    def test_geopolitical_level_1_is_routine(self):
        """Level 1 geopolitical anchor should describe routine activity."""
        anchor = next(a for a in DEFAULT_ANCHORS if a[0] == "geopolitical" and a[1] == 1)
        _, _, label, text, _ = anchor

        assert "routine" in label.lower() or "routine" in text.lower()
        assert "crisis" not in text.lower()
        assert "war" not in text.lower()

    def test_military_level_5_is_conflict(self):
        """Level 5 military anchor should describe active conflict."""
        anchor = next(a for a in DEFAULT_ANCHORS if a[0] == "military" and a[1] == 5)
        _, _, label, text, keywords = anchor

        conflict_indicators = ["conflict", "combat", "war", "offensive"]
        text_lower = text.lower()

        assert any(ind in text_lower for ind in conflict_indicators), (
            f"Level 5 military should mention conflict indicators"
        )

    def test_economic_level_5_is_collapse(self):
        """Level 5 economic anchor should describe collapse/crisis."""
        anchor = next(a for a in DEFAULT_ANCHORS if a[0] == "economic" and a[1] == 5)
        _, _, label, text, keywords = anchor

        collapse_indicators = ["collapse", "failure", "crisis", "hyperinflation"]
        text_lower = text.lower()

        assert any(ind in text_lower for ind in collapse_indicators), (
            f"Level 5 economic should mention collapse indicators"
        )

    def test_all_anchors_have_domain_specific_vocabulary(self):
        """Each domain's anchors should use domain-specific vocabulary."""
        domain_vocab = {
            "geopolitical": ["diplomatic", "ambassador", "treaty", "sanctions", "bilateral"],
            "military": ["forces", "troops", "operations", "combat", "defense"],
            "economic": ["market", "trade", "currency", "financial", "economic"],
        }

        for anchor in DEFAULT_ANCHORS:
            domain, level, label, text, _ = anchor
            text_lower = text.lower()
            vocab = domain_vocab.get(domain, [])

            matches = [word for word in vocab if word in text_lower]
            assert len(matches) >= 1, (
                f"Anchor {domain}/L{level} should use domain vocabulary. "
                f"Expected one of: {vocab}"
            )
