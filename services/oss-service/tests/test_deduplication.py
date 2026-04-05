"""
Tests for Proposal Deduplication System

Issue #4: Tests for the deduplication module that prevents
duplicate proposals across analysis cycles.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from app.core.deduplication import ProposalDeduplicator, ProposalCacheEntry
from app.models.proposal import (
    OntologyChangeProposal,
    ChangeType,
    Severity,
    Evidence,
    ImpactAnalysis
)


@pytest.fixture
def deduplicator():
    """Create a fresh deduplicator instance for each test."""
    return ProposalDeduplicator(cache_ttl_hours=1, max_cache_size=100)


@pytest.fixture
def sample_entity_proposal():
    """Create a sample entity type proposal."""
    return OntologyChangeProposal(
        proposal_id="OSS_20241125_120000_abc12345",
        change_type=ChangeType.NEW_ENTITY_TYPE,
        severity=Severity.MEDIUM,
        title="Frequent entity type pattern: COMPANY",
        description="Detected 50 Entity nodes with entity_type='COMPANY'",
        evidence=[
            Evidence(
                example_id="12345",
                example_type="NODE",
                context="Example node with type 'COMPANY'",
                frequency=50
            )
        ],
        occurrence_count=50,
        confidence=0.75,
        impact_analysis=ImpactAnalysis(
            affected_entities_count=50,
            breaking_change=False,
            migration_complexity="MEDIUM"
        ),
        tags=["pattern-detection", "entity-type", "company"]
    )


@pytest.fixture
def sample_relationship_proposal():
    """Create a sample relationship type proposal."""
    return OntologyChangeProposal(
        proposal_id="OSS_20241125_120001_def67890",
        change_type=ChangeType.NEW_RELATIONSHIP_TYPE,
        severity=Severity.MEDIUM,
        title="Frequent relationship pattern: PERSON → COMPANY",
        description="Found 30 instances of PERSON entities related to COMPANY entities",
        pattern_query="""
        MATCH (a:Entity)-[r:RELATED_TO]->(b:Entity)
        WHERE a.entity_type = 'PERSON'
          AND b.entity_type = 'COMPANY'
        RETURN a, r, b
        LIMIT 10
        """,
        occurrence_count=30,
        confidence=0.70,
        impact_analysis=ImpactAnalysis(
            affected_relationships_count=30,
            breaking_change=False,
            migration_complexity="LOW"
        ),
        tags=["pattern-detection", "relationship-type"]
    )


class TestProposalDeduplicator:
    """Tests for ProposalDeduplicator class."""

    def test_initialization(self):
        """Test deduplicator initialization with custom settings."""
        dedup = ProposalDeduplicator(cache_ttl_hours=24, max_cache_size=5000)

        assert dedup.cache_ttl_hours == 24
        assert dedup.max_cache_size == 5000
        assert len(dedup._cache) == 0

    def test_fingerprint_generation_entity(self, deduplicator, sample_entity_proposal):
        """Test fingerprint generation for entity proposals."""
        fp1 = deduplicator._generate_fingerprint(sample_entity_proposal)

        assert fp1 is not None
        assert len(fp1) == 32  # SHA256 truncated to 32 chars
        assert isinstance(fp1, str)

        # Same proposal should generate same fingerprint
        fp2 = deduplicator._generate_fingerprint(sample_entity_proposal)
        assert fp1 == fp2

    def test_fingerprint_generation_relationship(self, deduplicator, sample_relationship_proposal):
        """Test fingerprint generation for relationship proposals."""
        fp = deduplicator._generate_fingerprint(sample_relationship_proposal)

        assert fp is not None
        assert len(fp) == 32

    def test_different_proposals_different_fingerprints(
        self, deduplicator, sample_entity_proposal, sample_relationship_proposal
    ):
        """Test that different proposals generate different fingerprints."""
        fp1 = deduplicator._generate_fingerprint(sample_entity_proposal)
        fp2 = deduplicator._generate_fingerprint(sample_relationship_proposal)

        assert fp1 != fp2

    def test_similar_proposals_same_fingerprint(self, deduplicator):
        """Test that similar proposals (same pattern) have same fingerprint."""
        # Create two proposals for the same pattern
        proposal1 = OntologyChangeProposal(
            proposal_id="OSS_20241125_120000_abc12345",
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.MEDIUM,
            title="Frequent entity type pattern: COMPANY",
            description="Different description",
            occurrence_count=50,
            confidence=0.75,
            impact_analysis=ImpactAnalysis(breaking_change=False),
            tags=["pattern-detection", "entity-type", "company"]
        )

        proposal2 = OntologyChangeProposal(
            proposal_id="OSS_20241125_130000_xyz99999",  # Different ID
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.HIGH,  # Different severity
            title="Frequent entity type pattern: COMPANY",  # Same title
            description="Yet another description",
            occurrence_count=50,  # Same count
            confidence=0.85,  # Different confidence
            impact_analysis=ImpactAnalysis(breaking_change=False),
            tags=["pattern-detection", "entity-type", "company"]  # Same tags
        )

        fp1 = deduplicator._generate_fingerprint(proposal1)
        fp2 = deduplicator._generate_fingerprint(proposal2)

        # Fingerprints should be the same because they represent the same pattern
        assert fp1 == fp2

    @pytest.mark.asyncio
    async def test_is_duplicate_empty_cache(self, deduplicator, sample_entity_proposal):
        """Test that proposals are not duplicates in empty cache."""
        is_dup = await deduplicator.is_duplicate(sample_entity_proposal)
        assert is_dup is False

    @pytest.mark.asyncio
    async def test_mark_submitted_and_is_duplicate(self, deduplicator, sample_entity_proposal):
        """Test marking a proposal as submitted and detecting duplicates."""
        # Initially not a duplicate
        assert await deduplicator.is_duplicate(sample_entity_proposal) is False

        # Mark as submitted
        await deduplicator.mark_submitted(sample_entity_proposal)

        # Now should be detected as duplicate
        assert await deduplicator.is_duplicate(sample_entity_proposal) is True

    @pytest.mark.asyncio
    async def test_cache_expiration(self, deduplicator, sample_entity_proposal):
        """Test that expired cache entries are not considered duplicates."""
        # Add to cache
        await deduplicator.mark_submitted(sample_entity_proposal)

        # Verify it's a duplicate
        assert await deduplicator.is_duplicate(sample_entity_proposal) is True

        # Manually expire the entry
        fingerprint = deduplicator._generate_fingerprint(sample_entity_proposal)
        deduplicator._cache[fingerprint].expires_at = datetime.now() - timedelta(hours=1)

        # Should no longer be detected as duplicate
        assert await deduplicator.is_duplicate(sample_entity_proposal) is False

    @pytest.mark.asyncio
    async def test_clear_cache(self, deduplicator, sample_entity_proposal):
        """Test clearing the deduplication cache."""
        # Add some entries
        await deduplicator.mark_submitted(sample_entity_proposal)
        assert len(deduplicator._cache) > 0

        # Clear cache
        count = await deduplicator.clear_cache()

        assert count > 0
        assert len(deduplicator._cache) == 0

    @pytest.mark.asyncio
    async def test_cache_cleanup_oldest(self, sample_entity_proposal):
        """Test that oldest entries are removed when cache is full."""
        # Create a small cache
        dedup = ProposalDeduplicator(cache_ttl_hours=1, max_cache_size=5)

        # Add 6 entries (exceeds max of 5)
        for i in range(6):
            proposal = OntologyChangeProposal(
                proposal_id=f"OSS_test_{i}",
                change_type=ChangeType.NEW_ENTITY_TYPE,
                severity=Severity.MEDIUM,
                title=f"Pattern {i}",
                description="Test",
                confidence=0.5,
                impact_analysis=ImpactAnalysis(breaking_change=False),
                tags=[f"tag-{i}"]
            )
            await dedup.mark_submitted(proposal)

        # Cache should not exceed max size
        assert len(dedup._cache) <= 5

    def test_get_stats(self, deduplicator):
        """Test getting deduplication statistics."""
        stats = deduplicator.get_stats()

        assert "total_cached" in stats
        assert "active_entries" in stats
        assert "cache_ttl_hours" in stats
        assert "max_cache_size" in stats
        assert stats["cache_ttl_hours"] == 1
        assert stats["max_cache_size"] == 100

    @pytest.mark.asyncio
    async def test_stats_after_submissions(self, deduplicator, sample_entity_proposal):
        """Test stats update after marking submissions."""
        initial_stats = deduplicator.get_stats()
        assert initial_stats["total_cached"] == 0

        await deduplicator.mark_submitted(sample_entity_proposal)

        updated_stats = deduplicator.get_stats()
        assert updated_stats["total_cached"] == 1
        assert updated_stats["active_entries"] == 1


class TestFingerprintEdgeCases:
    """Test fingerprint generation edge cases."""

    @pytest.fixture
    def deduplicator(self):
        return ProposalDeduplicator()

    def test_fingerprint_with_no_tags(self, deduplicator):
        """Test fingerprint generation when tags are None."""
        proposal = OntologyChangeProposal(
            proposal_id="test_no_tags",
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.LOW,
            title="Test",
            description="Test",
            confidence=0.5,
            impact_analysis=ImpactAnalysis(breaking_change=False),
            tags=None
        )

        fp = deduplicator._generate_fingerprint(proposal)
        assert fp is not None
        assert len(fp) == 32

    def test_fingerprint_with_no_occurrence_count(self, deduplicator):
        """Test fingerprint generation when occurrence_count is None."""
        proposal = OntologyChangeProposal(
            proposal_id="test_no_count",
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.LOW,
            title="Test",
            description="Test",
            confidence=0.5,
            impact_analysis=ImpactAnalysis(breaking_change=False),
            occurrence_count=None
        )

        fp = deduplicator._generate_fingerprint(proposal)
        assert fp is not None

    def test_fingerprint_flag_inconsistency(self, deduplicator):
        """Test fingerprint for FLAG_INCONSISTENCY type."""
        proposal = OntologyChangeProposal(
            proposal_id="test_inconsistency",
            change_type=ChangeType.FLAG_INCONSISTENCY,
            severity=Severity.HIGH,
            title="Data inconsistency detected",
            description="Test",
            evidence=[
                Evidence(example_id="node_1", example_type="NODE"),
                Evidence(example_id="node_2", example_type="NODE"),
            ],
            confidence=0.9,
            impact_analysis=ImpactAnalysis(breaking_change=False)
        )

        fp = deduplicator._generate_fingerprint(proposal)
        assert fp is not None

    def test_fingerprint_merge_entities(self, deduplicator):
        """Test fingerprint for MERGE_ENTITIES type."""
        proposal = OntologyChangeProposal(
            proposal_id="test_merge",
            change_type=ChangeType.MERGE_ENTITIES,
            severity=Severity.MEDIUM,
            title="Duplicate entities detected",
            description="Test",
            evidence=[
                Evidence(example_id="entity_1", example_type="NODE"),
                Evidence(example_id="entity_2", example_type="NODE"),
            ],
            confidence=0.85,
            impact_analysis=ImpactAnalysis(breaking_change=False)
        )

        fp = deduplicator._generate_fingerprint(proposal)
        assert fp is not None


class TestDeduplicationAPIIntegration:
    """Test API-related deduplication methods."""

    @pytest.fixture
    def deduplicator(self):
        return ProposalDeduplicator()

    @pytest.mark.asyncio
    async def test_is_duplicate_in_api_connection_error(
        self, deduplicator, sample_entity_proposal
    ):
        """Test API check handles connection errors gracefully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            # Should return False (not duplicate) on error
            result = await deduplicator.is_duplicate_in_api(sample_entity_proposal)
            assert result is False

    @pytest.mark.asyncio
    async def test_is_duplicate_in_api_non_200_response(
        self, deduplicator, sample_entity_proposal
    ):
        """Test API check handles non-200 responses."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await deduplicator.is_duplicate_in_api(sample_entity_proposal)
            assert result is False


@pytest.fixture
def sample_entity_proposal():
    """Create a sample entity type proposal for module-level tests."""
    return OntologyChangeProposal(
        proposal_id="OSS_20241125_120000_abc12345",
        change_type=ChangeType.NEW_ENTITY_TYPE,
        severity=Severity.MEDIUM,
        title="Frequent entity type pattern: COMPANY",
        description="Detected 50 Entity nodes with entity_type='COMPANY'",
        evidence=[
            Evidence(
                example_id="12345",
                example_type="NODE",
                context="Example node with type 'COMPANY'",
                frequency=50
            )
        ],
        occurrence_count=50,
        confidence=0.75,
        impact_analysis=ImpactAnalysis(
            affected_entities_count=50,
            breaking_change=False,
            migration_complexity="MEDIUM"
        ),
        tags=["pattern-detection", "entity-type", "company"]
    )
