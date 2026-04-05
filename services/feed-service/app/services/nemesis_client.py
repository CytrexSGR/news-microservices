"""Client for posting tasks to Nemesis MCP API."""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class NemesisClient:
    """Thin HTTP client for Nemesis MCP JSON-RPC endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:8765",
        timeout: int = 10,
    ):
        self.base_url = base_url
        self.timeout = timeout

    async def _call_tool(
        self, *, tool: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a JSON-RPC 2.0 tools/call request to Nemesis."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool, "arguments": arguments},
                    "id": 1,
                },
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise RuntimeError(f"Nemesis error: {data['error']}")
            return data.get("result", {})

    async def post_web_crawl_links_task(
        self,
        *,
        source_id: str,
        feed_id: str,
        item_id: str,
        url: str,
        title: str,
        content_preview: str,
        links: List[Dict[str, Any]],
        depth: int,
        crawl_session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Post a web_crawl_links task to Nemesis.

        Returns the task dict on success, None on failure.
        """
        try:
            return await self._call_tool(
                tool="task_post",
                arguments={
                    "type": "web_crawl_links",
                    "payload": {
                        "source_id": source_id,
                        "feed_id": feed_id,
                        "item_id": item_id,
                        "url": url,
                        "title": title,
                        "content_preview": content_preview,
                        "links": links,
                        "depth": depth,
                        "crawl_session_id": crawl_session_id,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    },
                },
            )
        except Exception as e:
            logger.warning(f"Failed to post web_crawl_links task to Nemesis: {e}")
            return None
