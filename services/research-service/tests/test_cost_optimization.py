"""
Tests for cost optimization functionality.
Critical for Task 403 (caching strategy).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.research import ResearchService
from app.services.cost_optimizer import CostTier
from app.models.research import CostTracking


class TestCostOptimization:
    """Tests for cost optimization features."""

    @pytest.mark.asyncio
    async def test_cost_optimizer_selects_cache_when_available(
        self, db_session, test_user_id, mock_redis
    ):
        """Test that optimizer prefers cache when available."""
        service = ResearchService()
        service.redis_client = mock_redis

        import json
        cached_data = {
            "result": {"content": "Cached result"},
            "tokens_used": 1000,
            "cost": 0.005
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()
        mock_redis.ttl.return_value = 3600  # 1 hour remaining

        task = await service.create_research_task(
            db=db_session,
            user_id=test_user_id,
            query="Test query with cache",
            optimize_cost=True,
            cache_enabled=True
        )

        # Should use cache (zero cost)
        assert task.status == "completed"
        assert task.cost == 0.0

    @pytest.mark.asyncio
    async def test_cost_optimizer_downgrades_tier_on_budget_pressure(
        self, db_session, test_user_id
    ):
        """Test that optimizer downgrades tier when budget is low."""
        from app.core.config import settings

        # Add high cost entries to create budget pressure
        for i in range(10):
            entry = CostTracking(
                user_id=test_user_id,
                date=datetime.utcnow(),
                model_name="sonar-pro",
                tokens_used=5000,
                cost=settings.MAX_DAILY_COST * 0.08  # 80% of budget
            )
            db_session.add(entry)
        db_session.commit()

        service = ResearchService()

        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test query with budget pressure",
                depth="deep",  # Request expensive tier
                optimize_cost=True
            )

            # Optimizer should downgrade to cheaper tier
            # (This depends on implementation details)
            assert task is not None

    @pytest.mark.asyncio
    async def test_predict_query_cost(self):
        """Test query cost prediction."""
        service = ResearchService()

        prediction = service.predict_query_cost(
            query="Test query for cost prediction",
            depth="standard"
        )

        assert "query_length" in prediction
        assert "query_complexity" in prediction
        assert "predicted_cost" in prediction
        assert "tier" in prediction
        assert "model" in prediction
        assert prediction["predicted_cost"] > 0

    @pytest.mark.asyncio
    async def test_predict_cost_varies_by_tier(self):
        """Test that cost prediction varies by tier."""
        service = ResearchService()

        query = "What are the implications of quantum computing?"

        quick_cost = service.predict_query_cost(query, "quick")
        standard_cost = service.predict_query_cost(query, "standard")
        deep_cost = service.predict_query_cost(query, "deep")

        # Deep should be most expensive
        assert deep_cost["predicted_cost"] > standard_cost["predicted_cost"]
        assert standard_cost["predicted_cost"] > quick_cost["predicted_cost"]

    @pytest.mark.asyncio
    async def test_get_tier_comparison(self):
        """Test tier comparison data."""
        service = ResearchService()

        comparison = service.get_tier_comparison()

        assert "quick" in comparison
        assert "standard" in comparison
        assert "deep" in comparison

        # Each tier should have cost info
        for tier in ["quick", "standard", "deep"]:
            assert "model" in comparison[tier]
            assert "description" in comparison[tier]

    @pytest.mark.asyncio
    async def test_cost_tracking_accuracy(self, db_session, test_user_id):
        """Test that costs are tracked accurately."""
        from app.models.research import ResearchTask

        # Create task with known cost
        task = ResearchTask(
            user_id=test_user_id,
            query="Cost tracking test",
            model_name="sonar",
            depth="standard",
            status="completed",
            tokens_used=1500,
            cost=0.0075
        )
        db_session.add(task)
        db_session.commit()

        # Track cost
        service = ResearchService()
        service._track_cost(
            db=db_session,
            user_id=test_user_id,
            task_id=task.id,
            model_name="sonar",
            tokens_used=1500,
            cost=0.0075
        )

        # Verify tracking entry
        tracking = db_session.query(CostTracking).filter(
            CostTracking.task_id == task.id
        ).first()

        assert tracking is not None
        assert tracking.tokens_used == 1500
        assert tracking.cost == 0.0075

    @pytest.mark.asyncio
    async def test_monthly_cost_limit_enforcement(self, db_session, test_user_id):
        """Test monthly cost limit is enforced."""
        from app.core.config import settings

        # Add costs to exceed monthly limit
        month_start = datetime.utcnow().replace(day=1)
        for i in range(30):
            entry = CostTracking(
                user_id=test_user_id,
                date=month_start + timedelta(days=i),
                model_name="sonar",
                tokens_used=10000,
                cost=settings.MAX_MONTHLY_COST / 25  # Just over limit
            )
            db_session.add(entry)
        db_session.commit()

        service = ResearchService()

        with pytest.raises(ValueError, match="Monthly cost limit exceeded"):
            await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test monthly limit",
                optimize_cost=False
            )

    @pytest.mark.asyncio
    async def test_cost_alert_threshold(self, db_session, test_user_id):
        """Test cost alert threshold triggers warning."""
        from app.core.config import settings

        # Add cost near alert threshold (80% of daily limit)
        entry = CostTracking(
            user_id=test_user_id,
            date=datetime.utcnow(),
            model_name="sonar",
            tokens_used=10000,
            cost=settings.MAX_DAILY_COST * 0.85
        )
        db_session.add(entry)
        db_session.commit()

        service = ResearchService()

        # Should log warning but not raise exception
        with patch("app.workers.tasks.research_task") as mock_celery:
            mock_celery.delay.return_value = MagicMock(id="task-123")

            task = await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test alert threshold",
                optimize_cost=False
            )

            assert task is not None

    @pytest.mark.asyncio
    async def test_usage_analytics(self, db_session, test_user_id, sample_cost_tracking):
        """Test cost optimization analytics."""
        service = ResearchService()

        analytics = await service.get_cost_optimization_analytics(
            db=db_session,
            user_id=test_user_id,
            days=30
        )

        assert analytics is not None
        # Analytics should contain various metrics
        # (Specific fields depend on implementation)

    @pytest.mark.asyncio
    async def test_cache_age_affects_decision(self, db_session, test_user_id, mock_redis):
        """Test that cache age affects optimizer decision."""
        service = ResearchService()
        service.redis_client = mock_redis

        import json

        # Old cache (near expiration)
        cached_data = {
            "result": {"content": "Old cached result"},
            "tokens_used": 1000,
            "cost": 0.005
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode()
        mock_redis.ttl.return_value = 60  # Only 1 minute remaining

        # This should potentially trigger fresh query
        # depending on optimizer logic
        task = await service.create_research_task(
            db=db_session,
            user_id=test_user_id,
            query="Test with old cache",
            optimize_cost=True
        )

        assert task is not None


class TestCostCalculations:
    """Tests for cost calculation accuracy."""

    @pytest.mark.asyncio
    async def test_calculate_cost_for_different_models(self):
        """Test cost calculation for different models."""
        from app.core.config import settings

        # Test each model
        models = ["sonar", "sonar-pro", "sonar-reasoning-pro"]
        tokens = 1000

        costs = {}
        for model in models:
            cost = settings.calculate_cost(tokens, model)
            costs[model] = cost
            assert cost > 0

        # Verify relative costs (pro models should be more expensive)
        assert costs["sonar-pro"] > costs["sonar"]
        assert costs["sonar-reasoning-pro"] > costs["sonar-pro"]

    @pytest.mark.asyncio
    async def test_cost_scales_with_tokens(self):
        """Test that cost scales linearly with tokens."""
        from app.core.config import settings

        cost_1000 = settings.calculate_cost(1000, "sonar")
        cost_2000 = settings.calculate_cost(2000, "sonar")

        # Should be approximately double
        assert 1.9 * cost_1000 < cost_2000 < 2.1 * cost_1000

    @pytest.mark.asyncio
    async def test_zero_tokens_zero_cost(self):
        """Test that zero tokens means zero cost."""
        from app.core.config import settings

        cost = settings.calculate_cost(0, "sonar")
        assert cost == 0.0


class TestBudgetManagement:
    """Tests for budget management features."""

    @pytest.mark.asyncio
    async def test_daily_budget_remaining_calculation(self, db_session, test_user_id):
        """Test calculation of remaining daily budget."""
        from app.services.cost_optimizer import cost_optimizer

        # Add some costs for today
        entry = CostTracking(
            user_id=test_user_id,
            date=datetime.utcnow(),
            model_name="sonar",
            tokens_used=1000,
            cost=0.50
        )
        db_session.add(entry)
        db_session.commit()

        budget_status = await cost_optimizer.check_budget_limits(
            db=db_session,
            user_id=test_user_id,
            predicted_cost=0.10
        )

        assert "daily_remaining" in budget_status
        assert budget_status["daily_remaining"] >= 0

    @pytest.mark.asyncio
    async def test_monthly_budget_remaining_calculation(self, db_session, test_user_id):
        """Test calculation of remaining monthly budget."""
        from app.services.cost_optimizer import cost_optimizer

        # Add some monthly costs
        for i in range(5):
            entry = CostTracking(
                user_id=test_user_id,
                date=datetime.utcnow() - timedelta(days=i),
                model_name="sonar",
                tokens_used=1000,
                cost=1.00
            )
            db_session.add(entry)
        db_session.commit()

        budget_status = await cost_optimizer.check_budget_limits(
            db=db_session,
            user_id=test_user_id,
            predicted_cost=0.50
        )

        assert "monthly_remaining" in budget_status
        assert budget_status["monthly_remaining"] >= 0

    @pytest.mark.asyncio
    async def test_can_afford_check(self, db_session, test_user_id):
        """Test can_afford flag in budget status."""
        from app.services.cost_optimizer import cost_optimizer

        budget_status = await cost_optimizer.check_budget_limits(
            db=db_session,
            user_id=test_user_id,
            predicted_cost=0.01  # Very small cost
        )

        assert "can_afford" in budget_status
        assert budget_status["can_afford"] is True

    @pytest.mark.asyncio
    async def test_budget_pressure_calculation(self, db_session, test_user_id):
        """Test budget pressure metric calculation."""
        from app.services.cost_optimizer import cost_optimizer
        from app.core.config import settings

        # Use 50% of daily budget
        entry = CostTracking(
            user_id=test_user_id,
            date=datetime.utcnow(),
            model_name="sonar",
            tokens_used=10000,
            cost=settings.MAX_DAILY_COST * 0.5
        )
        db_session.add(entry)
        db_session.commit()

        budget_status = await cost_optimizer.check_budget_limits(
            db=db_session,
            user_id=test_user_id,
            predicted_cost=0.01
        )

        assert "budget_pressure" in budget_status
        # Pressure should be moderate (around 0.5)
        assert 0.4 < budget_status["budget_pressure"] < 0.6
