"""
Risk Scoring Service - Calculate 1-week delta risk scores
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.models.cluster import IntelligenceCluster
from app.models.risk_history import IntelligenceRiskHistory
from app.models.event import IntelligenceEvent

logger = logging.getLogger(__name__)


class RiskScoringService:
    """Service for calculating and updating risk scores"""

    async def get_last_week_metrics(
        self,
        db: AsyncSession,
        cluster_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Get metrics from previous week"""
        # Get last week's record
        result = await db.execute(
            select(IntelligenceRiskHistory)
            .where(IntelligenceRiskHistory.cluster_id == cluster_id)
            .order_by(IntelligenceRiskHistory.week_start.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        return {
            "risk_score": record.risk_score,
            "article_count": record.article_count,
            "avg_sentiment": record.avg_sentiment,
            "unique_sources": record.unique_sources,
        }

    async def calculate_current_metrics(
        self,
        db: AsyncSession,
        cluster_id: uuid.UUID,
        days: int = 7
    ) -> Dict[str, Any]:
        """Calculate current week metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Count articles
        article_count_result = await db.execute(
            select(func.count(IntelligenceEvent.id))
            .where(
                IntelligenceEvent.cluster_id == cluster_id,
                IntelligenceEvent.published_at >= cutoff_date
            )
        )
        article_count = article_count_result.scalar() or 0

        # Average sentiment
        sentiment_result = await db.execute(
            select(func.avg(IntelligenceEvent.sentiment))
            .where(
                IntelligenceEvent.cluster_id == cluster_id,
                IntelligenceEvent.published_at >= cutoff_date,
                IntelligenceEvent.sentiment.isnot(None)
            )
        )
        avg_sentiment = sentiment_result.scalar() or 0.0

        # Unique sources
        sources_result = await db.execute(
            select(func.count(func.distinct(IntelligenceEvent.source)))
            .where(
                IntelligenceEvent.cluster_id == cluster_id,
                IntelligenceEvent.published_at >= cutoff_date
            )
        )
        unique_sources = sources_result.scalar() or 0

        return {
            "article_count": article_count,
            "avg_sentiment": avg_sentiment,
            "unique_sources": unique_sources,
        }

    def calculate_risk_score(
        self,
        current_metrics: Dict[str, Any],
        last_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Calculate risk score based on metrics

        Returns:
            Dict with risk_score and risk_delta
        """
        article_count = current_metrics.get("article_count", 0)
        sentiment = current_metrics.get("avg_sentiment", 0.0)
        unique_sources = current_metrics.get("unique_sources", 0)

        # Base risk score (0-100)
        # Higher article count = higher risk
        # Negative sentiment = higher risk
        # More sources = higher credibility = higher risk

        article_factor = min(article_count / 100.0, 1.0)  # Normalize to 0-1
        sentiment_factor = (1.0 - sentiment) / 2.0  # -1 (negative) → 1.0, +1 (positive) → 0.0
        source_factor = min(unique_sources / 10.0, 1.0)  # Normalize to 0-1

        risk_score = (article_factor * 40 + sentiment_factor * 40 + source_factor * 20) * 100

        # Calculate delta
        risk_delta = 0.0
        if last_metrics and last_metrics.get("risk_score"):
            last_risk = last_metrics["risk_score"]
            if last_risk > 0:
                risk_delta = ((risk_score - last_risk) / last_risk) * 100

        return {
            "risk_score": round(risk_score, 2),
            "risk_delta": round(risk_delta, 2),
        }

    async def update_cluster_risk(
        self,
        db: AsyncSession,
        cluster_id: uuid.UUID
    ) -> Optional[IntelligenceCluster]:
        """Update risk score for a cluster"""
        # Get cluster
        result = await db.execute(
            select(IntelligenceCluster).where(IntelligenceCluster.id == cluster_id)
        )
        cluster = result.scalar_one_or_none()
        if not cluster:
            return None

        # Get last week's metrics
        last_metrics = await self.get_last_week_metrics(db, cluster_id)

        # Calculate current metrics
        current_metrics = await self.calculate_current_metrics(db, cluster_id)

        # Calculate risk score
        risk_data = self.calculate_risk_score(current_metrics, last_metrics)

        # Update cluster
        cluster.risk_score = risk_data["risk_score"]
        cluster.risk_delta = risk_data["risk_delta"]
        cluster.last_updated = datetime.utcnow()

        await db.commit()
        await db.refresh(cluster)

        logger.info(f"Updated risk for cluster {cluster_id}: {risk_data}")
        return cluster


# Global instance
risk_scoring_service = RiskScoringService()
