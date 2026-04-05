"""
Pytest Configuration and Fixtures for OSS Service Tests.

Provides mock Neo4j connections and test data for unit testing
analyzers and API endpoints without requiring real database access.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.database import Neo4jConnection
from app.config import Settings


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_settings():
    """Test settings with sensible defaults."""
    return Settings(
        APP_NAME="OSS Service Test",
        APP_VERSION="1.0.0-test",
        DEBUG=True,
        ENVIRONMENT="test",
        NEO4J_URI="bolt://localhost:7687",
        NEO4J_USER="neo4j",
        NEO4J_PASSWORD="test_password",
        NEO4J_DATABASE="neo4j",
        PROPOSALS_API_URL="http://localhost:8109",
        ANALYSIS_INTERVAL_SECONDS=3600,
        MIN_PATTERN_OCCURRENCES=10,
        CONFIDENCE_THRESHOLD=0.7,
        LOG_LEVEL="DEBUG"
    )


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_neo4j():
    """
    Mock Neo4j connection for unit testing.

    Returns a MagicMock that simulates Neo4jConnection behavior.
    Use neo4j.execute_read.return_value to set query results.

    Example:
        mock_neo4j.execute_read.return_value = [
            {"type": "PERSON", "count": 50, "sample_ids": [1, 2, 3]}
        ]
    """
    neo4j = MagicMock(spec=Neo4jConnection)
    neo4j.execute_read = MagicMock(return_value=[])
    neo4j.check_connection = MagicMock(return_value=True)
    neo4j.connect = MagicMock()
    neo4j.close = MagicMock()
    return neo4j


@pytest.fixture
def mock_neo4j_disconnected():
    """Mock Neo4j connection that appears disconnected."""
    neo4j = MagicMock(spec=Neo4jConnection)
    neo4j.execute_read = MagicMock(side_effect=ConnectionError("Neo4j unavailable"))
    neo4j.check_connection = MagicMock(return_value=False)
    return neo4j


# ============================================================================
# Pattern Detection Test Data
# ============================================================================

@pytest.fixture
def entity_pattern_data():
    """Sample data for entity pattern detection tests."""
    return [
        {"type": "PERSON", "count": 150, "sample_ids": [101, 102, 103, 104, 105]},
        {"type": "ORGANIZATION", "count": 80, "sample_ids": [201, 202, 203]},
        {"type": "LOCATION", "count": 45, "sample_ids": [301, 302]},
    ]


@pytest.fixture
def relationship_pattern_data():
    """Sample data for relationship pattern detection tests."""
    return [
        {"source_type": "PERSON", "target_type": "ORGANIZATION", "count": 50},
        {"source_type": "ORGANIZATION", "target_type": "LOCATION", "count": 30},
        {"source_type": "PERSON", "target_type": "PERSON", "count": 25},
    ]


@pytest.fixture
def empty_pattern_data():
    """Empty data for testing no-result scenarios."""
    return []


# ============================================================================
# Inconsistency Detection Test Data
# ============================================================================

@pytest.fixture
def iso_violation_data():
    """Sample data for ISO code violation tests."""
    return [
        {"entity_id": "us", "name": "United States", "labels": ["Country"], "node_id": 1001},
        {"entity_id": "USA", "name": "USA", "labels": ["Country"], "node_id": 1002},
        {"entity_id": None, "name": "Germany", "labels": ["Country"], "node_id": 1003},
        {"entity_id": "D", "name": "Deutschland", "labels": ["Country"], "node_id": 1004},
    ]


@pytest.fixture
def duplicate_entity_data():
    """Sample data for duplicate entity detection tests."""
    return [
        {"id": "AAPL", "duplicate_count": 3, "sample_node_ids": [2001, 2002, 2003]},
        {"id": "GOOGL", "duplicate_count": 2, "sample_node_ids": [2004, 2005]},
    ]


@pytest.fixture
def missing_properties_data():
    """Sample data for missing properties tests."""
    return [
        {"node_id": 3001, "labels": ["Entity"], "entity_id": None, "entity_type": "PERSON", "name": "John Doe"},
        {"node_id": 3002, "labels": ["Entity"], "entity_id": "JD001", "entity_type": None, "name": "Jane Doe"},
        {"node_id": 3003, "labels": ["Entity"], "entity_id": "JD002", "entity_type": "ORGANIZATION", "name": None},
    ]


@pytest.fixture
def unknown_entity_data():
    """Sample data for UNKNOWN entity type tests."""
    return [
        {"unknown_count": 38000, "sample_ids": [4001, 4002, 4003, 4004, 4005, 4006, 4007, 4008, 4009, 4010]}
    ]


@pytest.fixture
def article_entity_data():
    """Sample data for ARTICLE entity tests."""
    return [
        {
            "article_count": 500,
            "sample_ids": [5001, 5002, 5003, 5004, 5005],
            "sample_names": [
                "Article 550e8400-e29b-41d4-a716-446655440000",
                "Article 6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "Article 6ba7b811-9dad-11d1-80b4-00c04fd430c8"
            ]
        }
    ]


# ============================================================================
# API Test Fixtures
# ============================================================================

@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API submission tests."""
    with patch("httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value.__aenter__.return_value = client
        mock.return_value.__aexit__.return_value = None
        yield client


@pytest.fixture
def successful_api_response():
    """Mock successful API response."""
    response = MagicMock()
    response.status_code = 201
    response.text = '{"id": "proposal_123"}'
    return response


@pytest.fixture
def failed_api_response():
    """Mock failed API response."""
    response = MagicMock()
    response.status_code = 500
    response.text = '{"error": "Internal server error"}'
    return response


# ============================================================================
# Analyzer Fixtures
# ============================================================================

@pytest.fixture
def pattern_detector(mock_neo4j):
    """PatternDetector with mock Neo4j."""
    from app.analyzers.pattern_detector import PatternDetector
    return PatternDetector(mock_neo4j)


@pytest.fixture
def inconsistency_detector(mock_neo4j):
    """InconsistencyDetector with mock Neo4j."""
    from app.analyzers.inconsistency_detector import InconsistencyDetector
    return InconsistencyDetector(mock_neo4j)


# ============================================================================
# Helper Functions
# ============================================================================

def assert_valid_proposal(proposal):
    """Assert that a proposal has all required fields."""
    assert proposal is not None
    assert proposal.proposal_id is not None
    assert proposal.proposal_id.startswith("OSS_")
    assert proposal.change_type is not None
    assert proposal.severity is not None
    assert proposal.title is not None
    assert proposal.description is not None
    assert 0.0 <= proposal.confidence <= 1.0
    assert proposal.impact_analysis is not None


def assert_proposal_count(proposals, expected_count):
    """Assert proposal list has expected count."""
    assert len(proposals) == expected_count, f"Expected {expected_count} proposals, got {len(proposals)}"
