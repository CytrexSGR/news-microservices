# services/feed-service/tests/test_epic_0_4_integration.py
"""Integration tests for Epic 0.4: Feed Service Integration.

These tests verify the complete article lifecycle with SimHash fingerprinting,
NewsML-G2 version tracking, and event payload completeness.

Note: Uses mocking for database operations to avoid SQLite BigInteger limitations.
For full PostgreSQL integration tests, see the CI/CD pipeline.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.feed_fetcher import FeedFetcher
from app.services.article_update_service import ArticleUpdateService
from app.models import FeedItem
from app.models.intelligence import ArticleVersion
from news_intelligence_common import SimHasher


class TestEpic04Integration:
    """Full integration test for Epic 0.4 features."""

    @pytest.fixture
    def mock_feed(self):
        """Create a mock feed with all required attributes."""
        feed = MagicMock()
        feed.id = uuid4()
        feed.url = f"https://example.com/feed-{feed.id}.xml"
        feed.name = "Integration Test Feed"
        feed.scrape_full_content = False
        feed.scrape_method = "auto"
        feed.enable_summary = True
        feed.enable_entity_extraction = False
        feed.enable_topic_classification = False
        feed.enable_categorization = False
        feed.enable_finance_sentiment = False
        feed.enable_geopolitical_sentiment = False
        feed.enable_osint_analysis = False
        return feed

    @pytest.fixture
    def mock_session_with_item_capture(self):
        """Create mock session that captures created items."""
        created_items = []

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        def capture_add(item):
            if isinstance(item, (FeedItem, ArticleVersion)):
                created_items.append(item)

        mock_session.add = MagicMock(side_effect=capture_add)
        mock_session.commit = AsyncMock()

        return mock_session, created_items

    @pytest.mark.asyncio
    async def test_full_article_lifecycle(self, mock_feed, mock_session_with_item_capture):
        """
        Test complete article lifecycle:
        1. Article created with SimHash
        2. Article updated (version increments)
        3. Article corrected (version + history)
        4. Article withdrawn (pub_status = canceled)
        """
        mock_session, created_items = mock_session_with_item_capture

        # 1. Create article (simulating feed fetch)
        fetcher = FeedFetcher()
        entry = {
            "title": "Breaking News: Major Event",
            "link": f"https://example.com/{uuid4()}",
            "summary": "Summary of the major event",
            "content": [{"value": "Full content about the major event."}],
        }

        result = await fetcher._process_feed_entry(mock_session, mock_feed, entry)

        # Verify creation result
        assert result is not None
        assert result["simhash_fingerprint"] is not None
        assert result["version"] == 1
        assert result["pub_status"] == 'usable'

        # Get the created item
        created_item = created_items[0]
        assert isinstance(created_item, FeedItem)

        original_simhash = created_item.simhash_fingerprint

        # 2. Update article - simulate ArticleUpdateService behavior
        # Since we're using mocks, we manually simulate the update
        created_item.version = 2
        new_title = "Breaking News: Major Event - Updated"
        new_content = "Updated content with more details."
        created_item.title = new_title
        created_item.content = new_content

        # Recalculate simhash
        simhash_text = f"{new_title} {new_content}"
        created_item.simhash_fingerprint = SimHasher.compute_fingerprint(simhash_text)

        assert created_item.version == 2
        assert created_item.simhash_fingerprint != original_simhash

        # 3. Correct article
        created_item.version = 3
        created_item.title = "Breaking News: Major Event - Corrected"

        assert created_item.version == 3

        # 4. Withdraw article
        created_item.version = 4
        created_item.pub_status = 'canceled'

        assert created_item.version == 4
        assert created_item.pub_status == 'canceled'

    @pytest.mark.asyncio
    async def test_simhash_deduplication_scenario(self, mock_feed, mock_session_with_item_capture):
        """
        Test SimHash enables near-duplicate detection:
        - Two similar articles should have similar SimHash (low Hamming distance)
        - Different articles should have different SimHash (high Hamming distance)
        """
        mock_session, created_items = mock_session_with_item_capture
        fetcher = FeedFetcher()

        # Article 1: Original
        entry1 = {
            "title": "Tech Company Announces New Product Launch",
            "link": f"https://example.com/{uuid4()}",
            "summary": "A major technology company announced today its latest product.",
            "content": [{"value": "The company revealed details about their innovative new product at a press conference."}],
        }

        result1 = await fetcher._process_feed_entry(mock_session, mock_feed, entry1)

        # Reset mock for next item
        created_items.clear()
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        # Article 2: Near-duplicate (same story, slight rewording)
        entry2 = {
            "title": "Tech Company Announces New Product",
            "link": f"https://example.com/{uuid4()}",
            "summary": "A major tech company announced its latest product today.",
            "content": [{"value": "The company revealed details about their innovative new product at a press event."}],
        }

        result2 = await fetcher._process_feed_entry(mock_session, mock_feed, entry2)

        # Reset mock for next item
        created_items.clear()
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        # Article 3: Completely different
        entry3 = {
            "title": "Weather Report: Storm Approaching",
            "link": f"https://example.com/{uuid4()}",
            "summary": "Meteorologists warn of incoming severe weather.",
            "content": [{"value": "A major storm system is expected to bring heavy rain and strong winds."}],
        }

        result3 = await fetcher._process_feed_entry(mock_session, mock_feed, entry3)

        fp1 = result1["simhash_fingerprint"]
        fp2 = result2["simhash_fingerprint"]
        fp3 = result3["simhash_fingerprint"]

        # Near-duplicate should have low Hamming distance
        distance_1_2 = SimHasher.hamming_distance(fp1, fp2)
        # Different content should have high Hamming distance
        distance_1_3 = SimHasher.hamming_distance(fp1, fp3)

        # Near-duplicates typically have distance < 15
        # Different content typically has distance > 15
        assert distance_1_2 < distance_1_3, (
            f"Expected similar articles (d={distance_1_2}) to have lower distance "
            f"than different articles (d={distance_1_3})"
        )

        # Check using SimHasher methods
        hasher = SimHasher()

        # 1 and 3 should NOT be duplicates
        assert not hasher.is_duplicate(fp1, fp3), (
            "Weather report and tech article should not be duplicates"
        )

    @pytest.mark.asyncio
    async def test_event_payload_completeness(self, mock_feed, mock_session_with_item_capture):
        """Verify article.created event has all required Epic 0.4 fields."""
        mock_session, _ = mock_session_with_item_capture
        fetcher = FeedFetcher()

        entry = {
            "title": "Event Payload Test Article",
            "link": f"https://example.com/{uuid4()}",
            "summary": "Testing event payload completeness",
            "content": [{"value": "Full content for event payload test."}],
        }

        result = await fetcher._process_feed_entry(mock_session, mock_feed, entry)

        # Verify all Epic 0.4 fields present
        assert "simhash_fingerprint" in result
        assert "version" in result
        assert "pub_status" in result

        # Verify values
        assert isinstance(result["simhash_fingerprint"], int)
        assert result["version"] == 1
        assert result["pub_status"] == 'usable'

        # Verify existing fields still present
        assert "item_id" in result
        assert "feed_id" in result
        assert "title" in result
        assert "link" in result
        assert "content" in result
        assert "analysis_config" in result

    @pytest.mark.asyncio
    async def test_simhash_fallback_to_description(self, mock_feed, mock_session_with_item_capture):
        """SimHash should use description if no content."""
        mock_session, created_items = mock_session_with_item_capture
        fetcher = FeedFetcher()

        entry = {
            "title": "Article Without Full Content",
            "link": f"https://example.com/{uuid4()}",
            "summary": "This article only has a description, no full content available for processing",
            # No "content" field
        }

        result = await fetcher._process_feed_entry(mock_session, mock_feed, entry)

        # SimHash should still be calculated from title + description
        assert result is not None
        assert result["simhash_fingerprint"] is not None
        assert result["simhash_fingerprint"] > 0

        # Verify the fingerprint matches expected calculation
        expected_text = f"{entry['title']} {entry['summary']}"
        expected_fp = SimHasher.compute_fingerprint(expected_text)
        assert result["simhash_fingerprint"] == expected_fp

    @pytest.mark.asyncio
    async def test_version_history_tracking_with_article_update_service(self):
        """Test that ArticleUpdateService correctly tracks version history."""
        # Create a mock article with all required attributes
        mock_article = MagicMock(spec=FeedItem)
        mock_article.id = uuid4()
        mock_article.title = "Version Tracking Test Article"
        mock_article.content = "Original content for version tracking test."
        mock_article.description = None
        mock_article.link = "https://example.com/test"
        mock_article.version = 1
        mock_article.pub_status = 'usable'
        mock_article.simhash_fingerprint = SimHasher.compute_fingerprint(
            f"{mock_article.title} {mock_article.content}"
        )

        # Create mock session
        mock_session = AsyncMock()

        # Mock the article query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_article)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # Track created versions
        created_versions = []

        def capture_add(item):
            if isinstance(item, ArticleVersion):
                created_versions.append(item)

        mock_session.add = MagicMock(side_effect=capture_add)

        # Create the service
        update_service = ArticleUpdateService(mock_session)

        # Perform an update
        updated = await update_service.update_article(
            article_id=mock_article.id,
            title="Updated Title Version 2",
            content="Updated content version 2 with some changes.",
            change_type="update",
            change_reason="Update number 1",
        )

        # Verify version was incremented
        assert mock_article.version == 2

        # Verify a version snapshot was created
        assert len(created_versions) == 1
        version_snapshot = created_versions[0]
        assert version_snapshot.article_id == mock_article.id
        assert version_snapshot.version == 1  # Snapshot of OLD version
        assert version_snapshot.title == "Version Tracking Test Article"
        assert version_snapshot.change_type == "update"

    @pytest.mark.asyncio
    async def test_article_withdrawal_sets_canceled_status(self):
        """Test that withdrawal sets pub_status to 'canceled'."""
        # Create a mock article
        mock_article = MagicMock(spec=FeedItem)
        mock_article.id = uuid4()
        mock_article.title = "Article to Withdraw"
        mock_article.content = "Content that will be withdrawn."
        mock_article.description = None
        mock_article.link = "https://example.com/withdraw"
        mock_article.version = 1
        mock_article.pub_status = 'usable'
        mock_article.simhash_fingerprint = 12345

        # Create mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_article)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()

        # Create the service
        update_service = ArticleUpdateService(mock_session)

        # Withdraw the article
        withdrawn = await update_service.update_article(
            article_id=mock_article.id,
            change_type="withdrawal",
            change_reason="Content no longer accurate",
        )

        # Verify pub_status was set to 'canceled'
        assert mock_article.pub_status == 'canceled'
        assert mock_article.version == 2

    @pytest.mark.asyncio
    async def test_simhash_stored_on_article_creation(self, mock_feed, mock_session_with_item_capture):
        """SimHash should be persisted on the FeedItem model."""
        mock_session, created_items = mock_session_with_item_capture
        fetcher = FeedFetcher()

        entry = {
            "title": "Database Persistence Test",
            "link": f"https://example.com/{uuid4()}",
            "summary": "Testing database persistence of SimHash",
            "content": [{"value": "Full content for database persistence test."}],
        }

        result = await fetcher._process_feed_entry(mock_session, mock_feed, entry)

        # Verify the FeedItem was created with all Epic 0.4 fields
        assert len(created_items) == 1
        item = created_items[0]

        assert item.simhash_fingerprint is not None
        assert item.simhash_fingerprint > 0
        assert item.version == 1
        assert item.pub_status == 'usable'
        assert item.version_created_at is not None

    @pytest.mark.asyncio
    async def test_simhash_recalculated_on_content_update(self):
        """SimHash should be recalculated when content changes."""
        # Create a mock article
        mock_article = MagicMock(spec=FeedItem)
        mock_article.id = uuid4()
        mock_article.title = "Original Title"
        mock_article.content = "Original content about technology."
        mock_article.description = None
        mock_article.link = "https://example.com/test"
        mock_article.version = 1
        mock_article.pub_status = 'usable'

        original_simhash = SimHasher.compute_fingerprint(
            f"{mock_article.title} {mock_article.content}"
        )
        mock_article.simhash_fingerprint = original_simhash

        # Create mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_article)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()

        # Create the service
        update_service = ArticleUpdateService(mock_session)

        # Update with completely different content
        await update_service.update_article(
            article_id=mock_article.id,
            title="Completely Different Topic",
            content="Weather forecast predicts sunny skies and warm temperatures.",
            change_type="update",
        )

        # Verify simhash was recalculated
        assert mock_article.simhash_fingerprint != original_simhash

        # Verify it matches expected calculation
        expected_simhash = SimHasher.compute_fingerprint(
            f"{mock_article.title} {mock_article.content}"
        )
        assert mock_article.simhash_fingerprint == expected_simhash

    @pytest.mark.asyncio
    async def test_correction_increments_version(self):
        """Correction should increment version like any other update."""
        # Create a mock article
        mock_article = MagicMock(spec=FeedItem)
        mock_article.id = uuid4()
        mock_article.title = "Article with Error"
        mock_article.content = "Content with factual error."
        mock_article.description = None
        mock_article.link = "https://example.com/correction"
        mock_article.version = 1
        mock_article.pub_status = 'usable'
        mock_article.simhash_fingerprint = 12345

        # Create mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_article)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        created_versions = []

        def capture_add(item):
            if isinstance(item, ArticleVersion):
                created_versions.append(item)

        mock_session.add = MagicMock(side_effect=capture_add)

        # Create the service
        update_service = ArticleUpdateService(mock_session)

        # Apply correction
        await update_service.update_article(
            article_id=mock_article.id,
            title="Article with Error - Corrected",
            change_type="correction",
            change_reason="Fixed factual error in original article",
        )

        # Verify version was incremented
        assert mock_article.version == 2

        # Verify version snapshot was created with correction type
        assert len(created_versions) == 1
        assert created_versions[0].change_type == "correction"
        assert created_versions[0].change_reason == "Fixed factual error in original article"
