"""Publish geo.article.located events to RabbitMQ for the geospatial-service."""
import json
import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

import aio_pika
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stats_aggregator import get_country_centroid

logger = logging.getLogger(__name__)


async def publish_article_located(
    channel: aio_pika.Channel,
    db: AsyncSession,
    article_id: UUID,
    mapped_countries: List[str],
) -> None:
    """
    Fetch article title + country centroids, then publish geo.article.located event.
    """
    if not channel or not mapped_countries:
        return

    # Fetch article title
    title = "News Event"
    try:
        result = await db.execute(
            text("SELECT title FROM feed_items WHERE id = :aid LIMIT 1"),
            {"aid": str(article_id)},
        )
        row = result.fetchone()
        if row and row.title:
            title = row.title
    except Exception as e:
        logger.warning(f"Could not fetch title for {article_id}: {e}")

    # Build locations with centroids
    locations = []
    for iso_code in mapped_countries:
        centroid = await get_country_centroid(db, iso_code)
        if centroid:
            lat, lon = centroid
            locations.append({
                "iso_code": iso_code,
                "lat": lat,
                "lon": lon,
                "name": iso_code,
            })

    if not locations:
        logger.debug(f"No centroids found for {article_id}, skipping publish")
        return

    event = {
        "article_id": str(article_id),
        "title": title,
        "locations": locations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        exchange = await channel.get_exchange("news.events")
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(event).encode(),
                content_type="application/json",
            ),
            routing_key="geo.article.located",
        )
        logger.info(f"Published geo.article.located for {article_id} ({len(locations)} locations)")
    except Exception as e:
        logger.error(f"Failed to publish geo.article.located for {article_id}: {e}")
