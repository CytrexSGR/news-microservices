"""Tests for template engine."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.services.template_engine import (
    TemplateEngine,
    TemplateValidationError,
    template_engine
)
from app.models.research import ResearchTemplate, ResearchTask


class TestTemplateEngine:
    """Test template engine functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.engine = TemplateEngine()

    def test_parse_simple_template(self):
        """Test parsing template with simple variables."""
        template_text = "Research {{topic}} in {{domain}}"

        result = self.engine.parse_template(template_text)

        assert set(result["variables"]) == {"topic", "domain"}
        assert set(result["required_variables"]) == {"topic", "domain"}
        assert result["optional_variables"] == []
        assert result["has_conditionals"] is False

    def test_parse_template_with_conditionals(self):
        """Test parsing template with conditional blocks."""
        template_text = """Research {{topic}}
{{#if timeframe}}from {{timeframe}}{{/if}}
in {{domain}}"""

        result = self.engine.parse_template(template_text)

        assert set(result["variables"]) == {"topic", "timeframe", "domain"}
        assert "timeframe" in result["optional_variables"]
        assert "topic" in result["required_variables"]
        assert "domain" in result["required_variables"]
        assert result["has_conditionals"] is True

    def test_parse_template_with_else(self):
        """Test parsing template with if/else."""
        template_text = "{{#if premium}}Deep analysis{{else}}Quick overview{{/if}} of {{topic}}"

        result = self.engine.parse_template(template_text)

        assert "premium" in result["optional_variables"]
        assert "topic" in result["required_variables"]
        conditionals = result["conditionals"]
        assert len(conditionals) == 1
        assert conditionals[0]["has_else"] is True

    def test_validate_parameters_success(self):
        """Test successful parameter validation."""
        template = Mock(spec=ResearchTemplate)
        template.query_template = "Research {{topic}} in {{domain}}"

        variables = {"topic": "AI", "domain": "healthcare"}

        is_valid, error = self.engine.validate_parameters(template, variables)

        assert is_valid is True
        assert error is None

    def test_validate_parameters_missing_required(self):
        """Test validation with missing required parameters."""
        template = Mock(spec=ResearchTemplate)
        template.query_template = "Research {{topic}} in {{domain}}"

        variables = {"topic": "AI"}  # Missing 'domain'

        is_valid, error = self.engine.validate_parameters(template, variables)

        assert is_valid is False
        assert "domain" in error

    def test_substitute_simple_variables(self):
        """Test simple variable substitution."""
        template_text = "Research {{topic}} in {{domain}}"
        variables = {"topic": "AI", "domain": "healthcare"}

        result = self.engine.substitute_variables(template_text, variables)

        assert result == "Research AI in healthcare"

    def test_substitute_with_conditional_true(self):
        """Test conditional substitution when condition is true."""
        template_text = "Research {{topic}}{{#if timeframe}} from {{timeframe}}{{/if}}"
        variables = {"topic": "AI", "timeframe": "2024"}

        result = self.engine.substitute_variables(template_text, variables)

        assert result == "Research AI from 2024"

    def test_substitute_with_conditional_false(self):
        """Test conditional substitution when condition is false."""
        template_text = "Research {{topic}}{{#if timeframe}} from {{timeframe}}{{/if}}"
        variables = {"topic": "AI", "timeframe": ""}

        result = self.engine.substitute_variables(template_text, variables)

        assert result == "Research AI"

    def test_substitute_with_else_true_branch(self):
        """Test if/else taking true branch."""
        template_text = "{{#if premium}}Deep analysis{{else}}Quick overview{{/if}}"
        variables = {"premium": "yes"}

        result = self.engine.substitute_variables(template_text, variables)

        assert result == "Deep analysis"

    def test_substitute_with_else_false_branch(self):
        """Test if/else taking false branch."""
        template_text = "{{#if premium}}Deep analysis{{else}}Quick overview{{/if}}"
        variables = {"premium": ""}

        result = self.engine.substitute_variables(template_text, variables)

        assert result == "Quick overview"

    @pytest.mark.asyncio
    async def test_render_query_success(self):
        """Test successful query rendering."""
        db = Mock()
        template = Mock(spec=ResearchTemplate)
        template.query_template = "Research {{topic}} in {{domain}}"
        template.usage_count = 0

        variables = {"topic": "AI", "domain": "healthcare"}

        result = await self.engine.render_query(db, template, variables)

        assert result == "Research AI in healthcare"
        assert template.usage_count == 1
        assert template.last_used_at is not None
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_render_query_validation_error(self):
        """Test rendering with validation error."""
        db = Mock()
        template = Mock(spec=ResearchTemplate)
        template.query_template = "Research {{topic}} in {{domain}}"

        variables = {"topic": "AI"}  # Missing 'domain'

        with pytest.raises(TemplateValidationError) as exc_info:
            await self.engine.render_query(db, template, variables)

        assert "domain" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_template(self):
        """Test template execution."""
        db = Mock()
        template = Mock(spec=ResearchTemplate)
        template.id = 1
        template.query_template = "Research {{topic}}"
        template.default_model = "sonar"
        template.default_depth = "standard"
        template.usage_count = 0

        variables = {"topic": "AI"}

        mock_task = Mock(spec=ResearchTask)
        mock_task.id = 123

        with patch.object(
            self.engine.research_service,
            "create_research_task",
            new_callable=AsyncMock,
            return_value=mock_task
        ):
            result = await self.engine.execute_template(
                db=db,
                user_id=1,
                template=template,
                variables=variables
            )

        assert result == mock_task
        assert template.usage_count == 1

    @pytest.mark.asyncio
    async def test_batch_execute(self):
        """Test batch template execution."""
        db = Mock()
        template = Mock(spec=ResearchTemplate)
        template.id = 1
        template.query_template = "Research {{topic}}"
        template.default_model = "sonar"
        template.default_depth = "standard"
        template.usage_count = 0

        variable_sets = [
            {"topic": "AI"},
            {"topic": "ML"},
            {"topic": "NLP"}
        ]

        mock_tasks = [Mock(spec=ResearchTask, id=i) for i in range(3)]

        with patch.object(
            self.engine,
            "execute_template",
            new_callable=AsyncMock,
            side_effect=mock_tasks
        ):
            results = await self.engine.batch_execute(
                db=db,
                user_id=1,
                template=template,
                variable_sets=variable_sets
            )

        assert len(results) == 3
        assert all(isinstance(task, Mock) for task in results)

    @pytest.mark.asyncio
    async def test_schedule_execution(self):
        """Test scheduling template execution."""
        db = Mock()
        template = Mock(spec=ResearchTemplate)
        template.id = 1
        template.query_template = "Research {{topic}}"
        template.default_model = "sonar"
        template.default_depth = "standard"

        variables = {"topic": "AI"}
        schedule_at = datetime.utcnow() + timedelta(hours=1)

        mock_celery_task = Mock()
        mock_celery_task.id = "celery-task-123"

        with patch("app.services.template_engine.process_template_execution") as mock_task:
            mock_task.apply_async.return_value = mock_celery_task

            result = await self.engine.schedule_execution(
                db=db,
                user_id=1,
                template=template,
                variables=variables,
                schedule_at=schedule_at
            )

        assert result["celery_task_id"] == "celery-task-123"
        assert result["template_id"] == 1
        assert result["status"] == "scheduled"

    @pytest.mark.asyncio
    async def test_aggregate_results(self):
        """Test result aggregation."""
        db = Mock()

        # Create mock tasks
        completed_task1 = Mock(spec=ResearchTask)
        completed_task1.id = 1
        completed_task1.query = "Query 1"
        completed_task1.status = "completed"
        completed_task1.result = {
            "content": "Result 1",
            "citations": [{"url": "http://example1.com"}],
            "sources": [{"url": "http://example1.com", "title": "Source 1"}]
        }
        completed_task1.tokens_used = 100
        completed_task1.cost = 0.01
        completed_task1.created_at = datetime.utcnow()
        completed_task1.completed_at = datetime.utcnow()

        completed_task2 = Mock(spec=ResearchTask)
        completed_task2.id = 2
        completed_task2.query = "Query 2"
        completed_task2.status = "completed"
        completed_task2.result = {
            "content": "Result 2",
            "citations": [{"url": "http://example2.com"}],
            "sources": [{"url": "http://example2.com", "title": "Source 2"}]
        }
        completed_task2.tokens_used = 150
        completed_task2.cost = 0.015
        completed_task2.created_at = datetime.utcnow()
        completed_task2.completed_at = datetime.utcnow()

        failed_task = Mock(spec=ResearchTask)
        failed_task.id = 3
        failed_task.status = "failed"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [completed_task1, completed_task2, failed_task]

        db.query.return_value = mock_query

        result = await self.engine.aggregate_results(
            db=db,
            task_ids=[1, 2, 3],
            user_id=1
        )

        assert result["total"] == 3
        assert result["completed"] == 2
        assert result["failed"] == 1
        assert result["total_tokens"] == 250
        assert result["total_cost"] == 0.025
        assert result["unique_sources"] == 2
        assert len(result["tasks"]) == 3

    def test_preview_template(self):
        """Test template preview."""
        template = Mock(spec=ResearchTemplate)
        template.id = 1
        template.name = "Test Template"
        template.query_template = "Research {{topic}} in {{domain}}"
        template.default_model = "sonar"
        template.default_depth = "standard"

        variables = {"topic": "AI", "domain": "healthcare"}

        with patch("app.services.template_engine.settings") as mock_settings:
            mock_settings.calculate_cost.return_value = 0.05

            result = self.engine.preview_template(template, variables)

        assert result["template_id"] == 1
        assert result["template_name"] == "Test Template"
        assert result["is_valid"] is True
        assert result["error"] is None
        assert result["rendered_query"] == "Research AI in healthcare"
        assert result["estimated_cost"] > 0

    def test_preview_template_invalid(self):
        """Test template preview with invalid variables."""
        template = Mock(spec=ResearchTemplate)
        template.id = 1
        template.name = "Test Template"
        template.query_template = "Research {{topic}} in {{domain}}"
        template.default_model = "sonar"
        template.default_depth = "standard"

        variables = {"topic": "AI"}  # Missing 'domain'

        result = self.engine.preview_template(template, variables)

        assert result["is_valid"] is False
        assert result["error"] is not None
        assert "domain" in result["error"]

    @pytest.mark.asyncio
    async def test_create_from_pattern_feed_analysis(self):
        """Test creating template from feed_analysis pattern."""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()

        context = {
            "topic": "Technology",
            "feed_name": "TechCrunch"
        }

        template = await self.engine.create_from_pattern(
            db=db,
            user_id=1,
            pattern_name="feed_analysis",
            context=context
        )

        assert template.name == "Feed Analysis: Technology"
        assert "{{topic}}" in template.query_template
        assert "{{feed_name}}" in template.query_template
        db.add.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_from_pattern_fact_check(self):
        """Test creating template from fact_check pattern."""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()

        context = {
            "claim": "Test claim"
        }

        template = await self.engine.create_from_pattern(
            db=db,
            user_id=1,
            pattern_name="fact_check",
            context=context
        )

        assert "Fact Check" in template.name
        assert "{{claim}}" in template.query_template
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_from_pattern_invalid(self):
        """Test creating template with invalid pattern."""
        db = Mock()

        with pytest.raises(ValueError) as exc_info:
            await self.engine.create_from_pattern(
                db=db,
                user_id=1,
                pattern_name="invalid_pattern",
                context={}
            )

        assert "Unknown pattern" in str(exc_info.value)


