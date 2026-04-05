"""
Tests for research service business logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.research import ResearchService, TemplateService
from app.models.research import ResearchTask, ResearchTemplate


class TestResearchService:
    """Tests for ResearchService."""

    @pytest.mark.asyncio
    async def test_create_research_task_success(
        self, db_session, test_user_id, mock_perplexity_client, disable_cost_tracking
    ):
        """Test successful research task creation."""
        service = ResearchService()

        task = await service.create_research_task(
            db=db_session,
            user_id=test_user_id,
            query="What is AI?",
            model_name="sonar",
            depth="standard"
        )

        assert task.id is not None
        assert task.user_id == test_user_id
        assert task.query == "What is AI?"
        assert task.status == "completed"
        assert task.result is not None
        assert task.tokens_used > 0

    @pytest.mark.asyncio
    async def test_create_task_with_caching(
        self, db_session, test_user_id, mock_redis, mock_perplexity_client, disable_cost_tracking
    ):
        """Test task creation with cache hit."""
        service = ResearchService()
        service.redis_client = mock_redis

        # Mock cache hit
        import json
        cached_data = {
            "result": {"content": "Cached result"},
            "tokens_used": 1000,
            "cost": 0.005
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        task = await service.create_research_task(
            db=db_session,
            user_id=test_user_id,
            query="Cached query",
            model_name="sonar",
            depth="standard"
        )

        assert task.status == "completed"
        assert task.tokens_used == 0  # No new tokens for cached result
        assert task.cost == 0.0

    @pytest.mark.asyncio
    async def test_create_task_cost_limit_exceeded(
        self, db_session, test_user_id
    ):
        """Test task creation when cost limit exceeded."""
        from app.models.research import CostTracking

        # Add high cost entries for today
        for i in range(5):
            entry = CostTracking(
                user_id=test_user_id,
                date=datetime.utcnow(),
                model_name="sonar",
                tokens_used=10000,
                cost=10.0
            )
            db_session.add(entry)
        db_session.commit()

        service = ResearchService()

        with pytest.raises(ValueError, match="Daily cost limit exceeded"):
            await service.create_research_task(
                db=db_session,
                user_id=test_user_id,
                query="Test query",
                model_name="sonar"
            )

    @pytest.mark.asyncio
    async def test_get_task_success(
        self, db_session, test_user_id, sample_research_task
    ):
        """Test getting a task."""
        service = ResearchService()

        task = await service.get_task(
            db=db_session,
            task_id=sample_research_task.id,
            user_id=test_user_id
        )

        assert task is not None
        assert task.id == sample_research_task.id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, db_session, test_user_id):
        """Test getting nonexistent task."""
        service = ResearchService()

        task = await service.get_task(
            db=db_session,
            task_id=uuid4(),
            user_id=test_user_id
        )

        assert task is None

    @pytest.mark.asyncio
    async def test_list_tasks(
        self, db_session, test_user_id, sample_research_task
    ):
        """Test listing tasks."""
        service = ResearchService()

        tasks, total = await service.list_tasks(
            db=db_session,
            user_id=test_user_id
        )

        assert total >= 1
        assert len(tasks) >= 1
        assert any(t.id == sample_research_task.id for t in tasks)

    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(
        self, db_session, test_user_id
    ):
        """Test listing tasks with filters."""
        # Create multiple tasks
        feed_uuid = uuid4()
        for i in range(3):
            task = ResearchTask(
                user_id=test_user_id,
                query=f"Query {i}",
                model_name="sonar",
                depth="standard",
                status="completed",
                feed_id=feed_uuid if i == 0 else None
            )
            db_session.add(task)
        db_session.commit()

        service = ResearchService()

        # Filter by status
        tasks, total = await service.list_tasks(
            db=db_session,
            user_id=test_user_id,
            status="completed"
        )
        assert all(t.status == "completed" for t in tasks)

        # Filter by feed_id
        tasks, total = await service.list_tasks(
            db=db_session,
            user_id=test_user_id,
            feed_id=feed_uuid
        )
        assert all(t.feed_id == feed_uuid for t in tasks)

    @pytest.mark.asyncio
    async def test_get_usage_stats(
        self, db_session, test_user_id, sample_cost_tracking
    ):
        """Test getting usage statistics."""
        service = ResearchService()

        stats = await service.get_usage_stats(
            db=db_session,
            user_id=test_user_id,
            days=30
        )

        assert stats["total_requests"] >= 5
        assert stats["total_tokens"] > 0
        assert stats["total_cost"] > 0
        assert "requests_by_model" in stats
        assert "cost_by_model" in stats

    def test_generate_cache_key(self):
        """Test cache key generation."""
        service = ResearchService()

        key1 = service._generate_cache_key("query1", "sonar", "standard")
        key2 = service._generate_cache_key("query1", "sonar", "standard")
        key3 = service._generate_cache_key("query2", "sonar", "standard")

        assert key1 == key2  # Same inputs produce same key
        assert key1 != key3  # Different inputs produce different keys
        assert len(key1) == 64  # SHA256 hash


class TestTemplateService:
    """Tests for TemplateService."""

    @pytest.mark.asyncio
    async def test_create_template_success(self, db_session, test_user_id):
        """Test successful template creation."""
        service = TemplateService()

        template = await service.create_template(
            db=db_session,
            user_id=test_user_id,
            template_data={
                "name": "Test Template",
                "description": "Test description",
                "query_template": "Research {{topic}}",
                "parameters": {"topic": "string"},
                "default_model": "sonar",
                "default_depth": "standard"
            }
        )

        assert template.id is not None
        assert template.name == "Test Template"
        assert template.query_template == "Research {{topic}}"
        assert template.is_active is True

    @pytest.mark.asyncio
    async def test_create_template_limit_exceeded(self, db_session, test_user_id):
        """Test template creation when limit exceeded."""
        service = TemplateService()

        # Create max templates
        from app.core.config import settings
        for i in range(settings.MAX_TEMPLATES_PER_USER):
            template = ResearchTemplate(
                user_id=test_user_id,
                name=f"Template {i}",
                query_template="Test {{var}}",
                parameters={},
                default_model="sonar",
                default_depth="standard",
                is_active=True
            )
            db_session.add(template)
        db_session.commit()

        with pytest.raises(ValueError, match="Maximum templates limit reached"):
            await service.create_template(
                db=db_session,
                user_id=test_user_id,
                template_data={
                    "name": "Exceeded Template",
                    "query_template": "Test {{var}}"
                }
            )

    @pytest.mark.asyncio
    async def test_get_template_success(
        self, db_session, test_user_id, sample_template
    ):
        """Test getting a template."""
        service = TemplateService()

        template = await service.get_template(
            db=db_session,
            template_id=sample_template.id,
            user_id=test_user_id
        )

        assert template is not None
        assert template.id == sample_template.id

    @pytest.mark.asyncio
    async def test_list_templates(
        self, db_session, test_user_id, sample_template
    ):
        """Test listing templates."""
        service = TemplateService()

        templates = await service.list_templates(
            db=db_session,
            user_id=test_user_id
        )

        assert len(templates) >= 1
        assert any(t.id == sample_template.id for t in templates)

    @pytest.mark.asyncio
    async def test_apply_template(
        self, db_session, test_user_id, sample_template
    ):
        """Test applying a template."""
        service = TemplateService()

        rendered = await service.apply_template(
            db=db_session,
            template=sample_template,
            variables={
                "topic": "artificial intelligence",
                "aspect": "ethics"
            }
        )

        assert "artificial intelligence" in rendered
        assert "ethics" in rendered
        assert "{{topic}}" not in rendered
        assert "{{aspect}}" not in rendered

        # Check usage count updated
        db_session.refresh(sample_template)
        assert sample_template.usage_count == 1
        assert sample_template.last_used_at is not None

    @pytest.mark.asyncio
    async def test_apply_template_missing_variables(
        self, db_session, test_user_id, sample_template
    ):
        """Test applying template with missing variables."""
        service = TemplateService()

        rendered = await service.apply_template(
            db=db_session,
            template=sample_template,
            variables={"topic": "AI"}  # Missing 'aspect'
        )

        assert "AI" in rendered
        assert "{{aspect}}" in rendered  # Placeholder remains
