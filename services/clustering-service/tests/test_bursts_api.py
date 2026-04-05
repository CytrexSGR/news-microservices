# services/clustering-service/tests/test_bursts_api.py
"""Tests for burst detection API endpoints (Epic 1.3: Task 6).

Uses FastAPI's dependency_overrides for proper test isolation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import List
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.dependencies import get_current_user_id
from app.db.session import get_db
from app.models.burst_alert import BurstAlert


# -----------------------------------------------------------------------------
# Fixtures and Helpers
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_burst_id() -> UUID:
    """Generate a sample burst alert UUID."""
    return uuid4()


@pytest.fixture
def sample_cluster_id() -> UUID:
    """Generate a sample cluster UUID."""
    return uuid4()


@pytest.fixture
def mock_burst_alert(sample_burst_id: UUID, sample_cluster_id: UUID) -> MagicMock:
    """Create a mock BurstAlert object."""
    alert = MagicMock(spec=BurstAlert)
    alert.id = sample_burst_id
    alert.cluster_id = sample_cluster_id
    alert.severity = "high"
    alert.velocity = 15
    alert.window_minutes = 5
    alert.alert_sent = True
    alert.alert_sent_at = datetime.now(timezone.utc)
    alert.acknowledged = False
    alert.acknowledged_at = None
    alert.acknowledged_by = None
    alert.detected_at = datetime.now(timezone.utc)
    return alert


@pytest.fixture
def mock_burst_alerts_list(sample_cluster_id: UUID) -> List[MagicMock]:
    """Create multiple mock burst alerts."""
    alerts = []
    now = datetime.now(timezone.utc)

    for i, severity in enumerate(["low", "medium", "high", "critical"]):
        alert = MagicMock(spec=BurstAlert)
        alert.id = uuid4()
        alert.cluster_id = sample_cluster_id
        alert.severity = severity
        alert.velocity = 3 + (i * 5)
        alert.window_minutes = 5
        alert.alert_sent = i % 2 == 0
        alert.alert_sent_at = now if i % 2 == 0 else None
        alert.acknowledged = False
        alert.acknowledged_at = None
        alert.acknowledged_by = None
        alert.detected_at = now - timedelta(hours=i)
        alerts.append(alert)

    return alerts


def create_mock_session(
    execute_results: list = None,
    get_result: MagicMock = None,
) -> AsyncMock:
    """Create a mock database session with configurable execute results."""
    session = AsyncMock(spec=AsyncSession)

    if execute_results:
        session.execute = AsyncMock(side_effect=execute_results)
    else:
        # Default empty result
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

    session.get = AsyncMock(return_value=get_result)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    return session


def override_dependencies(
    mock_session: AsyncMock,
    user_id: str = "test-user-123"
):
    """Set up dependency overrides for testing."""
    async def mock_get_db():
        yield mock_session

    async def mock_get_user():
        return user_id

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user_id] = mock_get_user


@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# API Endpoint Tests
# -----------------------------------------------------------------------------

class TestBurstsAPIEndpoints:
    """Tests for /api/v1/bursts endpoints."""

    @pytest.mark.asyncio
    async def test_list_bursts_returns_list(
        self,
        mock_burst_alerts_list: List[MagicMock],
    ):
        """Test GET /api/v1/bursts returns burst alerts list."""
        # Set up mock execute results
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = len(mock_burst_alerts_list)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_burst_alerts_list

        mock_session = create_mock_session(
            execute_results=[mock_count_result, mock_result]
        )
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/bursts")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data
        assert data["total"] == 4

    @pytest.mark.asyncio
    async def test_list_active_bursts_returns_unacknowledged(
        self,
        mock_burst_alerts_list: List[MagicMock],
    ):
        """Test GET /api/v1/bursts/active returns only unacknowledged alerts."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_burst_alerts_list[:2]

        mock_session = create_mock_session(
            execute_results=[mock_count_result, mock_result]
        )
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/bursts/active")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_bursts_with_severity_filter(
        self,
        mock_burst_alerts_list: List[MagicMock],
    ):
        """Test GET /api/v1/bursts with severity filter."""
        high_alerts = [a for a in mock_burst_alerts_list if a.severity == "high"]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = len(high_alerts)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = high_alerts

        mock_session = create_mock_session(
            execute_results=[mock_count_result, mock_result]
        )
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/bursts",
                params={"severity": "high"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_burst_stats(self):
        """Test GET /api/v1/bursts/stats returns statistics."""
        # Create mock results for stats queries (24h, 7d, 4 severities, avg)
        results = []
        for val in [10, 50, 20, 15, 10, 5, 12.5]:
            mock_res = MagicMock()
            mock_res.scalar.return_value = val
            results.append(mock_res)

        mock_session = create_mock_session(execute_results=results)
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/bursts/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_bursts_24h" in data
        assert "total_bursts_7d" in data
        assert "by_severity" in data
        assert "avg_velocity" in data
        assert data["total_bursts_24h"] == 10
        assert data["total_bursts_7d"] == 50

    @pytest.mark.asyncio
    async def test_get_burst_by_id(
        self,
        mock_burst_alert: MagicMock,
        sample_burst_id: UUID,
    ):
        """Test GET /api/v1/bursts/{burst_id} returns burst details."""
        mock_session = create_mock_session(get_result=mock_burst_alert)
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/bursts/{sample_burst_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_burst_id)
        assert data["severity"] == "high"
        assert data["velocity"] == 15

    @pytest.mark.asyncio
    async def test_get_burst_by_id_not_found(self):
        """Test GET /api/v1/bursts/{burst_id} returns 404 when not found."""
        non_existent_id = uuid4()

        mock_session = create_mock_session(get_result=None)
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/bursts/{non_existent_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_acknowledge_burst(
        self,
        mock_burst_alert: MagicMock,
        sample_burst_id: UUID,
    ):
        """Test POST /api/v1/bursts/{burst_id}/acknowledge marks burst as acknowledged."""
        mock_burst_alert.acknowledged = False

        mock_session = create_mock_session(get_result=mock_burst_alert)
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/bursts/{sample_burst_id}/acknowledge"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_burst_id)
        assert data["acknowledged"] is True
        assert data["acknowledged_by"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_acknowledge_burst_not_found(self):
        """Test POST /api/v1/bursts/{burst_id}/acknowledge returns 404."""
        non_existent_id = uuid4()

        mock_session = create_mock_session(get_result=None)
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/bursts/{non_existent_id}/acknowledge"
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_acknowledge_already_acknowledged_burst(
        self,
        sample_burst_id: UUID,
        sample_cluster_id: UUID,
    ):
        """Test acknowledging already acknowledged burst returns 400."""
        acknowledged_alert = MagicMock(spec=BurstAlert)
        acknowledged_alert.id = sample_burst_id
        acknowledged_alert.cluster_id = sample_cluster_id
        acknowledged_alert.acknowledged = True
        acknowledged_alert.acknowledged_at = datetime.now(timezone.utc)
        acknowledged_alert.acknowledged_by = "previous-user"

        mock_session = create_mock_session(get_result=acknowledged_alert)
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/bursts/{sample_burst_id}/acknowledge"
            )

        assert response.status_code == 400
        assert "already acknowledged" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_cluster_burst_history(
        self,
        mock_burst_alerts_list: List[MagicMock],
        sample_cluster_id: UUID,
    ):
        """Test GET /api/v1/bursts/cluster/{cluster_id} returns cluster history."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_burst_alerts_list

        mock_session = create_mock_session(execute_results=[mock_result])
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/bursts/cluster/{sample_cluster_id}"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["cluster_id"] == str(sample_cluster_id)
        assert "alerts" in data
        assert "total" in data
        assert data["total"] == 4


class TestBurstsAPIPagination:
    """Tests for pagination in burst endpoints."""

    @pytest.mark.asyncio
    async def test_list_bursts_pagination(self):
        """Test pagination parameters work correctly."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = create_mock_session(
            execute_results=[mock_count_result, mock_result]
        )
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/bursts",
                params={"limit": 10, "offset": 20}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 20
        assert data["total"] == 100
        assert data["has_more"] is True

    @pytest.mark.asyncio
    async def test_list_bursts_hours_filter(self):
        """Test hours filter parameter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = create_mock_session(
            execute_results=[mock_count_result, mock_result]
        )
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/bursts",
                params={"hours": 48}
            )

        assert response.status_code == 200


class TestBurstsAPIValidation:
    """Tests for input validation."""

    @pytest.mark.asyncio
    async def test_list_bursts_invalid_severity(self):
        """Test invalid severity filter is accepted (filtering logic)."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = create_mock_session(
            execute_results=[mock_count_result, mock_result]
        )
        override_dependencies(mock_session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/bursts",
                params={"severity": "invalid"}
            )

        # Should return 200 with empty list (invalid severity matches nothing)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_bursts_hours_out_of_range(self):
        """Test hours parameter out of range returns 422."""
        # Need to override user but not DB since validation happens first
        async def mock_get_user():
            return "test-user-123"
        app.dependency_overrides[get_current_user_id] = mock_get_user

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/bursts",
                params={"hours": 1000}  # Max is 168
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_bursts_limit_out_of_range(self):
        """Test limit parameter out of range returns 422."""
        async def mock_get_user():
            return "test-user-123"
        app.dependency_overrides[get_current_user_id] = mock_get_user

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/bursts",
                params={"limit": 1000}  # Max is 100
            )

        assert response.status_code == 422


class TestBurstsAPIAuth:
    """Tests for authentication requirements."""

    @pytest.mark.asyncio
    async def test_list_bursts_requires_auth(self):
        """Test GET /api/v1/bursts requires authentication."""
        # Don't set any overrides - auth should fail
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/bursts")

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_acknowledge_burst_requires_auth(self):
        """Test POST /api/v1/bursts/{id}/acknowledge requires authentication."""
        burst_id = uuid4()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/bursts/{burst_id}/acknowledge")

        assert response.status_code in [401, 403]
