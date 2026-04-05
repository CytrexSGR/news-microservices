"""
Narrative Analysis API Endpoints - OPTIMIZED VERSION
Provides frame detection, bias analysis, and narrative clustering with caching
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from app.database import get_db
from app.models.narrative_frame import NarrativeFrame
from app.models.narrative_cluster import NarrativeCluster
from app.models.bias_analysis import BiasAnalysis
from app.schemas.narrative import (
    NarrativeFrameCreate,
    NarrativeFrameResponse,
    BiasAnalysisResponse,
    NarrativeClusterResponse,
    NarrativeOverviewResponse,
    FramesListResponse,
    BiasComparisonResponse,
)
from app.services.frame_detection import frame_detection_service
from app.services.bias_analysis import bias_analysis_service
from app.services.narrative_clustering import narrative_clustering_service
from app.cache import get_cache_manager
from app.errors import validate_text_length, handle_analysis_error, async_retry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/narrative", tags=["narrative"])


@router.get("/overview", response_model=NarrativeOverviewResponse)
@async_retry(max_retries=2, delay=0.5)
async def get_narrative_overview(
    days: int = Query(7, ge=1, le=30, description="Days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get narrative overview statistics (CACHED)

    Returns:
        - Total frames and clusters
        - Frame type distribution
        - Bias distribution
        - Average bias score and sentiment
        - Top narratives

    Performance: ~300ms without cache, ~5ms with cache
    """
    # Check cache
    cache = get_cache_manager()
    if cache:
        cache_key = f"days={days}"
        cached = await cache.get_overview(cache_key)
        if cached:
            logger.debug(f"Overview cache hit for days={days}")
            return NarrativeOverviewResponse(**cached)

    try:
        # Calculate date threshold
        since = datetime.utcnow() - timedelta(days=days)

        # Execute queries sequentially to avoid session race conditions
        # Note: asyncio.gather on same session causes IllegalStateChangeError

        # Total frames
        total_frames_result = await db.execute(
            select(func.count(NarrativeFrame.id)).where(NarrativeFrame.created_at >= since)
        )
        total_frames = total_frames_result.scalar() or 0

        # Total clusters
        total_clusters_result = await db.execute(
            select(func.count(NarrativeCluster.id)).where(NarrativeCluster.is_active == True)
        )
        total_clusters = total_clusters_result.scalar() or 0

        # Frame distribution
        frame_dist_result = await db.execute(
            select(
                NarrativeFrame.frame_type,
                func.count(NarrativeFrame.id).label("count")
            )
            .where(NarrativeFrame.created_at >= since)
            .group_by(NarrativeFrame.frame_type)
        )
        frame_distribution = {row[0]: row[1] for row in frame_dist_result.all()}

        # Bias distribution - from article_analysis BIAS_SCORER (tier2_results)
        # Note: No date filter - shows historical aggregate across all analyzed articles
        bias_dist_result = await db.execute(
            text("""
                SELECT
                    tier2_results->'BIAS_SCORER'->'political_bias'->>'political_direction' as bias_direction,
                    COUNT(*) as count
                FROM article_analysis
                WHERE tier2_results->'BIAS_SCORER'->'political_bias'->>'political_direction' IS NOT NULL
                GROUP BY tier2_results->'BIAS_SCORER'->'political_bias'->>'political_direction'
                ORDER BY count DESC
            """)
        )
        bias_distribution = {row[0]: row[1] for row in bias_dist_result.all()}

        # Get average bias score - from article_analysis BIAS_SCORER
        avg_bias_result = await db.execute(
            text("""
                SELECT AVG((tier2_results->'BIAS_SCORER'->'political_bias'->>'bias_score')::float)
                FROM article_analysis
                WHERE tier2_results->'BIAS_SCORER'->'political_bias'->>'bias_score' IS NOT NULL
            """)
        )
        avg_bias_score = avg_bias_result.scalar() or 0.0

        # Get average sentiment - from article_analysis SENTIMENT_ANALYZER
        # Sentiment is calculated as (bullish_ratio - bearish_ratio) to get a -1 to +1 scale
        avg_sentiment_result = await db.execute(
            text("""
                SELECT AVG(
                    (tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bullish_ratio')::float -
                    (tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bearish_ratio')::float
                )
                FROM article_analysis
                WHERE tier2_results->'SENTIMENT_ANALYZER'->'sentiment_metrics'->'metrics'->>'bullish_ratio' IS NOT NULL
            """)
        )
        avg_sentiment = avg_sentiment_result.scalar() or 0.0

        # Top narratives
        top_narratives_result = await db.execute(
            select(NarrativeCluster)
            .where(NarrativeCluster.is_active == True)
            .order_by(desc(NarrativeCluster.frame_count))
            .limit(10)
        )
        top_narratives = top_narratives_result.scalars().all()

        result = NarrativeOverviewResponse(
            total_frames=total_frames,
            total_clusters=total_clusters,
            frame_distribution=frame_distribution,
            bias_distribution=bias_distribution,
            avg_bias_score=round(avg_bias_score, 3),
            avg_sentiment=round(avg_sentiment, 3),
            top_narratives=[NarrativeClusterResponse.model_validate(c) for c in top_narratives],
        )

        # Cache result
        if cache:
            await cache.set_overview(cache_key, result.model_dump())

        return result

    except Exception as e:
        raise handle_analysis_error(e, "narrative overview")


