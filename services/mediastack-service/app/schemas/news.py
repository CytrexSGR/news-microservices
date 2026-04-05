"""Pydantic schemas for news-related API operations."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class NewsArticle(BaseModel):
    """Schema for a single news article from MediaStack."""

    author: Optional[str] = Field(None, description="Article author name")
    title: str = Field(..., description="Article headline")
    description: Optional[str] = Field(None, description="Article snippet/summary")
    url: str = Field(..., description="Link to full article")
    source: str = Field(..., description="News source identifier")
    image: Optional[str] = Field(None, description="Image URL if available")
    category: str = Field(..., description="Article category")
    language: str = Field(..., description="Language code (en, de, etc.)")
    country: str = Field(..., description="Country code")
    published_at: datetime = Field(..., description="Publication timestamp")


class Pagination(BaseModel):
    """Pagination metadata from MediaStack API."""

    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Current offset")
    count: int = Field(..., description="Results returned")
    total: int = Field(..., description="Total available results")


class NewsRequest(BaseModel):
    """Request schema for fetching news articles."""

    keywords: Optional[str] = Field(
        None,
        description="Search keywords (comma-separated for OR logic)",
        examples=["bitcoin,crypto", "trump"]
    )
    sources: Optional[str] = Field(
        None,
        description="Filter by sources (comma-separated)",
        examples=["cnn,bbc"]
    )
    categories: Optional[str] = Field(
        None,
        description="Filter by categories: general,business,technology,entertainment,health,science,sports",
        examples=["business,technology"]
    )
    countries: Optional[str] = Field(
        None,
        description="Filter by country codes (comma-separated)",
        examples=["us,gb,de"]
    )
    languages: Optional[str] = Field(
        None,
        description="Filter by language codes",
        examples=["en,de"]
    )
    limit: int = Field(
        25,
        ge=1,
        le=100,
        description="Results per page (max 100)"
    )
    offset: int = Field(
        0,
        ge=0,
        description="Pagination offset"
    )

    # Historical news only (paid plans)
    date_from: Optional[str] = Field(
        None,
        description="Start date (YYYY-MM-DD) - paid plans only",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    date_to: Optional[str] = Field(
        None,
        description="End date (YYYY-MM-DD) - paid plans only",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )


class NewsResponse(BaseModel):
    """Response schema for news articles."""

    pagination: Pagination = Field(..., description="Pagination metadata")
    data: List[NewsArticle] = Field(..., description="List of news articles")
    usage: Optional["UsageStats"] = Field(None, description="Current API usage stats")


class SourceInfo(BaseModel):
    """Schema for a news source."""

    id: str = Field(..., description="Source identifier (e.g., 'cnn')")
    name: str = Field(..., description="Source display name")
    category: str = Field(..., description="Source category")
    country: str = Field(..., description="Country code")
    language: str = Field(..., description="Primary language")
    url: Optional[str] = Field(None, description="Source website URL")


class SourcesRequest(BaseModel):
    """Request schema for fetching available sources."""

    countries: Optional[str] = Field(
        None,
        description="Filter by country codes"
    )
    categories: Optional[str] = Field(
        None,
        description="Filter by categories"
    )
    languages: Optional[str] = Field(
        None,
        description="Filter by languages"
    )
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Max sources to return"
    )


class SourcesResponse(BaseModel):
    """Response schema for sources list."""

    data: List[SourceInfo] = Field(..., description="List of available sources")
    usage: Optional["UsageStats"] = Field(None, description="Current API usage stats")


class UsageStats(BaseModel):
    """Schema for API usage statistics."""

    current_calls: int = Field(..., description="Calls made this month")
    monthly_limit: int = Field(..., description="Monthly call limit")
    remaining: int = Field(..., description="Remaining calls")
    percentage: float = Field(..., description="Percentage of limit used")
    month: str = Field(..., description="Current month (YYYY-MM)")
    days_remaining: int = Field(..., description="Days left in month")
    calls_per_day_remaining: int = Field(..., description="Suggested calls/day")
    status: str = Field(
        ...,
        description="Status: ok (<70%), warning (70-90%), critical (>90%)"
    )


# Forward references for Pydantic v2
NewsResponse.model_rebuild()
SourcesResponse.model_rebuild()
