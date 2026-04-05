"""Security View API endpoints for military/intelligence perspective on geo-map.

Provides:
- GET /geo/security/overview      - Global security dashboard
- GET /geo/security/events        - Paginated security events
- GET /geo/security/countries     - Country threat profiles
- GET /geo/security/country/{iso} - Single country detail
- GET /geo/security/relations     - Geopolitical relations network
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List

import httpx
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.security import (
    SecurityOverview,
    SecurityEvent,
    SecurityEventList,
    CountryThreatSummary,
    CountryThreatDetail,
    ThreatLevel,
    SecurityCategory,
    GeopoliticalRelation,
    RelationNetwork,
    SecurityMarker,
    AnomalyData,
    AnomalyResponse,
    EntityNode,
    EntityEdge,
    EntityGraphResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geo/security", tags=["security"])


def get_threat_level(priority_score: int) -> ThreatLevel:
    """Convert priority score to threat level."""
    if priority_score >= 9:
        return ThreatLevel.CRITICAL
    elif priority_score >= 7:
        return ThreatLevel.HIGH
    elif priority_score >= 5:
        return ThreatLevel.MEDIUM
    else:
        return ThreatLevel.LOW


# =============================================================================
# Overview Endpoint
# =============================================================================

@router.get("/overview", response_model=SecurityOverview)
async def get_security_overview(
    days: int = Query(7, ge=1, le=90, description="Days to look back"),
    min_priority: int = Query(5, ge=0, le=10, description="Minimum priority score"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get global security overview for dashboard.

    Returns aggregated threat statistics, hotspots, and critical events.
    """
    from_date = datetime.utcnow() - timedelta(days=days)
    to_date = datetime.utcnow()

    # Main aggregation query
    query = text("""
        WITH security_events AS (
            SELECT
                aa.article_id,
                aa.triage_results->>'category' as category,
                (aa.triage_results->>'priority_score')::int as priority_score,
                al.country_code,
                c.region,
                fi.published_at
            FROM article_analysis aa
            JOIN article_locations al ON aa.article_id = al.article_id
            JOIN countries c ON al.country_code = c.iso_code
            JOIN feed_items fi ON aa.article_id = fi.id
            WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
              AND (aa.triage_results->>'priority_score')::int >= :min_priority
              AND fi.published_at >= :from_date
        )
        SELECT
            COUNT(*) as total_events,
            COUNT(*) FILTER (WHERE priority_score >= 9) as critical_count,
            COUNT(*) FILTER (WHERE priority_score >= 7 AND priority_score < 9) as high_count,
            COUNT(*) FILTER (WHERE priority_score >= 5 AND priority_score < 7) as medium_count,
            jsonb_object_agg(
                COALESCE(category, 'OTHER'),
                category_count
            ) FILTER (WHERE category IS NOT NULL) as by_category,
            jsonb_object_agg(
                COALESCE(region, 'Unknown'),
                region_count
            ) FILTER (WHERE region IS NOT NULL) as by_region
        FROM security_events,
        LATERAL (SELECT category, COUNT(*) as category_count FROM security_events GROUP BY category) cat,
        LATERAL (SELECT region, COUNT(*) as region_count FROM security_events GROUP BY region) reg
    """)

    # Simplified aggregation
    agg_query = text("""
        SELECT
            COUNT(*) as total_events,
            COUNT(*) FILTER (WHERE (aa.triage_results->>'priority_score')::int >= 9) as critical_count,
            COUNT(*) FILTER (WHERE (aa.triage_results->>'priority_score')::int >= 7 AND (aa.triage_results->>'priority_score')::int < 9) as high_count,
            COUNT(*) FILTER (WHERE (aa.triage_results->>'priority_score')::int >= 5 AND (aa.triage_results->>'priority_score')::int < 7) as medium_count
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
          AND (aa.triage_results->>'priority_score')::int >= :min_priority
          AND fi.published_at >= :from_date
    """)
    result = await db.execute(agg_query, {"from_date": from_date, "min_priority": min_priority})
    row = result.fetchone()

    # By category
    cat_query = text("""
        SELECT
            aa.triage_results->>'category' as category,
            COUNT(*) as count
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
          AND (aa.triage_results->>'priority_score')::int >= :min_priority
          AND fi.published_at >= :from_date
        GROUP BY aa.triage_results->>'category'
    """)
    cat_result = await db.execute(cat_query, {"from_date": from_date, "min_priority": min_priority})
    by_category = {r.category: r.count for r in cat_result.fetchall()}

    # By region
    region_query = text("""
        SELECT
            c.region,
            COUNT(*) as count
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN countries c ON al.country_code = c.iso_code
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
          AND (aa.triage_results->>'priority_score')::int >= :min_priority
          AND fi.published_at >= :from_date
        GROUP BY c.region
    """)
    region_result = await db.execute(region_query, {"from_date": from_date, "min_priority": min_priority})
    by_region = {r.region or "Unknown": r.count for r in region_result.fetchall()}

    # Hotspots (top countries)
    hotspot_query = text("""
        SELECT
            al.country_code,
            c.name as country_name,
            c.centroid_lat as lat,
            c.centroid_lon as lon,
            c.region,
            COUNT(*) as total_events,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'CONFLICT') as conflict_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'SECURITY') as security_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'HUMANITARIAN') as humanitarian_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'POLITICS') as politics_count,
            MAX((aa.triage_results->>'priority_score')::int) as max_priority_score,
            AVG((aa.triage_results->>'priority_score')::int)::numeric(3,1) as avg_priority_score,
            MAX(fi.published_at) as last_event_at
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN countries c ON al.country_code = c.iso_code
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
          AND (aa.triage_results->>'priority_score')::int >= :min_priority
          AND fi.published_at >= :from_date
        GROUP BY al.country_code, c.name, c.centroid_lat, c.centroid_lon, c.region
        ORDER BY max_priority_score DESC, total_events DESC
        LIMIT 10
    """)
    hotspot_result = await db.execute(hotspot_query, {"from_date": from_date, "min_priority": min_priority})

    hotspots = []
    for r in hotspot_result.fetchall():
        hotspots.append(CountryThreatSummary(
            country_code=r.country_code,
            country_name=r.country_name,
            lat=r.lat or 0.0,
            lon=r.lon or 0.0,
            region=r.region,
            total_events=r.total_events,
            conflict_count=r.conflict_count,
            security_count=r.security_count,
            humanitarian_count=r.humanitarian_count,
            politics_count=r.politics_count,
            max_priority_score=r.max_priority_score,
            avg_priority_score=float(r.avg_priority_score or 0),
            max_threat_level=get_threat_level(r.max_priority_score),
            last_event_at=r.last_event_at,
        ))

    # Critical events
    critical_query = text("""
        SELECT
            al.id::text as id,
            aa.article_id,
            fi.title,
            al.country_code,
            c.name as country_name,
            c.centroid_lat as lat,
            c.centroid_lon as lon,
            aa.triage_results->>'category' as category,
            (aa.triage_results->>'priority_score')::int as priority_score,
            (aa.tier1_results->'scores'->>'impact_score')::float as impact_score,
            (aa.tier1_results->'scores'->>'urgency_score')::float as urgency_score,
            (aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'conflict_severity')::float as conflict_severity,
            (aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'regional_stability_risk')::float as regional_stability_risk,
            aa.tier2_results->'NARRATIVE_ANALYST'->'narrative_frame_metrics'->>'dominant_frame' as dominant_frame,
            fi.published_at,
            aa.created_at
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN countries c ON al.country_code = c.iso_code
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN')
          AND (aa.triage_results->>'priority_score')::int >= 8
          AND fi.published_at >= :from_date
        ORDER BY priority_score DESC, fi.published_at DESC
        LIMIT 10
    """)
    critical_result = await db.execute(critical_query, {"from_date": from_date})

    critical_events = []
    for r in critical_result.fetchall():
        critical_events.append(SecurityEvent(
            id=r.id,
            article_id=r.article_id,
            title=r.title or "",
            country_code=r.country_code,
            country_name=r.country_name,
            lat=r.lat or 0.0,
            lon=r.lon or 0.0,
            category=r.category or "OTHER",
            threat_level=get_threat_level(r.priority_score),
            priority_score=r.priority_score,
            impact_score=r.impact_score,
            urgency_score=r.urgency_score,
            conflict_severity=r.conflict_severity,
            regional_stability_risk=r.regional_stability_risk,
            dominant_frame=r.dominant_frame,
            published_at=r.published_at,
            created_at=r.created_at,
        ))

    return SecurityOverview(
        from_date=from_date,
        to_date=to_date,
        total_events=row.total_events or 0,
        critical_count=row.critical_count or 0,
        high_count=row.high_count or 0,
        medium_count=row.medium_count or 0,
        by_category=by_category,
        by_region=by_region,
        hotspots=hotspots,
        critical_events=critical_events,
    )


