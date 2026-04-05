"""
Pytest fixtures for knowledge-graph-service tests.

Provides mocked Neo4j connections and other test utilities.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.neo4j_service import Neo4jService
from app.services.ingestion_service import IngestionService
from app.models.graph import Entity, Relationship, Triplet


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j AsyncDriver."""
    driver = AsyncMock()
    driver.session = MagicMock()
    driver.verify_connectivity = AsyncMock()
    driver.close = AsyncMock()
    return driver


@pytest.fixture
def mock_neo4j_session():
    """Mock Neo4j AsyncSession."""
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.run = AsyncMock()
    return session


@pytest.fixture
def neo4j_service_with_mock():
    """Create Neo4jService with mocked driver."""
    service = Neo4jService()
    service.driver = AsyncMock()
    return service


@pytest.fixture
def ingestion_service():
    """Create IngestionService instance."""
    return IngestionService()


@pytest.fixture
def sample_entity_person():
    """Sample PERSON entity."""
    return Entity(
        name="Elon Musk",
        type="PERSON",
        properties={
            "wikidata_id": "Q317521",
            "bio": "Tesla CEO"
        },
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )


@pytest.fixture
def sample_entity_organization():
    """Sample ORGANIZATION entity."""
    return Entity(
        name="Tesla",
        type="ORGANIZATION",
        properties={
            "wikidata_id": "Q478214",
            "sector": "Automotive"
        },
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )


@pytest.fixture
def sample_entity_location():
    """Sample LOCATION entity."""
    return Entity(
        name="United States",
        type="LOCATION",
        properties={
            "wikidata_id": "Q30"
        },
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )


@pytest.fixture
def sample_relationship():
    """Sample relationship."""
    return Relationship(
        subject="Elon Musk",
        subject_type="PERSON",
        relationship_type="WORKS_FOR",
        object="Tesla",
        object_type="ORGANIZATION",
        confidence=0.95,
        evidence="Elon Musk is the CEO of Tesla",
        source_url="https://example.com/article",
        article_id="article-001",
        created_at=datetime.utcnow(),
        mention_count=1,
        sentiment_score=0.8,
        sentiment_category="positive",
        sentiment_confidence=0.9
    )


@pytest.fixture
def sample_triplet(sample_entity_person, sample_entity_organization, sample_relationship):
    """Sample (subject)-[relationship]->(object) triplet."""
    return Triplet(
        subject=sample_entity_person,
        relationship=sample_relationship,
        object=sample_entity_organization
    )


@pytest.fixture
def sample_triplet_location(sample_entity_organization, sample_entity_location):
    """Sample location relationship triplet."""
    relationship = Relationship(
        subject="Tesla",
        subject_type="ORGANIZATION",
        relationship_type="LOCATED_IN",
        object="United States",
        object_type="LOCATION",
        confidence=0.99,
        evidence="Tesla is headquartered in the United States",
        source_url="https://example.com/article2",
        article_id="article-002",
        mention_count=1
    )
    return Triplet(
        subject=sample_entity_organization,
        relationship=relationship,
        object=sample_entity_location
    )


@pytest.fixture
def mock_neo4j_write_result():
    """Mock Neo4j write operation result."""
    result = AsyncMock()
    result.consume = AsyncMock()
    result.consume.return_value = MagicMock(
        counters=MagicMock(
            nodes_created=1,
            nodes_deleted=0,
            relationships_created=1,
            relationships_deleted=0,
            properties_set=5
        )
    )
    return result


@pytest.fixture
def mock_neo4j_query_result_single():
    """Mock Neo4j query result (single entity)."""
    result = AsyncMock()
    result.data = AsyncMock(return_value=[
        {
            "e.name": "Tesla",
            "e.type": "ORGANIZATION",
            "e.created_at": datetime.utcnow()
        }
    ])
    return result


@pytest.fixture
def mock_neo4j_query_result_connections():
    """Mock Neo4j connections query result."""
    result = AsyncMock()
    result.data = AsyncMock(return_value=[
        {
            "source_name": "Tesla",
            "source_type": "ORGANIZATION",
            "target_name": "Elon Musk",
            "target_type": "PERSON",
            "rel_type": "WORKS_FOR",
            "confidence": 0.95,
            "mention_count": 1,
            "evidence": "CEO relationship"
        },
        {
            "source_name": "Tesla",
            "source_type": "ORGANIZATION",
            "target_name": "United States",
            "target_type": "LOCATION",
            "rel_type": "LOCATED_IN",
            "confidence": 0.99,
            "mention_count": 1,
            "evidence": "Headquartered"
        }
    ])
    return result


@pytest.fixture
def mock_neo4j_query_result_empty():
    """Mock empty Neo4j query result."""
    result = AsyncMock()
    result.data = AsyncMock(return_value=[])
    return result
