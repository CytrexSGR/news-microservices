"""
Tests for DIA Planner (Stage 1 & 2)

Coverage:
- Two-stage planning process
- OpenAI API integration
- Retry logic
- Error handling
- Prompt building
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from app.services.dia_planner import DIAPlanner


class TestDIAPlannerInitialization:
    """Test DIAPlanner initialization."""

    def test_initialization_with_default_config(self, mock_settings):
        """Test planner initializes with default configuration."""
        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI') as mock_openai:
                planner = DIAPlanner()

                assert planner.model == "gpt-4o-mini"
                assert planner.stage1_temperature == 0.3
                assert planner.stage2_temperature == 0.2
                assert planner.max_retries == 3
                mock_openai.assert_called_once_with(api_key="test-openai-key")


class TestStage1DiagnosisRefinement:
    """Test Stage 1: Root Cause Analysis."""

    @pytest.mark.asyncio
    async def test_diagnose_root_cause_success(
        self,
        sample_verification_event,
        mock_openai_client,
        mock_openai_stage1_response,
        mock_settings
    ):
        """Test successful root cause diagnosis."""
        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI', return_value=mock_openai_client):
                planner = DIAPlanner()
                hypothesis = await planner._diagnose_root_cause(sample_verification_event)

                assert hypothesis.primary_concern == "Financial figure appears incorrect"
                assert hypothesis.hypothesis_type == "factual_error"
                assert hypothesis.confidence == 0.85
                assert "SEC filings" in hypothesis.verification_approach

    @pytest.mark.asyncio
    async def test_diagnose_root_cause_retry_on_json_error(
        self,
        sample_verification_event,
        mock_settings
    ):
        """Test retry logic when LLM returns invalid JSON."""
        mock_client = Mock()
        mock_response_invalid = Mock()
        mock_response_invalid.choices = [Mock()]
        mock_response_invalid.choices[0].message = Mock()
        mock_response_invalid.choices[0].message.content = "Invalid JSON{{{}"

        mock_response_valid = Mock()
        mock_response_valid.choices = [Mock()]
        mock_response_valid.choices[0].message = Mock()
        mock_response_valid.choices[0].message.content = json.dumps({
            "primary_concern": "Test concern",
            "affected_content": "Test content",
            "hypothesis_type": "factual_error",
            "confidence": 0.8,
            "reasoning": "Test reasoning",
            "verification_approach": "Test approach"
        })

        # First call fails, second succeeds
        mock_client.chat.completions.create = Mock(
            side_effect=[mock_response_invalid, mock_response_valid]
        )

        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI', return_value=mock_client):
                planner = DIAPlanner()
                hypothesis = await planner._diagnose_root_cause(sample_verification_event)

                assert hypothesis.primary_concern == "Test concern"
                assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_diagnose_root_cause_max_retries_exceeded(
        self,
        sample_verification_event,
        mock_settings
    ):
        """Test that ValueError is raised after max retries exceeded."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Invalid JSON{{{}"

        mock_client.chat.completions.create = Mock(return_value=mock_response)

        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI', return_value=mock_client):
                planner = DIAPlanner()

                with pytest.raises(ValueError, match="Failed to parse LLM response"):
                    await planner._diagnose_root_cause(sample_verification_event)

                assert mock_client.chat.completions.create.call_count == 3  # max_retries

    @pytest.mark.asyncio
    async def test_diagnose_root_cause_api_error(
        self,
        sample_verification_event,
        mock_settings
    ):
        """Test handling of OpenAI API errors."""
        mock_client = Mock()
        mock_client.chat.completions.create = Mock(
            side_effect=Exception("API connection failed")
        )

        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI', return_value=mock_client):
                planner = DIAPlanner()

                with pytest.raises(Exception, match="API connection failed"):
                    await planner._diagnose_root_cause(sample_verification_event)