# =============================================================================
# Events Endpoint
# =============================================================================

@router.get("/events", response_model=SecurityEventList)
async def get_security_events(
    days: int = Query(7, ge=1, le=90),
    min_priority: int = Query(5, ge=0, le=10),
    category: Optional[str] = Query(None, description="Filter by category: CONFLICT, SECURITY, HUMANITARIAN, POLITICS"),
    country: Optional[str] = Query(None, description="Filter by country ISO code"),
    region: Optional[str] = Query(None, description="Filter by region"),
    threat_level: Optional[str] = Query(None, description="Filter: critical, high, medium, low"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated security events with filters.

    Returns individual security-relevant articles with full analysis data.
    """
    from_date = datetime.utcnow() - timedelta(days=days)
    offset = (page - 1) * per_page

    # Build dynamic WHERE clause
    where_clauses = [
        "aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')",
        "(aa.triage_results->>'priority_score')::int >= :min_priority",
        "fi.published_at >= :from_date",
    ]
    params = {"from_date": from_date, "min_priority": min_priority, "limit": per_page, "offset": offset}

    if category:
        where_clauses.append("aa.triage_results->>'category' = :category")
        params["category"] = category.upper()

    if country:
        where_clauses.append("al.country_code = :country")
        params["country"] = country.upper()

    if region:
        where_clauses.append("c.region = :region")
        params["region"] = region

    if threat_level:
        level_map = {
            "critical": "(aa.triage_results->>'priority_score')::int >= 9",
            "high": "(aa.triage_results->>'priority_score')::int >= 7 AND (aa.triage_results->>'priority_score')::int < 9",
            "medium": "(aa.triage_results->>'priority_score')::int >= 5 AND (aa.triage_results->>'priority_score')::int < 7",
            "low": "(aa.triage_results->>'priority_score')::int < 5",
        }
        if threat_level in level_map:
            where_clauses.append(level_map[threat_level])

    where_sql = " AND ".join(where_clauses)

    # Count query
    count_query = text(f"""
        SELECT COUNT(*) as total
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN countries c ON al.country_code = c.iso_code
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE {where_sql}
    """)
    count_result = await db.execute(count_query, params)
    total = count_result.scalar() or 0

    # Data query
    data_query = text(f"""
        SELECT
            al.id::text as id,
            aa.article_id,
            fi.title,
            al.country_code,
            c.name as country_name,
            c.centroid_lat as lat,
            c.centroid_lon as lon,
            aa.triage_results->>'category' as category,
            (aa.triage_results->>'priority_score')::int as priority_score,
            (aa.tier1_results->'scores'->>'impact_score')::float as impact_score,
            (aa.tier1_results->'scores'->>'urgency_score')::float as urgency_score,
            (aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'conflict_severity')::float as conflict_severity,
            (aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'diplomatic_impact')::float as diplomatic_impact,
            (aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'regional_stability_risk')::float as regional_stability_risk,
            aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'countries_involved' as countries_involved_json,
            aa.tier2_results->'NARRATIVE_ANALYST'->'narrative_frame_metrics'->>'dominant_frame' as dominant_frame,
            (aa.tier2_results->'NARRATIVE_ANALYST'->'narrative_frame_metrics'->>'narrative_tension')::float as narrative_tension,
            aa.tier2_results->'NARRATIVE_ANALYST'->'narrative_frame_metrics'->'propaganda_indicators' as propaganda_json,
            aa.tier1_results->'entities' as entities_json,
            fi.published_at,
            aa.created_at
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN countries c ON al.country_code = c.iso_code
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE {where_sql}
        ORDER BY priority_score DESC, fi.published_at DESC
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(data_query, params)

    events = []
    for r in result.fetchall():
        # Parse JSON fields safely
        countries_involved = []
        if r.countries_involved_json:
            try:
                countries_involved = r.countries_involved_json if isinstance(r.countries_involved_json, list) else []
            except (TypeError, ValueError):
                pass

        propaganda_indicators = []
        propaganda_detected = False
        if r.propaganda_json:
            try:
                propaganda_indicators = r.propaganda_json if isinstance(r.propaganda_json, list) else []
                propaganda_detected = len(propaganda_indicators) > 0
            except (TypeError, ValueError):
                pass

        entities = []
        if r.entities_json:
            try:
                entities = r.entities_json if isinstance(r.entities_json, list) else []
            except (TypeError, ValueError):
                pass

        events.append(SecurityEvent(
            id=r.id,
            article_id=r.article_id,
            title=r.title or "",
            country_code=r.country_code,
            country_name=r.country_name,
            lat=r.lat or 0.0,
            lon=r.lon or 0.0,
            category=r.category or "OTHER",
            threat_level=get_threat_level(r.priority_score),
            priority_score=r.priority_score,
            impact_score=r.impact_score,
            urgency_score=r.urgency_score,
            conflict_severity=r.conflict_severity,
            diplomatic_impact=r.diplomatic_impact,
            regional_stability_risk=r.regional_stability_risk,
            countries_involved=countries_involved,
            dominant_frame=r.dominant_frame,
            narrative_tension=r.narrative_tension,
            propaganda_detected=propaganda_detected,
            entities=entities,
            published_at=r.published_at,
            created_at=r.created_at,
        ))

    filters_applied = {
        "days": days,
        "min_priority": min_priority,
        "category": category,
        "country": country,
        "region": region,
        "threat_level": threat_level,
    }

    return SecurityEventList(
        events=events,
        total=total,
        page=page,
        per_page=per_page,
        filters_applied={k: v for k, v in filters_applied.items() if v is not None},
    )


# =============================================================================
# Countries Endpoint
# =============================================================================

@router.get("/countries", response_model=List[CountryThreatSummary])
async def get_country_threats(
    days: int = Query(7, ge=1, le=90),
    min_priority: int = Query(5, ge=0, le=10),
    region: Optional[str] = Query(None),
    min_events: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated threat data per country.

    Returns countries with security events, sorted by threat level.
    """
    from_date = datetime.utcnow() - timedelta(days=days)

    region_filter = "AND c.region = :region" if region else ""

    query = text(f"""
        SELECT
            al.country_code,
            c.name as country_name,
            c.centroid_lat as lat,
            c.centroid_lon as lon,
            c.region,
            COUNT(*) as total_events,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'CONFLICT') as conflict_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'SECURITY') as security_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'HUMANITARIAN') as humanitarian_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'POLITICS') as politics_count,
            MAX((aa.triage_results->>'priority_score')::int) as max_priority_score,
            AVG((aa.triage_results->>'priority_score')::int)::numeric(3,1) as avg_priority_score,
            AVG((aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'conflict_severity')::float)::numeric(3,1) as avg_conflict_severity,
            AVG((aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'regional_stability_risk')::float)::numeric(3,1) as avg_regional_stability_risk,
            AVG((aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'diplomatic_impact')::float)::numeric(3,1) as avg_diplomatic_impact,
            MAX(fi.published_at) as last_event_at
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN countries c ON al.country_code = c.iso_code
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
          AND (aa.triage_results->>'priority_score')::int >= :min_priority
          AND fi.published_at >= :from_date
          {region_filter}
        GROUP BY al.country_code, c.name, c.centroid_lat, c.centroid_lon, c.region
        HAVING COUNT(*) >= :min_events
        ORDER BY max_priority_score DESC, total_events DESC
        LIMIT :limit
    """)

    params = {
        "from_date": from_date,
        "min_priority": min_priority,
        "min_events": min_events,
        "limit": limit,
    }
    if region:
        params["region"] = region

    result = await db.execute(query, params)

    countries = []
    for r in result.fetchall():
        countries.append(CountryThreatSummary(
            country_code=r.country_code,
            country_name=r.country_name,
            lat=r.lat or 0.0,
            lon=r.lon or 0.0,
            region=r.region,
            total_events=r.total_events,
            conflict_count=r.conflict_count,
            security_count=r.security_count,
            humanitarian_count=r.humanitarian_count,
            politics_count=r.politics_count,
            max_priority_score=r.max_priority_score,
            avg_priority_score=float(r.avg_priority_score or 0),
            max_threat_level=get_threat_level(r.max_priority_score),
            avg_conflict_severity=float(r.avg_conflict_severity) if r.avg_conflict_severity else None,
            avg_regional_stability_risk=float(r.avg_regional_stability_risk) if r.avg_regional_stability_risk else None,
            avg_diplomatic_impact=float(r.avg_diplomatic_impact) if r.avg_diplomatic_impact else None,
            last_event_at=r.last_event_at,
        ))

    return countries


# =============================================================================
# Single Country Detail
# =============================================================================

@router.get("/country/{iso_code}", response_model=CountryThreatDetail)
async def get_country_detail(
    iso_code: str,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed threat profile for a single country.

    Includes recent events, key entities, and geopolitical relations.
    """
    from_date = datetime.utcnow() - timedelta(days=days)
    iso_code = iso_code.upper()

    # Check country exists
    country_query = text("""
        SELECT iso_code, name, centroid_lat, centroid_lon, region
        FROM countries WHERE iso_code = :iso_code
    """)
    country_result = await db.execute(country_query, {"iso_code": iso_code})
    country = country_result.fetchone()

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {iso_code} not found")

    # Aggregation
    agg_query = text("""
        SELECT
            COUNT(*) as total_events,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'CONFLICT') as conflict_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'SECURITY') as security_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'HUMANITARIAN') as humanitarian_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'POLITICS') as politics_count,
            MAX((aa.triage_results->>'priority_score')::int) as max_priority_score,
            AVG((aa.triage_results->>'priority_score')::int)::numeric(3,1) as avg_priority_score,
            AVG((aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'conflict_severity')::float)::numeric(3,1) as avg_conflict_severity,
            AVG((aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'regional_stability_risk')::float)::numeric(3,1) as avg_regional_stability_risk,
            MAX(fi.published_at) as last_event_at
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE al.country_code = :iso_code
          AND aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
          AND fi.published_at >= :from_date
    """)
    agg_result = await db.execute(agg_query, {"iso_code": iso_code, "from_date": from_date})
    agg = agg_result.fetchone()

    # Recent events
    events_query = text("""
        SELECT
            al.id::text as id,
            aa.article_id,
            fi.title,
            al.country_code,
            :country_name as country_name,
            :lat as lat,
            :lon as lon,
            aa.triage_results->>'category' as category,
            (aa.triage_results->>'priority_score')::int as priority_score,
            fi.published_at,
            aa.created_at
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE al.country_code = :iso_code
          AND aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
          AND fi.published_at >= :from_date
        ORDER BY priority_score DESC, fi.published_at DESC
        LIMIT 20
    """)
    events_result = await db.execute(events_query, {
        "iso_code": iso_code,
        "from_date": from_date,
        "country_name": country.name,
        "lat": country.centroid_lat or 0.0,
        "lon": country.centroid_lon or 0.0,
    })

    recent_events = []
    for r in events_result.fetchall():
        recent_events.append(SecurityEvent(
            id=r.id,
            article_id=r.article_id,
            title=r.title or "",
            country_code=r.country_code,
            country_name=r.country_name,
            lat=r.lat,
            lon=r.lon,
            category=r.category or "OTHER",
            threat_level=get_threat_level(r.priority_score),
            priority_score=r.priority_score,
            published_at=r.published_at,
            created_at=r.created_at,
        ))

    return CountryThreatDetail(
        country_code=country.iso_code,
        country_name=country.name,
        lat=country.centroid_lat or 0.0,
        lon=country.centroid_lon or 0.0,
        region=country.region,
        total_events=agg.total_events or 0,
        conflict_count=agg.conflict_count or 0,
        security_count=agg.security_count or 0,
        humanitarian_count=agg.humanitarian_count or 0,
        politics_count=agg.politics_count or 0,
        max_priority_score=agg.max_priority_score or 0,
        avg_priority_score=float(agg.avg_priority_score or 0),
        max_threat_level=get_threat_level(agg.max_priority_score or 0),
        avg_conflict_severity=float(agg.avg_conflict_severity) if agg.avg_conflict_severity else None,
        avg_regional_stability_risk=float(agg.avg_regional_stability_risk) if agg.avg_regional_stability_risk else None,
        last_event_at=agg.last_event_at,
        recent_events=recent_events,
    )


