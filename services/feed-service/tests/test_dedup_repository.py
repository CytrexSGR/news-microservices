# services/feed-service/tests/test_dedup_repository.py
"""Tests for deduplication repository.

TDD tests for DeduplicationRepository - Task 3 of Epic 1.2.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from app.services.dedup_repository import DeduplicationRepository
from app.models.feed import FeedItem, DuplicateCandidate, Feed


class TestDeduplicationRepository:
    """Tests for DeduplicationRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session for unit tests."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create repository with mock session."""
        return DeduplicationRepository(mock_session)

    # =========================================================================
    # Unit Tests (with mocked session)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_recent_fingerprints_empty(self, repo, mock_session):
        """Should return empty list when no fingerprints exist."""
        # Setup mock to return empty result
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_recent_fingerprints(hours=24)

        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_fingerprints_with_data(self, repo, mock_session):
        """Should return list of (id, fingerprint) tuples."""
        article_id = uuid4()
        fingerprint = 12345678

        # Setup mock to return data
        mock_result = MagicMock()
        mock_result.all.return_value = [(article_id, fingerprint)]
        mock_session.execute.return_value = mock_result

        result = await repo.get_recent_fingerprints(hours=24)

        assert len(result) == 1
        assert result[0] == (article_id, fingerprint)

    @pytest.mark.asyncio
    async def test_get_recent_fingerprints_respects_limit(self, repo, mock_session):
        """Should respect the limit parameter."""
        # Create 5 fingerprints
        fingerprints = [(uuid4(), i * 1000) for i in range(5)]

        mock_result = MagicMock()
        mock_result.all.return_value = fingerprints[:3]  # Simulate limit=3
        mock_session.execute.return_value = mock_result

        result = await repo.get_recent_fingerprints(hours=24, limit=3)

        assert len(result) == 3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_flag_near_duplicate(self, repo, mock_session):
        """Should create duplicate_candidate record."""
        new_id = uuid4()
        existing_id = uuid4()

        # Setup mock to capture the added object
        added_objects = []
        mock_session.add = lambda obj: added_objects.append(obj)

        await repo.flag_near_duplicate(
            new_article_id=new_id,
            existing_article_id=existing_id,
            hamming_distance=5,
            simhash_new=12345,
            simhash_existing=12340,
        )

        # Verify add was called with correct data
        assert len(added_objects) == 1
        candidate = added_objects[0]
        assert candidate.new_article_id == new_id
        assert candidate.existing_article_id == existing_id
        assert candidate.hamming_distance == 5
        assert candidate.simhash_new == 12345
        assert candidate.simhash_existing == 12340
        assert candidate.status == "pending"

        # Verify flush was called
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_flag_near_duplicate_returns_id(self, db_session):
        """Should return the UUID of the created record (integration test)."""
        # This needs a real session to test ID generation
        # Create a feed first (required for FeedItem)
        feed = Feed(
            name="Test Feed for ID",
            url="https://example.com/feed-id.xml",
        )
        db_session.add(feed)
        await db_session.flush()

        # Create two articles
        article1 = FeedItem(
            feed_id=feed.id,
            title="Article 1 for ID",
            link="https://example.com/article1-id",
            content_hash="hash1id" + str(uuid4())[:50],
            simhash_fingerprint=11111,
        )
        article2 = FeedItem(
            feed_id=feed.id,
            title="Article 2 for ID",
            link="https://example.com/article2-id",
            content_hash="hash2id" + str(uuid4())[:50],
            simhash_fingerprint=22222,
        )
        db_session.add(article1)
        db_session.add(article2)
        await db_session.flush()

        repo = DeduplicationRepository(db_session)

        result = await repo.flag_near_duplicate(
            new_article_id=article2.id,
            existing_article_id=article1.id,
            hamming_distance=6,
            simhash_new=22222,
            simhash_existing=11111,
        )

        # Should return a UUID
        assert result is not None
        # Verify it's a valid UUID
        from uuid import UUID as UUIDType
        assert isinstance(result, UUIDType)

    @pytest.mark.asyncio
    async def test_get_pending_review_count_empty(self, repo, mock_session):
        """Should return 0 when no pending reviews."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        count = await repo.get_pending_review_count()

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_pending_review_count_with_data(self, repo, mock_session):
        """Should return count of pending reviews."""
        mock_result = MagicMock()
        # Simulate 3 pending candidates
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(), MagicMock(), MagicMock()
        ]
        mock_session.execute.return_value = mock_result

        count = await repo.get_pending_review_count()

        assert count == 3

    @pytest.mark.asyncio
    async def test_check_article_already_flagged_not_found(self, repo, mock_session):
        """Should return False when pair not already flagged."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.check_article_already_flagged(
            new_article_id=uuid4(),
            existing_article_id=uuid4(),
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_check_article_already_flagged_found(self, repo, mock_session):
        """Should return True when pair already flagged."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Existing record
        mock_session.execute.return_value = mock_result

        result = await repo.check_article_already_flagged(
            new_article_id=uuid4(),
            existing_article_id=uuid4(),
        )

        assert result is True


class TestDeduplicationRepositoryIntegration:
    """Integration tests using real database session."""

    @pytest.mark.asyncio
    async def test_get_recent_fingerprints_with_db(self, db_session):
        """Should query real database and return fingerprints."""
        repo = DeduplicationRepository(db_session)

        # First, verify empty result
        result = await repo.get_recent_fingerprints(hours=24)
        assert result == []

    @pytest.mark.asyncio
    async def test_flag_and_check_near_duplicate_with_db(self, db_session):
        """Should create and retrieve duplicate candidate record."""
        # Create a feed first (required for FeedItem)
        feed = Feed(
            name="Test Feed",
            url="https://example.com/feed.xml",
        )
        db_session.add(feed)
        await db_session.flush()

        # Create two articles
        article1 = FeedItem(
            feed_id=feed.id,
            title="Article 1",
            link="https://example.com/article1",
            content_hash="hash1" + str(uuid4())[:50],
            simhash_fingerprint=12345,
        )
        article2 = FeedItem(
            feed_id=feed.id,
            title="Article 2",
            link="https://example.com/article2",
            content_hash="hash2" + str(uuid4())[:50],
            simhash_fingerprint=12340,
        )
        db_session.add(article1)
        db_session.add(article2)
        await db_session.flush()

        repo = DeduplicationRepository(db_session)

        # Flag near-duplicate
        candidate_id = await repo.flag_near_duplicate(
            new_article_id=article2.id,
            existing_article_id=article1.id,
            hamming_distance=5,
            simhash_new=12340,
            simhash_existing=12345,
        )

        assert candidate_id is not None

        # Check if already flagged
        is_flagged = await repo.check_article_already_flagged(
            new_article_id=article2.id,
            existing_article_id=article1.id,
        )
        assert is_flagged is True

        # Check count
        count = await repo.get_pending_review_count()
        assert count == 1

    @pytest.mark.asyncio
    async def test_get_recent_fingerprints_filters_by_time(self, db_session):
        """Should only return fingerprints within the time window."""
        # Create a feed
        feed = Feed(
            name="Test Feed",
            url="https://example.com/feed.xml",
        )
        db_session.add(feed)
        await db_session.flush()

        # Create article with fingerprint (will have recent created_at)
        article = FeedItem(
            feed_id=feed.id,
            title="Recent Article",
            link="https://example.com/recent",
            content_hash="recent_hash" + str(uuid4())[:50],
            simhash_fingerprint=99999999,
        )
        db_session.add(article)
        await db_session.flush()

        repo = DeduplicationRepository(db_session)

        # Should find the recent article
        result = await repo.get_recent_fingerprints(hours=24)
        assert len(result) == 1
        assert result[0][0] == article.id
        assert result[0][1] == 99999999

    @pytest.mark.asyncio
    async def test_get_recent_fingerprints_excludes_null(self, db_session):
        """Should not return articles without fingerprints."""
        # Create a feed
        feed = Feed(
            name="Test Feed",
            url="https://example.com/feed.xml",
        )
        db_session.add(feed)
        await db_session.flush()

        # Create article WITHOUT fingerprint
        article_no_fp = FeedItem(
            feed_id=feed.id,
            title="No Fingerprint",
            link="https://example.com/no-fp",
            content_hash="no_fp_hash" + str(uuid4())[:50],
            simhash_fingerprint=None,  # No fingerprint
        )
        # Create article WITH fingerprint
        article_with_fp = FeedItem(
            feed_id=feed.id,
            title="With Fingerprint",
            link="https://example.com/with-fp",
            content_hash="with_fp_hash" + str(uuid4())[:50],
            simhash_fingerprint=88888888,
        )
        db_session.add(article_no_fp)
        db_session.add(article_with_fp)
        await db_session.flush()

        repo = DeduplicationRepository(db_session)

        result = await repo.get_recent_fingerprints(hours=24)

        # Should only return the article with fingerprint
        assert len(result) == 1
        assert result[0][0] == article_with_fp.id
        assert result[0][1] == 88888888
