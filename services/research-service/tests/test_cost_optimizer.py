"""Tests for cost optimizer service."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.cost_optimizer import (
    cost_optimizer,
    CostOptimizer,
    CostTier,
    TierConfig
)
from app.models.research import ResearchTask, CostTracking
from app.core.config import settings


# ========== Module-level fixtures ==========

@pytest.fixture
def optimizer():
    """Create optimizer instance."""
    return CostOptimizer()


class TestCostTier:
    """Test CostTier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert CostTier.QUICK.value == "quick"
        assert CostTier.STANDARD.value == "standard"
        assert CostTier.DEEP.value == "deep"


class TestTierConfig:
    """Test TierConfig dataclass."""

    def test_tier_config_creation(self):
        """Test creating tier configuration."""
        config = TierConfig(
            name="Test",
            model="sonar",
            cache_priority=0.8,
            max_tokens=2000,
            temperature=0.3,
            recency_filter="day",
            cost_multiplier=1.0,
            description="Test config"
        )

        assert config.name == "Test"
        assert config.model == "sonar"
        assert config.cache_priority == 0.8
        assert config.max_tokens == 2000
        assert config.temperature == 0.3
        assert config.recency_filter == "day"
        assert config.cost_multiplier == 1.0
        assert config.description == "Test config"


