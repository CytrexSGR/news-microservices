"""
Direct Scraping API Endpoint

Provides synchronous scraping without going through the queue.
Useful for:
- MCP tools (Claude Desktop)
- Ad-hoc scraping requests
- Testing

Note: For high-volume scraping, use the priority queue endpoints instead.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging

from app.services.scraper import scraper, ScrapeStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scrape", tags=["scrape"])


class ScrapeRequest(BaseModel):
    """Request to scrape a URL directly"""
    url: str
    method: Optional[str] = None  # auto, newspaper4k, playwright, stealth
    extract_links: bool = False


class ScrapeResponse(BaseModel):
    """Response from direct scraping"""
    url: str
    status: str
    content: Optional[str] = None
    word_count: int = 0
    method_used: Optional[str] = None
    extracted_title: Optional[str] = None
    extracted_authors: Optional[List[str]] = None
    extracted_publish_date: Optional[str] = None
    extracted_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    extracted_links: Optional[List[Dict[str, Any]]] = None


@router.post("", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape a URL directly and return content.

    This is a synchronous operation - the response waits until scraping completes.
    For high-volume or background scraping, use /api/v1/queue/enqueue instead.

    Args:
        url: The URL to scrape
        method: Scraping method (auto, newspaper4k, playwright, stealth)
                If not specified, auto-selects based on source profile.
    """
    logger.info(f"Direct scrape request for: {request.url}")

    try:
        # Perform the scrape
        result = await scraper.scrape(request.url, extract_links=request.extract_links)

        # Format response
        return ScrapeResponse(
            url=request.url,
            status=result.status.value,
            content=result.content,
            word_count=result.word_count,
            method_used=result.method_used,
            extracted_title=result.extracted_title,
            extracted_authors=result.extracted_authors,
            extracted_publish_date=(
                result.extracted_publish_date.isoformat()
                if result.extracted_publish_date else None
            ),
            extracted_metadata=result.extracted_metadata,
            error_message=result.error_message,
            extracted_links=result.extracted_links
        )

    except Exception as e:
        logger.error(f"Scraping failed for {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@router.get("/test")
async def test_scrape():
    """Test endpoint to verify scraping service is ready"""
    return {
        "status": "ready",
        "message": "Direct scraping endpoint is operational",
        "usage": "POST /api/v1/scrape with {\"url\": \"https://example.com\"}"
    }
