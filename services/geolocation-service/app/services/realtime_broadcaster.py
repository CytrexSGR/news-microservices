"""Broadcast geo events to WebSocket clients."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Import manager lazily to avoid circular imports
_manager = None


def get_manager():
    """Get WebSocket connection manager."""
    global _manager
    if _manager is None:
        from app.api.websocket import manager
        _manager = manager
    return _manager


async def broadcast_new_article(
    article_id: str,
    iso_code: str,
    title: str,
    lat: float,
    lon: float,
    category: Optional[str] = None,
    impact_score: Optional[float] = None,
) -> None:
    """
    Broadcast new article location to WebSocket clients.

    Called by geo_consumer after processing an article.
    """
    manager = get_manager()

    data = {
        "article_id": article_id,
        "iso_code": iso_code,
        "title": title,
        "lat": lat,
        "lon": lon,
    }

    if category:
        data["category"] = category
    if impact_score is not None:
        data["impact_score"] = impact_score

    try:
        await manager.broadcast_article(data)
        logger.debug(f"Broadcasted article {article_id} to WebSocket clients")
    except Exception as e:
        logger.warning(f"Failed to broadcast article: {e}")


async def broadcast_stats_change(
    iso_code: str,
    article_count_24h: int,
    change: int,
) -> None:
    """
    Broadcast country stats update to WebSocket clients.

    Called after country stats are updated.
    """
    manager = get_manager()

    try:
        await manager.broadcast_stats_update(iso_code, {
            "article_count_24h": article_count_24h,
            "change": change,
        })
        logger.debug(f"Broadcasted stats change for {iso_code}")
    except Exception as e:
        logger.warning(f"Failed to broadcast stats change: {e}")
