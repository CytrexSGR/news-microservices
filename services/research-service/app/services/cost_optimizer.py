"""Cost optimization service for research queries.

Implements 3-tier cost optimization strategy:
- Tier 1 (Quick): Cache-first, minimal API calls, sonar model (most cost-effective)
- Tier 2 (Standard): Balanced cost and quality, cache + API, sonar model
- Tier 3 (Deep): Quality-first, comprehensive research, sonar-pro model
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.core.config import settings
from app.models.research import CostTracking, ResearchTask, ResearchCache

logger = logging.getLogger(__name__)


class CostTier(str, Enum):
    """Cost optimization tiers."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass
class TierConfig:
    """Configuration for a cost tier."""
    name: str
    model: str
    cache_priority: float  # 0.0-1.0, higher = prefer cache more
    max_tokens: int
    temperature: float
    recency_filter: str
    cost_multiplier: float
    description: str


class CostOptimizer:
    """
    Cost optimizer for research service.

    Implements intelligent cost management across three tiers:
    - Quick: Best for simple queries, maximizes cache usage
    - Standard: Balanced approach for typical research
    - Deep: Premium quality for complex analysis
    """

    # Tier configurations
    TIER_CONFIGS = {
        CostTier.QUICK: TierConfig(
            name="Quick",
            model="sonar",
            cache_priority=0.9,  # Strongly prefer cache
            max_tokens=2000,
            temperature=0.3,
            recency_filter="day",
            cost_multiplier=1.0,
            description="Fast, cost-effective research with high cache usage"
        ),
        CostTier.STANDARD: TierConfig(
            name="Standard",
            model="sonar",
            cache_priority=0.6,  # Balanced cache usage
            max_tokens=4000,
            temperature=0.5,
            recency_filter="week",
            cost_multiplier=1.5,
            description="Balanced cost and quality for typical research"
        ),
        CostTier.DEEP: TierConfig(
            name="Deep",
            model="sonar-pro",
            cache_priority=0.3,  # Prefer fresh results
            max_tokens=8000,
            temperature=0.7,
            recency_filter="month",
            cost_multiplier=3.0,
            description="Premium quality research with comprehensive analysis"
        )
    }

    def __init__(self):
        """Initialize cost optimizer."""
        self.logger = logger

    def select_tier(
        self,
        user_preference: Optional[str] = None,
        query_complexity: Optional[float] = None,
        budget_remaining: Optional[float] = None,
        cache_available: bool = False
    ) -> CostTier:
        """
        Select optimal cost tier based on multiple factors.

        Args:
            user_preference: User's explicit tier preference (quick/standard/deep)
            query_complexity: Estimated query complexity (0.0-1.0)
            budget_remaining: Remaining budget for user
            cache_available: Whether cached result exists

        Returns:
            Selected cost tier
        """
        # If user specified a tier, respect it (unless budget constraints)
        if user_preference:
            tier = self._parse_tier(user_preference)
            if self._can_afford_tier(tier, budget_remaining):
                return tier
            else:
                logger.warning(
                    f"User requested {tier} but budget insufficient, downgrading"
                )

        # If cache available and user didn't specify, use quick tier
        if cache_available and not user_preference:
            return CostTier.QUICK

        # Budget-based selection
        if budget_remaining is not None:
            if budget_remaining < 0.10:  # Less than $0.10
                return CostTier.QUICK
            elif budget_remaining < 1.00:  # Less than $1.00
                return CostTier.STANDARD

        # Complexity-based selection
        if query_complexity is not None:
            if query_complexity < 0.3:
                return CostTier.QUICK
            elif query_complexity < 0.7:
                return CostTier.STANDARD
            else:
                return CostTier.DEEP

        # Default to standard
        return CostTier.STANDARD

    def get_tier_config(self, tier: CostTier) -> TierConfig:
        """Get configuration for a specific tier."""
        return self.TIER_CONFIGS[tier]

    def predict_cost(
        self,
        tier: CostTier,
        query_length: int,
        use_cache: bool = False
    ) -> float:
        """
        Predict cost for a research query.

        Args:
            tier: Cost tier to use
            query_length: Length of query in characters
            use_cache: Whether result will come from cache

        Returns:
            Predicted cost in USD
        """
        if use_cache:
            return 0.0

        config = self.get_tier_config(tier)
        model_config = settings.get_model_config(config.model)

        # Estimate tokens (rough: 4 chars per token)
        estimated_input_tokens = query_length // 4
        estimated_output_tokens = config.max_tokens // 2  # Assume half max
        estimated_total_tokens = estimated_input_tokens + estimated_output_tokens

        # Calculate cost
        cost_per_1k = model_config["cost_per_1k_tokens"]
        base_cost = (estimated_total_tokens / 1000.0) * cost_per_1k

        return base_cost * config.cost_multiplier

    def should_use_cache(
        self,
        tier: CostTier,
        cache_age_seconds: Optional[int],
        budget_pressure: float = 0.0
    ) -> bool:
        """
        Determine if cache should be used based on tier and conditions.

        Args:
            tier: Cost tier
            cache_age_seconds: Age of cached result in seconds
            budget_pressure: Budget pressure (0.0-1.0, higher = more pressure)

        Returns:
            True if cache should be used
        """
        if cache_age_seconds is None:
            return False

        config = self.get_tier_config(tier)

        # Calculate cache freshness score (0.0-1.0)
        max_age_seconds = 7 * 24 * 60 * 60  # 7 days
        freshness = max(0.0, 1.0 - (cache_age_seconds / max_age_seconds))

        # Adjust threshold based on tier and budget pressure
        cache_threshold = config.cache_priority
        cache_threshold += budget_pressure * 0.2  # Increase threshold if budget tight

        return freshness >= cache_threshold

    async def check_budget_limits(
        self,
        db: Session,
        user_id: int,
        predicted_cost: float
    ) -> Dict[str, Any]:
        """
        Check if user has sufficient budget for predicted cost.

        Args:
            db: Database session
            user_id: User ID
            predicted_cost: Predicted cost for query

        Returns:
            Dict with budget status and limits
        """
        today = datetime.utcnow().date()

        # Get daily usage
        daily_cost = db.query(func.sum(CostTracking.cost)).filter(
            and_(
                CostTracking.user_id == user_id,
                func.date(CostTracking.date) == today
            )
        ).scalar() or 0.0

        # Get monthly usage
        month_start = datetime(today.year, today.month, 1)
        monthly_cost = db.query(func.sum(CostTracking.cost)).filter(
            and_(
                CostTracking.user_id == user_id,
                CostTracking.date >= month_start
            )
        ).scalar() or 0.0

        # Calculate remaining budgets
        daily_remaining = settings.MAX_DAILY_COST - daily_cost
        monthly_remaining = settings.MAX_MONTHLY_COST - monthly_cost

        # Check if predicted cost fits
        can_afford_daily = predicted_cost <= daily_remaining
        can_afford_monthly = predicted_cost <= monthly_remaining
        can_afford = can_afford_daily and can_afford_monthly

        # Calculate budget pressure (0.0-1.0)
        daily_pressure = daily_cost / settings.MAX_DAILY_COST
        monthly_pressure = monthly_cost / settings.MAX_MONTHLY_COST
        budget_pressure = max(daily_pressure, monthly_pressure)

        return {
            "can_afford": can_afford,
            "daily_used": daily_cost,
            "daily_remaining": daily_remaining,
            "daily_limit": settings.MAX_DAILY_COST,
            "monthly_used": monthly_cost,
            "monthly_remaining": monthly_remaining,
            "monthly_limit": settings.MAX_MONTHLY_COST,
            "predicted_cost": predicted_cost,
            "budget_pressure": budget_pressure,
            "warning": budget_pressure >= settings.COST_ALERT_THRESHOLD
        }

    def estimate_query_complexity(self, query: str) -> float:
        """
        Estimate query complexity (0.0-1.0).

        Simple heuristic based on:
        - Query length
        - Question complexity (multiple questions, nested clauses)
        - Technical terms

        Args:
            query: Research query

        Returns:
            Complexity score (0.0-1.0)
        """
        complexity = 0.0

        # Length factor (longer = more complex)
        length_factor = min(1.0, len(query) / 1000.0)
        complexity += length_factor * 0.3

        # Question complexity
        question_marks = query.count("?")
        if question_marks > 2:
            complexity += 0.2
        elif question_marks > 0:
            complexity += 0.1

        # Technical keywords
        technical_keywords = [
            "analysis", "compare", "evaluate", "synthesize", "investigate",
            "comprehensive", "detailed", "in-depth", "research", "examine"
        ]
        keyword_count = sum(1 for kw in technical_keywords if kw in query.lower())
        complexity += min(0.3, keyword_count * 0.1)

        # Conditional complexity
        conditional_words = ["if", "when", "unless", "provided", "assuming"]
        conditional_count = sum(1 for cw in conditional_words if cw in query.lower())
        complexity += min(0.2, conditional_count * 0.1)

        return min(1.0, complexity)

    async def get_usage_analytics(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get detailed usage analytics for cost optimization.

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Analytics data with recommendations
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get task statistics by tier
        tier_stats = db.query(
            ResearchTask.depth,
            func.count(ResearchTask.id).label("count"),
            func.sum(ResearchTask.cost).label("total_cost"),
            func.avg(ResearchTask.cost).label("avg_cost"),
            func.sum(ResearchTask.tokens_used).label("total_tokens")
        ).filter(
            and_(
                ResearchTask.user_id == user_id,
                ResearchTask.created_at >= start_date,
                ResearchTask.status == "completed"
            )
        ).group_by(ResearchTask.depth).all()

        # Get cache hit rate
        total_tasks = db.query(func.count(ResearchTask.id)).filter(
            and_(
                ResearchTask.user_id == user_id,
                ResearchTask.created_at >= start_date
            )
        ).scalar() or 0

        cached_tasks = db.query(func.count(ResearchTask.id)).filter(
            and_(
                ResearchTask.user_id == user_id,
                ResearchTask.created_at >= start_date,
                ResearchTask.cost == 0.0  # Cache hits have zero cost
            )
        ).scalar() or 0

        cache_hit_rate = (cached_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

        # Calculate savings from cache
        avg_cost_per_tier = {
            stat.depth: float(stat.avg_cost) if stat.avg_cost else 0.0
            for stat in tier_stats
        }
        avg_cost = sum(avg_cost_per_tier.values()) / len(avg_cost_per_tier) if avg_cost_per_tier else 0.05
        estimated_savings = cached_tasks * avg_cost

        # Build tier breakdown
        tier_breakdown = {}
        for stat in tier_stats:
            tier_breakdown[stat.depth] = {
                "count": stat.count,
                "total_cost": float(stat.total_cost or 0.0),
                "avg_cost": float(stat.avg_cost or 0.0),
                "total_tokens": stat.total_tokens or 0,
                "percentage": (stat.count / total_tasks * 100) if total_tasks > 0 else 0.0
            }

        # Generate recommendations
        recommendations = self._generate_recommendations(
            tier_breakdown, cache_hit_rate, total_tasks
        )

        return {
            "period_days": days,
            "total_tasks": total_tasks,
            "cached_tasks": cached_tasks,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "estimated_savings": round(estimated_savings, 4),
            "tier_breakdown": tier_breakdown,
            "recommendations": recommendations,
            "period_start": start_date.isoformat(),
            "period_end": datetime.utcnow().isoformat()
        }

    def _generate_recommendations(
        self,
        tier_breakdown: Dict[str, Any],
        cache_hit_rate: float,
        total_tasks: int
    ) -> List[str]:
        """Generate cost optimization recommendations."""
        recommendations = []

        # Cache recommendations
        if cache_hit_rate < 30 and total_tasks > 10:
            recommendations.append(
                "Low cache hit rate detected. Consider using more specific queries "
                "or enabling longer cache TTL to improve cost efficiency."
            )
        elif cache_hit_rate > 70:
            recommendations.append(
                "Excellent cache usage! You're saving significantly on API costs."
            )

        # Tier usage recommendations
        deep_usage = tier_breakdown.get("deep", {}).get("percentage", 0)
        if deep_usage > 50:
            recommendations.append(
                "High usage of Deep tier detected. Consider if Standard tier "
                "could meet your needs for some queries to reduce costs."
            )

        quick_usage = tier_breakdown.get("quick", {}).get("percentage", 0)
        if quick_usage < 20 and total_tasks > 20:
            recommendations.append(
                "Consider using Quick tier for simple queries to optimize costs. "
                "It's 3x more cost-effective for straightforward research."
            )

        # General recommendations
        if total_tasks < 10:
            recommendations.append(
                "Limited usage history. Continue using the service to get "
                "personalized cost optimization recommendations."
            )

        if not recommendations:
            recommendations.append(
                "Your usage patterns look optimal. Keep up the balanced approach!"
            )

        return recommendations

    def _parse_tier(self, tier_str: str) -> CostTier:
        """Parse tier string to enum."""
        tier_map = {
            "quick": CostTier.QUICK,
            "standard": CostTier.STANDARD,
            "deep": CostTier.DEEP
        }
        return tier_map.get(tier_str.lower(), CostTier.STANDARD)

    def _can_afford_tier(
        self,
        tier: CostTier,
        budget_remaining: Optional[float]
    ) -> bool:
        """Check if user can afford a specific tier."""
        if budget_remaining is None:
            return True

        config = self.get_tier_config(tier)
        estimated_cost = 0.05 * config.cost_multiplier  # Rough estimate

        return budget_remaining >= estimated_cost

    def get_tier_comparison(self) -> Dict[str, Any]:
        """
        Get comparison of all tiers for user decision-making.

        Returns:
            Dict with tier comparison data
        """
        comparison = {}

        for tier, config in self.TIER_CONFIGS.items():
            model_config = settings.get_model_config(config.model)

            comparison[tier.value] = {
                "name": config.name,
                "model": config.model,
                "description": config.description,
                "max_tokens": config.max_tokens,
                "cost_per_1k_tokens": model_config["cost_per_1k_tokens"],
                "relative_cost": config.cost_multiplier,
                "cache_priority": config.cache_priority,
                "best_for": self._get_best_use_case(tier)
            }

        return comparison

    def _get_best_use_case(self, tier: CostTier) -> str:
        """Get best use case description for a tier."""
        use_cases = {
            CostTier.QUICK: "Simple questions, fact-checking, quick lookups",
            CostTier.STANDARD: "General research, article analysis, typical queries",
            CostTier.DEEP: "Complex analysis, comprehensive reports, multi-topic research"
        }
        return use_cases[tier]


# Global optimizer instance
cost_optimizer = CostOptimizer()
