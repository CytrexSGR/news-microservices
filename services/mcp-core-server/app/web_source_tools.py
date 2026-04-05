"""MCP Tools for web source management.

Provides tools to add/list web sources, trigger crawls,
and check crawl session status via Feed Service and Nemesis.
"""
import logging
from typing import Any, Dict, Optional

import httpx

from .mcp.tools import MCPToolRegistry, tool_registry

logger = logging.getLogger(__name__)

FEED_SERVICE_URL = "http://feed-service:8000"
NEMESIS_URL = "http://localhost:8765"


@tool_registry.register(
    name="add_web_source",
    description="Add a web page for regular scraping (like adding an RSS feed, but for any URL)",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to monitor"},
            "name": {"type": "string", "description": "Name for this source"},
            "fetch_interval": {
                "type": "integer",
                "description": "Check interval in minutes (default 60)",
                "default": 60,
            },
            "category": {
                "type": "string",
                "description": "Category (science, news, tech, etc.)",
            },
        },
        "required": ["url", "name"],
    },
    category="web_sources",
)
async def add_web_source(
    registry: MCPToolRegistry,
    url: str,
    name: str,
    fetch_interval: int = 60,
    category: str = None,
) -> Dict[str, Any]:
    """Add a web source (feed_type=web) to the Feed Service."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{FEED_SERVICE_URL}/api/v1/feeds",
            json={
                "url": url,
                "name": name,
                "feed_type": "web",
                "fetch_interval": fetch_interval,
                "category": category,
                "scrape_full_content": True,
            },
        )
        response.raise_for_status()
        return response.json()


@tool_registry.register(
    name="list_web_sources",
    description="List all configured web sources (non-RSS feeds with feed_type=web)",
    input_schema={"type": "object", "properties": {}},
    category="web_sources",
)
async def list_web_sources(registry: MCPToolRegistry) -> Dict[str, Any]:
    """List web sources by filtering feeds with feed_type=web."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{FEED_SERVICE_URL}/api/v1/feeds",
            params={"feed_type": "web"},
        )
        response.raise_for_status()
        return {"sources": response.json()}


@tool_registry.register(
    name="trigger_web_crawl",
    description="Start an ad-hoc web crawl. CypherHouse decides depth and which links to follow.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Starting URL"},
            "topic": {
                "type": "string",
                "description": "Topic to guide link selection",
            },
        },
        "required": ["url"],
    },
    category="web_sources",
)
async def trigger_web_crawl(
    registry: MCPToolRegistry,
    url: str,
    topic: str = None,
) -> Dict[str, Any]:
    """Trigger a web crawl via Nemesis task queue."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{NEMESIS_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "task_post",
                    "arguments": {
                        "type": "web_crawl",
                        "payload": {
                            "seed_url": url,
                            "topic": topic,
                            "current_depth": 0,
                            "pages_scraped": 0,
                        },
                    },
                },
                "id": 1,
            },
        )
        response.raise_for_status()
        return response.json().get("result", {})


@tool_registry.register(
    name="get_crawl_session",
    description="Get status of a crawl session by its UUID",
    input_schema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Session UUID",
            },
        },
        "required": ["session_id"],
    },
    category="web_sources",
)
async def get_crawl_session(
    registry: MCPToolRegistry,
    session_id: str,
) -> Dict[str, Any]:
    """Get crawl session status from Feed Service."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{FEED_SERVICE_URL}/api/v1/crawl-sessions/{session_id}"
        )
        response.raise_for_status()
        return response.json()
