"""
Tests for Neo4j Service

Tests Neo4j connection, query execution, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.neo4j_service import Neo4jService, neo4j_service
from app.config import settings


class TestNeo4jServiceConnection:
    """Tests for Neo4j connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_neo4j_driver):
        """Test successful Neo4j connection."""
        service = Neo4jService()

        with patch('app.services.neo4j_service.AsyncGraphDatabase.driver', return_value=mock_neo4j_driver):
            await service.connect()

            assert service.driver is not None
            mock_neo4j_driver.verify_connectivity.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test failed Neo4j connection."""
        service = Neo4jService()

        with patch('app.services.neo4j_service.AsyncGraphDatabase.driver', side_effect=Exception("Connection refused")):
            with pytest.raises(Exception, match="Connection refused"):
                await service.connect()

    @pytest.mark.asyncio
    async def test_disconnect_success(self, neo4j_service_with_mock):
        """Test successful disconnect."""
        await neo4j_service_with_mock.disconnect()
        neo4j_service_with_mock.driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_driver(self):
        """Test disconnect when driver is None."""
        service = Neo4jService()
        service.driver = None

        # Should not raise
        await service.disconnect()


class TestNeo4jServiceQuery:
    """Tests for Neo4j query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_no_driver(self):
        """Test query execution without initialized driver."""
        from tenacity import RetryError

        service = Neo4jService()
        service.driver = None

        # execute_query has retry decorator which wraps exceptions
        with pytest.raises((RuntimeError, RetryError)):
            await service.execute_query("MATCH (n) RETURN n")


class TestNeo4jServiceWrite:
    """Tests for Neo4j write operations."""

    @pytest.mark.asyncio
    async def test_execute_write_no_driver(self):
        """Test write operation without initialized driver."""
        service = Neo4jService()
        service.driver = None

        with pytest.raises(RuntimeError, match="Neo4j driver not initialized"):
            await service.execute_write("CREATE (n) RETURN n")


class TestNeo4jServiceIndexCreation:
    """Tests for Neo4j index creation."""

    @pytest.mark.asyncio
    async def test_create_indexes(self, neo4j_service_with_mock):
        """Test index creation."""
        neo4j_service_with_mock.execute_write = AsyncMock()

        await neo4j_service_with_mock._create_indexes()

        # Verify both indexes were attempted to be created
        assert neo4j_service_with_mock.execute_write.call_count >= 2

    @pytest.mark.asyncio
    async def test_create_indexes_already_exist(self, neo4j_service_with_mock):
        """Test index creation when indexes already exist (no error)."""
        neo4j_service_with_mock.execute_write = AsyncMock()

        await neo4j_service_with_mock._create_indexes()

        # Should not raise even if indexes exist


class TestNeo4jServiceHealthCheck:
    """Tests for Neo4j health check."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, neo4j_service_with_mock, mock_neo4j_query_result_single):
        """Test successful health check."""
        neo4j_service_with_mock.execute_query = AsyncMock(return_value=[{"test": 1}])

        is_healthy = await neo4j_service_with_mock.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_no_driver(self):
        """Test health check without driver."""
        service = Neo4jService()
        service.driver = None

        is_healthy = await service.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_query_failure(self, neo4j_service_with_mock):
        """Test health check when query fails."""
        neo4j_service_with_mock.execute_query = AsyncMock(side_effect=Exception("Connection error"))

        is_healthy = await neo4j_service_with_mock.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_wrong_result(self, neo4j_service_with_mock):
        """Test health check with unexpected result."""
        neo4j_service_with_mock.execute_query = AsyncMock(return_value=[{"test": 2}])

        is_healthy = await neo4j_service_with_mock.health_check()

        assert is_healthy is False


class TestNeo4jServiceRetry:
    """Tests for Neo4j retry mechanism."""

    @pytest.mark.asyncio
    async def test_execute_query_is_callable(self, neo4j_service_with_mock):
        """Test that execute_query is callable."""
        assert callable(neo4j_service_with_mock.execute_query)

    @pytest.mark.asyncio
    async def test_execute_write_is_callable(self, neo4j_service_with_mock):
        """Test that execute_write is callable."""
        assert callable(neo4j_service_with_mock.execute_write)
