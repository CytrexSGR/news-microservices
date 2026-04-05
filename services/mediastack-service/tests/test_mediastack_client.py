"""Tests for MediaStack API Client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


@pytest.fixture
def client():
    """Create client instance."""
    from app.clients.mediastack_client import MediaStackClient
    return MediaStackClient()


class TestMediaStackClient:
    """Tests for MediaStack API client."""

    @pytest.mark.asyncio
    async def test_fetch_live_news_success(self, client):
        """Test fetching live news returns articles."""
        from app.clients.mediastack_client import MediaStackClient

        mock_response = {
            "pagination": {"limit": 25, "offset": 0, "count": 25, "total": 1000},
            "data": [
                {
                    "author": "Test Author",
                    "title": "Test Article",
                    "description": "Test description",
                    "url": "https://example.com/article",
                    "source": "example",
                    "image": "https://example.com/image.jpg",
                    "category": "general",
                    "language": "en",
                    "country": "us",
                    "published_at": "2025-12-26T12:00:00+00:00"
                }
            ]
        }

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.fetch_live_news(keywords="trump", countries="us")

            assert len(result["data"]) == 1
            assert result["data"][0]["title"] == "Test Article"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_live_news_with_sources(self, client):
        """Test fetching news filtered by sources."""
        mock_response = {"pagination": {}, "data": []}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client.fetch_live_news(sources="cnn,bbc")

            call_args = mock_request.call_args
            assert "sources" in call_args[1]["params"]
            assert call_args[1]["params"]["sources"] == "cnn,bbc"

    @pytest.mark.asyncio
    async def test_fetch_historical_news(self, client):
        """Test fetching historical news with date range."""
        mock_response = {"pagination": {}, "data": []}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client.fetch_historical_news(
                keywords="bitcoin",
                date_from="2025-12-01",
                date_to="2025-12-26"
            )

            call_args = mock_request.call_args
            assert call_args[1]["params"]["date"] == "2025-12-01,2025-12-26"

    @pytest.mark.asyncio
    async def test_get_sources(self, client):
        """Test fetching available sources."""
        mock_response = {
            "data": [
                {"id": "cnn", "name": "CNN", "category": "general", "country": "us"},
                {"id": "bbc", "name": "BBC", "category": "general", "country": "gb"}
            ]
        }

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.get_sources(countries="us,gb")

            assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_api_error_handling(self, client):
        """Test proper error handling for API errors."""
        from app.clients.mediastack_client import MediaStackError

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = MediaStackError("API Error", code=101)

            with pytest.raises(MediaStackError) as exc_info:
                await client.fetch_live_news()

            assert exc_info.value.code == 101