# =============================================================================
# Security Markers (for map)
# =============================================================================

@router.get("/markers", response_model=List[SecurityMarker])
async def get_security_markers(
    days: int = Query(7, ge=1, le=90),
    min_priority: int = Query(6, ge=0, le=10),
    categories: Optional[str] = Query(None, description="Comma-separated: CONFLICT,SECURITY,HUMANITARIAN"),
    region: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Get security markers for map visualization.

    Returns simplified marker data optimized for map rendering.
    """
    from_date = datetime.utcnow() - timedelta(days=days)

    # Build filters
    category_filter = ""
    params = {"from_date": from_date, "min_priority": min_priority, "limit": limit}
    if categories:
        cat_list = [c.strip().upper() for c in categories.split(",") if c.strip()]
        if cat_list:
            category_filter = "AND aa.triage_results->>'category' = ANY(:cat_list)"
            params["cat_list"] = cat_list
    else:
        category_filter = "AND aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN')"

    region_filter = "AND c.region = :region" if region else ""

    query = text(f"""
        SELECT
            al.id::text as id,
            c.centroid_lat as lat,
            c.centroid_lon as lon,
            al.country_code,
            aa.triage_results->>'category' as category,
            (aa.triage_results->>'priority_score')::int as priority_score,
            fi.title,
            (aa.tier2_results->'GEOPOLITICAL_ANALYST'->'geopolitical_metrics'->'metrics'->>'conflict_severity')::float as conflict_severity,
            (aa.tier1_results->'scores'->>'impact_score')::float as impact_score,
            aa.tier2_results->'NARRATIVE_ANALYST'->'narrative_frame_metrics'->>'dominant_frame' as dominant_frame,
            jsonb_array_length(COALESCE(aa.tier2_results->'NARRATIVE_ANALYST'->'narrative_frame_metrics'->'propaganda_indicators', '[]'::jsonb)) > 0 as propaganda_detected,
            fi.published_at as first_seen,
            aa.created_at as last_update
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN countries c ON al.country_code = c.iso_code
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE (aa.triage_results->>'priority_score')::int >= :min_priority
          AND fi.published_at >= :from_date
          AND c.centroid_lat IS NOT NULL
          {category_filter}
          {region_filter}
        ORDER BY priority_score DESC, fi.published_at DESC
        LIMIT :limit
    """)

    if region:
        params["region"] = region

    result = await db.execute(query, params)

    markers = []
    for r in result.fetchall():
        markers.append(SecurityMarker(
            id=r.id,
            lat=r.lat,
            lon=r.lon,
            country_code=r.country_code,
            threat_level=get_threat_level(r.priority_score),
            category=r.category or "OTHER",
            title=r.title or "",
            priority_score=r.priority_score,
            conflict_severity=r.conflict_severity,
            impact_score=r.impact_score,
            dominant_frame=r.dominant_frame,
            propaganda_detected=r.propaganda_detected or False,
            first_seen=r.first_seen,
            last_update=r.last_update,
        ))

    return markers


# =============================================================================
# Anomaly Detection Endpoint
# =============================================================================

@router.get("/anomalies", response_model=AnomalyResponse)
async def get_anomalies(
    period: str = Query("24h", description="Current period: 24h, 7d"),
    baseline_days: int = Query(30, ge=7, le=90, description="Baseline comparison period"),
    min_deviation: float = Query(2.0, ge=1.0, le=5.0, description="Min stddev for anomaly"),
    min_events: int = Query(5, ge=1, description="Min events to consider"),
    db: AsyncSession = Depends(get_db),
):
    """
    Detect anomalies by comparing current activity to historical baseline.

    Returns regions/countries with unusual activity spikes.
    """
    # Calculate period ranges
    if period == "24h":
        current_start = datetime.utcnow() - timedelta(hours=24)
    else:
        current_start = datetime.utcnow() - timedelta(days=7)

    baseline_start = datetime.utcnow() - timedelta(days=baseline_days)
    baseline_end = current_start  # Baseline ends where current period starts

    # Get current period counts by region
    current_query = text("""
        SELECT
            c.region,
            COUNT(*) as event_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'CONFLICT') as conflict_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'SECURITY') as security_count,
            COUNT(*) FILTER (WHERE aa.triage_results->>'category' = 'HUMANITARIAN') as humanitarian_count
        FROM article_analysis aa
        JOIN article_locations al ON aa.article_id = al.article_id
        JOIN countries c ON al.country_code = c.iso_code
        JOIN feed_items fi ON aa.article_id = fi.id
        WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
          AND (aa.triage_results->>'priority_score')::int >= 5
          AND fi.published_at >= :current_start
        GROUP BY c.region
    """)

    current_result = await db.execute(current_query, {"current_start": current_start})
    current_by_region = {r.region: r for r in current_result.fetchall() if r.region}

    # Get baseline stats by region (daily averages)
    baseline_query = text("""
        SELECT
            region,
            AVG(daily_count) as avg_count,
            COALESCE(STDDEV(daily_count), 1) as stddev_count
        FROM (
            SELECT
                c.region,
                DATE(fi.published_at) as day,
                COUNT(*) as daily_count
            FROM article_analysis aa
            JOIN article_locations al ON aa.article_id = al.article_id
            JOIN countries c ON al.country_code = c.iso_code
            JOIN feed_items fi ON aa.article_id = fi.id
            WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
              AND (aa.triage_results->>'priority_score')::int >= 5
              AND fi.published_at >= :baseline_start
              AND fi.published_at < :baseline_end
            GROUP BY c.region, DATE(fi.published_at)
        ) daily_counts
        GROUP BY region
    """)

    baseline_result = await db.execute(baseline_query, {
        "baseline_start": baseline_start,
        "baseline_end": baseline_end,
    })
    baseline_by_region = {r.region: r for r in baseline_result.fetchall() if r.region}

    # Calculate anomalies
    anomalies = []
    escalating_regions = []

    # Normalize current count to daily equivalent
    period_days = 1 if period == "24h" else 7

    for region, current in current_by_region.items():
        if current.event_count < min_events:
            continue

        baseline = baseline_by_region.get(region)
        if not baseline or not baseline.avg_count:
            continue

        daily_equivalent = current.event_count / period_days
        avg = float(baseline.avg_count)
        stddev = float(baseline.stddev_count or 1)  # Avoid div by zero

        deviation = (daily_equivalent - avg) / stddev if stddev > 0 else 0
        is_anomaly = deviation >= min_deviation

        if deviation >= 3:
            trend = "spike"
            escalating_regions.append(region)
        elif deviation >= 2:
            trend = "elevated"
        elif deviation >= -1:
            trend = "normal"
        else:
            trend = "low"

        anomalies.append(AnomalyData(
            entity=region,
            entity_type="region",
            current_count=current.event_count,
            baseline_avg=round(avg, 1),
            baseline_stddev=round(stddev, 1),
            deviation_factor=round(deviation, 2),
            is_anomaly=is_anomaly,
            trend=trend,
            category_breakdown={
                "CONFLICT": current.conflict_count,
                "SECURITY": current.security_count,
                "HUMANITARIAN": current.humanitarian_count,
            },
        ))

    # Sort by deviation (highest first)
    anomalies.sort(key=lambda x: x.deviation_factor, reverse=True)

    return AnomalyResponse(
        period=period,
        baseline_days=baseline_days,
        anomalies=anomalies,
        escalating_regions=escalating_regions,
    )


# =============================================================================
# Entity Relationship Graph Endpoint
# =============================================================================

@router.get("/entity-graph", response_model=EntityGraphResponse)
async def get_entity_graph(
    entity: Optional[str] = Query(None, description="Center entity name"),
    country: Optional[str] = Query(None, description="Filter by country"),
    limit: int = Query(50, ge=10, le=200),
    min_mentions: int = Query(2, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Get entity relationship graph for security-relevant entities.

    Proxies to knowledge-graph-service and enriches with threat data.
    """
    # First, get high-priority entities from recent security events
    params = {"min_mentions": min_mentions, "limit": limit}

    if country:
        entity_query = text("""
            WITH recent_entities AS (
                SELECT
                    e->>'name' as name,
                    e->>'type' as type,
                    COUNT(DISTINCT aa.article_id) as mention_count,
                    ARRAY_AGG(DISTINCT al.country_code) as countries,
                    AVG((aa.triage_results->>'priority_score')::int) as avg_priority
                FROM article_analysis aa
                JOIN article_locations al ON aa.article_id = al.article_id
                JOIN feed_items fi ON aa.article_id = fi.id
                CROSS JOIN LATERAL jsonb_array_elements(aa.tier1_results->'entities') as e
                WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
                  AND (aa.triage_results->>'priority_score')::int >= 6
                  AND fi.published_at >= NOW() - INTERVAL '7 days'
                  AND al.country_code = :country
                  AND e->>'type' IN ('PERSON', 'ORG', 'GPE', 'NORP', 'FAC', 'EVENT')
                GROUP BY e->>'name', e->>'type'
                HAVING COUNT(DISTINCT aa.article_id) >= :min_mentions
            )
            SELECT * FROM recent_entities
            ORDER BY avg_priority DESC, mention_count DESC
            LIMIT :limit
        """)
        params["country"] = country.upper()
    else:
        entity_query = text("""
            WITH recent_entities AS (
                SELECT
                    e->>'name' as name,
                    e->>'type' as type,
                    COUNT(DISTINCT aa.article_id) as mention_count,
                    ARRAY_AGG(DISTINCT al.country_code) as countries,
                    AVG((aa.triage_results->>'priority_score')::int) as avg_priority
                FROM article_analysis aa
                JOIN article_locations al ON aa.article_id = al.article_id
                JOIN feed_items fi ON aa.article_id = fi.id
                CROSS JOIN LATERAL jsonb_array_elements(aa.tier1_results->'entities') as e
                WHERE aa.triage_results->>'category' IN ('CONFLICT', 'SECURITY', 'HUMANITARIAN', 'POLITICS')
                  AND (aa.triage_results->>'priority_score')::int >= 6
                  AND fi.published_at >= NOW() - INTERVAL '7 days'
                  AND e->>'type' IN ('PERSON', 'ORG', 'GPE', 'NORP', 'FAC', 'EVENT')
                GROUP BY e->>'name', e->>'type'
                HAVING COUNT(DISTINCT aa.article_id) >= :min_mentions
            )
            SELECT * FROM recent_entities
            ORDER BY avg_priority DESC, mention_count DESC
            LIMIT :limit
        """)

    result = await db.execute(entity_query, params)
    entities = result.fetchall()

    # Build nodes
    nodes = []
    entity_names = set()
    for e in entities:
        entity_names.add(e.name)
        nodes.append(EntityNode(
            id=e.name.lower().replace(' ', '_'),
            name=e.name,
            type=e.type or "UNKNOWN",
            threat_score=float(e.avg_priority) if e.avg_priority else None,
            mention_count=e.mention_count,
            countries=e.countries or [],
        ))

    # Try to get relationships from knowledge-graph-service
    edges = []
    if entity_names:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                for entity_name in list(entity_names)[:20]:  # Limit API calls
                    response = await client.get(
                        f"http://knowledge-graph-service:8000/api/v1/graph/entity/{entity_name}/connections",
                        params={"limit": 20}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for edge in data.get("edges", []):
                            if edge["target"] in entity_names or edge["source"] in entity_names:
                                edges.append(EntityEdge(
                                    source=edge["source"].lower().replace(' ', '_'),
                                    target=edge["target"].lower().replace(' ', '_'),
                                    relationship=edge["relationship_type"],
                                    weight=edge.get("confidence", 1.0),
                                    evidence=edge.get("evidence"),
                                ))
        except Exception as e:
            logger.warning(f"Failed to fetch from knowledge-graph: {e}")

    # Deduplicate edges
    unique_edges = {}
    for edge in edges:
        key = f"{edge.source}-{edge.target}-{edge.relationship}"
        if key not in unique_edges:
            unique_edges[key] = edge

    return EntityGraphResponse(
        nodes=nodes,
        edges=list(unique_edges.values()),
        total_nodes=len(nodes),
        total_edges=len(unique_edges),
    )
