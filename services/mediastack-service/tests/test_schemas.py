"""Tests for Pydantic schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestNewsArticle:
    """Tests for NewsArticle schema."""

    def test_valid_article(self):
        """Test creating a valid article."""
        from app.schemas.news import NewsArticle

        article = NewsArticle(
            author="John Doe",
            title="Breaking News: Test Article",
            description="This is a test article description",
            url="https://example.com/article/123",
            source="cnn",
            image="https://example.com/image.jpg",
            category="general",
            language="en",
            country="us",
            published_at=datetime(2025, 12, 26, 12, 0, 0)
        )

        assert article.title == "Breaking News: Test Article"
        assert article.source == "cnn"
        assert article.language == "en"

    def test_article_optional_fields(self):
        """Test article with optional fields omitted."""
        from app.schemas.news import NewsArticle

        article = NewsArticle(
            title="Minimal Article",
            url="https://example.com/article",
            source="bbc",
            category="business",
            language="en",
            country="gb",
            published_at=datetime.now()
        )

        assert article.author is None
        assert article.description is None
        assert article.image is None


class TestNewsRequest:
    """Tests for NewsRequest schema."""

    def test_valid_request_with_all_fields(self):
        """Test request with all optional fields."""
        from app.schemas.news import NewsRequest

        request = NewsRequest(
            keywords="bitcoin,crypto",
            sources="cnn,bbc",
            categories="business,technology",
            countries="us,gb",
            languages="en",
            limit=50,
            offset=25
        )

        assert request.keywords == "bitcoin,crypto"
        assert request.limit == 50
        assert request.offset == 25

    def test_default_values(self):
        """Test request with default values."""
        from app.schemas.news import NewsRequest

        request = NewsRequest()

        assert request.keywords is None
        assert request.limit == 25
        assert request.offset == 0

    def test_limit_validation(self):
        """Test limit validation bounds."""
        from app.schemas.news import NewsRequest

        # Max 100
        with pytest.raises(ValidationError):
            NewsRequest(limit=101)

        # Min 1
        with pytest.raises(ValidationError):
            NewsRequest(limit=0)

    def test_date_format_validation(self):
        """Test date format pattern validation."""
        from app.schemas.news import NewsRequest

        # Valid dates
        request = NewsRequest(
            date_from="2025-12-01",
            date_to="2025-12-26"
        )
        assert request.date_from == "2025-12-01"

        # Invalid format (will fail pattern validation)
        with pytest.raises(ValidationError):
            NewsRequest(date_from="12-01-2025")


class TestNewsResponse:
    """Tests for NewsResponse schema."""

    def test_valid_response(self):
        """Test creating a valid response."""
        from app.schemas.news import NewsResponse, NewsArticle, Pagination

        response = NewsResponse(
            pagination=Pagination(limit=25, offset=0, count=25, total=1000),
            data=[
                NewsArticle(
                    title="Test",
                    url="https://example.com",
                    source="test",
                    category="general",
                    language="en",
                    country="us",
                    published_at=datetime.now()
                )
            ]
        )

        assert response.pagination.total == 1000
        assert len(response.data) == 1


class TestUsageStats:
    """Tests for UsageStats schema."""

    def test_valid_stats(self):
        """Test creating valid usage stats."""
        from app.schemas.news import UsageStats

        stats = UsageStats(
            current_calls=5000,
            monthly_limit=10000,
            remaining=5000,
            percentage=50.0,
            month="2025-12",
            days_remaining=5,
            calls_per_day_remaining=1000,
            status="ok"
        )

        assert stats.remaining == 5000
        assert stats.status == "ok"


class TestSourceInfo:
    """Tests for SourceInfo schema."""

    def test_valid_source(self):
        """Test creating valid source info."""
        from app.schemas.news import SourceInfo

        source = SourceInfo(
            id="cnn",
            name="CNN",
            category="general",
            country="us",
            language="en",
            url="https://www.cnn.com"
        )

        assert source.id == "cnn"
        assert source.name == "CNN"
