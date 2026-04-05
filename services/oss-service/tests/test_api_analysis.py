"""
Unit Tests for API Analysis Endpoints.

Tests the analysis API routes with mocked dependencies.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.proposal import AnalysisResult, OntologyChangeProposal, ChangeType, Severity, ImpactAnalysis


class TestAnalysisAPI:
    """Tests for Analysis API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_proposal(self):
        """Create a sample proposal for testing."""
        return OntologyChangeProposal(
            proposal_id="OSS_20251125_120000_abc12345",
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.MEDIUM,
            title="Test Proposal",
            description="Test description",
            confidence=0.8,
            impact_analysis=ImpactAnalysis(
                affected_entities_count=100,
                breaking_change=False,
                migration_complexity="LOW"
            )
        )

    # ========================================================================
    # GET /api/v1/analysis/status Tests
    # ========================================================================

    def test_get_status_success(self, client):
        """Test status endpoint returns service information."""
        with patch("app.api.analysis.get_neo4j") as mock_get_neo4j:
            mock_neo4j = MagicMock()
            mock_neo4j.check_connection.return_value = True
            mock_get_neo4j.return_value = mock_neo4j

            response = client.get("/api/v1/analysis/status")

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "OSS Service"
            assert "version" in data
            assert data["status"] == "operational"

    def test_get_status_neo4j_disconnected(self, client):
        """Test status endpoint when Neo4j is disconnected."""
        with patch("app.api.analysis.get_neo4j") as mock_get_neo4j:
            mock_neo4j = MagicMock()
            mock_neo4j.check_connection.return_value = False
            mock_get_neo4j.return_value = mock_neo4j

            response = client.get("/api/v1/analysis/status")

            assert response.status_code == 200
            data = response.json()
            assert data["neo4j_connected"] is False


class TestRunAnalysisCycle:
    """Tests for run_analysis_cycle function."""

    @pytest.mark.asyncio
    async def test_run_analysis_cycle_success(self):
        """Test successful analysis cycle."""
        from app.api.analysis import run_analysis_cycle

        mock_neo4j = MagicMock()
        # Configure mock to return empty results for all queries
        mock_neo4j.execute_read.return_value = []

        with patch("app.api.analysis.submit_proposal_to_api", new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = True

            result = await run_analysis_cycle(mock_neo4j)

            assert isinstance(result, AnalysisResult)
            assert result.cycle_id.startswith("cycle_")
            assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_run_analysis_cycle_with_proposals(self):
        """Test analysis cycle that generates proposals."""
        from app.api.analysis import run_analysis_cycle

        mock_neo4j = MagicMock()
        # Return entity patterns for first call, empty for rest
        mock_neo4j.execute_read.side_effect = [
            [{"type": "PERSON", "count": 100, "sample_ids": [1, 2, 3]}],  # Entity patterns
            [],  # Relationship patterns
            [],  # ISO violations
            [],  # Duplicates
            [],  # Missing props
            [],  # Unknown entities
            [],  # Article entities
        ]

        with patch("app.api.analysis.submit_proposal_to_api", new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = True

            result = await run_analysis_cycle(mock_neo4j)

            assert result.patterns_detected >= 1
            assert result.proposals_generated >= 1

    @pytest.mark.asyncio
    async def test_run_analysis_cycle_handles_errors(self):
        """Test analysis cycle handles errors gracefully."""
        from app.api.analysis import run_analysis_cycle

        mock_neo4j = MagicMock()
        mock_neo4j.execute_read.side_effect = Exception("Database error")

        result = await run_analysis_cycle(mock_neo4j)

        assert isinstance(result, AnalysisResult)
        assert len(result.errors) > 0
        assert result.completed_at is not None


class TestSubmitProposalToAPI:
    """Tests for submit_proposal_to_api function."""

    @pytest.mark.asyncio
    async def test_submit_proposal_success(self):
        """Test successful proposal submission."""
        from app.api.analysis import submit_proposal_to_api
        from app.models.proposal import OntologyChangeProposal, ChangeType, Severity, ImpactAnalysis

        proposal = OntologyChangeProposal(
            proposal_id="OSS_test_123",
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.MEDIUM,
            title="Test",
            description="Test description",
            confidence=0.8,
            impact_analysis=ImpactAnalysis(
                affected_entities_count=10,
                breaking_change=False,
                migration_complexity="LOW"
            )
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await submit_proposal_to_api(proposal)

            assert result is True

    @pytest.mark.asyncio
    async def test_submit_proposal_failure(self):
        """Test failed proposal submission."""
        from app.api.analysis import submit_proposal_to_api
        from app.models.proposal import OntologyChangeProposal, ChangeType, Severity, ImpactAnalysis

        proposal = OntologyChangeProposal(
            proposal_id="OSS_test_123",
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.MEDIUM,
            title="Test",
            description="Test description",
            confidence=0.8,
            impact_analysis=ImpactAnalysis(
                affected_entities_count=10,
                breaking_change=False,
                migration_complexity="LOW"
            )
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await submit_proposal_to_api(proposal)

            assert result is False

    @pytest.mark.asyncio
    async def test_submit_proposal_network_error(self):
        """Test proposal submission with network error."""
        from app.api.analysis import submit_proposal_to_api
        from app.models.proposal import OntologyChangeProposal, ChangeType, Severity, ImpactAnalysis

        proposal = OntologyChangeProposal(
            proposal_id="OSS_test_123",
            change_type=ChangeType.NEW_ENTITY_TYPE,
            severity=Severity.MEDIUM,
            title="Test",
            description="Test description",
            confidence=0.8,
            impact_analysis=ImpactAnalysis(
                affected_entities_count=10,
                breaking_change=False,
                migration_complexity="LOW"
            )
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await submit_proposal_to_api(proposal)

            assert result is False


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_healthy(self):
        """Test health check when Neo4j is healthy."""
        client = TestClient(app)

        with patch("app.main.check_db_connection") as mock_check:
            mock_check.return_value = True

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["neo4j"] == "connected"

    def test_health_check_degraded(self):
        """Test health check when Neo4j is unhealthy."""
        client = TestClient(app)

        with patch("app.main.check_db_connection") as mock_check:
            mock_check.return_value = False

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["neo4j"] == "disconnected"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint returns service info."""
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["status"] == "running"
        assert "version" in data
