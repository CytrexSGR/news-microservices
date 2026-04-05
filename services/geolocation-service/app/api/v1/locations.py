"""REST endpoints for country data."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.geo import CountryWithStats, CountryDetail

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/countries", response_model=List[CountryWithStats])
async def list_countries(
    region: Optional[str] = Query(None, description="Filter by region"),
    db: AsyncSession = Depends(get_db),
):
    """List all countries with article statistics."""
    query = text("""
        SELECT
            c.iso_code,
            c.name,
            c.name_de,
            c.region,
            COALESCE(s.article_count_24h, 0) as article_count_24h,
            COALESCE(s.article_count_7d, 0) as article_count_7d,
            ARRAY[c.centroid_lon, c.centroid_lat] as centroid
        FROM countries c
        LEFT JOIN country_stats s ON c.iso_code = s.country_code
        WHERE (CAST(:region AS TEXT) IS NULL OR c.region = :region)
        ORDER BY s.article_count_24h DESC NULLS LAST
    """)
    result = await db.execute(query, {"region": region})
    return [CountryWithStats(**row._mapping) for row in result.fetchall()]


@router.get("/countries/{iso_code}", response_model=CountryDetail)
async def get_country(
    iso_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get country details with statistics."""
    query = text("""
        SELECT
            c.iso_code, c.name, c.name_de, c.region, c.subregion,
            COALESCE(s.article_count_24h, 0) as article_count_24h,
            COALESCE(s.article_count_7d, 0) as article_count_7d,
            COALESCE(s.article_count_30d, 0) as article_count_30d,
            s.avg_impact_score, s.dominant_category, s.last_article_at,
            ARRAY[c.centroid_lon, c.centroid_lat] as centroid
        FROM countries c
        LEFT JOIN country_stats s ON c.iso_code = s.country_code
        WHERE c.iso_code = :iso_code
    """)
    result = await db.execute(query, {"iso_code": iso_code.upper()})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Country not found")
    return CountryDetail(**row._mapping)


@router.get("/countries/{iso_code}/articles")
async def get_country_articles(
    iso_code: str,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get articles for a specific country."""
    # First verify country exists
    country_check = await db.execute(
        text("SELECT 1 FROM countries WHERE iso_code = :iso_code"),
        {"iso_code": iso_code.upper()}
    )
    if not country_check.fetchone():
        raise HTTPException(status_code=404, detail="Country not found")

    # Get articles via article_locations join with feed_items
    query = text("""
        SELECT
            al.article_id as id,
            fi.title,
            fi.link,
            fi.source_type as source,
            fi.published_at,
            al.confidence,
            al.created_at as located_at
        FROM article_locations al
        JOIN feed_items fi ON al.article_id = fi.id
        WHERE al.country_code = :iso_code
        ORDER BY al.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(query, {
        "iso_code": iso_code.upper(),
        "limit": limit,
        "offset": offset,
    })

    articles = [dict(row._mapping) for row in result.fetchall()]

    # Get total count
    count_query = text("""
        SELECT COUNT(*) FROM article_locations WHERE country_code = :iso_code
    """)
    count_result = await db.execute(count_query, {"iso_code": iso_code.upper()})
    total = count_result.scalar()

    return {
        "articles": articles,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    }
