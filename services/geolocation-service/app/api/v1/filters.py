"""Filter options endpoints."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.geo import RegionInfo

router = APIRouter(prefix="/geo/filters", tags=["filters"])


@router.get("/regions", response_model=List[RegionInfo])
async def get_regions(db: AsyncSession = Depends(get_db)):
    """Get available regions with country counts."""
    query = text("""
        SELECT
            region as id,
            region as name,
            COUNT(*) as country_count,
            array_agg(iso_code ORDER BY name) as country_codes
        FROM countries
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY region
    """)
    result = await db.execute(query)
    return [RegionInfo(**row._mapping) for row in result.fetchall()]


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get available V3 categories with article counts from geo-tagged articles."""
    query = text("""
        WITH geo_articles AS (
            SELECT DISTINCT al.article_id
            FROM article_locations al
        ),
        category_counts AS (
            SELECT
                aa.triage_results->>'category' as category,
                COUNT(*) as total_count,
                COUNT(*) FILTER (WHERE aa.created_at >= NOW() - INTERVAL '24 hours') as count_24h,
                COUNT(*) FILTER (WHERE aa.created_at >= NOW() - INTERVAL '7 days') as count_7d
            FROM article_analysis aa
            JOIN geo_articles ga ON aa.article_id = ga.article_id
            WHERE aa.triage_results->>'category' IS NOT NULL
            GROUP BY aa.triage_results->>'category'
        )
        SELECT
            category as id,
            category as name,
            total_count,
            count_24h,
            count_7d
        FROM category_counts
        ORDER BY total_count DESC
    """)
    result = await db.execute(query)

    # Map category IDs to display info
    category_icons = {
        "CONFLICT": "swords",
        "FINANCE": "chart-line",
        "POLITICS": "landmark",
        "HUMANITARIAN": "heart-handshake",
        "SECURITY": "shield",
        "TECHNOLOGY": "cpu",
        "HEALTH": "heart-pulse",
        "OTHER": "newspaper",
    }

    categories = []
    for row in result.fetchall():
        categories.append({
            "id": row.id,
            "name": row.name.title() if row.name else "Other",
            "icon": category_icons.get(row.id, "newspaper"),
            "total_count": row.total_count,
            "count_24h": row.count_24h,
            "count_7d": row.count_7d,
        })

    return categories
