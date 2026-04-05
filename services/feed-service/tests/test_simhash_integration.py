# services/feed-service/tests/test_simhash_integration.py
"""Tests for SimHash integration in feed-service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from news_intelligence_common import SimHasher


class TestSimHashIntegration:
    """Test SimHash fingerprint calculation during article ingestion."""

    @pytest.fixture
    def sample_entry(self):
        """Create sample RSS entry."""
        return {
            "title": "Breaking News: Major Tech Company Announces New Product",
            "link": f"https://example.com/news/{uuid4()}",
            "summary": "A leading technology company has announced a revolutionary new product that could change the industry.",
            "content": [{"value": "Full article content here with detailed information about the new product launch."}],
            "author": "John Doe",
            "id": "guid-12345",
        }

    # ============== Unit Tests (no DB) ==============

    @pytest.mark.asyncio
    async def test_simhash_uses_title_and_content(self):
        """SimHash should be calculated from title + content."""
        title = "Breaking News: Major Tech Company Announces New Product"
        content = "Full article content here with detailed information."

        # Calculate expected fingerprint
        text = f"{title} {content}"
        fp = SimHasher.compute_fingerprint(text)

        # Should be non-zero
        assert fp > 0
        assert isinstance(fp, int)

    @pytest.mark.asyncio
    async def test_simhash_fallback_to_description(self):
        """SimHash should use description if no content."""
        title = "News Title"
        description = "Article description without full content"

        # Calculate fingerprint from title + description
        text = f"{title} {description}"
        fp = SimHasher.compute_fingerprint(text)

        assert fp > 0

    @pytest.mark.asyncio
    async def test_simhash_compute_fingerprint_consistency(self):
        """SimHash should return consistent fingerprint for same text."""
        text = "Breaking news about technology companies and their new products"

        fp1 = SimHasher.compute_fingerprint(text)
        fp2 = SimHasher.compute_fingerprint(text)

        assert fp1 == fp2
        assert fp1 > 0

    @pytest.mark.asyncio
    async def test_simhash_hamming_distance_for_similar_content(self):
        """Similar content should have low Hamming distance."""
        text1 = "Tech Company Announces New Product Launch Today"
        text2 = "Tech Company Announces New Product Launch"  # Very similar

        fp1 = SimHasher.compute_fingerprint(text1)
        fp2 = SimHasher.compute_fingerprint(text2)

        distance = SimHasher.hamming_distance(fp1, fp2)

        # Similar content should have low Hamming distance (typically < 10)
        assert distance < 15, f"Expected low distance for similar content, got {distance}"

    @pytest.mark.asyncio
    async def test_simhash_hamming_distance_for_different_content(self):
        """Different content should have high Hamming distance."""
        text1 = "Tech Company Announces New Product Launch"
        text2 = "Weather forecast shows sunny skies for the weekend"

        fp1 = SimHasher.compute_fingerprint(text1)
        fp2 = SimHasher.compute_fingerprint(text2)

        distance = SimHasher.hamming_distance(fp1, fp2)

        # Different content should have higher Hamming distance (typically > 15)
        assert distance > 10, f"Expected high distance for different content, got {distance}"

    # ============== Integration Tests with Mocking ==============

    @pytest.mark.asyncio
    async def test_simhash_calculated_on_article_creation(self, sample_entry):
        """SimHash fingerprint should be calculated when article is created."""
        from app.services.feed_fetcher import FeedFetcher

        fetcher = FeedFetcher()

        # Create mock feed
        mock_feed = MagicMock()
        mock_feed.id = uuid4()
        mock_feed.scrape_full_content = False
        mock_feed.scrape_method = "auto"
        mock_feed.enable_summary = True
        mock_feed.enable_entity_extraction = False
        mock_feed.enable_topic_classification = False
        mock_feed.enable_categorization = False
        mock_feed.enable_finance_sentiment = False
        mock_feed.enable_geopolitical_sentiment = False
        mock_feed.enable_osint_analysis = False

        # Mock session
        mock_session = AsyncMock()

        # Mock the duplicate check query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # Track the FeedItem that gets created
        created_item = None

        def capture_add(item):
            nonlocal created_item
            from app.models import FeedItem
            if isinstance(item, FeedItem):
                created_item = item

        mock_session.add = MagicMock(side_effect=capture_add)

        # Process entry
        result = await fetcher._process_feed_entry(mock_session, mock_feed, sample_entry)

        # Verify result
        assert result is not None

        # Verify SimHash was calculated and included in result
        assert "simhash_fingerprint" in result
        assert isinstance(result["simhash_fingerprint"], int)
        assert result["simhash_fingerprint"] > 0

        # Verify the FeedItem was created with simhash
        assert created_item is not None
        assert created_item.simhash_fingerprint is not None
        assert created_item.simhash_fingerprint > 0

    @pytest.mark.asyncio
    async def test_version_fields_set_on_creation(self, sample_entry):
        """NewsML-G2 version fields should be set on article creation."""
        from app.services.feed_fetcher import FeedFetcher

        fetcher = FeedFetcher()

        mock_feed = MagicMock()
        mock_feed.id = uuid4()
        mock_feed.scrape_full_content = False
        mock_feed.scrape_method = "auto"
        mock_feed.enable_summary = False
        mock_feed.enable_entity_extraction = False
        mock_feed.enable_topic_classification = False
        mock_feed.enable_categorization = False
        mock_feed.enable_finance_sentiment = False
        mock_feed.enable_geopolitical_sentiment = False
        mock_feed.enable_osint_analysis = False

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        created_item = None

        def capture_add(item):
            nonlocal created_item
            from app.models import FeedItem
            if isinstance(item, FeedItem):
                created_item = item

        mock_session.add = MagicMock(side_effect=capture_add)

        sample_entry["link"] = f"https://example.com/{uuid4()}"
        result = await fetcher._process_feed_entry(mock_session, mock_feed, sample_entry)

        # Verify NewsML-G2 fields in the FeedItem
        assert created_item is not None
        assert created_item.version == 1
        assert created_item.version_created_at is not None
        assert created_item.pub_status == 'usable'

        # Verify in result (event payload)
        assert result["version"] == 1
        assert result["pub_status"] == 'usable'

    @pytest.mark.asyncio
    async def test_event_payload_includes_simhash(self, sample_entry):
        """article.created event payload should include simhash_fingerprint."""
        from app.services.feed_fetcher import FeedFetcher

        fetcher = FeedFetcher()

        mock_feed = MagicMock()
        mock_feed.id = uuid4()
        mock_feed.scrape_full_content = False
        mock_feed.scrape_method = "auto"
        mock_feed.enable_summary = True
        mock_feed.enable_entity_extraction = False
        mock_feed.enable_topic_classification = False
        mock_feed.enable_categorization = False
        mock_feed.enable_finance_sentiment = False
        mock_feed.enable_geopolitical_sentiment = False
        mock_feed.enable_osint_analysis = False

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()

        sample_entry["link"] = f"https://example.com/{uuid4()}"
        result = await fetcher._process_feed_entry(mock_session, mock_feed, sample_entry)

        # Verify event payload includes simhash
        assert result is not None
        assert "simhash_fingerprint" in result
        assert result["simhash_fingerprint"] is not None
        assert isinstance(result["simhash_fingerprint"], int)

    @pytest.mark.asyncio
    async def test_event_payload_includes_version(self, sample_entry):
        """article.created event should include version metadata."""
        from app.services.feed_fetcher import FeedFetcher

        fetcher = FeedFetcher()

        mock_feed = MagicMock()
        mock_feed.id = uuid4()
        mock_feed.scrape_full_content = False
        mock_feed.scrape_method = "auto"
        mock_feed.enable_summary = False
        mock_feed.enable_entity_extraction = False
        mock_feed.enable_topic_classification = False
        mock_feed.enable_categorization = False
        mock_feed.enable_finance_sentiment = False
        mock_feed.enable_geopolitical_sentiment = False
        mock_feed.enable_osint_analysis = False

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()

        sample_entry["link"] = f"https://example.com/{uuid4()}"
        result = await fetcher._process_feed_entry(mock_session, mock_feed, sample_entry)

        assert result["version"] == 1
        assert result["pub_status"] == 'usable'

    @pytest.mark.asyncio
    async def test_simhash_deduplication_scenario(self):
        """
        Test SimHash enables near-duplicate detection:
        - Two similar articles should have similar SimHash (low Hamming distance)
        - Different articles should have different SimHash (high Hamming distance)
        """
        # Article 1: Original
        text1 = "Tech Company Announces New Product Launch A major technology company announced today its latest product. The company revealed details about their innovative new product at a press conference."

        # Article 2: Near-duplicate (same story, slight rewording)
        text2 = "Tech Company Announces New Product A major tech company announced its latest product today. The company revealed details about their innovative new product at a press event."

        # Article 3: Completely different
        text3 = "Weather Report: Storm Approaching Meteorologists warn of incoming severe weather. A major storm system is expected to bring heavy rain and strong winds."

        fp1 = SimHasher.compute_fingerprint(text1)
        fp2 = SimHasher.compute_fingerprint(text2)
        fp3 = SimHasher.compute_fingerprint(text3)

        # Near-duplicate should have low Hamming distance
        distance_1_2 = SimHasher.hamming_distance(fp1, fp2)
        # Different content should have high Hamming distance
        distance_1_3 = SimHasher.hamming_distance(fp1, fp3)

        # Near-duplicates typically have distance < 10-15
        # Different content typically has distance > 20
        assert distance_1_2 < distance_1_3, f"Expected similar articles to have lower distance: d(1,2)={distance_1_2}, d(1,3)={distance_1_3}"

        # 1 and 3 should NOT be duplicates
        hasher = SimHasher()
        assert not hasher.is_duplicate(fp1, fp3), "Weather report and tech article should not be duplicates"

    @pytest.mark.asyncio
    async def test_event_payload_completeness(self, sample_entry):
        """Verify article.created event has all required Epic 0.4 fields."""
        from app.services.feed_fetcher import FeedFetcher

        fetcher = FeedFetcher()

        mock_feed = MagicMock()
        mock_feed.id = uuid4()
        mock_feed.scrape_full_content = False
        mock_feed.scrape_method = "auto"
        mock_feed.enable_summary = True
        mock_feed.enable_entity_extraction = True
        mock_feed.enable_topic_classification = False
        mock_feed.enable_categorization = False
        mock_feed.enable_finance_sentiment = False
        mock_feed.enable_geopolitical_sentiment = False
        mock_feed.enable_osint_analysis = False

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()

        sample_entry["link"] = f"https://example.com/{uuid4()}"
        result = await fetcher._process_feed_entry(mock_session, mock_feed, sample_entry)

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
    async def test_simhash_with_description_only(self):
        """SimHash should work when only description is available (no content)."""
        from app.services.feed_fetcher import FeedFetcher

        fetcher = FeedFetcher()

        mock_feed = MagicMock()
        mock_feed.id = uuid4()
        mock_feed.scrape_full_content = False
        mock_feed.scrape_method = "auto"
        mock_feed.enable_summary = False
        mock_feed.enable_entity_extraction = False
        mock_feed.enable_topic_classification = False
        mock_feed.enable_categorization = False
        mock_feed.enable_finance_sentiment = False
        mock_feed.enable_geopolitical_sentiment = False
        mock_feed.enable_osint_analysis = False

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        created_item = None

        def capture_add(item):
            nonlocal created_item
            from app.models import FeedItem
            if isinstance(item, FeedItem):
                created_item = item

        mock_session.add = MagicMock(side_effect=capture_add)

        # Entry with only description, no content
        entry = {
            "title": "Article Title Without Full Content",
            "link": f"https://example.com/{uuid4()}",
            "summary": "This is the description/summary of the article without full content.",
        }

        result = await fetcher._process_feed_entry(mock_session, mock_feed, entry)

        # Verify SimHash was calculated from title + description
        assert result is not None
        assert result["simhash_fingerprint"] is not None
        assert result["simhash_fingerprint"] > 0

        # Verify the expected text was used (title + description)
        expected_text = f"{entry['title']} {entry['summary']}"
        expected_fp = SimHasher.compute_fingerprint(expected_text)
        assert result["simhash_fingerprint"] == expected_fp