class TestTemplateEngineIntegration:
    """Integration tests for template engine."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete template workflow."""
        db = Mock()
        template = Mock(spec=ResearchTemplate)
        template.id = 1
        template.query_template = "Research {{topic}} in {{domain}}{{#if year}} in {{year}}{{/if}}"
        template.default_model = "sonar"
        template.default_depth = "standard"
        template.usage_count = 0

        variables = {
            "topic": "AI",
            "domain": "healthcare",
            "year": "2024"
        }

        engine = TemplateEngine()

        # 1. Parse template
        metadata = engine.parse_template(template.query_template)
        assert len(metadata["variables"]) == 3

        # 2. Validate parameters
        is_valid, error = engine.validate_parameters(template, variables)
        assert is_valid is True

        # 3. Preview
        preview = engine.preview_template(template, variables)
        assert preview["is_valid"] is True
        assert "AI" in preview["rendered_query"]
        assert "healthcare" in preview["rendered_query"]
        assert "2024" in preview["rendered_query"]

        # 4. Execute (mocked)
        mock_task = Mock(spec=ResearchTask, id=123)
        with patch.object(
            engine.research_service,
            "create_research_task",
            new_callable=AsyncMock,
            return_value=mock_task
        ):
            result = await engine.execute_template(
                db=db,
                user_id=1,
                template=template,
                variables=variables
            )

        assert result.id == 123
