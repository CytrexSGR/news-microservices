"""
API endpoints for the Feed Service

Modular API structure:
- feeds.py: Core feed CRUD operations
- items.py: Feed item/article endpoints
- operations.py: Fetch operations (trigger, bulk-fetch, reset-error)
- health.py: Health & quality endpoints
- scraping.py: Scraping management
- research.py: Research article & analysis trigger endpoints
- sources.py: Unified source management (sources + source_feeds)
- duplicates.py: Duplicate review management (HITL)
- review.py: HITL publication review queue (Epic 2.3)
- routes/assessment.py: Source assessment endpoints
- routes/admiralty_codes.py: Admiralty code system
"""

from .feeds import router as feeds_router
from .items import router as items_router
from .operations import router as operations_router
from .health import router as health_router
from .scraping import router as scraping_router
from .research import router as research_router
from .sources import sources_router, source_feeds_router
from .duplicates import router as duplicates_router
from .review import router as review_router
from .routes.assessment import router as assessment_router

__all__ = [
    "feeds_router",
    "items_router",
    "operations_router",
    "health_router",
    "scraping_router",
    "research_router",
    "sources_router",
    "source_feeds_router",
    "duplicates_router",
    "review_router",
    "assessment_router",
]
