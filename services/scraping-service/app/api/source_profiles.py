"""
Source Profile API Endpoints

Provides management interface for Source Registry:
- List source profiles
- Get/Update individual profiles
- View statistics
- Seed known sources
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.services.source_registry import get_source_registry
from app.models.source_profile import (
    SourceProfile,
    SourceProfileUpdate,
    ScrapeStatusEnum,
    ScrapeMethodEnum,
    PaywallTypeEnum
)

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("/", response_model=List[SourceProfile])
async def list_source_profiles(
    status: Optional[ScrapeStatusEnum] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    List all tracked source profiles.

    Returns domains with their scraping configuration and performance metrics.
    """
    registry = get_source_registry()
    profiles = registry.list_profiles(status=status, limit=limit, offset=offset)
    return profiles


@router.get("/statistics")
async def get_source_statistics():
    """
    Get overall source registry statistics.

    Returns:
    - Total sources tracked
    - Breakdown by status (working, degraded, blocked, unknown)
    - Average success rate
    """
    registry = get_source_registry()
    return registry.get_statistics()


@router.get("/lookup")
async def lookup_source(url: str = Query(..., description="URL to lookup source for")):
    """
    Lookup source profile for a URL.

    Returns the source profile for the domain extracted from the URL.
    Creates a new profile with defaults if none exists.
    """
    registry = get_source_registry()
    profile = registry.get_or_create_profile(url)
    return profile


@router.get("/config")
async def get_scrape_config(url: str = Query(..., description="URL to get config for")):
    """
    Get complete scraping configuration for a URL.

    Returns the recommended scraping method, fallbacks, and settings
    based on the source profile.
    """
    registry = get_source_registry()
    config = registry.get_scrape_config(url)
    return {
        "url": url,
        "config": config
    }


@router.get("/{domain}", response_model=SourceProfile)
async def get_source_profile(domain: str):
    """
    Get source profile by domain.

    Args:
        domain: Domain name (e.g., 'spiegel.de')
    """
    registry = get_source_registry()
    profile = registry.get_profile(f"https://{domain}/")

    if not profile:
        raise HTTPException(status_code=404, detail=f"Source profile for {domain} not found")

    return profile


@router.patch("/{domain}", response_model=SourceProfile)
async def update_source_profile(domain: str, update: SourceProfileUpdate):
    """
    Update source profile settings.

    Allows manual configuration of:
    - Scraping method
    - Fallback methods
    - Paywall type
    - Rate limits
    - Anti-detection settings
    """
    registry = get_source_registry()
    profile = registry.update_profile(domain, update)

    if not profile:
        raise HTTPException(status_code=404, detail=f"Source profile for {domain} not found")

    return profile


@router.post("/seed")
async def seed_known_sources():
    """
    Seed the registry with known German news sources.

    Pre-configures profiles for major German news sites with
    optimal scraping settings.
    """
    registry = get_source_registry()

    # Known German news sources with pre-configured settings
    GERMAN_NEWS_SOURCES = [
        # Major news sites - newspaper4k works well
        {
            "domain": "spiegel.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.METERED,
            "notes": "Metered paywall, soft limit"
        },
        {
            "domain": "faz.net",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.METERED,
            "notes": "Metered paywall, some articles free"
        },
        {
            "domain": "sueddeutsche.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.METERED,
            "notes": "Metered paywall"
        },
        {
            "domain": "zeit.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.METERED,
            "notes": "Metered paywall, Z+ articles paywalled"
        },
        {
            "domain": "welt.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA, ScrapeMethodEnum.PLAYWRIGHT],
            "paywall": PaywallTypeEnum.METERED,
            "notes": "WELTplus articles paywalled"
        },
        # Free news sources
        {
            "domain": "tagesschau.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.NONE,
            "notes": "Public broadcaster, no paywall"
        },
        {
            "domain": "heise.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.NONE,
            "notes": "Tech news, mostly free"
        },
        {
            "domain": "golem.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.SOFT,
            "notes": "Tech news, some Plus articles"
        },
        # Regional/tabloids
        {
            "domain": "bild.de",
            "method": ScrapeMethodEnum.PLAYWRIGHT,
            "fallbacks": [ScrapeMethodEnum.NEWSPAPER4K],
            "paywall": PaywallTypeEnum.SOFT,
            "stealth": True,
            "notes": "Heavy JS, BILDplus paywalled"
        },
        {
            "domain": "focus.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.SOFT,
            "notes": "Mixed content types"
        },
        # Financial
        {
            "domain": "handelsblatt.com",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.HARD,
            "notes": "Hard paywall for premium content"
        },
        {
            "domain": "manager-magazin.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.METERED,
            "notes": "Business news, metered"
        },
        # Tech/Startup
        {
            "domain": "t3n.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.NONE,
            "notes": "Startup/Tech news"
        },
        {
            "domain": "gruenderszene.de",
            "method": ScrapeMethodEnum.NEWSPAPER4K,
            "fallbacks": [ScrapeMethodEnum.TRAFILATURA],
            "paywall": PaywallTypeEnum.NONE,
            "notes": "Startup news"
        },
    ]

    seeded_count = 0
    for source in GERMAN_NEWS_SOURCES:
        # Create profile
        profile = registry.get_or_create_profile(f"https://{source['domain']}/")

        # Update with known settings
        update = SourceProfileUpdate(
            scrape_method=source["method"],
            fallback_methods=source.get("fallbacks", []),
            paywall_type=source["paywall"],
            requires_stealth=source.get("stealth", False),
            notes=source.get("notes")
        )
        registry.update_profile(source["domain"], update)
        seeded_count += 1

    return {
        "message": f"Seeded {seeded_count} German news source profiles",
        "sources": [s["domain"] for s in GERMAN_NEWS_SOURCES]
    }


@router.delete("/cache")
async def clear_cache():
    """
    Clear the in-memory source profile cache.

    Forces re-fetch from database on next access.
    """
    registry = get_source_registry()
    registry.clear_cache()
    return {"message": "Source profile cache cleared"}