@router.get("/frames", response_model=FramesListResponse)
async def list_narrative_frames(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    frame_type: Optional[str] = Query(None, description="Filter by frame type"),
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence"),
    db: AsyncSession = Depends(get_db),
):
    """
    List narrative frames with pagination and filters

    Available frame types:
        - victim: Entity portrayed as victim/suffering
        - hero: Entity portrayed as hero/savior
        - threat: Entity portrayed as threat/danger
        - solution: Entity/action portrayed as solution
        - conflict: Conflict/opposition framing
        - economic: Economic impact framing
    """
    try:
        # Build query
        query = select(NarrativeFrame).order_by(desc(NarrativeFrame.created_at))

        # Apply filters
        if frame_type:
            query = query.where(NarrativeFrame.frame_type == frame_type)
        if event_id:
            query = query.where(NarrativeFrame.event_id == event_id)
        if min_confidence > 0:
            query = query.where(NarrativeFrame.confidence >= min_confidence)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())

        # Apply pagination
        offset = (page - 1) * per_page
        paginated_query = query.offset(offset).limit(per_page)

        # Execute sequentially to avoid session race conditions
        # Note: asyncio.gather on same session causes IllegalStateChangeError
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        frames_result = await db.execute(paginated_query)
        frames = frames_result.scalars().all()

        return FramesListResponse(
            frames=[NarrativeFrameResponse.model_validate(f) for f in frames],
            total=total,
            page=page,
            per_page=per_page,
        )

    except Exception as e:
        raise handle_analysis_error(e, "list frames")


