"""Fetches configured web sources via the Scraping Service API."""
import hashlib
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.nemesis_client import NemesisClient

logger = logging.getLogger(__name__)


class WebFetcher:
    """Fetches web pages via scraping-service and manages crawl sessions."""

    def __init__(
        self,
        scraping_service_url: str = "http://scraping-service:8009",
        nemesis_client: Optional[NemesisClient] = None,
    ):
        self.scraping_url = scraping_service_url
        self.nemesis = nemesis_client or NemesisClient()

    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """Fetch and scrape a single URL via the scraping service."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.scraping_url}/api/v1/scrape",
                json={"url": url, "extract_links": True},
            )
            response.raise_for_status()
            return response.json()

    def content_has_changed(self, new_content: str, old_hash: Optional[str]) -> bool:
        """Check whether content differs from a previous hash."""
        if old_hash is None:
            return True
        return hashlib.sha256(new_content.encode()).hexdigest() != old_hash

    def compute_content_hash(self, content: str) -> str:
        """Return SHA-256 hex digest of *content*."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def create_crawl_session(
        self,
        session: AsyncSession,
        feed_id: str,
        seed_url: str,
        topic: Optional[str] = None,
    ) -> str:
        """Insert a new crawl_sessions row and return its id."""
        session_id = str(uuid4())
        await session.execute(
            text(
                "INSERT INTO crawl_sessions (id, feed_id, seed_url, topic) "
                "VALUES (:id, :feed_id, :seed_url, :topic)"
            ),
            {
                "id": session_id,
                "feed_id": feed_id,
                "seed_url": seed_url,
                "topic": topic,
            },
        )
        return session_id

    async def update_crawl_session(
        self, session: AsyncSession, crawl_session_id: str, url: str
    ) -> None:
        """Append *url* to visited_urls and bump pages_scraped."""
        await session.execute(
            text(
                "UPDATE crawl_sessions "
                "SET visited_urls = visited_urls || CAST(:url_json AS jsonb), "
                "    pages_scraped = pages_scraped + 1 "
                "WHERE id = :id"
            ),
            {"id": crawl_session_id, "url_json": f'["{url}"]'},
        )

    async def publish_links_to_nemesis(
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
    ) -> None:
        """Filter links to main-content non-document entries and publish to Nemesis."""
        if not links:
            return

        crawl_links = [
            l
            for l in links
            if l.get("position") == "main_content"
            and not l.get("is_document", False)
        ]
        if not crawl_links:
            return

        await self.nemesis.post_web_crawl_links_task(
            source_id=source_id,
            feed_id=feed_id,
            item_id=item_id,
            url=url,
            title=title,
            content_preview=content_preview[:500],
            links=crawl_links,
            depth=depth,
            crawl_session_id=crawl_session_id,
        )
        logger.info(
            f"Published {len(crawl_links)} links to Nemesis for {url} (depth={depth})"
        )