class TestCostOptimizer:
    """Test CostOptimizer class."""

    def test_tier_configs_exist(self, optimizer):
        """Test that all tier configurations exist."""
        assert CostTier.QUICK in optimizer.TIER_CONFIGS
        assert CostTier.STANDARD in optimizer.TIER_CONFIGS
        assert CostTier.DEEP in optimizer.TIER_CONFIGS

    def test_get_tier_config(self, optimizer):
        """Test getting tier configuration."""
        config = optimizer.get_tier_config(CostTier.QUICK)
        assert isinstance(config, TierConfig)
        assert config.name == "Quick"
        assert config.model == "sonar"
        assert config.cache_priority == 0.9

        config = optimizer.get_tier_config(CostTier.DEEP)
        assert config.name == "Deep"
        assert config.model == "sonar-pro"
        assert config.cache_priority == 0.3

    def test_select_tier_user_preference(self, optimizer):
        """Test tier selection with user preference."""
        tier = optimizer.select_tier(user_preference="deep")
        assert tier == CostTier.DEEP

        tier = optimizer.select_tier(user_preference="quick")
        assert tier == CostTier.QUICK

    def test_select_tier_cache_available(self, optimizer):
        """Test tier selection with cache available."""
        tier = optimizer.select_tier(cache_available=True)
        assert tier == CostTier.QUICK

    def test_select_tier_complexity(self, optimizer):
        """Test tier selection based on query complexity."""
        tier = optimizer.select_tier(query_complexity=0.2)
        assert tier == CostTier.QUICK

        tier = optimizer.select_tier(query_complexity=0.5)
        assert tier == CostTier.STANDARD

        tier = optimizer.select_tier(query_complexity=0.8)
        assert tier == CostTier.DEEP

    def test_select_tier_budget(self, optimizer):
        """Test tier selection based on budget."""
        tier = optimizer.select_tier(budget_remaining=0.05)
        assert tier == CostTier.QUICK

        tier = optimizer.select_tier(budget_remaining=0.50)
        assert tier == CostTier.STANDARD

        tier = optimizer.select_tier(budget_remaining=5.00)
        assert tier == CostTier.STANDARD  # Default when no constraints

    def test_predict_cost_with_cache(self, optimizer):
        """Test cost prediction with cache."""
        cost = optimizer.predict_cost(CostTier.QUICK, 100, use_cache=True)
        assert cost == 0.0

    def test_predict_cost_without_cache(self, optimizer):
        """Test cost prediction without cache."""
        cost = optimizer.predict_cost(CostTier.QUICK, 400, use_cache=False)
        assert cost > 0.0

        # Deep tier should cost more than quick
        quick_cost = optimizer.predict_cost(CostTier.QUICK, 400, use_cache=False)
        deep_cost = optimizer.predict_cost(CostTier.DEEP, 400, use_cache=False)
        assert deep_cost > quick_cost

    def test_should_use_cache_fresh(self, optimizer):
        """Test cache usage decision with fresh cache."""
        # Fresh cache (10 seconds old)
        should_use = optimizer.should_use_cache(
            CostTier.QUICK,
            cache_age_seconds=10,
            budget_pressure=0.0
        )
        assert should_use is True

    def test_should_use_cache_old(self, optimizer):
        """Test cache usage decision with old cache."""
        # Old cache (8 days old) with low priority tier
        should_use = optimizer.should_use_cache(
            CostTier.DEEP,
            cache_age_seconds=8 * 24 * 60 * 60,
            budget_pressure=0.0
        )
        assert should_use is False

    def test_should_use_cache_budget_pressure(self, optimizer):
        """Test cache usage with high budget pressure."""
        # High budget pressure should increase cache usage
        should_use = optimizer.should_use_cache(
            CostTier.DEEP,
            cache_age_seconds=5 * 24 * 60 * 60,  # 5 days
            budget_pressure=0.9
        )
        # With high budget pressure, even deep tier prefers cache
        assert should_use is True

    def test_estimate_query_complexity_simple(self, optimizer):
        """Test complexity estimation for simple query."""
        query = "What is the weather?"
        complexity = optimizer.estimate_query_complexity(query)
        assert 0.0 <= complexity <= 1.0
        assert complexity < 0.5  # Simple query

    def test_estimate_query_complexity_complex(self, optimizer):
        """Test complexity estimation for complex query."""
        query = """
        Provide a comprehensive analysis of the economic impacts of climate change
        on developing nations, comparing the effects across different regions,
        and evaluate potential mitigation strategies. What are the long-term
        implications if current trends continue? How do experts assess the
        feasibility of various intervention approaches?
        """
        complexity = optimizer.estimate_query_complexity(query)
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.5  # Complex query

    def test_estimate_query_complexity_technical(self, optimizer):
        """Test complexity estimation for technical query."""
        query = "Analyze and synthesize research on machine learning approaches"
        complexity = optimizer.estimate_query_complexity(query)
        assert complexity > 0.3  # Contains technical keywords

    @pytest.mark.asyncio
    async def test_check_budget_limits_within_limits(self, optimizer, db_session, test_user):
        """Test budget check when within limits."""
        # No usage yet
        budget_status = await optimizer.check_budget_limits(
            db_session,
            test_user.id,
            predicted_cost=0.10
        )

        assert budget_status["can_afford"] is True
        assert budget_status["daily_used"] == 0.0
        assert budget_status["monthly_used"] == 0.0
        assert budget_status["budget_pressure"] < 0.1

    @pytest.mark.asyncio
    async def test_check_budget_limits_exceeds_daily(self, optimizer, db_session, test_user):
        """Test budget check when exceeding daily limit."""
        # Add cost tracking entries that exceed daily limit
        today = datetime.utcnow()
        for i in range(5):
            cost_entry = CostTracking(
                user_id=test_user.id,
                model_name="sonar",
                tokens_used=10000,
                cost=settings.MAX_DAILY_COST / 5,
                date=today
            )
            db_session.add(cost_entry)
        db_session.commit()

        budget_status = await optimizer.check_budget_limits(
            db_session,
            test_user.id,
            predicted_cost=0.10
        )

        assert budget_status["can_afford"] is False
        assert budget_status["daily_used"] >= settings.MAX_DAILY_COST
        assert budget_status["budget_pressure"] >= 0.9

    @pytest.mark.asyncio
    async def test_check_budget_limits_approaching_limit(self, optimizer, db_session, test_user):
        """Test budget check when approaching limit."""
        # Add cost tracking entries approaching limit
        today = datetime.utcnow()
        cost_entry = CostTracking(
            user_id=test_user.id,
            model_name="sonar",
            tokens_used=10000,
            cost=settings.MAX_DAILY_COST * 0.85,
            date=today
        )
        db_session.add(cost_entry)
        db_session.commit()

        budget_status = await optimizer.check_budget_limits(
            db_session,
            test_user.id,
            predicted_cost=0.10
        )

        assert budget_status["can_afford"] is True
        assert budget_status["warning"] is True
        assert budget_status["budget_pressure"] >= settings.COST_ALERT_THRESHOLD

    @pytest.mark.asyncio
    async def test_get_usage_analytics_no_usage(self, optimizer, db_session, test_user):
        """Test analytics with no usage."""
        analytics = await optimizer.get_usage_analytics(
            db_session,
            test_user.id,
            days=30
        )

        assert analytics["total_tasks"] == 0
        assert analytics["cached_tasks"] == 0
        assert analytics["cache_hit_rate"] == 0.0
        assert "recommendations" in analytics
        assert len(analytics["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_get_usage_analytics_with_usage(self, optimizer, db_session, test_user):
        """Test analytics with usage data."""
        # Create research tasks
        for i in range(10):
            task = ResearchTask(
                user_id=test_user.id,
                query=f"Test query {i}",
                model_name="sonar",
                depth="standard",
                status="completed",
                cost=0.05 if i < 3 else 0.10,  # 3 cached, 7 not cached
                tokens_used=0 if i < 3 else 1000,
                completed_at=datetime.utcnow()
            )
            db_session.add(task)
        db_session.commit()

        analytics = await optimizer.get_usage_analytics(
            db_session,
            test_user.id,
            days=30
        )

        assert analytics["total_tasks"] == 10
        assert analytics["cached_tasks"] == 3
        assert analytics["cache_hit_rate"] == 30.0
        assert "tier_breakdown" in analytics
        assert "recommendations" in analytics

    def test_get_tier_comparison(self, optimizer):
        """Test tier comparison data."""
        comparison = optimizer.get_tier_comparison()

        assert "quick" in comparison
        assert "standard" in comparison
        assert "deep" in comparison

        # Check quick tier data
        quick = comparison["quick"]
        assert quick["name"] == "Quick"
        assert quick["model"] == "sonar"
        assert quick["relative_cost"] == 1.0
        assert "description" in quick
        assert "best_for" in quick

        # Check deep tier data
        deep = comparison["deep"]
        assert deep["name"] == "Deep"
        assert deep["model"] == "sonar-pro"
        assert deep["relative_cost"] == 3.0

    def test_parse_tier(self, optimizer):
        """Test tier string parsing."""
        assert optimizer._parse_tier("quick") == CostTier.QUICK
        assert optimizer._parse_tier("STANDARD") == CostTier.STANDARD
        assert optimizer._parse_tier("Deep") == CostTier.DEEP
        assert optimizer._parse_tier("invalid") == CostTier.STANDARD  # Default

    def test_can_afford_tier(self, optimizer):
        """Test tier affordability check."""
        # Can afford with sufficient budget
        assert optimizer._can_afford_tier(CostTier.QUICK, 1.0) is True
        assert optimizer._can_afford_tier(CostTier.STANDARD, 1.0) is True

        # Cannot afford with insufficient budget
        assert optimizer._can_afford_tier(CostTier.DEEP, 0.05) is False

        # No budget limit (None)
        assert optimizer._can_afford_tier(CostTier.DEEP, None) is True


class TestCostOptimizerIntegration:
    """Integration tests for cost optimizer."""

    @pytest.mark.asyncio
    async def test_full_optimization_flow(self, optimizer, db_session, test_user):
        """Test complete optimization flow."""
        # 1. Estimate query complexity
        query = "Perform comprehensive analysis of AI ethics"
        complexity = optimizer.estimate_query_complexity(query)
        assert complexity > 0.0

        # 2. Predict cost
        predicted_cost = optimizer.predict_cost(
            CostTier.STANDARD,
            len(query),
            use_cache=False
        )
        assert predicted_cost > 0.0

        # 3. Check budget
        budget_status = await optimizer.check_budget_limits(
            db_session,
            test_user.id,
            predicted_cost
        )
        assert budget_status["can_afford"] is True

        # 4. Select optimal tier
        tier = optimizer.select_tier(
            user_preference="standard",
            query_complexity=complexity,
            budget_remaining=budget_status["daily_remaining"],
            cache_available=False
        )
        assert tier in [CostTier.QUICK, CostTier.STANDARD, CostTier.DEEP]

    @pytest.mark.asyncio
    async def test_optimization_with_budget_constraint(self, optimizer, db_session, test_user):
        """Test optimization adjusts tier based on budget."""
        # Create high usage
        today = datetime.utcnow()
        cost_entry = CostTracking(
            user_id=test_user.id,
            model_name="sonar",
            tokens_used=100000,
            cost=settings.MAX_DAILY_COST * 0.95,
            date=today
        )
        db_session.add(cost_entry)
        db_session.commit()

        # Select tier with tight budget
        tier = optimizer.select_tier(
            user_preference="deep",
            budget_remaining=0.50,
            cache_available=False
        )

        # Should downgrade from deep
        assert tier != CostTier.DEEP

    def test_recommendations_quality(self, optimizer):
        """Test that recommendations are helpful."""
        # Low cache hit rate
        recommendations = optimizer._generate_recommendations(
            tier_breakdown={
                "standard": {"percentage": 100.0}
            },
            cache_hit_rate=15.0,
            total_tasks=50
        )
        assert len(recommendations) > 0
        assert any("cache" in r.lower() for r in recommendations)

        # High deep tier usage
        recommendations = optimizer._generate_recommendations(
            tier_breakdown={
                "deep": {"percentage": 70.0}
            },
            cache_hit_rate=40.0,
            total_tasks=50
        )
        assert any("deep tier" in r.lower() or "standard tier" in r.lower() for r in recommendations)


# Fixtures for tests
@pytest.fixture
def db_session(request):
    """Create test database session."""
    from app.core.database import SessionLocal, Base, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    def teardown():
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)

    request.addfinalizer(teardown)
    return session


@pytest.fixture
def test_user(db_session):
    """Create test user (mock)."""
    from dataclasses import dataclass

    @dataclass
    class TestUser:
        id: int = 1
        email: str = "test@example.com"

    return TestUser()