class TestStage2PlanGeneration:
    """Test Stage 2: Verification Plan Generation."""

    @pytest.mark.asyncio
    async def test_generate_plan_success(
        self,
        sample_verification_event,
        sample_problem_hypothesis,
        mock_openai_client,
        mock_settings
    ):
        """Test successful plan generation."""
        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI', return_value=mock_openai_client):
                planner = DIAPlanner()
                plan = await planner._generate_plan(
                    sample_problem_hypothesis,
                    sample_verification_event
                )

                assert plan.priority == "high"
                assert len(plan.verification_methods) == 2
                assert "perplexity_deep_search" in plan.verification_methods[0]
                assert "financial_data_lookup" in plan.verification_methods[1]
                assert len(plan.expected_corrections) == 1
                assert plan.estimated_verification_time_seconds == 45

    @pytest.mark.asyncio
    async def test_generate_plan_with_specific_tools(
        self,
        sample_verification_event,
        sample_problem_hypothesis,
        mock_settings
    ):
        """Test that plan includes specific tool parameters."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "priority": "critical",
            "verification_methods": [
                "perplexity_deep_search(query='Tesla earnings Q3 2024', search_domain_filter=['sec.gov'])",
                "financial_data_lookup(company='TSLA', metric='earnings', period='Q3 2024')"
            ],
            "external_sources": ["SEC 10-Q"],
            "expected_corrections": [],
            "estimated_verification_time_seconds": 30
        })

        mock_client.chat.completions.create = Mock(return_value=mock_response)

        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI', return_value=mock_client):
                planner = DIAPlanner()
                plan = await planner._generate_plan(
                    sample_problem_hypothesis,
                    sample_verification_event
                )

                assert plan.priority == "critical"
                assert "search_domain_filter" in plan.verification_methods[0]


class TestPromptBuilding:
    """Test prompt building for Stage 1 and Stage 2."""

    def test_build_stage1_prompt_includes_context(
        self,
        sample_verification_event,
        mock_settings
    ):
        """Test Stage 1 prompt includes all necessary context."""
        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI'):
                planner = DIAPlanner()
                prompt = planner._build_stage1_prompt(sample_verification_event)

                assert sample_verification_event.article_title in prompt
                assert sample_verification_event.article_url in prompt
                assert str(sample_verification_event.uq_confidence_score) in prompt
                assert sample_verification_event.uncertainty_factors[0] in prompt
                assert "Root Cause Analysis" in prompt or "root cause" in prompt.lower()

    def test_build_stage1_prompt_truncates_long_content(
        self,
        sample_verification_event,
        mock_settings
    ):
        """Test that long article content is truncated."""
        # Create event with very long content
        long_event = sample_verification_event.model_copy()
        long_event.article_content = "A" * 5000  # 5000 characters

        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI'):
                planner = DIAPlanner()
                prompt = planner._build_stage1_prompt(long_event)

                assert "[truncated]" in prompt
                # Ensure content is limited to ~2000 chars + metadata
                assert len(prompt) < 3000

    def test_build_stage2_prompt_includes_hypothesis(
        self,
        sample_verification_event,
        sample_problem_hypothesis,
        mock_settings
    ):
        """Test Stage 2 prompt includes hypothesis and available tools."""
        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI'):
                planner = DIAPlanner()
                prompt = planner._build_stage2_prompt(
                    sample_problem_hypothesis,
                    sample_verification_event
                )

                # Check hypothesis is included
                assert sample_problem_hypothesis.primary_concern in prompt
                assert sample_problem_hypothesis.hypothesis_type in prompt

                # Check article context
                assert sample_verification_event.article_title in prompt

                # Check tools are described
                assert "perplexity_deep_search" in prompt
                assert "financial_data_lookup" in prompt
                assert "entity_lookup" in prompt


class TestTwoStageProcess:
    """Test complete two-stage planning process."""

    @pytest.mark.asyncio
    async def test_process_verification_request_end_to_end(
        self,
        sample_verification_event,
        mock_openai_client,
        mock_settings
    ):
        """Test complete two-stage process from event to plan."""
        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI', return_value=mock_openai_client):
                planner = DIAPlanner()

                hypothesis, plan = await planner.process_verification_request(
                    sample_verification_event
                )

                # Stage 1 output
                assert hypothesis.primary_concern is not None
                assert hypothesis.hypothesis_type in [
                    "factual_error", "bias", "missing_context", "outdated_info"
                ]
                assert 0.0 <= hypothesis.confidence <= 1.0

                # Stage 2 output
                assert plan.priority in ["low", "medium", "high", "critical"]
                assert len(plan.verification_methods) > 0
                assert plan.estimated_verification_time_seconds > 0

    @pytest.mark.asyncio
    async def test_process_verification_request_stage2_uses_stage1_output(
        self,
        sample_verification_event,
        mock_settings
    ):
        """Test that Stage 2 receives and uses Stage 1 hypothesis."""
        stage2_calls = []

        def capture_stage2_call(*args, **kwargs):
            # Capture Stage 2 prompt to verify it includes Stage 1 output
            messages = kwargs.get('messages', [])
            user_message = next((m for m in messages if m['role'] == 'user'), None)
            if user_message:
                stage2_calls.append(user_message['content'])

            # Return Stage 2 response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = json.dumps({
                "priority": "high",
                "verification_methods": ["perplexity_deep_search(query='test')"],
                "external_sources": [],
                "expected_corrections": [],
                "estimated_verification_time_seconds": 30
            })
            return mock_response

        mock_client = Mock()
        stage1_response = Mock()
        stage1_response.choices = [Mock()]
        stage1_response.choices[0].message = Mock()
        stage1_response.choices[0].message.content = json.dumps({
            "primary_concern": "STAGE1_CONCERN",
            "affected_content": "test",
            "hypothesis_type": "factual_error",
            "confidence": 0.8,
            "reasoning": "test",
            "verification_approach": "test"
        })

        mock_client.chat.completions.create = Mock(
            side_effect=[stage1_response, capture_stage2_call]
        )

        with patch('app.services.dia_planner.settings', mock_settings):
            with patch('app.services.dia_planner.OpenAI', return_value=mock_client):
                planner = DIAPlanner()
                await planner.process_verification_request(sample_verification_event)

                # Verify Stage 2 prompt includes Stage 1 output
                assert len(stage2_calls) == 1
                assert "STAGE1_CONCERN" in stage2_calls[0]
