"""
Tests for database models.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.research import ResearchTask, ResearchTemplate, ResearchCache, CostTracking


class TestResearchTaskModel:
    """Tests for ResearchTask model."""

    def test_create_research_task(self, db_session, test_user_id):
        """Test creating a research task."""
        task = ResearchTask(
            user_id=test_user_id,
            query="What is AI?",
            model_name="sonar",
            depth="standard",
            status="pending"
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.id is not None
        assert task.user_id == test_user_id
        assert task.query == "What is AI?"
        assert task.status == "pending"
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_with_result(self, db_session, test_user_id):
        """Test task with result data."""
        result_data = {
            "content": "AI is...",
            "sources": [{"url": "https://example.com", "title": "AI Article"}]
        }

        task = ResearchTask(
            user_id=test_user_id,
            query="What is AI?",
            model_name="sonar",
            depth="standard",
            status="completed",
            result=result_data,
            tokens_used=1500,
            cost=0.0075,
            completed_at=datetime.utcnow()
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.result == result_data
        assert task.tokens_used == 1500
        assert task.cost == 0.0075

    def test_task_with_feed_article(self, db_session, test_user_id):
        """Test task linked to feed and article."""
        feed_uuid = uuid4()
        article_uuid = uuid4()
        task = ResearchTask(
            user_id=test_user_id,
            query="Research this article",
            model_name="sonar",
            depth="standard",
            status="pending",
            feed_id=feed_uuid,
            legacy_feed_id=123,
            article_id=article_uuid,
            legacy_article_id=456
        )

        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        assert task.feed_id == feed_uuid
        assert task.legacy_feed_id == 123
        assert task.article_id == article_uuid
        assert task.legacy_article_id == 456


class TestResearchTemplateModel:
    """Tests for ResearchTemplate model."""

    def test_create_template(self, db_session, test_user_id):
        """Test creating a template."""
        template = ResearchTemplate(
            user_id=test_user_id,
            name="Test Template",
            description="Test description",
            query_template="Research {{topic}}",
            parameters={"topic": "string"},
            default_model="sonar",
            default_depth="standard"
        )

        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        assert template.id is not None
        assert template.name == "Test Template"
        assert template.is_active is True
        assert template.is_public is False
        assert template.usage_count == 0

    def test_template_usage_tracking(self, db_session, test_user_id):
        """Test template usage tracking."""
        template = ResearchTemplate(
            user_id=test_user_id,
            name="Test Template",
            query_template="Test {{var}}",
            parameters={},
            default_model="sonar",
            default_depth="standard",
            usage_count=5,
            last_used_at=datetime.utcnow()
        )

        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        assert template.usage_count == 5
        assert template.last_used_at is not None

    def test_public_template(self, db_session, test_user_id):
        """Test public template."""
        template = ResearchTemplate(
            user_id=test_user_id,
            name="Public Template",
            query_template="Test {{var}}",
            parameters={},
            default_model="sonar",
            default_depth="standard",
            is_public=True
        )

        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        assert template.is_public is True


class TestResearchCacheModel:
    """Tests for ResearchCache model."""

    def test_create_cache_entry(self, db_session):
        """Test creating a cache entry."""
        cache_entry = ResearchCache(
            cache_key="test_cache_key",
            query="Test query",
            model_name="sonar",
            depth="standard",
            result={"content": "Cached result"},
            tokens_used=1000,
            cost=0.005,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        db_session.add(cache_entry)
        db_session.commit()
        db_session.refresh(cache_entry)

        assert cache_entry.id is not None
        assert cache_entry.cache_key == "test_cache_key"
        assert cache_entry.hit_count == 0

    def test_cache_hit_tracking(self, db_session):
        """Test cache hit tracking."""
        cache_entry = ResearchCache(
            cache_key="test_key",
            query="Test",
            model_name="sonar",
            depth="standard",
            result={"content": "Test"},
            tokens_used=1000,
            cost=0.005,
            expires_at=datetime.utcnow() + timedelta(days=7),
            hit_count=10
        )

        db_session.add(cache_entry)
        db_session.commit()
        db_session.refresh(cache_entry)

        assert cache_entry.hit_count == 10


class TestCostTrackingModel:
    """Tests for CostTracking model."""

    def test_create_cost_entry(self, db_session, test_user_id):
        """Test creating a cost tracking entry."""
        cost_entry = CostTracking(
            user_id=test_user_id,
            date=datetime.utcnow(),
            model_name="sonar",
            tokens_used=1500,
            cost=0.0075
        )

        db_session.add(cost_entry)
        db_session.commit()
        db_session.refresh(cost_entry)

        assert cost_entry.id is not None
        assert cost_entry.user_id == test_user_id
        assert cost_entry.tokens_used == 1500
        assert cost_entry.cost == 0.0075

    def test_cost_entry_with_task(self, db_session, test_user_id, sample_research_task):
        """Test cost entry linked to task."""
        cost_entry = CostTracking(
            user_id=test_user_id,
            date=datetime.utcnow(),
            model_name="sonar",
            tokens_used=1500,
            cost=0.0075,
            task_id=sample_research_task.id
        )

        db_session.add(cost_entry)
        db_session.commit()
        db_session.refresh(cost_entry)

        assert cost_entry.task_id == sample_research_task.id


class TestModelIndexes:
    """Tests for model indexes."""

    def test_research_task_indexes(self):
        """Test ResearchTask has correct indexes."""
        from sqlalchemy import inspect

        indexes = {idx.name for idx in inspect(ResearchTask).indexes}

        assert 'ix_research_tasks_user_id' in indexes
        assert 'ix_research_tasks_status' in indexes
        assert 'ix_research_tasks_created' in indexes

    def test_cost_tracking_indexes(self):
        """Test CostTracking has correct indexes."""
        from sqlalchemy import inspect

        indexes = {idx.name for idx in inspect(CostTracking).indexes}

        assert 'ix_cost_tracking_user_id' in indexes
        assert 'ix_cost_tracking_date' in indexes
