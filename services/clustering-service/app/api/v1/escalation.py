"""Escalation API endpoints.

Provides endpoints for accessing aggregated escalation data, domain scores,
market regime correlation, and active alerts for the Intelligence Interpretation Layer.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.cluster import ArticleCluster
from app.models.escalation import FMPNewsCorrelation
from app.schemas.escalation import (
    ClusterEscalationDetailResponse,
    CorrelationAlertResponse,
    DomainEscalationResponse,
    EscalationSummaryResponse,
    RegimeStateResponse,
    SignalDetailResponse,
)
from app.services.fmp_correlation_service import FMPCorrelationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/escalation", tags=["escalation"])


def _create_default_domain(domain: str) -> DomainEscalationResponse:
    """Create a default domain response with neutral values.

    Args:
        domain: Domain name (geopolitical, military, economic)

    Returns:
        DomainEscalationResponse with neutral defaults
    """
    return DomainEscalationResponse(
        domain=domain,
        level=3,
        score=Decimal("0.500"),
        confidence=0.0,
    )


def _aggregate_domain(
    clusters: List[ArticleCluster],
    domain_attr: str,
) -> DomainEscalationResponse:
    """Aggregate domain scores from clusters.

    Args:
        clusters: List of ArticleCluster objects with escalation data
        domain_attr: Attribute name (e.g., 'escalation_geopolitical')

    Returns:
        Aggregated DomainEscalationResponse
    """
    domain_name = domain_attr.replace("escalation_", "")

    scores = [
        float(getattr(c, domain_attr) or 0)
        for c in clusters
        if getattr(c, domain_attr) is not None
    ]

    if not scores:
        return _create_default_domain(domain_name)

    avg_score = sum(scores) / len(scores)
    # Convert score (0-1) to level (1-5): level = round(score * 4) + 1
    level = max(1, min(5, round(avg_score * 4) + 1))

    return DomainEscalationResponse(
        domain=domain_name,
        level=level,
        score=Decimal(str(round(avg_score, 3))),
        # Confidence scales with sample size, max 1.0 at 10+ samples
        confidence=min(1.0, len(scores) / 10),
    )


@router.get("/summary", response_model=EscalationSummaryResponse)
async def get_escalation_summary(
    hours: int = Query(24, ge=1, le=168, description="Hours to include in analysis"),
    db: AsyncSession = Depends(get_db),
) -> EscalationSummaryResponse:
    """Get aggregated escalation summary across all recent clusters.

    Returns domain-level escalation scores, combined metrics,
    current market regime, and active correlation alerts.

    Args:
        hours: Time window for analysis (1-168 hours, default 24)
        db: Database session

    Returns:
        EscalationSummaryResponse with aggregated escalation data
    """
    # Get clusters with escalation data from the last N hours
    cutoff = datetime.now() - timedelta(hours=hours)

    stmt = (
        select(ArticleCluster)
        .where(ArticleCluster.created_at >= cutoff)
        .where(ArticleCluster.escalation_combined.isnot(None))
    )
    result = await db.execute(stmt)
    clusters = list(result.scalars().all())

    if not clusters:
        # Return defaults when no escalation data
        return EscalationSummaryResponse(
            geopolitical=_create_default_domain("geopolitical"),
            military=_create_default_domain("military"),
            economic=_create_default_domain("economic"),
            combined_level=3,
            combined_score=Decimal("0.500"),
            market_regime=None,
            correlation_alerts=[],
            cluster_count=0,
            calculated_at=datetime.now(),
        )

    # Aggregate domain scores
    geo = _aggregate_domain(clusters, "escalation_geopolitical")
    mil = _aggregate_domain(clusters, "escalation_military")
    eco = _aggregate_domain(clusters, "escalation_economic")

    # Combined metrics
    combined_level = max(geo.level, mil.level, eco.level)
    combined_score = (geo.score + mil.score + eco.score) / 3

    # Fetch market regime
    fmp_service = FMPCorrelationService(session=db)
    regime_state = await fmp_service.get_current_regime()

    market_regime = None
    if regime_state:
        market_regime = RegimeStateResponse(
            regime=regime_state.regime,
            confidence=regime_state.confidence,
            vix_level=regime_state.vix_level,
            fear_greed_index=regime_state.fear_greed_index,
            timestamp=regime_state.timestamp,
        )

    # Get active correlation alerts
    alerts = await fmp_service.get_active_alerts(limit=5)
    alert_responses = [
        CorrelationAlertResponse(
            id=a.id,
            correlation_type=a.correlation_type,
            fmp_regime=a.fmp_regime,
            escalation_level=a.escalation_level or 3,
            confidence=Decimal(str(a.confidence)) if a.confidence else Decimal("0.5"),
            reasoning=(
                a.extra_metadata.get("reasoning") if a.extra_metadata else None
            ),
            detected_at=a.detected_at,
            expires_at=a.expires_at,
            related_cluster_count=len(a.related_clusters or []),
        )
        for a in alerts
    ]

    return EscalationSummaryResponse(
        geopolitical=geo,
        military=mil,
        economic=eco,
        combined_level=combined_level,
        combined_score=combined_score.quantize(Decimal("0.001")),
        market_regime=market_regime,
        correlation_alerts=alert_responses,
        cluster_count=len(clusters),
        calculated_at=datetime.now(),
    )


@router.get("/clusters/{cluster_id}", response_model=ClusterEscalationDetailResponse)
async def get_cluster_escalation_detail(
    cluster_id: UUID,
    recalculate: bool = Query(False, description="Force recalculation of escalation"),
    db: AsyncSession = Depends(get_db),
) -> ClusterEscalationDetailResponse:
    """Get detailed escalation data for a specific cluster.

    Returns domain-level scores with individual signal breakdowns
    (embedding, content, keywords) for each domain.

    Args:
        cluster_id: UUID of the cluster
        recalculate: If True, recalculate escalation even if cached

    Returns:
        ClusterEscalationDetailResponse with detailed escalation data

    Raises:
        HTTPException: 404 if cluster not found
    """
    from uuid import UUID as UUIDType

    # Fetch cluster from database
    stmt = select(ArticleCluster).where(ArticleCluster.id == cluster_id)
    result = await db.execute(stmt)
    cluster = result.scalar_one_or_none()

    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    # Check if recalculation is needed
    if recalculate or cluster.escalation_combined is None:
        # Attempt recalculation using EscalationCalculator
        from app.services.escalation_calculator import EscalationCalculator

        calculator = EscalationCalculator(session=db)

        # Get cluster centroid and text
        cluster_embedding = []
        if cluster.centroid_vector and isinstance(cluster.centroid_vector, dict):
            cluster_embedding = cluster.centroid_vector.get("embedding", [])
        elif cluster.centroid_vector and isinstance(cluster.centroid_vector, list):
            cluster_embedding = cluster.centroid_vector

        cluster_text = cluster.title or ""

        # Only recalculate if we have a valid embedding
        if len(cluster_embedding) == 1536:
            try:
                escalation_result = await calculator.calculate_cluster_escalation(
                    cluster_id=cluster.id,
                    cluster_embedding=cluster_embedding,
                    cluster_text=cluster_text,
                    article_count=cluster.article_count or 1,
                )

                # Update cluster with new escalation data
                cluster.escalation_geopolitical = float(escalation_result.geopolitical.score)
                cluster.escalation_military = float(escalation_result.military.score)
                cluster.escalation_economic = float(escalation_result.economic.score)
                cluster.escalation_combined = float(escalation_result.combined_score)
                cluster.escalation_level = escalation_result.combined_level

                # Store signals as JSON
                cluster.escalation_signals = {
                    "geopolitical": [
                        {
                            "source": s.source,
                            "level": s.level,
                            "confidence": s.confidence,
                            "matched_anchor_id": str(s.matched_anchor_id) if s.matched_anchor_id else None,
                            "matched_keywords": s.matched_keywords,
                            "reasoning": s.reasoning,
                        }
                        for s in escalation_result.geopolitical.signals
                    ],
                    "military": [
                        {
                            "source": s.source,
                            "level": s.level,
                            "confidence": s.confidence,
                            "matched_anchor_id": str(s.matched_anchor_id) if s.matched_anchor_id else None,
                            "matched_keywords": s.matched_keywords,
                            "reasoning": s.reasoning,
                        }
                        for s in escalation_result.military.signals
                    ],
                    "economic": [
                        {
                            "source": s.source,
                            "level": s.level,
                            "confidence": s.confidence,
                            "matched_anchor_id": str(s.matched_anchor_id) if s.matched_anchor_id else None,
                            "matched_keywords": s.matched_keywords,
                            "reasoning": s.reasoning,
                        }
                        for s in escalation_result.economic.signals
                    ],
                }
                cluster.escalation_calculated_at = datetime.now()

                await db.commit()
                await db.refresh(cluster)
            except Exception as e:
                logger.warning(f"Failed to recalculate escalation for cluster {cluster_id}: {e}")
                # Continue with existing data if recalculation fails

    def _build_domain_response(domain: str, score_attr: str) -> DomainEscalationResponse:
        """Build domain response from cluster attributes."""
        score = getattr(cluster, score_attr, None)
        if score is None:
            score = Decimal("0.500")
        else:
            score = Decimal(str(score))

        # Convert score to level: level = round(score * 4) + 1
        level = max(1, min(5, round(float(score) * 4) + 1))

        # Confidence based on whether we have calculated data
        confidence = 0.7 if cluster.escalation_calculated_at else 0.0

        return DomainEscalationResponse(
            domain=domain,
            level=level,
            score=score,
            confidence=confidence,
        )

    def _get_signals(domain: str) -> List[SignalDetailResponse]:
        """Extract signal responses from stored escalation_signals JSON."""
        signals_data = cluster.escalation_signals or {}
        domain_signals = signals_data.get(domain, [])

        responses = []
        for s in domain_signals:
            try:
                # Parse anchor_id if present
                anchor_id = None
                if s.get("matched_anchor_id"):
                    try:
                        anchor_id = UUIDType(s["matched_anchor_id"])
                    except (ValueError, TypeError):
                        anchor_id = None

                responses.append(
                    SignalDetailResponse(
                        source=s.get("source", "unknown"),
                        level=max(1, min(5, s.get("level", 3))),
                        confidence=max(0.0, min(1.0, s.get("confidence", 0.0))),
                        matched_anchor_id=anchor_id,
                        matched_keywords=s.get("matched_keywords"),
                        reasoning=s.get("reasoning"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse signal: {e}")
                continue

        return responses

    # Build domain responses
    geo = _build_domain_response("geopolitical", "escalation_geopolitical")
    mil = _build_domain_response("military", "escalation_military")
    eco = _build_domain_response("economic", "escalation_economic")

    # Combined level and score
    combined_level = cluster.escalation_level or max(geo.level, mil.level, eco.level)
    combined_score = cluster.escalation_combined
    if combined_score is None:
        combined_score = (geo.score + mil.score + eco.score) / 3
    else:
        combined_score = Decimal(str(combined_score))

    return ClusterEscalationDetailResponse(
        cluster_id=cluster.id,
        cluster_title=cluster.title or "Untitled Cluster",
        article_count=cluster.article_count or 0,
        geopolitical=geo,
        military=mil,
        economic=eco,
        combined_level=combined_level,
        combined_score=combined_score,
        geopolitical_signals=_get_signals("geopolitical"),
        military_signals=_get_signals("military"),
        economic_signals=_get_signals("economic"),
        escalation_calculated_at=cluster.escalation_calculated_at,
        created_at=cluster.created_at,
    )
