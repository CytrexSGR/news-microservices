"""
Tests for Admin Query Endpoints

Tests custom Cypher query execution with security validation.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAdminCypherQuery:
    """Test admin Cypher query execution endpoint."""

    def test_execute_valid_query(self):
        """Test executing a valid read-only query."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "MATCH (e:Entity) RETURN e.name LIMIT 5",
                "parameters": {},
                "limit": 5,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert "total_results" in data
        assert "query_time_ms" in data
        assert "query_hash" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["total_results"], int)
        assert isinstance(data["query_time_ms"], int)
        assert len(data["query_hash"]) == 64  # SHA256 hash

    def test_execute_parameterized_query(self):
        """Test executing a parameterized query."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "MATCH (e:Entity) WHERE e.type = $entity_type RETURN e.name LIMIT 3",
                "parameters": {"entity_type": "PERSON"},
                "limit": 3,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert isinstance(data["results"], list)

    def test_reject_create_operation(self):
        """Test that CREATE operations are rejected."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "CREATE (n:Entity {name: 'Test'}) RETURN n",
                "parameters": {},
                "limit": 10,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 400
        assert "CREATE" in response.json()["detail"]

    def test_reject_delete_operation(self):
        """Test that DELETE operations are rejected."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "MATCH (e:Entity) DELETE e",
                "parameters": {},
                "limit": 10,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 400
        assert "DELETE" in response.json()["detail"]

    def test_reject_set_operation(self):
        """Test that SET operations are rejected."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "MATCH (e:Entity) SET e.modified = true RETURN e",
                "parameters": {},
                "limit": 10,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 400
        assert "SET" in response.json()["detail"]

    def test_reject_merge_operation(self):
        """Test that MERGE operations are rejected."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "MERGE (n:Entity {name: 'Test'}) RETURN n",
                "parameters": {},
                "limit": 10,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 400
        assert "MERGE" in response.json()["detail"]

    def test_reject_drop_operation(self):
        """Test that DROP operations are rejected."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "DROP INDEX entity_name_index",
                "parameters": {},
                "limit": 10,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 400
        assert "DROP" in response.json()["detail"]

    def test_enforce_max_limit(self):
        """Test that limit is enforced to maximum."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "MATCH (e:Entity) RETURN e",
                "parameters": {},
                "limit": 10000,  # Exceeds max
                "timeout_seconds": 10
            }
        )

        # Should fail validation (limit > 1000)
        assert response.status_code == 422  # Validation error

    def test_auto_add_limit(self):
        """Test that LIMIT is automatically added if missing."""
        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "MATCH (e:Entity) RETURN e.name",  # No LIMIT
                "parameters": {},
                "limit": 5,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should return limited results
        assert len(data["results"]) <= 5


class TestQueryValidation:
    """Test query validation endpoint."""

    def test_validate_valid_query(self):
        """Test validation of a valid query."""
        response = client.post(
            "/api/v1/graph/admin/query/validate",
            json={
                "query": "MATCH (e:Entity) RETURN e.name LIMIT 10",
                "parameters": {}
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is True
        assert data["validation_error"] is None
        assert data["has_limit"] is True
        assert len(data["query_hash"]) == 64

    def test_validate_invalid_query(self):
        """Test validation of an invalid query."""
        response = client.post(
            "/api/v1/graph/admin/query/validate",
            json={
                "query": "CREATE (n:Entity) RETURN n",
                "parameters": {}
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert data["validation_error"] is not None
        assert "CREATE" in data["validation_error"]


class TestAllowedClauses:
    """Test allowed/forbidden clauses endpoint."""

    def test_get_allowed_clauses(self):
        """Test retrieving allowed and forbidden clauses."""
        response = client.get("/api/v1/graph/admin/query/clauses")

        assert response.status_code == 200
        data = response.json()

        assert "allowed_clauses" in data
        assert "forbidden_clauses" in data
        assert "max_query_length" in data
        assert "max_timeout_seconds" in data

        # Check expected clauses
        assert "MATCH" in data["allowed_clauses"]
        assert "RETURN" in data["allowed_clauses"]
        assert "CREATE" in data["forbidden_clauses"]
        assert "DELETE" in data["forbidden_clauses"]

        # Check limits
        assert data["max_query_length"] == 10000
        assert data["max_timeout_seconds"] == 30


class TestQueryExamples:
    """Test query examples endpoint."""

    def test_get_query_examples(self):
        """Test retrieving example queries."""
        response = client.get("/api/v1/graph/admin/query/examples")

        assert response.status_code == 200
        data = response.json()

        assert "examples" in data
        assert "total_examples" in data
        assert len(data["examples"]) > 0

        # Check example structure
        example = data["examples"][0]
        assert "title" in example
        assert "description" in example
        assert "query" in example
        assert "parameters" in example


class TestSecurityLogging:
    """Test that admin queries are properly logged."""

    def test_admin_query_creates_warning_log(self, caplog):
        """Test that admin queries generate WARNING level logs."""
        import logging
        caplog.set_level(logging.WARNING)

        response = client.post(
            "/api/v1/graph/admin/query/cypher",
            json={
                "query": "MATCH (e:Entity) RETURN e.name LIMIT 1",
                "parameters": {},
                "limit": 1,
                "timeout_seconds": 10
            }
        )

        assert response.status_code == 200

        # Check that WARNING log was created
        warning_logs = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_logs) > 0

        # Check log contains admin query information
        admin_log = next((r for r in warning_logs if "ADMIN QUERY" in r.message), None)
        assert admin_log is not None
        assert "query_length" in admin_log.message
        assert "timeout" in admin_log.message
