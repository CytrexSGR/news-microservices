"""
Feed Quality Scoring Service V2

Comprehensive feed quality scoring that aggregates article-level quality metrics
from content-analysis-v2 with feed-level operational metrics.

Based on design document: docs/design/feed-quality-scoring-model.md

Components:
1. Article Quality (50% weight) - From content-analysis-v2
2. Source Credibility (20% weight) - Research service + trends
3. Operational Reliability (20% weight) - Feed health metrics
4. Freshness & Consistency (10% weight) - Publishing patterns

Version: 1.0
Date: 2025-11-06
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feed, FeedItem, FeedHealth
from app.services.admiralty_code import AdmiraltyCodeService
from app.services.feed_quality import FeedQualityScorer  # Reuse freshness/consistency

logger = logging.getLogger(__name__)


# Default configurable weights
DEFAULT_COMPONENT_WEIGHTS = {
    'article_quality': 0.50,
    'source_credibility': 0.20,
    'operational': 0.20,
    'freshness_consistency': 0.10
}

DEFAULT_ARTICLE_QUALITY_WEIGHTS = {
    'credibility': 0.25,
    'objectivity': 0.15,
    'verification': 0.20,
    'relevance': 0.15,
    'completeness': 0.15,
    'consistency': 0.10
}


class FeedQualityScorerV2:
    """
    Advanced feed quality scorer that combines article-level analysis
    with feed-level operational metrics.
    """

    def __init__(
        self,
        component_weights: Optional[Dict[str, float]] = None,
        article_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize scorer with configurable weights.

        Args:
            component_weights: Weights for main components (article, source, operational, freshness)
            article_weights: Weights for article quality sub-components
        """
        self.component_weights = component_weights or DEFAULT_COMPONENT_WEIGHTS
        self.article_weights = article_weights or DEFAULT_ARTICLE_QUALITY_WEIGHTS

        # Reuse existing scorer for freshness/consistency
        self.base_scorer = FeedQualityScorer()

    async def calculate_comprehensive_quality(
        self,
        session: AsyncSession,
        feed_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive feed quality score.

        Args:
            session: Database session
            feed_id: Feed UUID
            days: Number of days to analyze (default: 30)

        Returns:
            Comprehensive quality report with scores, trends, and recommendations
        """
        try:
            # Get feed data
            feed = await self._get_feed(session, feed_id)
            if not feed:
                raise ValueError(f"Feed {feed_id} not found")

            # Calculate all components
            article_quality = await self._calculate_article_quality(session, feed_id, days)
            source_credibility = await self._calculate_source_credibility(session, feed, days)
            operational = await self._calculate_operational_score(session, feed_id)
            freshness_consistency = await self._calculate_freshness_consistency(session, feed_id)

            # Calculate overall score
            overall_score = self._calculate_overall_score(
                article_quality,
                source_credibility,
                operational,
                freshness_consistency
            )

            # Get Admiralty Code
            admiralty_service = AdmiraltyCodeService(session)
            admiralty_code = await admiralty_service.get_admiralty_code(int(overall_score))

            # Calculate trends
            trends = await self._calculate_trends(session, feed_id, days)

            # Calculate confidence
            confidence_data = await self._calculate_confidence(session, feed_id, days)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                overall_score,
                article_quality,
                source_credibility,
                operational,
                freshness_consistency,
                trends,
                feed
            )

            return {
                "feed_id": str(feed_id),
                "feed_name": feed.name,
                "quality_score": round(overall_score, 2),
                "admiralty_code": admiralty_code,
                "confidence": confidence_data['confidence'],
                "confidence_score": confidence_data['confidence_score'],
                "trend": trends['trend_label'],
                "trend_direction": trends['trend_value'],

                "component_scores": {
                    "article_quality": article_quality,
                    "source_credibility": source_credibility,
                    "operational": operational,
                    "freshness_consistency": freshness_consistency
                },

                "quality_distribution": article_quality.get('distribution', {}),
                "red_flags": article_quality.get('red_flags', {}),
                "trends": trends,
                "data_stats": confidence_data['data_stats'],
                "recommendations": recommendations,
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to calculate quality for feed {feed_id}: {e}", exc_info=True)
            raise

    # ==================== Component Calculations ====================

    async def _calculate_article_quality(
        self,
        session: AsyncSession,
        feed_id: UUID,
        days: int
    ) -> Dict[str, Any]:
        """
        Calculate article quality component from content-analysis-v2 pipeline data.

        Phase 1.2 Update: Now uses NEW pipeline format (triage/tier1/tier2/tier3)
        instead of old relevance_score/score_breakdown format.

        Pipeline Mapping:
        - Relevance: triage.PriorityScore
        - Objectivity: tier2.BIAS_DETECTOR scores
        - Credibility: tier2 agent confidence scores
        - Verification: presence of tier2/tier3 analysis
        - Completeness: tier1 entities + tier2 agents count
        - Consistency: tier2 agent confidence variance

        Returns dict with:
        - score: 0-100 or None
        - weight: component weight
        - breakdown: individual quality metrics
        - distribution: quality category percentages
        - red_flags: aggregated warnings
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get feed items with NEW pipeline format
        query = text("""
            SELECT fi.id as item_id,
                   aa.triage_results, aa.tier1_results, aa.tier2_results, aa.tier3_results
            FROM feed_items fi
            LEFT JOIN public.article_analysis aa ON aa.article_id = fi.id
            WHERE fi.feed_id = :feed_id
              AND fi.created_at >= :cutoff_date
              AND aa.id IS NOT NULL
              AND aa.triage_results IS NOT NULL
            ORDER BY fi.created_at DESC
        """)

        result = await session.execute(query, {
            "feed_id": str(feed_id),
            "cutoff_date": cutoff_date
        })
        rows = result.fetchall()

        if not rows or len(rows) < 5:
            # Insufficient data - return None to avoid false confidence
            logger.warning(f"Feed {feed_id}: Only {len(rows)} analyzed articles in new format, insufficient for quality score")
            return {
                "score": None,
                "weight": 0.10,
                "breakdown": {},
                "distribution": {},
                "red_flags": {"insufficient_data": True},
                "articles_analyzed": len(rows),
                "confidence_level": "insufficient_data"
            }

        # Extract quality metrics from NEW pipeline format
        scores = {
            'credibility': [],
            'objectivity': [],
            'verification': [],
            'relevance': [],
            'completeness': [],
            'consistency': []
        }

        quality_categories = []
        red_flags_count = {}

        for row in rows:
            row_dict = dict(row._mapping)

            # Parse JSON fields
            triage = row_dict.get('triage_results') or {}
            tier1 = row_dict.get('tier1_results') or {}
            tier2 = row_dict.get('tier2_results') or {}
            tier3 = row_dict.get('tier3_results') or {}

            # 1. RELEVANCE: From triage.PriorityScore (0-100)
            priority_score = triage.get('PriorityScore')
            if priority_score is not None:
                scores['relevance'].append(float(priority_score))

            # 2. OBJECTIVITY: From tier2.BIAS_DETECTOR
            bias_detector = tier2.get('BIAS_DETECTOR', {})
            if bias_detector:
                # Lower bias = higher objectivity
                political_bias = bias_detector.get('political_bias', {}).get('score', 0)
                balance_score = bias_detector.get('framing_analysis', {}).get('balance_score', 1.0)
                clickbait_score = bias_detector.get('headline_analysis', {}).get('clickbait_score', 0)

                # Combine: 100 - bias, balance (0-1 → 0-100), 100 - clickbait
                objectivity = (
                    (100 - political_bias * 10) * 0.4 +  # political_bias is 0-10 scale
                    balance_score * 100 * 0.4 +
                    (100 - clickbait_score * 100) * 0.2
                )
                scores['objectivity'].append(max(0, min(100, objectivity)))

            # 3. CREDIBILITY: From tier2 agent confidence scores
            agent_confidences = []
            for agent_name in ['BIAS_DETECTOR', 'SENTIMENT_ANALYST', 'TOPIC_CLASSIFIER']:
                agent_data = tier2.get(agent_name, {})
                if agent_data:
                    confidence = agent_data.get('confidence', 0)
                    if confidence > 0:
                        agent_confidences.append(confidence * 100)

            if agent_confidences:
                scores['credibility'].append(sum(agent_confidences) / len(agent_confidences))

            # 4. VERIFICATION: Based on tier2/tier3 presence
            verification_score = 0
            tier2_agents_present = len([k for k in tier2.keys() if isinstance(tier2.get(k), dict)])
            verification_score += min(tier2_agents_present * 15, 70)  # Up to 70 for tier2
            if tier3:
                verification_score += 30  # Bonus for tier3 synthesis
            if verification_score > 0:
                scores['verification'].append(min(verification_score, 100))

            # 5. COMPLETENESS: Based on tier1 entities + tier2 coverage
            completeness_score = 0
            entities_count = len(tier1.get('entities', []))
            completeness_score += min(entities_count * 10, 50)  # Up to 50 for entities
            completeness_score += min(tier2_agents_present * 10, 50)  # Up to 50 for tier2 agents
            if completeness_score > 0:
                scores['completeness'].append(min(completeness_score, 100))

            # 6. CONSISTENCY: Based on tier2 agent confidence variance
            if len(agent_confidences) >= 2:
                # Low variance = high consistency
                mean_conf = sum(agent_confidences) / len(agent_confidences)
                variance = sum((c - mean_conf) ** 2 for c in agent_confidences) / len(agent_confidences)
                consistency = 100 - min(variance, 50)  # High variance reduces consistency
                scores['consistency'].append(max(50, consistency))

            # Categorize article quality based on priority score
            priority = triage.get('PriorityScore', 0)
            if priority >= 80:
                quality_categories.append('premium')
            elif priority >= 60:
                quality_categories.append('high_quality')
            elif priority >= 40:
                quality_categories.append('moderate_quality')
            elif priority >= 20:
                quality_categories.append('low_quality')
            else:
                quality_categories.append('very_low_quality')

        # Calculate average scores with coverage-aware defaults
        avg_scores = {}
        total_articles = len(rows)

        for dimension, values in scores.items():
            if values:
                coverage = len(values) / total_articles
                avg_scores[dimension] = sum(values) / len(values)

                # Apply coverage penalty for low coverage dimensions
                if coverage < 0.10:  # Less than 10% coverage
                    avg_scores[dimension] = None  # Insufficient data
                elif coverage < 0.50:  # 10-50% coverage
                    # Weight towards neutral with low confidence
                    avg_scores[dimension] = avg_scores[dimension] * 0.7 + 50.0 * 0.3
            else:
                # No data for this dimension - explicitly mark as None
                avg_scores[dimension] = None

        # Calculate weighted article quality score (skip None dimensions)
        valid_dimensions = {
            dim: (avg_scores.get(dim), weight)
            for dim, weight in self.article_weights.items()
            if avg_scores.get(dim) is not None
        }

        if not valid_dimensions:
            # No valid dimensions - insufficient data
            logger.warning(f"Feed {feed_id}: No valid quality dimensions, returning None score")
            return {
                "score": None,
                "weight": 0.10,
                "breakdown": avg_scores,
                "distribution": {},
                "red_flags": {"insufficient_data": True},
                "articles_analyzed": len(rows),
                "confidence_level": "insufficient_data"
            }

        # Normalize weights (since some dimensions may be missing)
        total_weight = sum(weight for _, weight in valid_dimensions.values())
        normalized_article_score = sum(
            score * (weight / total_weight)
            for score, weight in valid_dimensions.values()
        )

        # Calculate quality distribution
        total_articles = len(quality_categories)
        distribution = {
            'premium': quality_categories.count('premium') / total_articles if total_articles > 0 else 0,
            'high_quality': quality_categories.count('high_quality') / total_articles if total_articles > 0 else 0,
            'moderate_quality': quality_categories.count('moderate_quality') / total_articles if total_articles > 0 else 0,
            'low_quality': quality_categories.count('low_quality') / total_articles if total_articles > 0 else 0,
            'very_low_quality': quality_categories.count('very_low_quality') / total_articles if total_articles > 0 else 0,
        }

        # Distribution bonus/penalty
        distribution_bonus = (
            distribution['premium'] * 10 +
            distribution['high_quality'] * 5 +
            distribution['moderate_quality'] * 0 +
            distribution['low_quality'] * -5 +
            distribution['very_low_quality'] * -10
        )
        distribution_bonus = max(-5, min(5, distribution_bonus))  # Clamp to ±5

        return {
            "score": round(min(100, max(0, normalized_article_score + distribution_bonus)), 2),
            "weight": self.component_weights['article_quality'],
            "breakdown": avg_scores,
            "distribution": distribution,
            "distribution_bonus": round(distribution_bonus, 2),
            "red_flags": red_flags_count,
            "articles_analyzed": len(rows)
        }

    async def _calculate_source_credibility(
        self,
        session: AsyncSession,
        feed: Feed,
        days: int
    ) -> Dict[str, Any]:
        """
        Calculate source credibility from research service assessment + trends.
        """
        # Base credibility from research service
        base_credibility = feed.reputation_score or 50

        # Tier adjustment
        tier_bonus = {
            'tier_1': 15,
            'tier_2': 0,
            'tier_3': -10
        }.get(feed.credibility_tier, 0)

        # Article credibility trend (if we have article data)
        trend_adjustment = 0
        try:
            # Get credibility trend from recent vs historical
            cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
            cutoff_30d = datetime.now(timezone.utc) - timedelta(days=days)

            query_recent = text("""
                SELECT AVG(relevance_score) as avg_score
                FROM feed_items fi
                JOIN public.article_analysis aa ON aa.article_id = fi.id
                WHERE fi.feed_id = :feed_id AND fi.created_at >= :cutoff_date
            """)

            result_7d = await session.execute(query_recent, {
                "feed_id": str(feed.id),
                "cutoff_date": cutoff_7d
            })
            recent_score = result_7d.scalar() or 0

            result_30d = await session.execute(query_recent, {
                "feed_id": str(feed.id),
                "cutoff_date": cutoff_30d
            })
            historical_score = result_30d.scalar() or 0

            if recent_score and historical_score:
                trend_adjustment = (recent_score - historical_score) * 0.1

        except Exception as e:
            logger.warning(f"Could not calculate credibility trend: {e}")

        # Editorial standards bonus
        editorial_bonus = 0
        if feed.editorial_standards:
            if feed.editorial_standards.get('fact_checking_level') == 'rigorous':
                editorial_bonus += 5
            if feed.editorial_standards.get('corrections_policy') == 'transparent':
                editorial_bonus += 3

        final_score = base_credibility + tier_bonus + trend_adjustment + editorial_bonus
        final_score = max(0, min(100, final_score))

        return {
            "score": round(final_score, 2),
            "weight": self.component_weights['source_credibility'],
            "reputation_score": base_credibility,
            "credibility_tier": feed.credibility_tier,
            "tier_adjustment": tier_bonus,
            "trend_adjustment": round(trend_adjustment, 2),
            "editorial_bonus": editorial_bonus
        }

    async def _calculate_operational_score(
        self,
        session: AsyncSession,
        feed_id: UUID
    ) -> Dict[str, Any]:
        """
        Calculate operational reliability from feed health metrics.
        """
        # Get health record
        result = await session.execute(
            select(FeedHealth).where(FeedHealth.feed_id == feed_id)
        )
        health = result.scalar_one_or_none()

        if not health:
            return {
                "score": 50.0,
                "weight": self.component_weights['operational'],
                "success_rate": None,
                "uptime_7d": None,
                "consecutive_failures": 0
            }

        # Calculate reliability score
        reliability_score = (
            (health.success_rate or 0) * 0.4 +
            (health.uptime_24h or 0) * 0.2 +
            (health.uptime_7d or 0) * 0.2 +
            (health.uptime_30d or 0) * 0.2
        ) * 100

        # Penalty for consecutive failures
        penalty = 0
        if health.consecutive_failures > 0:
            penalty = min(health.consecutive_failures * 5, 30)
            reliability_score = max(0, reliability_score - penalty)

        return {
            "score": round(reliability_score, 2),
            "weight": self.component_weights['operational'],
            "success_rate": float(health.success_rate) if health.success_rate else 0,
            "uptime_7d": float(health.uptime_7d) if health.uptime_7d else 0,
            "uptime_30d": float(health.uptime_30d) if health.uptime_30d else 0,
            "consecutive_failures": health.consecutive_failures,
            "failure_penalty": penalty
        }

    async def _calculate_freshness_consistency(
        self,
        session: AsyncSession,
        feed_id: UUID
    ) -> Dict[str, Any]:
        """
        Calculate freshness and consistency using existing FeedQualityScorer.
        """
        try:
            freshness_score = await self.base_scorer._calculate_freshness_score(session, feed_id)
            consistency_score = await self.base_scorer._calculate_consistency_score(session, feed_id)

            combined_score = (
                freshness_score * 0.6 +
                consistency_score * 0.4
            )

            return {
                "score": round(combined_score, 2),
                "weight": self.component_weights['freshness_consistency'],
                "freshness": round(freshness_score, 2),
                "consistency": round(consistency_score, 2)
            }

        except Exception as e:
            logger.error(f"Failed to calculate freshness/consistency: {e}")
            return {
                "score": 50.0,
                "weight": self.component_weights['freshness_consistency'],
                "freshness": 50.0,
                "consistency": 50.0
            }

    def _calculate_overall_score(
        self,
        article_quality: Dict[str, Any],
        source_credibility: Dict[str, Any],
        operational: Dict[str, Any],
        freshness_consistency: Dict[str, Any]
    ) -> Optional[float]:
        """
        Calculate weighted overall feed quality score.

        Phase 1.1 Update: Returns None if insufficient data (all components are None).
        Only components with valid scores (not None) contribute to the weighted average.
        """
        # Collect valid components (score is not None)
        components = []

        if article_quality['score'] is not None:
            components.append({
                'score': article_quality['score'],
                'weight': article_quality.get('weight', self.component_weights['article_quality'])
            })

        if source_credibility['score'] is not None:
            components.append({
                'score': source_credibility['score'],
                'weight': source_credibility['weight']
            })

        if operational['score'] is not None:
            components.append({
                'score': operational['score'],
                'weight': operational['weight']
            })

        if freshness_consistency['score'] is not None:
            components.append({
                'score': freshness_consistency['score'],
                'weight': freshness_consistency['weight']
            })

        # If no valid components, return None (insufficient data)
        if not components:
            return None

        # Calculate weighted score using only valid components
        total_weight = sum(c['weight'] for c in components)
        weighted_sum = sum(c['score'] * c['weight'] for c in components)

        overall = weighted_sum / total_weight if total_weight > 0 else None

        # Return None if calculation failed, otherwise clamp to [0, 100]
        return max(0, min(100, overall)) if overall is not None else None

    # ==================== Trends & Analysis ====================

    async def _calculate_trends(
        self,
        session: AsyncSession,
        feed_id: UUID,
        days: int
    ) -> Dict[str, Any]:
        """
        Calculate quality trends (7 days vs 30 days).
        """
        try:
            # For now, use simplified trend based on recent articles
            # Full implementation would recalculate quality for different time periods
            cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
            cutoff_30d = datetime.now(timezone.utc) - timedelta(days=days)

            query = text("""
                SELECT AVG(relevance_score) as avg_score
                FROM feed_items fi
                JOIN public.article_analysis aa ON aa.article_id = fi.id
                WHERE fi.feed_id = :feed_id AND fi.created_at >= :cutoff_date
            """)

            result_7d = await session.execute(query, {
                "feed_id": str(feed_id),
                "cutoff_date": cutoff_7d
            })
            score_7d = result_7d.scalar() or 50

            result_30d = await session.execute(query, {
                "feed_id": str(feed_id),
                "cutoff_date": cutoff_30d
            })
            score_30d = result_30d.scalar() or 50

            trend_value = score_7d - score_30d

            if trend_value > 5:
                trend_label = "improving"
            elif trend_value < -5:
                trend_label = "declining"
            else:
                trend_label = "stable"

            return {
                "trend_label": trend_label,
                "trend_value": round(trend_value, 2),
                "quality_7d_vs_30d": round(trend_value, 2),
                "score_7d": round(score_7d, 2),
                "score_30d": round(score_30d, 2)
            }

        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            return {
                "trend_label": "unknown",
                "trend_value": 0,
                "quality_7d_vs_30d": 0
            }

    async def _calculate_confidence(
        self,
        session: AsyncSession,
        feed_id: UUID,
        days: int
    ) -> Dict[str, Any]:
        """
        Calculate confidence level based on data completeness with 4-tier granularity.

        Confidence Levels:
        - insufficient_data: < 10% coverage or < 5 articles
        - low: 10-50% coverage
        - medium: 50-80% coverage
        - high: > 80% coverage
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Count total articles vs analyzed articles
        query_total = text("""
            SELECT COUNT(*) FROM feed_items
            WHERE feed_id = :feed_id AND created_at >= :cutoff_date
        """)
        result_total = await session.execute(query_total, {
            "feed_id": str(feed_id),
            "cutoff_date": cutoff_date
        })
        total_articles = result_total.scalar() or 0

        query_analyzed = text("""
            SELECT COUNT(*)
            FROM feed_items fi
            JOIN public.article_analysis aa ON aa.article_id = fi.id
            WHERE fi.feed_id = :feed_id AND fi.created_at >= :cutoff_date
        """)
        result_analyzed = await session.execute(query_analyzed, {
            "feed_id": str(feed_id),
            "cutoff_date": cutoff_date
        })
        articles_analyzed = result_analyzed.scalar() or 0

        coverage_fraction = (articles_analyzed / total_articles) if total_articles > 0 else 0
        coverage_pct = coverage_fraction * 100

        # Calculate confidence level (4-tier system)
        confidence_level = self._calculate_confidence_level(coverage_fraction, articles_analyzed)

        # Backward-compatible confidence (3-tier system)
        if articles_analyzed >= 50 and coverage_pct >= 80:
            confidence = "high"
        elif articles_analyzed >= 20 and coverage_pct >= 50:
            confidence = "medium"
        else:
            confidence = "low"

        # Numerical confidence score (0-100)
        confidence_score = coverage_pct

        return {
            "confidence": confidence,  # Backward compatible (high/medium/low)
            "confidence_level": confidence_level,  # NEW: 4-tier (insufficient_data/low/medium/high)
            "confidence_score": round(confidence_score, 2),
            "data_stats": {
                "articles_analyzed": articles_analyzed,
                "total_articles": total_articles,
                "coverage_percentage": round(coverage_pct, 2),
                "coverage_fraction": round(coverage_fraction, 4),
                "date_range_days": days
            }
        }

    def _calculate_confidence_level(self, coverage_fraction: float, articles_count: int) -> str:
        """
        Calculate granular confidence level based on coverage and absolute article count.

        Args:
            coverage_fraction: Ratio of analyzed/total articles (0-1)
            articles_count: Absolute number of analyzed articles

        Returns:
            Confidence level: insufficient_data | low | medium | high
        """
        # Insufficient data: Very low coverage OR too few articles
        if coverage_fraction < 0.10 or articles_count < 5:
            return "insufficient_data"

        # Low confidence: 10-50% coverage
        if coverage_fraction < 0.50:
            return "low"

        # Medium confidence: 50-80% coverage
        if coverage_fraction < 0.80:
            return "medium"

        # High confidence: > 80% coverage
        return "high"

    # ==================== Recommendations ====================

    def _generate_recommendations(
        self,
        overall_score: Optional[float],
        article_quality: Dict[str, Any],
        source_credibility: Dict[str, Any],
        operational: Dict[str, Any],
        freshness_consistency: Dict[str, Any],
        trends: Dict[str, Any],
        feed: Feed
    ) -> List[str]:
        """
        Generate actionable recommendations based on scores and trends.

        Phase 1.1 Update: Handles None scores (insufficient data) gracefully.
        """
        recommendations = []

        # Overall quality tier recommendations (only if score is available)
        if overall_score is not None:
            if overall_score >= 90:
                recommendations.append("🌟 Excellent source. Prioritize in article distribution")
                recommendations.append("Consider for premium content features")
            elif overall_score >= 75:
                recommendations.append("✅ Reliable source. Good for general use")
                recommendations.append("Suitable for most use cases")
            elif overall_score >= 60:
                recommendations.append("⚠️ Acceptable source. Monitor quality trends")
                recommendations.append("Use with context and verification")
            elif overall_score >= 40:
                recommendations.append("⚠️ Low-quality source. Use with caution")
                recommendations.append("Consider additional fact-checking")
            else:
                recommendations.append("❌ Unreliable source. Not recommended for use")
                recommendations.append("Consider removing from active feeds")
        else:
            recommendations.append("ℹ️ Insufficient data for quality assessment")
            recommendations.append("Continue collecting data for accurate evaluation")

        # Article quality recommendations (only if score is available)
        if article_quality['score'] is not None and article_quality['score'] < 40:
            if article_quality.get('articles_analyzed', 0) < 10:
                recommendations.append("Insufficient analyzed articles for quality assessment")
            else:
                recommendations.append("Article quality is low - consider reviewing feed sources")

        # Trend-based recommendations
        if trends['trend_label'] == 'improving':
            recommendations.append("📈 Quality improving - good trend detected")
        elif trends['trend_label'] == 'declining':
            recommendations.append("📉 Quality declining - monitor closely")

        # Operational recommendations (only if score is available)
        if operational['score'] is not None and operational['score'] < 60:
            if operational.get('consecutive_failures', 0) > 3:
                recommendations.append(
                    f"⚠️ {operational['consecutive_failures']} consecutive failures detected"
                )
            recommendations.append("Feed reliability is low - check URL and server status")

        # Freshness recommendations
        freshness_score = freshness_consistency.get('freshness', 50)
        if freshness_score is not None and freshness_score < 40:
            recommendations.append("Feed appears inactive or updating slowly")

        # Data completeness recommendations
        articles_analyzed = article_quality.get('articles_analyzed', 0)
        if articles_analyzed < 20:
            recommendations.append(
                f"Limited data ({articles_analyzed} analyzed articles) - "
                f"continue collecting for more accurate assessment"
            )

        return recommendations

    # ==================== Helper Methods ====================

    async def _get_feed(self, session: AsyncSession, feed_id: UUID) -> Optional[Feed]:
        """Get feed by ID."""
        result = await session.execute(
            select(Feed).where(Feed.id == feed_id)
        )
        return result.scalar_one_or_none()

    def _extract_agent_score(self, breakdown: Dict, agent_name: str) -> float:
        """
        Extract agent score from score_breakdown.
        Returns 50.0 (neutral) if not found.
        """
        try:
            if isinstance(breakdown, dict):
                # Try to find agent score in various formats
                if agent_name in breakdown:
                    score = breakdown[agent_name]
                    if isinstance(score, (int, float)):
                        return float(score)
                    elif isinstance(score, dict) and 'score' in score:
                        return float(score['score'])
            return 50.0
        except Exception:
            return 50.0
