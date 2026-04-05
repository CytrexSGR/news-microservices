"""
Test configuration and fixtures for llm-orchestrator-service tests.

Provides reusable fixtures and mocks for testing.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4
import json

# Import models from project root
import sys
from pathlib import Path

# Determine if we're in Docker container or local environment
# In container: /app/tests/conftest.py -> /app/models
# Locally: /home/cytrex/.../tests/conftest.py -> /home/cytrex/.../models
current_file = Path(__file__)
app_dir = current_file.parent.parent  # Go up to service root

# Add models path to Python path
if (app_dir / "models").exists():
    # We're in container or service root
    sys.path.insert(0, str(app_dir))
else:
    # We're in project root structure
    project_root = app_dir.parent.parent
    sys.path.insert(0, str(project_root))

from models.verification_events import (
    VerificationRequiredEvent,
    ProblemHypothesis,
    ToolExecutionResult
)
from models.adversarial_test_case import VerificationPlan


# ============================================================================
# Sample Test Data
# ============================================================================

@pytest.fixture
def sample_verification_event():
    """Sample verification required event for testing."""
    return VerificationRequiredEvent(
        analysis_result_id=uuid4(),
        article_id=uuid4(),
        article_title="Tesla Reports Record Q3 Earnings",
        article_content="Tesla Inc. announced today record-breaking financial results for Q3 2024, reporting net profits of $5 billion...",
        article_url="https://example.com/tesla-earnings",
        article_published_at=datetime(2024, 10, 23, 14, 30),
        uq_confidence_score=0.45,
        uncertainty_factors=[
            "Low confidence in claim accuracy",
            "Numerical claim lacks verification"
        ],
        priority="high",
        analysis_summary="Tesla reported $5B profit in Q3 2024",
        extracted_entities=["Tesla", "Q3 2024"],
        category_analysis="Business/Finance"
    )


@pytest.fixture
def sample_problem_hypothesis():
    """Sample problem hypothesis from Stage 1."""
    return ProblemHypothesis(
        primary_concern="Financial figure appears incorrect or unverified",
        affected_content="Q3 earnings of $5 billion",
        hypothesis_type="factual_error",
        confidence=0.85,
        reasoning="The reported $5B profit seems unusually high compared to historical data. Requires verification against official SEC filings.",
        verification_approach="Cross-reference with SEC 10-Q filing and official Tesla investor relations data"
    )


@pytest.fixture
def sample_verification_plan():
    """Sample verification plan from Stage 2."""
    return VerificationPlan(
        priority="high",
        verification_methods=[
            "perplexity_deep_search(query='Tesla Q3 2024 earnings actual amount')",
            "financial_data_lookup(company='TSLA', metric='earnings', period='Q3 2024')"
        ],
        external_sources=["SEC 10-Q Filing", "Tesla Investor Relations"],
        expected_corrections=[
            {
                "field": "Q3 2024 net profit",
                "original": "$5 billion",
                "corrected": "$4.2 billion",
                "confidence_improvement": 0.35
            }
        ],
        estimated_verification_time_seconds=45
    )


@pytest.fixture
def sample_tool_execution_result():
    """Sample successful tool execution result."""
    return ToolExecutionResult(
        tool_name="perplexity_deep_search",
        tool_parameters={"query": "Tesla Q3 2024 earnings"},
        success=True,
        execution_time_ms=1234,
        result_data={
            "answer": "Tesla reported Q3 2024 earnings with net income of $2.17 billion...",
            "sources": ["https://sec.gov/filing", "https://ir.tesla.com"]
        },
        source_citations=["https://sec.gov/filing", "https://ir.tesla.com"],
        confidence=0.85
    )


# ============================================================================
# Mock OpenAI API
# ============================================================================

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    def _create_response(content: dict):
        """Create mock OpenAI response with given content."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps(content)
        return mock_response
    return _create_response


@pytest.fixture
def mock_openai_stage1_response(mock_openai_response):
    """Mock Stage 1 (diagnosis) OpenAI response."""
    content = {
        "primary_concern": "Financial figure appears incorrect",
        "affected_content": "Q3 earnings of $5 billion",
        "hypothesis_type": "factual_error",
        "confidence": 0.85,
        "reasoning": "Amount seems unusually high",
        "verification_approach": "Cross-reference with SEC filings"
    }
    return mock_openai_response(content)


@pytest.fixture
def mock_openai_stage2_response(mock_openai_response):
    """Mock Stage 2 (planning) OpenAI response."""
    content = {
        "priority": "high",
        "verification_methods": [
            "perplexity_deep_search(query='Tesla Q3 2024 earnings')",
            "financial_data_lookup(company='TSLA', metric='earnings', period='Q3 2024')"
        ],
        "external_sources": ["SEC filings", "Tesla IR"],
        "expected_corrections": [
            {
                "field": "earnings",
                "original": "$5 billion",
                "corrected": "$4.2 billion",
                "confidence_improvement": 0.35
            }
        ],
        "estimated_verification_time_seconds": 45
    }
    return mock_openai_response(content)


