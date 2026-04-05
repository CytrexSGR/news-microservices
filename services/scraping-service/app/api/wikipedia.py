"""
Wikipedia API Endpoints

REST API for Wikipedia data extraction using MediaWiki API.
Provides entity enrichment through structured Wikipedia data.

Issue P0-1: Authentication required for all endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.services.wikipedia_client import (
    WikipediaClient,
    WikipediaLanguage,
    WikipediaArticle,
    WikipediaSearchResult
)
from app.services.scraper import scraper
from app.core.auth import get_current_user, CurrentUser

router = APIRouter(prefix="/api/v1/wikipedia", tags=["wikipedia"])
logger = logging.getLogger(__name__)


# ===========================
# Request/Response Models
# ===========================

class SearchRequest(BaseModel):
    """Wikipedia search request"""
    query: str = Field(..., description="Search query (entity name)")
    language: WikipediaLanguage = Field(
        default=WikipediaLanguage.GERMAN,
        description="Wikipedia language (de, en)"
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")


class SearchResponse(BaseModel):
    """Wikipedia search response"""
    results: List[Dict[str, Any]]
    query: str
    count: int


class ArticleRequest(BaseModel):
    """Wikipedia article request"""
    title: str = Field(..., description="Article title (exact match)")
    language: WikipediaLanguage = Field(
        default=WikipediaLanguage.GERMAN,
        description="Wikipedia language (de, en)"
    )
    include_infobox: bool = Field(default=True, description="Extract infobox data")
    include_categories: bool = Field(default=True, description="Extract categories")
    include_links: bool = Field(default=True, description="Extract related links")


class ArticleResponse(BaseModel):
    """Wikipedia article response"""
    title: str
    extract: str
    url: str
    categories: List[str]
    infobox: Dict[str, Any]
    links: List[str]
    language: str
    page_id: int
    last_modified: Optional[str] = None


class RelationshipRequest(BaseModel):
    """Relationship extraction request"""
    title: str = Field(..., description="Article title (entity name)")
    language: WikipediaLanguage = Field(
        default=WikipediaLanguage.GERMAN,
        description="Wikipedia language (de, en)"
    )
    entity_type: Optional[str] = Field(
        default=None,
        description="Entity type hint (PERSON, ORGANIZATION, etc.)"
    )


class RelationshipResponse(BaseModel):
    """Relationship extraction response"""
    entity: str
    relationships: List[Dict[str, Any]]
    count: int


# ===========================
# API Endpoints
# ===========================

@router.post("/search", response_model=SearchResponse)
async def search_wikipedia(
    request: SearchRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Search Wikipedia articles by query.

    **Authentication Required:** Bearer token

    Returns a list of matching articles with snippets.
    Useful for finding the correct article title before extraction.

    Example:
        POST /api/v1/wikipedia/search
        Authorization: Bearer <token>
        {
            "query": "Elon Musk",
            "language": "de",
            "limit": 5
        }

        Response:
        {
            "results": [
                {
                    "title": "Elon Musk",
                    "page_id": 123456,
                    "snippet": "Elon Reeve Musk ist ein..."
                }
            ],
            "query": "Elon Musk",
            "count": 1
        }
    """
    try:
        # Create Wikipedia client
        client = WikipediaClient(http_client=scraper.http_client)

        # Search Wikipedia
        search_results = await client.search(
            query=request.query,
            language=request.language,
            limit=request.limit
        )

        # Convert to dict
        results = [
            {
                "title": result.title,
                "page_id": result.page_id,
                "snippet": result.snippet
            }
            for result in search_results
        ]

        logger.info(
            f"Wikipedia search: query='{request.query}', "
            f"language={request.language}, results={len(results)}"
        )

        return SearchResponse(
            results=results,
            query=request.query,
            count=len(results)
        )

    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Wikipedia search failed: {str(e)}"
        )


