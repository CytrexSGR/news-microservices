"""
Narrative Analysis API Endpoints
Provides frame detection, bias analysis, and narrative clustering
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta

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

router = APIRouter(prefix="/api/v1/narrative", tags=["narrative"])


@router.get("/overview", response_model=NarrativeOverviewResponse)
async def get_narrative_overview(
    days: int = Query(7, ge=1, le=30, description="Days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get narrative overview statistics

    Returns:
        - Total frames and clusters
        - Frame type distribution
        - Bias distribution
        - Average bias score and sentiment
        - Top narratives
    """
    # Calculate date threshold
    since = datetime.utcnow() - timedelta(days=days)

    # Get total frames
    total_frames_query = select(func.count(NarrativeFrame.id)).where(
        NarrativeFrame.created_at >= since
    )
    result = await db.execute(total_frames_query)
    total_frames = result.scalar() or 0

    # Get total clusters
    total_clusters_query = select(func.count(NarrativeCluster.id)).where(
        NarrativeCluster.is_active == True
    )
    result = await db.execute(total_clusters_query)
    total_clusters = result.scalar() or 0

    # Frame type distribution
    frame_dist_query = (
        select(
            NarrativeFrame.frame_type,
            func.count(NarrativeFrame.id).label("count")
        )
        .where(NarrativeFrame.created_at >= since)
        .group_by(NarrativeFrame.frame_type)
    )
    result = await db.execute(frame_dist_query)
    frame_distribution = {row[0]: row[1] for row in result.all()}

    # Bias distribution
    bias_dist_query = (
        select(
            BiasAnalysis.bias_label,
            func.count(BiasAnalysis.id).label("count")
        )
        .where(BiasAnalysis.created_at >= since)
        .group_by(BiasAnalysis.bias_label)
    )
    result = await db.execute(bias_dist_query)
    bias_distribution = {row[0]: row[1] for row in result.all()}

    # Average bias score
    avg_bias_query = select(func.avg(BiasAnalysis.bias_score)).where(
        BiasAnalysis.created_at >= since
    )
    result = await db.execute(avg_bias_query)
    avg_bias_score = result.scalar() or 0.0

    # Average sentiment
    avg_sentiment_query = select(func.avg(BiasAnalysis.sentiment)).where(
        BiasAnalysis.created_at >= since
    )
    result = await db.execute(avg_sentiment_query)
    avg_sentiment = result.scalar() or 0.0

    # Top narratives (most recent, active clusters)
    top_narratives_query = (
        select(NarrativeCluster)
        .where(NarrativeCluster.is_active == True)
        .order_by(desc(NarrativeCluster.frame_count))
        .limit(10)
    )
    result = await db.execute(top_narratives_query)
    top_narratives = result.scalars().all()

    return NarrativeOverviewResponse(
        total_frames=total_frames,
        total_clusters=total_clusters,
        frame_distribution=frame_distribution,
        bias_distribution=bias_distribution,
        avg_bias_score=round(avg_bias_score, 3),
        avg_sentiment=round(avg_sentiment, 3),
        top_narratives=[NarrativeClusterResponse.model_validate(c) for c in top_narratives],
    )


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
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    frames = result.scalars().all()

    return FramesListResponse(
        frames=[NarrativeFrameResponse.model_validate(f) for f in frames],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("/frames", response_model=NarrativeFrameResponse, status_code=201)
async def create_narrative_frame(
    frame_data: NarrativeFrameCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new narrative frame

    Typically called by content analysis service when processing articles.
    """
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

    return NarrativeFrameResponse.model_validate(frame)


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
    query = select(NarrativeCluster).order_by(desc(NarrativeCluster.frame_count))

    if active_only:
        query = query.where(NarrativeCluster.is_active == True)
    if min_frame_count > 0:
        query = query.where(NarrativeCluster.frame_count >= min_frame_count)

    query = query.limit(limit)

    result = await db.execute(query)
    clusters = result.scalars().all()

    return [NarrativeClusterResponse.model_validate(c) for c in clusters]


@router.post("/clusters/update", status_code=202)
async def update_narrative_clusters(db: AsyncSession = Depends(get_db)):
    """
    Update narrative clusters from recent frames

    Analyzes frames from last 7 days and creates/updates clusters.
    This is typically run as a periodic task.
    """
    result = await narrative_clustering_service.update_narrative_clusters(db)
    return result


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


@router.post("/analyze/text")
async def analyze_text(
    text: str,
    source: Optional[str] = None,
):
    """
    Analyze text for narrative frames and bias (without persisting)

    Useful for testing or one-off analysis.

    Returns:
        - Detected frames with confidence scores
        - Bias analysis (score, label, sentiment, perspective)
    """
    if not text or len(text) < 50:
        raise HTTPException(status_code=400, detail="Text must be at least 50 characters")

    # Detect frames
    frames = frame_detection_service.detect_frames(text)

    # Analyze bias
    bias = bias_analysis_service.analyze_bias(text, source)

    return {
        "frames": frames,
        "bias": bias,
        "text_length": len(text),
        "analyzed_at": datetime.utcnow().isoformat(),
    }