@router.post("/frames", response_model=NarrativeFrameResponse, status_code=201)
@async_retry(max_retries=2, delay=0.5)
async def create_narrative_frame(
    frame_data: NarrativeFrameCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new narrative frame

    Typically called by content analysis service when processing articles.
    """
    try:
        frame = NarrativeFrame(
            event_id=frame_data.event_id,
            frame_type=frame_data.frame_type,
            confidence=frame_data.confidence,
            text_excerpt=frame_data.text_excerpt,
            entities=frame_data.entities,
            frame_metadata=frame_data.frame_metadata,
        )

        db.add(frame)
        await db.flush()
        await db.refresh(frame)

        # Invalidate overview cache since we added new data
        cache = get_cache_manager()
        if cache:
            await cache.invalidate_pattern("narrative:overview:*")

        return NarrativeFrameResponse.model_validate(frame)

    except Exception as e:
        raise handle_analysis_error(e, "create frame", 500)


@router.get("/clusters", response_model=List[NarrativeClusterResponse])
async def list_narrative_clusters(
    active_only: bool = Query(True, description="Only return active clusters"),
    min_frame_count: int = Query(0, ge=0, description="Minimum frame count"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """
    List narrative clusters

    Clusters group similar narrative frames by type and entity overlap.
    """
    try:
        query = select(NarrativeCluster).order_by(desc(NarrativeCluster.frame_count))

        if active_only:
            query = query.where(NarrativeCluster.is_active == True)
        if min_frame_count > 0:
            query = query.where(NarrativeCluster.frame_count >= min_frame_count)

        query = query.limit(limit)

        result = await db.execute(query)
        clusters = result.scalars().all()

        return [NarrativeClusterResponse.model_validate(c) for c in clusters]

    except Exception as e:
        raise handle_analysis_error(e, "list clusters")


@router.post("/clusters/update", status_code=202)
@async_retry(max_retries=2, delay=1.0)
async def update_narrative_clusters(db: AsyncSession = Depends(get_db)):
    """
    Update narrative clusters from recent frames

    Analyzes frames from last 7 days and creates/updates clusters.
    This is typically run as a periodic task.
    """
    try:
        result = await narrative_clustering_service.update_narrative_clusters(db)

        # Invalidate cache since clusters changed
        cache = get_cache_manager()
        if cache:
            await cache.invalidate_pattern("narrative:overview:*")

        return result

    except Exception as e:
        raise handle_analysis_error(e, "update clusters")


@router.get("/bias", response_model=BiasComparisonResponse)
async def get_bias_comparison(
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    days: int = Query(7, ge=1, le=30, description="Days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get bias comparison across sources

    Returns:
        - Source count
        - Spectrum distribution (left, center-left, center, center-right, right)
        - Average bias score and sentiment
        - Individual source analyses
    """
    try:
        since = datetime.utcnow() - timedelta(days=days)

        # Build query
        query = select(BiasAnalysis).where(BiasAnalysis.created_at >= since)

        if event_id:
            query = query.where(BiasAnalysis.event_id == event_id)

        # Execute query
        result = await db.execute(query)
        analyses = result.scalars().all()

        if not analyses:
            return BiasComparisonResponse(
                source_count=0,
                spectrum_distribution={
                    "left": 0,
                    "center-left": 0,
                    "center": 0,
                    "center-right": 0,
                    "right": 0,
                },
                avg_bias_score=0.0,
                avg_sentiment=0.0,
                sources=[],
            )

        # Calculate spectrum distribution
        spectrum_distribution = {
            "left": 0,
            "center-left": 0,
            "center": 0,
            "center-right": 0,
            "right": 0,
        }

        for analysis in analyses:
            if analysis.bias_label in spectrum_distribution:
                spectrum_distribution[analysis.bias_label] += 1

        # Calculate averages
        avg_bias_score = sum(a.bias_score for a in analyses) / len(analyses)
        avg_sentiment = sum(a.sentiment for a in analyses) / len(analyses)

        return BiasComparisonResponse(
            source_count=len(analyses),
            spectrum_distribution=spectrum_distribution,
            avg_bias_score=round(avg_bias_score, 3),
            avg_sentiment=round(avg_sentiment, 3),
            sources=[BiasAnalysisResponse.model_validate(a) for a in analyses],
        )

    except Exception as e:
        raise handle_analysis_error(e, "bias comparison")


@router.post("/analyze/text")
async def analyze_text(
    text: str,
    source: Optional[str] = None,
):
    """
    Analyze text for narrative frames and bias (CACHED, without persisting)

    Useful for testing or one-off analysis.

    Returns:
        - Detected frames with confidence scores
        - Bias analysis (score, label, sentiment, perspective)

    Performance: ~150ms without cache, ~3ms with cache
    """
    # Validate text
    validate_text_length(text, min_length=50, max_length=50000)

    try:
        # Check cache for both frame and bias analysis
        cache = get_cache_manager()
        frames = None
        bias = None

        if cache:
            frames_cached = await cache.get_frame_detection(text)
            bias_cached = await cache.get_bias_analysis(text, source)

            if frames_cached and bias_cached:
                logger.debug("Full cache hit for analyze_text")
                return {
                    "frames": frames_cached,
                    "bias": bias_cached,
                    "text_length": len(text),
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "from_cache": True,
                }

            frames = frames_cached
            bias = bias_cached

        # Run missing analyses in parallel
        tasks = []
        if frames is None:
            tasks.append(asyncio.to_thread(frame_detection_service.detect_frames, text))
        if bias is None:
            tasks.append(asyncio.to_thread(bias_analysis_service.analyze_bias, text, source))

        if tasks:
            results = await asyncio.gather(*tasks)
            if frames is None:
                frames = results[0]
                if cache:
                    await cache.set_frame_detection(text, frames)
            if bias is None:
                bias = results[-1]
                if cache:
                    await cache.set_bias_analysis(text, source, bias)

        return {
            "frames": frames,
            "bias": bias,
            "text_length": len(text),
            "analyzed_at": datetime.utcnow().isoformat(),
            "from_cache": False,
        }

    except Exception as e:
        raise handle_analysis_error(e, "text analysis")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics

    Returns cache hit rate, total cached items, etc.
    Useful for monitoring cache performance.
    """
    cache = get_cache_manager()
    if not cache:
        return {
            "cache_enabled": False,
            "message": "Cache is disabled"
        }

    try:
        stats = await cache.get_stats()
        return {
            "cache_enabled": True,
            **stats
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "cache_enabled": True,
            "error": str(e)
        }


@router.post("/cache/clear", status_code=202)
async def clear_cache(pattern: Optional[str] = None):
    """
    Clear cache entries

    Args:
        pattern: Optional pattern to match (e.g., "narrative:frame:*")
                 If not provided, clears all narrative cache entries
    """
    cache = get_cache_manager()
    if not cache:
        return {
            "success": False,
            "message": "Cache is disabled"
        }

    try:
        if pattern:
            await cache.invalidate_pattern(pattern)
        else:
            await cache.invalidate_pattern("narrative:*")

        return {
            "success": True,
            "message": f"Cache cleared for pattern: {pattern or 'narrative:*'}"
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
