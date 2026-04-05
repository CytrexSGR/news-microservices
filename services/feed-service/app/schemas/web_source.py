"""Schemas for web source and crawl session responses."""
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class WebSourceCreate(BaseModel):
    """Create a web source (feed with feed_type='web')."""
    url: HttpUrl
    name: str = Field(..., max_length=200)
    fetch_interval: int = Field(default=60, ge=5, le=1440)
    category: Optional[str] = None
    description: Optional[str] = None


class CrawlSessionResponse(BaseModel):
    """Response for a crawl session."""
    id: str
    feed_id: Optional[str] = None
    seed_url: str
    topic: Optional[str] = None
    status: str
    pages_scraped: int
    visited_urls: list = []
    created_at: str
    completed_at: Optional[str] = None
