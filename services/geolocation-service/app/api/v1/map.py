"""Map data endpoints for frontend visualization."""
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.geo import MapMarker, HeatmapPoint

router = APIRouter(prefix="/geo/map", tags=["map"])


@router.get("/countries")
async def get_map_geojson(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get GeoJSON FeatureCollection for map rendering."""
    if not from_date:
        from_date = datetime.utcnow() - timedelta(days=7)
    elif from_date.tzinfo is not None:
        from_date = from_date.replace(tzinfo=None)
    if not to_date:
        to_date = datetime.utcnow()
    elif to_date.tzinfo is not None:
        to_date = to_date.replace(tzinfo=None)

    query = text("""
        SELECT
            c.iso_code,
            c.name,
            c.name_de,
            c.region,
            COALESCE(s.article_count_24h, 0) as article_count,
            c.boundary as geometry
        FROM countries c
        LEFT JOIN country_stats s ON c.iso_code = s.country_code
        WHERE c.boundary IS NOT NULL
    """)
    result = await db.execute(query)

    features = []
    for row in result.fetchall():
        if row.geometry:  # Only include countries with boundaries
            features.append({
                "type": "Feature",
                "properties": {
                    "iso_code": row.iso_code,
                    "name": row.name,
                    "name_de": row.name_de,
                    "region": row.region,
                    "article_count": row.article_count,
                },
                "geometry": row.geometry,
            })

    return {"type": "FeatureCollection", "features": features}


@router.get("/markers", response_model=List[MapMarker])
async def get_markers(
    from_date: Optional[datetime] = Query(None),
    time_range: Optional[str] = Query(None, description="Preset: today, 7d, 30d"),
    region: Optional[str] = Query(None),
    categories: Optional[str] = Query(None, description="Comma-separated category IDs"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get article markers for map visualization with filtering."""
    # Handle time range presets
    if time_range:
        now = datetime.utcnow()
        if time_range == "today":
            from_date = now - timedelta(days=1)
        elif time_range == "7d":
            from_date = now - timedelta(days=7)
        elif time_range == "30d":
            from_date = now - timedelta(days=30)
    elif not from_date:
        from_date = datetime.utcnow() - timedelta(days=1)
    elif from_date.tzinfo is not None:
        from_date = from_date.replace(tzinfo=None)

    # Parse categories
    category_list = None
    has_category_filter = False
    if categories:
        category_list = [c.strip().upper() for c in categories.split(",") if c.strip()]
        has_category_filter = len(category_list) > 0

    # Build query - use different query based on whether categories are filtered
    if has_category_filter:
        query = text("""
            SELECT
                al.id::text as id,
                al.article_id,
                al.country_code,
                c.name as country_name,
                c.centroid_lat as lat,
                c.centroid_lon as lon,
                COALESCE(fi.title, '') as title,
                aa.triage_results->>'category' as category,
                (aa.tier1_results->'scores'->>'impact_score')::float as impact_score,
                al.created_at
            FROM article_locations al
            JOIN countries c ON al.country_code = c.iso_code
            LEFT JOIN feed_items fi ON al.article_id = fi.id
            LEFT JOIN article_analysis aa ON al.article_id = aa.article_id
            WHERE al.created_at >= :from_date
            AND c.centroid_lon IS NOT NULL
            AND (CAST(:region AS TEXT) IS NULL OR c.region = :region)
            AND aa.triage_results->>'category' = ANY(:category_array)
            ORDER BY al.created_at DESC
            LIMIT :limit
        """)
        result = await db.execute(query, {
            "from_date": from_date,
            "region": region,
            "category_array": category_list,
            "limit": limit,
        })
    else:
        query = text("""
            SELECT
                al.id::text as id,
                al.article_id,
                al.country_code,
                c.name as country_name,
                c.centroid_lat as lat,
                c.centroid_lon as lon,
                COALESCE(fi.title, '') as title,
                aa.triage_results->>'category' as category,
                (aa.tier1_results->'scores'->>'impact_score')::float as impact_score,
                al.created_at
            FROM article_locations al
            JOIN countries c ON al.country_code = c.iso_code
            LEFT JOIN feed_items fi ON al.article_id = fi.id
            LEFT JOIN article_analysis aa ON al.article_id = aa.article_id
            WHERE al.created_at >= :from_date
            AND c.centroid_lon IS NOT NULL
            AND (CAST(:region AS TEXT) IS NULL OR c.region = :region)
            ORDER BY al.created_at DESC
            LIMIT :limit
        """)
        result = await db.execute(query, {
            "from_date": from_date,
            "region": region,
            "limit": limit,
        })

    markers = []
    for row in result.fetchall():
        markers.append(MapMarker(
            id=row.id,
            lat=row.lat,
            lon=row.lon,
            country_code=row.country_code,
            article_id=row.article_id,
            title=row.title or "",
            category=row.category,
            impact_score=row.impact_score,
        ))
    return markers


@router.get("/heatmap", response_model=List[HeatmapPoint])
async def get_heatmap(
    from_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get heatmap intensity data per country."""
    if not from_date:
        from_date = datetime.utcnow() - timedelta(days=7)
    elif from_date.tzinfo is not None:
        from_date = from_date.replace(tzinfo=None)

    query = text("""
        WITH counts AS (
            SELECT
                country_code,
                COUNT(*) as cnt
            FROM article_locations
            WHERE created_at >= :from_date
            GROUP BY country_code
        ),
        max_count AS (
            SELECT COALESCE(MAX(cnt), 1) as max_cnt FROM counts
        )
        SELECT
            c.iso_code,
            c.centroid_lat as lat,
            c.centroid_lon as lon,
            COALESCE(counts.cnt, 0) as article_count,
            COALESCE(counts.cnt::float / max_count.max_cnt, 0) as intensity
        FROM countries c
        LEFT JOIN counts ON c.iso_code = counts.country_code
        CROSS JOIN max_count
        WHERE c.centroid_lon IS NOT NULL
        AND COALESCE(counts.cnt, 0) > 0
        ORDER BY article_count DESC
    """)
    result = await db.execute(query, {"from_date": from_date})

    return [HeatmapPoint(**row._mapping) for row in result.fetchall()]
