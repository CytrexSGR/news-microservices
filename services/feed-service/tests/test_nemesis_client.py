"""Tests for Nemesis MCP client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.nemesis_client import NemesisClient


@pytest.mark.asyncio
async def test_post_task_sends_correct_payload():
    client = NemesisClient(base_url="http://fake:8765")
    with patch.object(client, "_call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"id": "task-123", "status": "pending"}
        result = await client.post_web_crawl_links_task(
            source_id="src-1",
            feed_id="feed-1",
            item_id="item-1",
            url="https://example.com",
            title="Test",
            content_preview="Preview",
            links=[{"url": "https://example.com/a", "anchor_text": "Link A"}],
            depth=0,
            crawl_session_id="session-1",
        )
        assert result["id"] == "task-123"
        call_args = mock_call.call_args
        assert call_args[1]["tool"] == "task_post"
        payload = call_args[1]["arguments"]
        assert payload["type"] == "web_crawl_links"
        assert "links" in payload["payload"]


@pytest.mark.asyncio
async def test_post_task_handles_failure_gracefully():
    client = NemesisClient(base_url="http://fake:8765", timeout=1)
    with patch.object(client, "_call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = Exception("Connection refused")
        result = await client.post_web_crawl_links_task(
            source_id="s",
            feed_id="f",
            item_id="i",
            url="https://example.com",
            title="T",
            content_preview="P",
            links=[],
            depth=0,
            crawl_session_id="cs",
        )
        assert result is None


@pytest.mark.asyncio
async def test_call_tool_sends_jsonrpc():
    client = NemesisClient(base_url="http://fake:8765")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": {"ok": True}}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp
        result = await client._call_tool(tool="task_post", arguments={"type": "test"})
        assert result == {"ok": True}
        posted_json = mock_post.call_args[1]["json"]
        assert posted_json["jsonrpc"] == "2.0"
        assert posted_json["method"] == "tools/call"
        assert posted_json["params"]["name"] == "task_post"