@pytest.fixture
def mock_openai_client(mock_openai_stage1_response, mock_openai_stage2_response):
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()

    # Stage 1 returns hypothesis, Stage 2 returns plan
    # Alternate between them based on call count
    call_count = [0]

    def create_side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] % 2 == 1:  # Odd calls = Stage 1
            return mock_openai_stage1_response
        else:  # Even calls = Stage 2
            return mock_openai_stage2_response

    mock_client.chat.completions.create = Mock(side_effect=create_side_effect)

    return mock_client


# ============================================================================
# Mock HTTP Clients (Perplexity, Alpha Vantage)
# ============================================================================

@pytest.fixture
def mock_perplexity_response():
    """Mock Perplexity API response."""
    return {
        "choices": [{
            "message": {
                "content": "Tesla reported Q3 2024 net income of $2.17 billion, up 17% year-over-year...",
                "citations": [
                    "https://sec.gov/Archives/edgar/data/1318605/000095017024116700/tsla-20240930.htm",
                    "https://ir.tesla.com/press-release/tesla-q3-2024-results"
                ]
            }
        }],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 300,
            "total_tokens": 450
        }
    }


@pytest.fixture
def mock_alpha_vantage_earnings_response():
    """Mock Alpha Vantage earnings API response."""
    return {
        "symbol": "TSLA",
        "quarterlyEarnings": [
            {
                "fiscalDateEnding": "2024-09-30",
                "reportedDate": "2024-10-23",
                "reportedEPS": "2.17",
                "estimatedEPS": "1.85",
                "surprise": "0.32",
                "surprisePercentage": "17.3"
            },
            {
                "fiscalDateEnding": "2024-06-30",
                "reportedDate": "2024-07-23",
                "reportedEPS": "1.91",
                "estimatedEPS": "1.75",
                "surprise": "0.16",
                "surprisePercentage": "9.1"
            }
        ]
    }


@pytest.fixture
def mock_alpha_vantage_quote_response():
    """Mock Alpha Vantage quote API response."""
    return {
        "Global Quote": {
            "01. symbol": "TSLA",
            "05. price": "242.84",
            "06. volume": "102847291",
            "07. latest trading day": "2024-10-30",
            "09. change": "3.45",
            "10. change percent": "1.44%"
        }
    }


@pytest.fixture
async def mock_httpx_client(mock_perplexity_response, mock_alpha_vantage_earnings_response):
    """Mock httpx AsyncClient for API calls."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()

    # Default to Perplexity response, can be overridden in tests
    mock_response.json = AsyncMock(return_value=mock_perplexity_response)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    return mock_client


# ============================================================================
# Mock RabbitMQ
# ============================================================================

@pytest.fixture
def mock_rabbitmq_message(sample_verification_event):
    """Mock RabbitMQ incoming message."""
    mock_msg = AsyncMock()
    mock_msg.body = json.dumps(sample_verification_event.model_dump(mode='json')).encode()
    mock_msg.routing_key = "verification.required.high"
    mock_msg.delivery_tag = 12345

    # Mock process context manager
    mock_msg.process = MagicMock()
    mock_msg.process.return_value.__aenter__ = AsyncMock()
    mock_msg.process.return_value.__aexit__ = AsyncMock()

    return mock_msg


@pytest.fixture
async def mock_rabbitmq_connection():
    """Mock RabbitMQ connection."""
    mock_conn = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()
    mock_queue = AsyncMock()

    # Setup mock chain
    mock_conn.channel = AsyncMock(return_value=mock_channel)
    mock_channel.set_qos = AsyncMock()
    mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)
    mock_queue.bind = AsyncMock()
    mock_queue.iterator = MagicMock()

    return {
        "connection": mock_conn,
        "channel": mock_channel,
        "exchange": mock_exchange,
        "queue": mock_queue
    }


# ============================================================================
# Configuration Mocks
# ============================================================================

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from app.core.config import Settings

    return Settings(
        DATABASE_URL="postgresql://test:test@localhost/test",
        RABBITMQ_URL="amqp://guest:guest@localhost:5672/",
        OPENAI_API_KEY="test-openai-key",
        OPENAI_MODEL="gpt-4o-mini",
        PERPLEXITY_API_KEY="test-perplexity-key",
        ALPHA_VANTAGE_API_KEY="test-alpha-vantage-key",
        DIA_STAGE1_TEMPERATURE=0.3,
        DIA_STAGE2_TEMPERATURE=0.2,
        DIA_MAX_RETRIES=3,
        TOOL_TIMEOUT_SECONDS=30,
        TOOL_MAX_RETRIES=2,
        LOG_LEVEL="INFO"
    )


# ============================================================================
# Async Test Support
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