@router.post("/article", response_model=ArticleResponse)
async def get_wikipedia_article(
    request: ArticleRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get full Wikipedia article data.

    **Authentication Required:** Bearer token

    Extracts structured information from Wikipedia:
    - Article summary (plain text)
    - Infobox structured data (key-value pairs)
    - Categories
    - Related entity links

    Example:
        POST /api/v1/wikipedia/article
        Authorization: Bearer <token>
        {
            "title": "Tesla, Inc.",
            "language": "en",
            "include_infobox": true
        }

        Response:
        {
            "title": "Tesla, Inc.",
            "extract": "Tesla, Inc. is an American automotive...",
            "url": "https://en.wikipedia.org/wiki/Tesla,_Inc.",
            "infobox": {
                "Industry": "Automotive",
                "Founded": "July 1, 2003",
                "Founder": "Elon Musk, Martin Eberhard, ...",
                "Headquarters": "Austin, Texas, U.S."
            },
            "categories": ["Electric vehicle manufacturers", ...],
            "links": ["Elon Musk", "SpaceX", "Model 3", ...],
            "language": "en",
            "page_id": 2242799
        }
    """
    try:
        # Create Wikipedia client
        client = WikipediaClient(http_client=scraper.http_client)

        # Get article
        article = await client.get_article(
            title=request.title,
            language=request.language,
            include_infobox=request.include_infobox,
            include_categories=request.include_categories,
            include_links=request.include_links
        )

        if not article:
            raise HTTPException(
                status_code=404,
                detail=f"Wikipedia article not found: {request.title}"
            )

        logger.info(
            f"Wikipedia article extracted: title='{article.title}', "
            f"language={request.language}, "
            f"extract_length={len(article.extract)}"
        )

        return ArticleResponse(
            title=article.title,
            extract=article.extract,
            url=article.url,
            categories=article.categories,
            infobox=article.infobox,
            links=article.links,
            language=article.language,
            page_id=article.page_id,
            last_modified=article.last_modified
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wikipedia article extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Wikipedia article extraction failed: {str(e)}"
        )


@router.post("/relationships", response_model=RelationshipResponse)
async def extract_relationships(
    request: RelationshipRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Extract relationship candidates from Wikipedia article.

    **Authentication Required:** Bearer token

    Analyzes article text and infobox to identify potential relationships
    between entities. Returns relationship candidates with confidence scores.

    Useful for enriching Knowledge Graph with structured relationships
    extracted from Wikipedia.

    Example:
        POST /api/v1/wikipedia/relationships
        Authorization: Bearer <token>
        {
            "title": "Tesla, Inc.",
            "language": "en",
            "entity_type": "ORGANIZATION"
        }

        Response:
        {
            "entity": "Tesla, Inc.",
            "relationships": [
                {
                    "entity1": "Tesla, Inc.",
                    "entity2": "Elon Musk",
                    "relationship_type": "CEO_of",
                    "confidence": 0.95,
                    "evidence": "Wikipedia infobox: CEO=Elon Musk",
                    "source": "wikipedia_infobox"
                },
                {
                    "entity1": "Tesla, Inc.",
                    "entity2": "Austin, Texas",
                    "relationship_type": "located_in",
                    "confidence": 0.90,
                    "evidence": "Wikipedia infobox: Headquarters=Austin, Texas",
                    "source": "wikipedia_infobox"
                }
            ],
            "count": 2
        }
    """
    try:
        # Create Wikipedia client
        client = WikipediaClient(http_client=scraper.http_client)

        # Extract relationships
        relationships = await client.extract_relationships(
            title=request.title,
            language=request.language,
            entity_type=request.entity_type
        )

        logger.info(
            f"Wikipedia relationships extracted: entity='{request.title}', "
            f"count={len(relationships)}"
        )

        return RelationshipResponse(
            entity=request.title,
            relationships=relationships,
            count=len(relationships)
        )

    except Exception as e:
        logger.error(f"Wikipedia relationship extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Relationship extraction failed: {str(e)}"
        )
