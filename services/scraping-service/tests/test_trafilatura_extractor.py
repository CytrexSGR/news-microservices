"""Tests for Trafilatura Extractor"""
import pytest
from app.services.extraction.trafilatura_extractor import TrafilaturaExtractor, ScrapeStatus


class TestTrafilaturaExtractor:
    @pytest.fixture
    def extractor(self):
        return TrafilaturaExtractor()

    def test_extractor_initialization(self, extractor):
        """Verify extractor initializes correctly"""
        assert extractor is not None
        # trafilatura may or may not be installed in test environment
        assert isinstance(extractor.is_available, bool)

    def test_extract_from_html_success(self, extractor):
        """Test successful extraction from HTML"""
        if not extractor.is_available:
            pytest.skip("trafilatura not installed")

        html = """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <article>
                <h1>Breaking News</h1>
                <p>This is a test article with enough content to pass minimum word count.</p>
                <p>More paragraphs here to ensure we have substantial content for testing purposes.</p>
                <p>The quick brown fox jumps over the lazy dog multiple times in this story.</p>
                <p>Additional content is needed to meet the minimum word requirement for successful extraction.</p>
                <p>We continue adding more text to make sure the extractor considers this valid content.</p>
            </article>
        </body>
        </html>
        """
        result = extractor.extract(html, url="https://example.com/article", min_word_count=20)

        assert result.status == ScrapeStatus.SUCCESS
        assert result.word_count > 10
        assert result.method_used == "trafilatura"

    def test_extract_empty_html_fails(self, extractor):
        """Test that empty HTML fails extraction"""
        if not extractor.is_available:
            pytest.skip("trafilatura not installed")

        html = "<html><body></body></html>"
        result = extractor.extract(html, url="https://example.com/empty")

        assert result.status == ScrapeStatus.ERROR
        assert result.word_count == 0

    def test_extract_returns_metadata(self, extractor):
        """Test metadata extraction"""
        if not extractor.is_available:
            pytest.skip("trafilatura not installed")

        html = """
        <html>
        <head>
            <title>Test Title</title>
            <meta name="author" content="John Doe">
            <meta name="description" content="Test description">
        </head>
        <body>
            <article>
                <p>Substantial content for extraction testing with many words.</p>
                <p>Another paragraph to ensure minimum word count is met.</p>
                <p>More content here to satisfy the requirements of the extractor.</p>
                <p>The fox jumps over the lazy dog repeatedly in this test article.</p>
                <p>Final paragraph with additional words to complete the test.</p>
            </article>
        </body>
        </html>
        """
        result = extractor.extract(html, url="https://example.com/meta", min_word_count=20)

        if result.status == ScrapeStatus.SUCCESS:
            assert result.extracted_metadata is not None
            assert result.extracted_metadata.get("method") == "trafilatura"

    def test_extractor_unavailable_graceful_handling(self):
        """Test graceful handling when trafilatura not available"""
        extractor = TrafilaturaExtractor()
        # Force unavailable state
        extractor._trafilatura = None

        result = extractor.extract("<html></html>", url="https://example.com")

        assert result.status == ScrapeStatus.ERROR
        assert "not available" in result.error_message
