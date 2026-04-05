"""Tests for WebFetcher — TDD first."""
import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.web_fetcher import WebFetcher


@pytest.mark.asyncio
async def test_fetch_page_calls_scraping_service_with_extract_links():
    fetcher = WebFetcher(scraping_service_url="http://fake:8009")
    mock_response = MagicMock(
        status_code=200,
        json=lambda: {
            "content": "Page content",
            "status": "success",
            "extracted_title": "Test",
            "extracted_links": [{"url": "https://example.com/a"}],
        },
    )
    mock_response.raise_for_status = MagicMock()
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_post:
        result = await fetcher.fetch_page("https://example.com")
        assert result["content"] == "Page content"
        posted_json = mock_post.call_args[1]["json"]
        assert posted_json["extract_links"] is True


def test_content_has_changed():
    fetcher = WebFetcher(scraping_service_url="http://fake:8009")
    old_hash = hashlib.sha256(b"old content").hexdigest()
    assert fetcher.content_has_changed("new content", old_hash) is True
    assert fetcher.content_has_changed("old content", old_hash) is False
    assert fetcher.content_has_changed("anything", None) is True


def test_compute_content_hash():
    fetcher = WebFetcher(scraping_service_url="http://fake:8009")
    assert fetcher.compute_content_hash("test") == hashlib.sha256(b"test").hexdigest()


@pytest.mark.asyncio
async def test_publish_links_filters_non_main_content():
    mock_nemesis = AsyncMock()
    mock_nemesis.post_web_crawl_links_task = AsyncMock(return_value={"id": "t1"})
    fetcher = WebFetcher(
        scraping_service_url="http://fake:8009", nemesis_client=mock_nemesis
    )
    links = [
        {"url": "https://e.com/article", "position": "main_content", "is_document": False},
        {"url": "https://e.com/nav", "position": "navigation", "is_document": False},
        {"url": "https://e.com/paper.pdf", "position": "main_content", "is_document": True},
    ]
    await fetcher.publish_links_to_nemesis(
        source_id="s",
        feed_id="f",
        item_id="i",
        url="https://e.com",
        title="T",
        content_preview="P",
        links=links,
        depth=0,
        crawl_session_id="cs",
    )
    published_links = mock_nemesis.post_web_crawl_links_task.call_args[1]["links"]
    assert len(published_links) == 1
    assert published_links[0]["url"] == "https://e.com/article"


@pytest.mark.asyncio
async def test_publish_links_skips_empty():
    mock_nemesis = AsyncMock()
    mock_nemesis.post_web_crawl_links_task = AsyncMock()
    fetcher = WebFetcher(
        scraping_service_url="http://fake:8009", nemesis_client=mock_nemesis
    )
    await fetcher.publish_links_to_nemesis(
        source_id="s",
        feed_id="f",
        item_id="i",
        url="https://e.com",
        title="T",
        content_preview="P",
        links=[],
        depth=0,
        crawl_session_id="cs",
    )
    mock_nemesis.post_web_crawl_links_task.assert_not_called()
