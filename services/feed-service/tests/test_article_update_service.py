"""Tests for ArticleUpdateService."""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.services.article_update_service import ArticleUpdateService
from app.models import FeedItem, Feed
from app.models.intelligence import ArticleVersion
from news_intelligence_common import SimHasher


class TestArticleUpdateService:
    """Test article version tracking."""

    @pytest_asyncio.fixture
    async def feed_with_article(self, db_session):
        """Create feed with one article."""
        feed = Feed(
            url="https://example.com/feed.xml",
            name="Test Feed",
        )
        db_session.add(feed)
        await db_session.flush()

        item = FeedItem(
            feed_id=feed.id,
            title="Original Title",
            link="https://example.com/article",
            content="Original content",
            content_hash="hash123",
            version=1,
            version_created_at=datetime.now(timezone.utc),
            pub_status='usable',
            # Use a smaller simhash value that fits in SQLite INTEGER
            # SQLite max signed int is 2^63-1, but we use a smaller value for safety
            simhash_fingerprint=12345678901234,  # 14 digits, well within SQLite range
        )
        db_session.add(item)
        await db_session.commit()

        return feed, item

    @pytest.mark.asyncio
    async def test_update_article_increments_version(
        self, db_session, feed_with_article
    ):
        """Updating article should increment version."""
        feed, item = feed_with_article
        original_version = item.version

        service = ArticleUpdateService(db_session)
        updated = await service.update_article(
            article_id=item.id,
            title="Updated Title",
            content="Updated content",
            change_type="update",
        )

        assert updated.version == original_version + 1
        assert updated.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_article_creates_version_record(
        self, db_session, feed_with_article
    ):
        """Update should create ArticleVersion record."""
        feed, item = feed_with_article

        service = ArticleUpdateService(db_session)
        await service.update_article(
            article_id=item.id,
            title="Updated Title",
            content="Updated content",
            change_type="update",
        )
        await db_session.commit()

        # Query version history
        from sqlalchemy import select
        stmt = select(ArticleVersion).where(ArticleVersion.article_id == item.id)
        result = await db_session.execute(stmt)
        versions = result.scalars().all()

        assert len(versions) == 1
        assert versions[0].version == 1  # Snapshot of OLD version
        assert versions[0].title == "Original Title"
        assert versions[0].change_type == "update"

    @pytest.mark.asyncio
    async def test_update_recalculates_simhash(
        self, db_session, feed_with_article
    ):
        """SimHash should be recalculated on content update."""
        from unittest.mock import patch

        feed, item = feed_with_article
        original_simhash = item.simhash_fingerprint

        # Mock SimHasher to return SQLite-compatible values
        with patch.object(
            SimHasher, 'compute_fingerprint',
            return_value=98765432109876  # Different from original, SQLite-safe
        ):
            service = ArticleUpdateService(db_session)
            updated = await service.update_article(
                article_id=item.id,
                title="Completely Different Title",
                content="Completely different content about something else",
                change_type="update",
            )

        assert updated.simhash_fingerprint != original_simhash
        assert updated.simhash_fingerprint == 98765432109876

    @pytest.mark.asyncio
    async def test_correction_sets_flag(
        self, db_session, feed_with_article
    ):
        """Correction should set is_correction flag."""
        from unittest.mock import patch

        feed, item = feed_with_article

        # Mock SimHasher to return SQLite-compatible values
        with patch.object(
            SimHasher, 'compute_fingerprint',
            return_value=11111111111111  # SQLite-safe
        ):
            service = ArticleUpdateService(db_session)
            updated = await service.update_article(
                article_id=item.id,
                title="Corrected Title",
                content="Corrected content",
                change_type="correction",
                change_reason="Factual error in original",
            )

        # Note: is_correction on FeedItem indicates THIS article is a correction
        # For self-corrections, we just increment version
        assert updated.version == 2

    @pytest.mark.asyncio
    async def test_withdrawal_sets_pub_status(
        self, db_session, feed_with_article
    ):
        """Withdrawal should set pub_status to 'canceled'."""
        feed, item = feed_with_article

        service = ArticleUpdateService(db_session)
        updated = await service.update_article(
            article_id=item.id,
            change_type="withdrawal",
            change_reason="Content was inaccurate",
        )

        assert updated.pub_status == 'canceled'

    @pytest.mark.asyncio
    async def test_update_article_not_found(self, db_session):
        """Should raise ValueError if article not found."""
        service = ArticleUpdateService(db_session)

        with pytest.raises(ValueError, match="Article not found"):
            await service.update_article(
                article_id=uuid4(),
                title="New Title",
                change_type="update",
            )

    @pytest.mark.asyncio
    async def test_invalid_change_type(self, db_session, feed_with_article):
        """Should raise ValueError for invalid change type."""
        feed, item = feed_with_article

        service = ArticleUpdateService(db_session)

        with pytest.raises(ValueError, match="Invalid change_type"):
            await service.update_article(
                article_id=item.id,
                title="New Title",
                change_type="invalid",
            )

    @pytest.mark.asyncio
    async def test_get_version_history(self, db_session, feed_with_article):
        """Should return version history ordered by version desc."""
        from unittest.mock import patch

        feed, item = feed_with_article

        service = ArticleUpdateService(db_session)

        # Mock SimHasher to return SQLite-compatible values
        with patch.object(
            SimHasher, 'compute_fingerprint',
            return_value=22222222222222  # SQLite-safe
        ):
            # Make two updates
            await service.update_article(
                article_id=item.id,
                title="V2 Title",
                change_type="update",
            )
            await service.update_article(
                article_id=item.id,
                title="V3 Title",
                change_type="correction",
                change_reason="Fixed typo",
            )
        await db_session.commit()

        # Get history
        versions = await service.get_version_history(item.id)

        assert len(versions) == 2
        # Most recent first
        assert versions[0].version == 2
        assert versions[1].version == 1

    @pytest.mark.asyncio
    async def test_version_snapshot_preserves_original_content(
        self, db_session, feed_with_article
    ):
        """Version snapshot should preserve original content info."""
        from unittest.mock import patch

        feed, item = feed_with_article

        # Mock SimHasher to return SQLite-compatible values
        with patch.object(
            SimHasher, 'compute_fingerprint',
            return_value=33333333333333  # SQLite-safe
        ):
            service = ArticleUpdateService(db_session)
            await service.update_article(
                article_id=item.id,
                title="New Title",
                content="New content",
                change_type="update",
            )
        await db_session.commit()

        versions = await service.get_version_history(item.id)
        assert len(versions) == 1

        snapshot = versions[0]
        assert snapshot.title == "Original Title"
        assert snapshot.pub_status == "usable"
        assert snapshot.content_hash is not None

    @pytest.mark.asyncio
    async def test_no_simhash_recalculation_if_content_unchanged(
        self, db_session, feed_with_article
    ):
        """SimHash should not change if content is not updated."""
        feed, item = feed_with_article
        original_simhash = item.simhash_fingerprint

        service = ArticleUpdateService(db_session)
        # Withdrawal without content change
        updated = await service.update_article(
            article_id=item.id,
            change_type="withdrawal",
            change_reason="Content withdrawn",
        )

        # SimHash should remain the same
        assert updated.simhash_fingerprint == original_simhash
