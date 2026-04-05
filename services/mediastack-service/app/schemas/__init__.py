"""Pydantic schemas for MediaStack Service."""

from app.schemas.news import (
    NewsArticle,
    NewsRequest,
    NewsResponse,
    Pagination,
    SourceInfo,
    SourcesRequest,
    SourcesResponse,
    UsageStats
)

__all__ = [
    "NewsArticle",
    "NewsRequest",
    "NewsResponse",
    "Pagination",
    "SourceInfo",
    "SourcesRequest",
    "SourcesResponse",
    "UsageStats"
]
