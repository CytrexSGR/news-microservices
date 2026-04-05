"""
Unit Tests for Database Connection.

Tests Neo4j connection management and query execution.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.database import Neo4jConnection, get_neo4j, check_db_connection


class TestNeo4jConnection:
    """Tests for Neo4jConnection class."""

    def test_init(self):
        """Test connection initialization."""
        conn = Neo4jConnection()
        assert conn._driver is None

    def test_connect_success(self):
        """Test successful connection."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_gdb.driver.return_value = mock_driver

            result = conn.connect()

            assert result == mock_driver
            assert conn._driver == mock_driver
            mock_gdb.driver.assert_called_once()

    def test_connect_reuses_existing(self):
        """Test connection reuses existing driver."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_gdb.driver.return_value = mock_driver

            # First connect
            result1 = conn.connect()
            # Second connect should reuse
            result2 = conn.connect()

            assert result1 == result2
            assert mock_gdb.driver.call_count == 1

    def test_connect_failure(self):
        """Test connection failure handling."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_gdb.driver.side_effect = Exception("Connection refused")

            with pytest.raises(Exception) as exc_info:
                conn.connect()

            assert "Connection refused" in str(exc_info.value)

    def test_close(self):
        """Test connection close."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_gdb.driver.return_value = mock_driver

            conn.connect()
            conn.close()

            mock_driver.close.assert_called_once()
            assert conn._driver is None

    def test_close_when_not_connected(self):
        """Test close when not connected."""
        conn = Neo4jConnection()

        # Should not raise
        conn.close()
        assert conn._driver is None

    def test_execute_read_success(self):
        """Test successful query execution."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.data.return_value = {"name": "Test", "count": 10}

            mock_result.__iter__ = lambda self: iter([mock_record])
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)
            mock_gdb.driver.return_value = mock_driver

            results = conn.execute_read("MATCH (n) RETURN n", {})

            assert len(results) == 1
            assert results[0]["name"] == "Test"
            assert results[0]["count"] == 10

    def test_execute_read_with_parameters(self):
        """Test query execution with parameters."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__ = lambda self: iter([])
            mock_session.run.return_value = mock_result
            mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)
            mock_gdb.driver.return_value = mock_driver

            params = {"min_count": 10, "entity_type": "PERSON"}
            conn.execute_read("MATCH (n) WHERE n.count > $min_count RETURN n", params)

            mock_session.run.assert_called_once_with(
                "MATCH (n) WHERE n.count > $min_count RETURN n",
                params
            )

    def test_execute_read_failure(self):
        """Test query execution failure."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_session.run.side_effect = Exception("Query failed")
            mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_driver.session.return_value.__exit__ = MagicMock(return_value=None)
            mock_gdb.driver.return_value = mock_driver

            with pytest.raises(Exception) as exc_info:
                conn.execute_read("INVALID CYPHER", {})

            assert "Query failed" in str(exc_info.value)

    def test_check_connection_success(self):
        """Test connection check success."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_gdb.driver.return_value = mock_driver

            result = conn.check_connection()

            assert result is True
            mock_driver.verify_connectivity.assert_called_once()

    def test_check_connection_failure(self):
        """Test connection check failure."""
        conn = Neo4jConnection()

        with patch("app.database.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.side_effect = Exception("Not connected")
            mock_gdb.driver.return_value = mock_driver

            result = conn.check_connection()

            assert result is False


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_neo4j_returns_connection(self):
        """Test get_neo4j returns connection instance."""
        result = get_neo4j()

        assert isinstance(result, Neo4jConnection)

    def test_check_db_connection(self):
        """Test check_db_connection function."""
        with patch("app.database.neo4j_connection") as mock_conn:
            mock_conn.check_connection.return_value = True

            result = check_db_connection()

            assert result is True
            mock_conn.check_connection.assert_called_once()
