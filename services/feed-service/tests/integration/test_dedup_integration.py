# services/feed-service/tests/integration/test_dedup_integration.py
"""Integration tests for the deduplication pipeline.

Tests the complete deduplication flow between:
- DeduplicationService: SimHash fingerprint comparison
- DeduplicationRepository: Database operations
- FeedItem/DuplicateCandidate models: Data storage

Test Scenarios:
1. Exact duplicate (Hamming <= 3): Article rejected/withheld
2. Near-duplicate (Hamming 4-7): DuplicateCandidate created with status="pending"
3. Non-duplicate (Hamming > 7): Article saved normally

This is part of Epic 1.2: Deduplication Pipeline (Task 6).
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.models.feed import Feed, FeedItem, DuplicateCandidate
from app.services.deduplication import DeduplicationService, DeduplicationResult
from app.services.dedup_repository import DeduplicationRepository


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def dedup_service():
    """Create DeduplicationService instance."""
    return DeduplicationService()


@pytest_asyncio.fixture
async def test_feed(db_session):
    """Create a test feed for article creation."""
    feed = Feed(
        name="Dedup Integration Test Feed",
        url=f"https://example.com/dedup-test-feed-{uuid4()}.xml",
    )
    db_session.add(feed)
    await db_session.flush()
    return feed


@pytest_asyncio.fixture
async def dedup_repository(db_session):
    """Create DeduplicationRepository with test session."""
    return DeduplicationRepository(db_session)


# Fingerprint fixtures for testing different Hamming distances
# Using 63-bit SimHash fingerprints (SQLite uses signed 64-bit integers)
# Max safe value: 0x7FFFFFFFFFFFFFFF (signed 64-bit max)

@pytest.fixture
def base_fingerprint():
    """Base fingerprint for comparison tests."""
    # Use a value within signed 64-bit range
    # All lower bits set except MSB to stay within SQLite INTEGER limit
    return 0x7FFFFFFFFFFFFFFF


@pytest.fixture
def exact_duplicate_fingerprint(base_fingerprint):
    """Fingerprint with Hamming distance = 0 (exact duplicate)."""
    return base_fingerprint  # Identical


@pytest.fixture
def duplicate_within_threshold_fingerprint(base_fingerprint):
    """Fingerprint with Hamming distance = 3 (still duplicate)."""
    # Flip 3 bits: bits 0, 1, 2
    return base_fingerprint ^ 0b111


@pytest.fixture
def near_duplicate_fingerprint(base_fingerprint):
    """Fingerprint with Hamming distance = 5 (near-duplicate, flagged for review)."""
    # Flip 5 bits: bits 0, 1, 2, 3, 4
    return base_fingerprint ^ 0b11111


@pytest.fixture
def near_duplicate_max_fingerprint(base_fingerprint):
    """Fingerprint with Hamming distance = 7 (max near-duplicate)."""
    # Flip 7 bits: bits 0-6
    return base_fingerprint ^ 0b1111111


@pytest.fixture
def non_duplicate_fingerprint(base_fingerprint):
    """Fingerprint with Hamming distance = 10 (different content)."""
    # Flip 10 bits: bits 0-9
    return base_fingerprint ^ 0b1111111111


# ============================================================================
# Scenario 1: Exact Duplicate Detection
# ============================================================================

class TestExactDuplicateDetection:
    """Tests for exact duplicate detection (Hamming <= 3)."""

    @pytest.mark.asyncio
    async def test_exact_duplicate_rejected(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        exact_duplicate_fingerprint,
    ):
        """Exact duplicate (Hamming = 0) should be rejected."""
        # Create existing article with base fingerprint
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article",
            link=f"https://example.com/existing-{uuid4()}",
            content_hash=f"existing-hash-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Get existing fingerprints from repository
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)

        # Check new article with exact same fingerprint
        result = dedup_service.check_duplicate(
            fingerprint=exact_duplicate_fingerprint,
            existing_fingerprints=existing_fps,
        )

        # Verify: exact duplicate is rejected
        assert result.is_allowed is False
        assert result.is_duplicate is True
        assert result.is_near_duplicate is False
        assert result.hamming_distance == 0
        assert result.matching_article_id == existing_article.id

    @pytest.mark.asyncio
    async def test_duplicate_within_threshold_rejected(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        duplicate_within_threshold_fingerprint,
    ):
        """Duplicate within threshold (Hamming = 3) should be rejected."""
        # Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Threshold",
            link=f"https://example.com/existing-threshold-{uuid4()}",
            content_hash=f"existing-hash-threshold-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Get existing fingerprints
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)

        # Check new article with 3-bit difference
        result = dedup_service.check_duplicate(
            fingerprint=duplicate_within_threshold_fingerprint,
            existing_fingerprints=existing_fps,
        )

        # Verify: within threshold is still rejected
        assert result.is_allowed is False
        assert result.is_duplicate is True
        assert result.is_near_duplicate is False
        assert result.hamming_distance == 3
        assert result.matching_article_id == existing_article.id

    @pytest.mark.asyncio
    async def test_duplicate_no_candidate_created(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        exact_duplicate_fingerprint,
    ):
        """Exact duplicates should NOT create DuplicateCandidate records."""
        # Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article No Candidate",
            link=f"https://example.com/existing-no-candidate-{uuid4()}",
            content_hash=f"existing-hash-no-candidate-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Get existing fingerprints and check duplicate
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        result = dedup_service.check_duplicate(
            fingerprint=exact_duplicate_fingerprint,
            existing_fingerprints=existing_fps,
        )

        # Since it's a duplicate, we reject it - NO candidate should be created
        # (Candidates are only for near-duplicates that need human review)
        assert result.is_duplicate is True

        # Verify no DuplicateCandidate records exist
        query = select(DuplicateCandidate)
        db_result = await db_session.execute(query)
        candidates = db_result.scalars().all()
        assert len(candidates) == 0


# ============================================================================
# Scenario 2: Near-Duplicate Detection (Flagged for Review)
# ============================================================================

class TestNearDuplicateDetection:
    """Tests for near-duplicate detection (Hamming 4-7)."""

    @pytest.mark.asyncio
    async def test_near_duplicate_allowed_but_flagged(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        near_duplicate_fingerprint,
    ):
        """Near-duplicate (Hamming = 5) should be allowed but flagged."""
        # Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Near-Dup",
            link=f"https://example.com/existing-neardup-{uuid4()}",
            content_hash=f"existing-hash-neardup-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Get existing fingerprints
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)

        # Check new article with 5-bit difference
        result = dedup_service.check_duplicate(
            fingerprint=near_duplicate_fingerprint,
            existing_fingerprints=existing_fps,
        )

        # Verify: near-duplicate is allowed but flagged
        assert result.is_allowed is True  # Still allowed!
        assert result.is_duplicate is False
        assert result.is_near_duplicate is True
        assert result.hamming_distance == 5
        assert result.matching_article_id == existing_article.id

    @pytest.mark.asyncio
    async def test_near_duplicate_creates_candidate(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        near_duplicate_fingerprint,
    ):
        """Near-duplicate should create DuplicateCandidate with status='pending'."""
        # Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Creates Candidate",
            link=f"https://example.com/existing-creates-candidate-{uuid4()}",
            content_hash=f"existing-hash-creates-candidate-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Create new article (simulating successful ingestion despite being near-dup)
        new_article = FeedItem(
            feed_id=test_feed.id,
            title="New Article Near-Dup Candidate",
            link=f"https://example.com/new-neardup-candidate-{uuid4()}",
            content_hash=f"new-hash-neardup-candidate-{uuid4()}",
            simhash_fingerprint=near_duplicate_fingerprint,
        )
        db_session.add(new_article)
        await db_session.flush()

        # Get existing fingerprints and check
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        result = dedup_service.check_duplicate(
            fingerprint=near_duplicate_fingerprint,
            existing_fingerprints=[(existing_article.id, base_fingerprint)],
        )

        # Now create the DuplicateCandidate (this is what the pipeline does)
        if result.is_near_duplicate:
            candidate_id = await dedup_repository.flag_near_duplicate(
                new_article_id=new_article.id,
                existing_article_id=result.matching_article_id,
                hamming_distance=result.hamming_distance,
                simhash_new=near_duplicate_fingerprint,
                simhash_existing=result.matching_fingerprint,
            )

        await db_session.flush()

        # Verify DuplicateCandidate was created correctly
        query = select(DuplicateCandidate).where(
            DuplicateCandidate.new_article_id == new_article.id
        )
        db_result = await db_session.execute(query)
        candidate = db_result.scalar_one_or_none()

        assert candidate is not None
        assert candidate.status == "pending"
        assert candidate.new_article_id == new_article.id
        assert candidate.existing_article_id == existing_article.id
        assert candidate.hamming_distance == 5
        assert candidate.simhash_new == near_duplicate_fingerprint
        assert candidate.simhash_existing == base_fingerprint

    @pytest.mark.asyncio
    async def test_near_duplicate_max_threshold(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        near_duplicate_max_fingerprint,
    ):
        """Near-duplicate at max threshold (Hamming = 7) should be flagged."""
        # Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Max Threshold",
            link=f"https://example.com/existing-max-threshold-{uuid4()}",
            content_hash=f"existing-hash-max-threshold-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Get existing fingerprints
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)

        # Check with 7-bit difference (max near-duplicate threshold)
        result = dedup_service.check_duplicate(
            fingerprint=near_duplicate_max_fingerprint,
            existing_fingerprints=existing_fps,
        )

        # Verify: at max threshold, still considered near-duplicate
        assert result.is_allowed is True
        assert result.is_duplicate is False
        assert result.is_near_duplicate is True
        assert result.hamming_distance == 7

    @pytest.mark.asyncio
    async def test_pending_review_count_increments(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        near_duplicate_fingerprint,
    ):
        """Pending review count should increment when candidates are created."""
        # Create existing and new articles
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Count Test",
            link=f"https://example.com/existing-count-{uuid4()}",
            content_hash=f"existing-hash-count-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        new_article = FeedItem(
            feed_id=test_feed.id,
            title="New Article Count Test",
            link=f"https://example.com/new-count-{uuid4()}",
            content_hash=f"new-hash-count-{uuid4()}",
            simhash_fingerprint=near_duplicate_fingerprint,
        )
        db_session.add(existing_article)
        db_session.add(new_article)
        await db_session.flush()

        # Check initial count
        initial_count = await dedup_repository.get_pending_review_count()
        assert initial_count == 0

        # Flag near-duplicate
        await dedup_repository.flag_near_duplicate(
            new_article_id=new_article.id,
            existing_article_id=existing_article.id,
            hamming_distance=5,
            simhash_new=near_duplicate_fingerprint,
            simhash_existing=base_fingerprint,
        )

        # Verify count incremented
        new_count = await dedup_repository.get_pending_review_count()
        assert new_count == 1


# ============================================================================
# Scenario 3: Non-Duplicate (Different Content)
# ============================================================================

class TestNonDuplicateDetection:
    """Tests for non-duplicate detection (Hamming > 7)."""

    @pytest.mark.asyncio
    async def test_non_duplicate_allowed(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        non_duplicate_fingerprint,
    ):
        """Non-duplicate (Hamming = 10) should be allowed without flagging."""
        # Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Non-Dup",
            link=f"https://example.com/existing-nondup-{uuid4()}",
            content_hash=f"existing-hash-nondup-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Get existing fingerprints
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)

        # Check new article with 10-bit difference
        result = dedup_service.check_duplicate(
            fingerprint=non_duplicate_fingerprint,
            existing_fingerprints=existing_fps,
        )

        # Verify: completely different content is allowed
        assert result.is_allowed is True
        assert result.is_duplicate is False
        assert result.is_near_duplicate is False
        assert result.hamming_distance == 10

    @pytest.mark.asyncio
    async def test_non_duplicate_no_candidate_created(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        non_duplicate_fingerprint,
    ):
        """Non-duplicates should NOT create DuplicateCandidate records."""
        # Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article No Candidate Non-Dup",
            link=f"https://example.com/existing-no-candidate-nondup-{uuid4()}",
            content_hash=f"existing-hash-no-candidate-nondup-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Create new article (different content)
        new_article = FeedItem(
            feed_id=test_feed.id,
            title="New Article Non-Dup No Candidate",
            link=f"https://example.com/new-nondup-no-candidate-{uuid4()}",
            content_hash=f"new-hash-nondup-no-candidate-{uuid4()}",
            simhash_fingerprint=non_duplicate_fingerprint,
        )
        db_session.add(new_article)
        await db_session.flush()

        # Check - should not create candidate since it's not near-duplicate
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        result = dedup_service.check_duplicate(
            fingerprint=non_duplicate_fingerprint,
            existing_fingerprints=[(existing_article.id, base_fingerprint)],
        )

        # Verify it's not a near-duplicate
        assert result.is_near_duplicate is False

        # Verify no DuplicateCandidate records exist
        query = select(DuplicateCandidate)
        db_result = await db_session.execute(query)
        candidates = db_result.scalars().all()
        assert len(candidates) == 0

    @pytest.mark.asyncio
    async def test_article_saved_normally(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        non_duplicate_fingerprint,
    ):
        """Non-duplicate articles should be saved normally to database."""
        # Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Save Normal",
            link=f"https://example.com/existing-save-normal-{uuid4()}",
            content_hash=f"existing-hash-save-normal-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Check deduplication - should allow
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        result = dedup_service.check_duplicate(
            fingerprint=non_duplicate_fingerprint,
            existing_fingerprints=existing_fps,
        )

        assert result.is_allowed is True

        # Save new article (simulating what the pipeline does)
        new_article = FeedItem(
            feed_id=test_feed.id,
            title="New Article Save Normal",
            link=f"https://example.com/new-save-normal-{uuid4()}",
            content_hash=f"new-hash-save-normal-{uuid4()}",
            simhash_fingerprint=non_duplicate_fingerprint,
        )
        db_session.add(new_article)
        await db_session.flush()

        # Verify article was saved
        query = select(FeedItem).where(FeedItem.id == new_article.id)
        db_result = await db_session.execute(query)
        saved_article = db_result.scalar_one_or_none()

        assert saved_article is not None
        assert saved_article.simhash_fingerprint == non_duplicate_fingerprint


# ============================================================================
# Edge Cases and Full Pipeline Tests
# ============================================================================

class TestDeduplicationPipelineEdgeCases:
    """Edge cases and full pipeline integration tests."""

    @pytest.mark.asyncio
    async def test_empty_database_allows_first_article(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
    ):
        """First article should always be allowed when database is empty."""
        # Get fingerprints from empty database
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        assert len(existing_fps) == 0

        # Check deduplication
        result = dedup_service.check_duplicate(
            fingerprint=base_fingerprint,
            existing_fingerprints=existing_fps,
        )

        assert result.is_allowed is True
        assert result.is_duplicate is False
        assert result.is_near_duplicate is False
        assert result.matching_article_id is None

    @pytest.mark.asyncio
    async def test_multiple_candidates_finds_closest_match(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
    ):
        """Should find the closest match when multiple candidates exist."""
        # Create multiple articles with different fingerprints
        # Hamming distance from base: 8, 5, 10
        fp_8_bits = base_fingerprint ^ 0xFF  # 8 bits different
        fp_5_bits = base_fingerprint ^ 0x1F  # 5 bits different
        fp_10_bits = base_fingerprint ^ 0x3FF  # 10 bits different

        for i, fp in enumerate([fp_8_bits, fp_5_bits, fp_10_bits]):
            article = FeedItem(
                feed_id=test_feed.id,
                title=f"Article {i}",
                link=f"https://example.com/article-{i}-{uuid4()}",
                content_hash=f"hash-{i}-{uuid4()}",
                simhash_fingerprint=fp,
            )
            db_session.add(article)
        await db_session.flush()

        # Get fingerprints
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        assert len(existing_fps) == 3

        # Check with base fingerprint - should find 5-bit match (closest)
        result = dedup_service.check_duplicate(
            fingerprint=base_fingerprint,
            existing_fingerprints=existing_fps,
        )

        assert result.hamming_distance == 5
        assert result.is_near_duplicate is True

    @pytest.mark.asyncio
    async def test_already_flagged_pair_detection(
        self,
        db_session,
        test_feed,
        dedup_repository,
        base_fingerprint,
        near_duplicate_fingerprint,
    ):
        """Should detect when article pair is already flagged."""
        # Create articles
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Already Flagged",
            link=f"https://example.com/existing-already-flagged-{uuid4()}",
            content_hash=f"existing-hash-already-flagged-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        new_article = FeedItem(
            feed_id=test_feed.id,
            title="New Article Already Flagged",
            link=f"https://example.com/new-already-flagged-{uuid4()}",
            content_hash=f"new-hash-already-flagged-{uuid4()}",
            simhash_fingerprint=near_duplicate_fingerprint,
        )
        db_session.add(existing_article)
        db_session.add(new_article)
        await db_session.flush()

        # Flag once
        await dedup_repository.flag_near_duplicate(
            new_article_id=new_article.id,
            existing_article_id=existing_article.id,
            hamming_distance=5,
            simhash_new=near_duplicate_fingerprint,
            simhash_existing=base_fingerprint,
        )

        # Check if already flagged
        is_flagged = await dedup_repository.check_article_already_flagged(
            new_article_id=new_article.id,
            existing_article_id=existing_article.id,
        )

        assert is_flagged is True

        # Different pair should not be flagged
        different_article = FeedItem(
            feed_id=test_feed.id,
            title="Different Article",
            link=f"https://example.com/different-{uuid4()}",
            content_hash=f"different-hash-{uuid4()}",
            simhash_fingerprint=base_fingerprint ^ 0xF,
        )
        db_session.add(different_article)
        await db_session.flush()

        is_flagged_different = await dedup_repository.check_article_already_flagged(
            new_article_id=different_article.id,
            existing_article_id=existing_article.id,
        )

        assert is_flagged_different is False

    @pytest.mark.asyncio
    async def test_boundary_hamming_distance_4(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
    ):
        """Hamming distance = 4 should be near-duplicate (boundary case)."""
        # 4 bits different - just over duplicate threshold
        fp_4_bits = base_fingerprint ^ 0xF

        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Boundary 4",
            link=f"https://example.com/existing-boundary-4-{uuid4()}",
            content_hash=f"existing-hash-boundary-4-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        result = dedup_service.check_duplicate(
            fingerprint=fp_4_bits,
            existing_fingerprints=existing_fps,
        )

        # Hamming = 4 is near-duplicate (> 3 threshold)
        assert result.is_allowed is True
        assert result.is_duplicate is False
        assert result.is_near_duplicate is True
        assert result.hamming_distance == 4

    @pytest.mark.asyncio
    async def test_boundary_hamming_distance_8(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
    ):
        """Hamming distance = 8 should NOT be near-duplicate (boundary case)."""
        # 8 bits different - just over near-duplicate threshold
        fp_8_bits = base_fingerprint ^ 0xFF

        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Boundary 8",
            link=f"https://example.com/existing-boundary-8-{uuid4()}",
            content_hash=f"existing-hash-boundary-8-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        result = dedup_service.check_duplicate(
            fingerprint=fp_8_bits,
            existing_fingerprints=existing_fps,
        )

        # Hamming = 8 is NOT near-duplicate (> 7 threshold)
        assert result.is_allowed is True
        assert result.is_duplicate is False
        assert result.is_near_duplicate is False
        assert result.hamming_distance == 8

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(
        self,
        db_session,
        test_feed,
        dedup_service,
        dedup_repository,
        base_fingerprint,
        near_duplicate_fingerprint,
    ):
        """Test complete pipeline: check -> flag -> verify."""
        # Step 1: Create existing article
        existing_article = FeedItem(
            feed_id=test_feed.id,
            title="Existing Article Full Pipeline",
            link=f"https://example.com/existing-full-pipeline-{uuid4()}",
            content_hash=f"existing-hash-full-pipeline-{uuid4()}",
            simhash_fingerprint=base_fingerprint,
        )
        db_session.add(existing_article)
        await db_session.flush()

        # Step 2: Simulate new article ingestion
        new_article = FeedItem(
            feed_id=test_feed.id,
            title="New Article Full Pipeline",
            link=f"https://example.com/new-full-pipeline-{uuid4()}",
            content_hash=f"new-hash-full-pipeline-{uuid4()}",
            simhash_fingerprint=near_duplicate_fingerprint,
        )
        db_session.add(new_article)
        await db_session.flush()

        # Step 3: Get existing fingerprints
        existing_fps = await dedup_repository.get_recent_fingerprints(hours=24)
        # Filter out the new article we just added
        existing_fps = [
            (id, fp) for id, fp in existing_fps
            if id != new_article.id
        ]

        # Step 4: Check for duplicates
        result = dedup_service.check_duplicate(
            fingerprint=near_duplicate_fingerprint,
            existing_fingerprints=existing_fps,
        )

        assert result.is_allowed is True
        assert result.is_near_duplicate is True

        # Step 5: Flag near-duplicate (if applicable)
        if result.is_near_duplicate:
            candidate_id = await dedup_repository.flag_near_duplicate(
                new_article_id=new_article.id,
                existing_article_id=result.matching_article_id,
                hamming_distance=result.hamming_distance,
                simhash_new=near_duplicate_fingerprint,
                simhash_existing=result.matching_fingerprint,
            )
            await db_session.flush()

            # Step 6: Verify candidate was created
            assert candidate_id is not None

            # Verify pending count
            pending_count = await dedup_repository.get_pending_review_count()
            assert pending_count == 1

            # Verify candidate details
            query = select(DuplicateCandidate).where(
                DuplicateCandidate.id == candidate_id
            )
            db_result = await db_session.execute(query)
            candidate = db_result.scalar_one()

            assert candidate.status == "pending"
            assert candidate.new_article_id == new_article.id
            assert candidate.existing_article_id == existing_article.id
            assert candidate.reviewed_by is None
            assert candidate.reviewed_at is None
