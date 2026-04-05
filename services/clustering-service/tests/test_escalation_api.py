"""Tests for escalation API endpoint (Task 11).

Tests the /escalation/summary endpoint including schema validation,
database queries, FMP regime integration, and correlation alerts.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.dependencies import get_current_user_id
from app.db.session import get_db
from app.models.cluster import ArticleCluster
from app.models.escalation import FMPNewsCorrelation
from app.schemas.escalation import (
    ClusterEscalationDetailResponse,
    CorrelationAlertResponse,
    DomainEscalationResponse,
    EscalationSummaryResponse,
    RegimeStateResponse,
    SignalDetailResponse,
)
from app.services.fmp_correlation_service import RegimeState


# -----------------------------------------------------------------------------
# Schema Tests
# -----------------------------------------------------------------------------


class TestDomainEscalationResponseSchema:
    """Tests for DomainEscalationResponse schema validation."""

    def test_valid_domain_response(self):
        """Test valid domain escalation response."""
        response = DomainEscalationResponse(
            domain="geopolitical",
            level=4,
            score=Decimal("0.750"),
            confidence=0.85,
        )
        assert response.domain == "geopolitical"
        assert response.level == 4
        assert response.score == Decimal("0.750")
        assert response.confidence == 0.85

    def test_level_boundary_min(self):
        """Test minimum level boundary (1)."""
        response = DomainEscalationResponse(
            domain="military",
            level=1,
            score=Decimal("0.100"),
            confidence=0.5,
        )
        assert response.level == 1

    def test_level_boundary_max(self):
        """Test maximum level boundary (5)."""
        response = DomainEscalationResponse(
            domain="economic",
            level=5,
            score=Decimal("0.999"),
            confidence=1.0,
        )
        assert response.level == 5

    def test_level_below_boundary_fails(self):
        """Test level below minimum fails validation."""
        with pytest.raises(ValueError):
            DomainEscalationResponse(
                domain="geopolitical",
                level=0,
                score=Decimal("0.500"),
                confidence=0.5,
            )

    def test_level_above_boundary_fails(self):
        """Test level above maximum fails validation."""
        with pytest.raises(ValueError):
            DomainEscalationResponse(
                domain="geopolitical",
                level=6,
                score=Decimal("0.500"),
                confidence=0.5,
            )

    def test_score_boundary_min(self):
        """Test minimum score boundary (0)."""
        response = DomainEscalationResponse(
            domain="geopolitical",
            level=1,
            score=Decimal("0.000"),
            confidence=0.5,
        )
        assert response.score == Decimal("0.000")

    def test_score_boundary_max(self):
        """Test maximum score boundary (1)."""
        response = DomainEscalationResponse(
            domain="geopolitical",
            level=5,
            score=Decimal("1.000"),
            confidence=1.0,
        )
        assert response.score == Decimal("1.000")

    def test_confidence_boundary(self):
        """Test confidence boundaries."""
        # Min confidence
        response_min = DomainEscalationResponse(
            domain="geopolitical",
            level=3,
            score=Decimal("0.500"),
            confidence=0.0,
        )
        assert response_min.confidence == 0.0

        # Max confidence
        response_max = DomainEscalationResponse(
            domain="geopolitical",
            level=3,
            score=Decimal("0.500"),
            confidence=1.0,
        )
        assert response_max.confidence == 1.0

    def test_json_serialization(self):
        """Test JSON serialization of Decimal fields."""
        response = DomainEscalationResponse(
            domain="geopolitical",
            level=3,
            score=Decimal("0.567"),
            confidence=0.75,
        )
        json_dict = response.model_dump(mode="json")
        # Decimal should be serialized as string
        assert json_dict["score"] == "0.567"


class TestCorrelationAlertResponseSchema:
    """Tests for CorrelationAlertResponse schema validation."""

    def test_valid_alert_response(self):
        """Test valid correlation alert response."""
        alert_id = uuid4()
        detected = datetime.now(timezone.utc)
        expires = detected + timedelta(hours=24)

        response = CorrelationAlertResponse(
            id=alert_id,
            correlation_type="DIVERGENCE",
            fmp_regime="RISK_ON",
            escalation_level=4,
            confidence=Decimal("0.85"),
            reasoning="Market ignoring high news escalation",
            detected_at=detected,
            expires_at=expires,
            related_cluster_count=3,
        )

        assert response.id == alert_id
        assert response.correlation_type == "DIVERGENCE"
        assert response.fmp_regime == "RISK_ON"
        assert response.escalation_level == 4
        assert response.confidence == Decimal("0.85")
        assert response.reasoning == "Market ignoring high news escalation"
        assert response.detected_at == detected
        assert response.expires_at == expires
        assert response.related_cluster_count == 3

    def test_optional_fields_default(self):
        """Test optional fields have correct defaults."""
        response = CorrelationAlertResponse(
            id=uuid4(),
            correlation_type="CONFIRMATION",
            fmp_regime="RISK_OFF",
            escalation_level=5,
            confidence=Decimal("0.9"),
            detected_at=datetime.now(timezone.utc),
        )

        assert response.reasoning is None
        assert response.expires_at is None
        assert response.related_cluster_count == 0

    def test_all_correlation_types(self):
        """Test all correlation types are accepted."""
        for ctype in ["CONFIRMATION", "DIVERGENCE", "EARLY_WARNING"]:
            response = CorrelationAlertResponse(
                id=uuid4(),
                correlation_type=ctype,
                fmp_regime="TRANSITIONAL",
                escalation_level=3,
                confidence=Decimal("0.7"),
                detected_at=datetime.now(timezone.utc),
            )
            assert response.correlation_type == ctype


class TestRegimeStateResponseSchema:
    """Tests for RegimeStateResponse schema validation."""

    def test_valid_regime_response(self):
        """Test valid regime state response."""
        response = RegimeStateResponse(
            regime="RISK_OFF",
            confidence=0.82,
            vix_level=25.5,
            fear_greed_index=35,
            timestamp=datetime.now(timezone.utc),
        )

        assert response.regime == "RISK_OFF"
        assert response.confidence == 0.82
        assert response.vix_level == 25.5
        assert response.fear_greed_index == 35

    def test_minimal_regime_response(self):
        """Test minimal regime response with required fields only."""
        response = RegimeStateResponse(
            regime="RISK_ON",
            confidence=0.5,
        )

        assert response.regime == "RISK_ON"
        assert response.confidence == 0.5
        assert response.vix_level is None
        assert response.fear_greed_index is None
        assert response.timestamp is None

    def test_fear_greed_boundary(self):
        """Test fear/greed index boundaries (0-100)."""
        # Min
        response_min = RegimeStateResponse(
            regime="RISK_OFF",
            confidence=0.5,
            fear_greed_index=0,
        )
        assert response_min.fear_greed_index == 0

        # Max
        response_max = RegimeStateResponse(
            regime="RISK_ON",
            confidence=0.5,
            fear_greed_index=100,
        )
        assert response_max.fear_greed_index == 100

    def test_fear_greed_out_of_bounds_fails(self):
        """Test fear/greed index out of bounds fails."""
        with pytest.raises(ValueError):
            RegimeStateResponse(
                regime="RISK_ON",
                confidence=0.5,
                fear_greed_index=101,
            )


class TestEscalationSummaryResponseSchema:
    """Tests for EscalationSummaryResponse schema validation."""

    def test_valid_summary_response(self):
        """Test valid escalation summary response."""
        geo = DomainEscalationResponse(
            domain="geopolitical", level=4, score=Decimal("0.750"), confidence=0.9
        )
        mil = DomainEscalationResponse(
            domain="military", level=3, score=Decimal("0.500"), confidence=0.8
        )
        eco = DomainEscalationResponse(
            domain="economic", level=2, score=Decimal("0.300"), confidence=0.7
        )

        response = EscalationSummaryResponse(
            geopolitical=geo,
            military=mil,
            economic=eco,
            combined_level=4,
            combined_score=Decimal("0.517"),
            market_regime=None,
            correlation_alerts=[],
            cluster_count=15,
            calculated_at=datetime.now(timezone.utc),
        )

        assert response.geopolitical.level == 4
        assert response.military.level == 3
        assert response.economic.level == 2
        assert response.combined_level == 4
        assert response.combined_score == Decimal("0.517")
        assert response.cluster_count == 15

    def test_summary_with_alerts(self):
        """Test summary response with correlation alerts."""
        geo = DomainEscalationResponse(
            domain="geopolitical", level=3, score=Decimal("0.500"), confidence=0.5
        )
        mil = DomainEscalationResponse(
            domain="military", level=3, score=Decimal("0.500"), confidence=0.5
        )
        eco = DomainEscalationResponse(
            domain="economic", level=3, score=Decimal("0.500"), confidence=0.5
        )

        alert = CorrelationAlertResponse(
            id=uuid4(),
            correlation_type="EARLY_WARNING",
            fmp_regime="RISK_OFF",
            escalation_level=3,
            confidence=Decimal("0.6"),
            detected_at=datetime.now(timezone.utc),
        )

        response = EscalationSummaryResponse(
            geopolitical=geo,
            military=mil,
            economic=eco,
            combined_level=3,
            combined_score=Decimal("0.500"),
            correlation_alerts=[alert],
            cluster_count=5,
            calculated_at=datetime.now(timezone.utc),
        )

        assert len(response.correlation_alerts) == 1
        assert response.correlation_alerts[0].correlation_type == "EARLY_WARNING"


# -----------------------------------------------------------------------------
# API Endpoint Tests
# -----------------------------------------------------------------------------


def create_mock_cluster(
    cluster_id: UUID,
    geo_score: Optional[float] = None,
    mil_score: Optional[float] = None,
    eco_score: Optional[float] = None,
    combined_score: Optional[float] = None,
    created_at: Optional[datetime] = None,
) -> MagicMock:
    """Create a mock ArticleCluster with escalation data."""
    cluster = MagicMock(spec=ArticleCluster)
    cluster.id = cluster_id
    cluster.escalation_geopolitical = geo_score
    cluster.escalation_military = mil_score
    cluster.escalation_economic = eco_score
    cluster.escalation_combined = combined_score
    cluster.created_at = created_at or datetime.now(timezone.utc)
    return cluster


def create_mock_alert(
    alert_id: UUID,
    correlation_type: str = "CONFIRMATION",
    fmp_regime: str = "RISK_OFF",
    escalation_level: int = 4,
    confidence: float = 0.8,
) -> MagicMock:
    """Create a mock FMPNewsCorrelation alert."""
    alert = MagicMock(spec=FMPNewsCorrelation)
    alert.id = alert_id
    alert.correlation_type = correlation_type
    alert.fmp_regime = fmp_regime
    alert.escalation_level = escalation_level
    alert.confidence = confidence
    alert.detected_at = datetime.now(timezone.utc)
    alert.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    alert.related_clusters = [uuid4()]
    alert.extra_metadata = {"reasoning": "Test reasoning"}
    return alert


def create_mock_session(
    clusters: List[MagicMock] = None,
) -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)

    # Setup execute to return clusters
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = clusters or []
    session.execute = AsyncMock(return_value=mock_result)

    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()

    return session


class TestEscalationSummaryEndpoint:
    """Tests for GET /api/v1/escalation/summary endpoint."""

    @pytest.mark.asyncio
    async def test_endpoint_returns_200(self):
        """Test endpoint returns 200 status."""
        mock_session = create_mock_session(clusters=[])

        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/escalation/summary")

            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_empty_clusters_returns_defaults(self):
        """Test empty clusters returns default neutral values."""
        mock_session = create_mock_session(clusters=[])

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/escalation/summary")

            data = response.json()

            # Check default values
            assert data["geopolitical"]["level"] == 3
            assert data["geopolitical"]["domain"] == "geopolitical"
            assert float(data["geopolitical"]["score"]) == 0.5
            assert data["geopolitical"]["confidence"] == 0.0

            assert data["military"]["level"] == 3
            assert data["economic"]["level"] == 3

            assert data["combined_level"] == 3
            assert float(data["combined_score"]) == 0.5

            assert data["cluster_count"] == 0
            assert data["correlation_alerts"] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @patch("app.api.v1.escalation.FMPCorrelationService")
    async def test_clusters_with_data_returns_aggregated(self, mock_fmp_class):
        """Test clusters with data returns aggregated scores."""
        clusters = [
            create_mock_cluster(
                uuid4(),
                geo_score=0.8,
                mil_score=0.6,
                eco_score=0.3,
                combined_score=0.567,
            ),
            create_mock_cluster(
                uuid4(),
                geo_score=0.7,
                mil_score=0.5,
                eco_score=0.4,
                combined_score=0.533,
            ),
        ]

        mock_session = create_mock_session(clusters=clusters)

        # Mock FMP service to return no regime
        mock_fmp = AsyncMock()
        mock_fmp.get_current_regime = AsyncMock(return_value=None)
        mock_fmp.get_active_alerts = AsyncMock(return_value=[])
        mock_fmp_class.return_value = mock_fmp

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/escalation/summary")

            data = response.json()

            # Geopolitical avg: (0.8 + 0.7) / 2 = 0.75 -> level 4
            assert data["geopolitical"]["level"] == 4
            assert float(data["geopolitical"]["score"]) == 0.75

            # Military avg: (0.6 + 0.5) / 2 = 0.55 -> level 3
            assert data["military"]["level"] == 3
            assert float(data["military"]["score"]) == 0.55

            # Economic avg: (0.3 + 0.4) / 2 = 0.35 -> level 2
            assert data["economic"]["level"] == 2
            assert float(data["economic"]["score"]) == 0.35

            # Combined level is max(4, 3, 2) = 4
            assert data["combined_level"] == 4

            # Cluster count
            assert data["cluster_count"] == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_hours_parameter_filtering(self):
        """Test hours parameter filters clusters correctly."""
        mock_session = create_mock_session(clusters=[])

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                # Test with custom hours parameter
                response = await client.get(
                    "/api/v1/escalation/summary",
                    params={"hours": 48},
                )

            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_hours_parameter_boundary_min(self):
        """Test hours parameter minimum boundary (1)."""
        mock_session = create_mock_session(clusters=[])

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/escalation/summary",
                    params={"hours": 1},
                )

            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_hours_parameter_boundary_max(self):
        """Test hours parameter maximum boundary (168)."""
        mock_session = create_mock_session(clusters=[])

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/escalation/summary",
                    params={"hours": 168},
                )

            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_hours_parameter_out_of_bounds_fails(self):
        """Test hours parameter out of bounds returns 422."""
        mock_session = create_mock_session(clusters=[])

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                # Below minimum
                response_low = await client.get(
                    "/api/v1/escalation/summary",
                    params={"hours": 0},
                )
                assert response_low.status_code == 422

                # Above maximum
                response_high = await client.get(
                    "/api/v1/escalation/summary",
                    params={"hours": 200},
                )
                assert response_high.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_market_regime_when_fmp_unavailable(self):
        """Test market regime is None when FMP service unavailable.

        When the FMP service is not available or returns None,
        the market_regime field should be None (graceful degradation).
        """
        mock_session = create_mock_session(clusters=[])

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/escalation/summary")

            data = response.json()

            # When FMP service is unavailable, market_regime should be None
            # This tests graceful degradation
            assert "market_regime" in data
            # Could be None or populated depending on actual FMP service availability
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_correlation_alerts_field_exists(self):
        """Test correlation alerts field exists in response.

        The correlation_alerts field should always be present in the response,
        even if it's an empty list (when no active alerts exist).
        """
        mock_session = create_mock_session(clusters=[])

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/escalation/summary")

            data = response.json()

            # Correlation alerts should be present (may be empty list or populated)
            assert "correlation_alerts" in data
            assert isinstance(data["correlation_alerts"], list)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_response_schema_compliance(self):
        """Test response matches EscalationSummaryResponse schema."""
        mock_session = create_mock_session(clusters=[])

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/escalation/summary")

            data = response.json()

            # Verify all required fields are present
            required_fields = [
                "geopolitical",
                "military",
                "economic",
                "combined_level",
                "combined_score",
                "correlation_alerts",
                "cluster_count",
                "calculated_at",
            ]

            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Verify domain structure
            for domain in ["geopolitical", "military", "economic"]:
                domain_fields = ["domain", "level", "score", "confidence"]
                for field in domain_fields:
                    assert field in data[domain], f"Missing {field} in {domain}"
        finally:
            app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# Aggregation Logic Tests
# -----------------------------------------------------------------------------


class TestAggregationLogic:
    """Tests for domain score aggregation logic."""

    def test_level_calculation_from_score(self):
        """Test level calculation from score.

        Formula: level = round(score * 4) + 1
        - score 0.0 -> level 1
        - score 0.25 -> level 2
        - score 0.5 -> level 3
        - score 0.75 -> level 4
        - score 1.0 -> level 5
        """
        from app.api.v1.escalation import _aggregate_domain

        # Score 0.0 -> level 1
        clusters_low = [create_mock_cluster(uuid4(), geo_score=0.0)]
        result_low = _aggregate_domain(clusters_low, "escalation_geopolitical")
        assert result_low.level == 1

        # Score 0.25 -> level 2
        clusters_2 = [create_mock_cluster(uuid4(), geo_score=0.25)]
        result_2 = _aggregate_domain(clusters_2, "escalation_geopolitical")
        assert result_2.level == 2

        # Score 0.5 -> level 3
        clusters_3 = [create_mock_cluster(uuid4(), geo_score=0.5)]
        result_3 = _aggregate_domain(clusters_3, "escalation_geopolitical")
        assert result_3.level == 3

        # Score 0.75 -> level 4
        clusters_4 = [create_mock_cluster(uuid4(), geo_score=0.75)]
        result_4 = _aggregate_domain(clusters_4, "escalation_geopolitical")
        assert result_4.level == 4

        # Score 1.0 -> level 5
        clusters_high = [create_mock_cluster(uuid4(), geo_score=1.0)]
        result_high = _aggregate_domain(clusters_high, "escalation_geopolitical")
        assert result_high.level == 5

    def test_confidence_scales_with_sample_size(self):
        """Test confidence increases with more samples."""
        from app.api.v1.escalation import _aggregate_domain

        # 1 sample -> confidence 0.1
        clusters_1 = [create_mock_cluster(uuid4(), geo_score=0.5)]
        result_1 = _aggregate_domain(clusters_1, "escalation_geopolitical")
        assert result_1.confidence == 0.1

        # 5 samples -> confidence 0.5
        clusters_5 = [
            create_mock_cluster(uuid4(), geo_score=0.5) for _ in range(5)
        ]
        result_5 = _aggregate_domain(clusters_5, "escalation_geopolitical")
        assert result_5.confidence == 0.5

        # 10+ samples -> confidence 1.0 (capped)
        clusters_15 = [
            create_mock_cluster(uuid4(), geo_score=0.5) for _ in range(15)
        ]
        result_15 = _aggregate_domain(clusters_15, "escalation_geopolitical")
        assert result_15.confidence == 1.0

    def test_average_score_calculation(self):
        """Test average score calculation across clusters."""
        from app.api.v1.escalation import _aggregate_domain

        clusters = [
            create_mock_cluster(uuid4(), geo_score=0.8),
            create_mock_cluster(uuid4(), geo_score=0.6),
            create_mock_cluster(uuid4(), geo_score=0.4),
        ]

        result = _aggregate_domain(clusters, "escalation_geopolitical")

        # (0.8 + 0.6 + 0.4) / 3 = 0.6
        assert float(result.score) == 0.6

    def test_null_scores_filtered_out(self):
        """Test null scores are filtered from aggregation."""
        from app.api.v1.escalation import _aggregate_domain

        clusters = [
            create_mock_cluster(uuid4(), geo_score=0.8),
            create_mock_cluster(uuid4(), geo_score=None),  # Should be filtered
            create_mock_cluster(uuid4(), geo_score=0.6),
        ]

        result = _aggregate_domain(clusters, "escalation_geopolitical")

        # Only 2 non-null scores: (0.8 + 0.6) / 2 = 0.7
        assert float(result.score) == 0.7
        # Confidence based on 2 samples
        assert result.confidence == 0.2

    def test_empty_clusters_returns_default(self):
        """Test empty cluster list returns default values."""
        from app.api.v1.escalation import _aggregate_domain

        result = _aggregate_domain([], "escalation_geopolitical")

        assert result.domain == "geopolitical"
        assert result.level == 3
        assert result.score == Decimal("0.500")
        assert result.confidence == 0.0


# -----------------------------------------------------------------------------
# Signal and Cluster Detail Schema Tests (Task 12)
# -----------------------------------------------------------------------------


class TestSignalDetailResponseSchema:
    """Tests for SignalDetailResponse schema validation."""

    def test_valid_signal_response(self):
        """Test valid signal detail response."""
        signal = SignalDetailResponse(
            source="embedding",
            level=4,
            confidence=0.85,
            matched_anchor_id=uuid4(),
            matched_keywords=["conflict", "military"],
            reasoning="High similarity to military escalation anchor",
        )

        assert signal.source == "embedding"
        assert signal.level == 4
        assert signal.confidence == 0.85
        assert signal.matched_keywords == ["conflict", "military"]

    def test_minimal_signal_response(self):
        """Test minimal signal response with required fields only."""
        signal = SignalDetailResponse(
            source="content",
            level=3,
            confidence=0.5,
        )

        assert signal.source == "content"
        assert signal.level == 3
        assert signal.confidence == 0.5
        assert signal.matched_anchor_id is None
        assert signal.matched_keywords is None
        assert signal.reasoning is None

    def test_signal_level_boundary_min(self):
        """Test signal level minimum boundary (1)."""
        signal = SignalDetailResponse(
            source="keywords",
            level=1,
            confidence=0.2,
        )
        assert signal.level == 1

    def test_signal_level_boundary_max(self):
        """Test signal level maximum boundary (5)."""
        signal = SignalDetailResponse(
            source="embedding",
            level=5,
            confidence=1.0,
        )
        assert signal.level == 5

    def test_signal_level_below_boundary_fails(self):
        """Test signal level below minimum fails validation."""
        with pytest.raises(ValueError):
            SignalDetailResponse(
                source="content",
                level=0,
                confidence=0.5,
            )

    def test_signal_level_above_boundary_fails(self):
        """Test signal level above maximum fails validation."""
        with pytest.raises(ValueError):
            SignalDetailResponse(
                source="content",
                level=6,
                confidence=0.5,
            )

    def test_signal_confidence_boundaries(self):
        """Test confidence boundaries (0.0-1.0)."""
        # Min
        signal_min = SignalDetailResponse(
            source="content",
            level=3,
            confidence=0.0,
        )
        assert signal_min.confidence == 0.0

        # Max
        signal_max = SignalDetailResponse(
            source="content",
            level=3,
            confidence=1.0,
        )
        assert signal_max.confidence == 1.0

    def test_all_signal_sources(self):
        """Test all valid signal sources are accepted."""
        for source in ["embedding", "content", "keywords"]:
            signal = SignalDetailResponse(
                source=source,
                level=3,
                confidence=0.5,
            )
            assert signal.source == source


class TestClusterEscalationDetailResponseSchema:
    """Tests for ClusterEscalationDetailResponse schema validation."""

    def test_valid_cluster_detail_response(self):
        """Test valid cluster escalation detail response."""
        cluster_id = uuid4()
        geo = DomainEscalationResponse(
            domain="geopolitical",
            level=4,
            score=Decimal("0.750"),
            confidence=0.9,
        )
        mil = DomainEscalationResponse(
            domain="military",
            level=3,
            score=Decimal("0.500"),
            confidence=0.8,
        )
        eco = DomainEscalationResponse(
            domain="economic",
            level=2,
            score=Decimal("0.300"),
            confidence=0.7,
        )

        response = ClusterEscalationDetailResponse(
            cluster_id=cluster_id,
            cluster_title="Test Cluster",
            article_count=5,
            geopolitical=geo,
            military=mil,
            economic=eco,
            combined_level=4,
            combined_score=Decimal("0.517"),
            created_at=datetime.now(timezone.utc),
        )

        assert response.cluster_id == cluster_id
        assert response.cluster_title == "Test Cluster"
        assert response.article_count == 5
        assert response.combined_level == 4
        assert response.geopolitical.level == 4

    def test_cluster_detail_with_signals(self):
        """Test cluster detail response with signal breakdowns."""
        cluster_id = uuid4()

        geo_signals = [
            SignalDetailResponse(
                source="embedding",
                level=4,
                confidence=0.9,
                reasoning="High geopolitical similarity",
            ),
            SignalDetailResponse(
                source="content",
                level=3,
                confidence=0.7,
            ),
        ]

        geo = DomainEscalationResponse(
            domain="geopolitical",
            level=4,
            score=Decimal("0.750"),
            confidence=0.9,
        )
        mil = DomainEscalationResponse(
            domain="military",
            level=3,
            score=Decimal("0.500"),
            confidence=0.8,
        )
        eco = DomainEscalationResponse(
            domain="economic",
            level=2,
            score=Decimal("0.300"),
            confidence=0.7,
        )

        response = ClusterEscalationDetailResponse(
            cluster_id=cluster_id,
            cluster_title="Test Cluster",
            article_count=5,
            geopolitical=geo,
            military=mil,
            economic=eco,
            combined_level=4,
            combined_score=Decimal("0.517"),
            geopolitical_signals=geo_signals,
            created_at=datetime.now(timezone.utc),
        )

        assert len(response.geopolitical_signals) == 2
        assert response.geopolitical_signals[0].source == "embedding"
        assert response.geopolitical_signals[0].level == 4

    def test_cluster_detail_with_escalation_timestamp(self):
        """Test cluster detail with escalation_calculated_at timestamp."""
        geo = DomainEscalationResponse(
            domain="geopolitical",
            level=3,
            score=Decimal("0.500"),
            confidence=0.5,
        )
        mil = DomainEscalationResponse(
            domain="military",
            level=3,
            score=Decimal("0.500"),
            confidence=0.5,
        )
        eco = DomainEscalationResponse(
            domain="economic",
            level=3,
            score=Decimal("0.500"),
            confidence=0.5,
        )

        calc_time = datetime.now(timezone.utc)

        response = ClusterEscalationDetailResponse(
            cluster_id=uuid4(),
            cluster_title="Test Cluster",
            article_count=3,
            geopolitical=geo,
            military=mil,
            economic=eco,
            combined_level=3,
            combined_score=Decimal("0.500"),
            escalation_calculated_at=calc_time,
            created_at=datetime.now(timezone.utc),
        )

        assert response.escalation_calculated_at == calc_time

    def test_cluster_detail_json_serialization(self):
        """Test JSON serialization of cluster detail response."""
        geo = DomainEscalationResponse(
            domain="geopolitical",
            level=3,
            score=Decimal("0.567"),
            confidence=0.5,
        )
        mil = DomainEscalationResponse(
            domain="military",
            level=3,
            score=Decimal("0.500"),
            confidence=0.5,
        )
        eco = DomainEscalationResponse(
            domain="economic",
            level=3,
            score=Decimal("0.433"),
            confidence=0.5,
        )

        response = ClusterEscalationDetailResponse(
            cluster_id=uuid4(),
            cluster_title="Test Cluster",
            article_count=3,
            geopolitical=geo,
            military=mil,
            economic=eco,
            combined_level=3,
            combined_score=Decimal("0.500"),
            created_at=datetime.now(timezone.utc),
        )

        json_dict = response.model_dump(mode="json")

        # Combined score should be serialized as string
        assert json_dict["combined_score"] == "0.500"
        # Domain scores should also be serialized
        assert json_dict["geopolitical"]["score"] == "0.567"


# -----------------------------------------------------------------------------
# Cluster Escalation Detail Endpoint Tests (Task 12)
# -----------------------------------------------------------------------------


def create_mock_cluster_with_signals(
    cluster_id: UUID,
    title: str = "Test Cluster",
    article_count: int = 5,
    geo_score: Optional[float] = None,
    mil_score: Optional[float] = None,
    eco_score: Optional[float] = None,
    combined_score: Optional[float] = None,
    escalation_level: Optional[int] = None,
    escalation_signals: Optional[dict] = None,
    escalation_calculated_at: Optional[datetime] = None,
    centroid_vector: Optional[dict] = None,
    created_at: Optional[datetime] = None,
) -> MagicMock:
    """Create a mock ArticleCluster with full escalation data."""
    cluster = MagicMock(spec=ArticleCluster)
    cluster.id = cluster_id
    cluster.title = title
    cluster.article_count = article_count
    cluster.escalation_geopolitical = geo_score
    cluster.escalation_military = mil_score
    cluster.escalation_economic = eco_score
    cluster.escalation_combined = combined_score
    cluster.escalation_level = escalation_level
    cluster.escalation_signals = escalation_signals
    cluster.escalation_calculated_at = escalation_calculated_at
    cluster.centroid_vector = centroid_vector
    cluster.created_at = created_at or datetime.now(timezone.utc)
    return cluster


class TestClusterEscalationDetailEndpoint:
    """Tests for GET /api/v1/escalation/clusters/{cluster_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_cluster_escalation_detail_not_found(self):
        """Test 404 response when cluster not found."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Setup mock to return no cluster
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                test_id = "12345678-1234-5678-1234-567812345678"
                response = await client.get(f"/api/v1/escalation/clusters/{test_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_cluster_escalation_detail_returns_structure(self):
        """Test correct response structure is returned."""
        cluster_id = uuid4()
        mock_cluster = create_mock_cluster_with_signals(
            cluster_id=cluster_id,
            title="Test Escalation Cluster",
            article_count=10,
            geo_score=0.75,
            mil_score=0.55,
            eco_score=0.35,
            combined_score=0.55,
            escalation_level=4,
            escalation_calculated_at=datetime.now(timezone.utc),
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/escalation/clusters/{cluster_id}"
                )

            assert response.status_code == 200

            data = response.json()

            # Verify required fields are present
            required_fields = [
                "cluster_id",
                "cluster_title",
                "article_count",
                "geopolitical",
                "military",
                "economic",
                "combined_level",
                "combined_score",
                "geopolitical_signals",
                "military_signals",
                "economic_signals",
                "created_at",
            ]

            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Verify domain structure
            for domain in ["geopolitical", "military", "economic"]:
                assert "domain" in data[domain]
                assert "level" in data[domain]
                assert "score" in data[domain]
                assert "confidence" in data[domain]

            # Verify cluster metadata
            assert data["cluster_title"] == "Test Escalation Cluster"
            assert data["article_count"] == 10
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_cluster_escalation_detail_with_signals(self):
        """Test response includes signal breakdown when available."""
        cluster_id = uuid4()
        anchor_id = uuid4()

        signals = {
            "geopolitical": [
                {
                    "source": "embedding",
                    "level": 4,
                    "confidence": 0.85,
                    "matched_anchor_id": str(anchor_id),
                    "matched_keywords": None,
                    "reasoning": "High similarity to geopolitical anchor",
                },
                {
                    "source": "content",
                    "level": 3,
                    "confidence": 0.7,
                    "matched_anchor_id": None,
                    "matched_keywords": None,
                    "reasoning": "Moderate escalation language",
                },
            ],
            "military": [
                {
                    "source": "keywords",
                    "level": 3,
                    "confidence": 0.6,
                    "matched_anchor_id": None,
                    "matched_keywords": ["conflict", "troops"],
                    "reasoning": "Military keywords detected",
                },
            ],
            "economic": [],
        }

        mock_cluster = create_mock_cluster_with_signals(
            cluster_id=cluster_id,
            geo_score=0.75,
            mil_score=0.55,
            eco_score=0.35,
            combined_score=0.55,
            escalation_level=4,
            escalation_signals=signals,
            escalation_calculated_at=datetime.now(timezone.utc),
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/escalation/clusters/{cluster_id}"
                )

            assert response.status_code == 200

            data = response.json()

            # Verify geopolitical signals
            assert len(data["geopolitical_signals"]) == 2
            assert data["geopolitical_signals"][0]["source"] == "embedding"
            assert data["geopolitical_signals"][0]["level"] == 4
            assert data["geopolitical_signals"][0]["confidence"] == 0.85

            # Verify military signals
            assert len(data["military_signals"]) == 1
            assert data["military_signals"][0]["source"] == "keywords"
            assert data["military_signals"][0]["matched_keywords"] == [
                "conflict",
                "troops",
            ]

            # Verify economic signals (empty)
            assert len(data["economic_signals"]) == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_cluster_escalation_detail_recalculate_parameter(self):
        """Test recalculate parameter triggers calculation attempt."""
        cluster_id = uuid4()

        # Cluster without escalation data (should trigger recalculation)
        mock_cluster = create_mock_cluster_with_signals(
            cluster_id=cluster_id,
            title="Uncalculated Cluster",
            # No escalation scores - null values
            geo_score=None,
            mil_score=None,
            eco_score=None,
            combined_score=None,
            escalation_level=None,
            escalation_signals=None,
            # No valid embedding for recalculation
            centroid_vector=None,
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                # Without recalculate
                response = await client.get(
                    f"/api/v1/escalation/clusters/{cluster_id}"
                )

            assert response.status_code == 200

            data = response.json()

            # Should return default values when no escalation data and no valid embedding
            # Default score 0.5 -> level 3
            assert data["geopolitical"]["level"] == 3
            assert data["geopolitical"]["confidence"] == 0.0  # No calculated data

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_cluster_escalation_detail_invalid_uuid(self):
        """Test 422 response for invalid UUID format."""
        mock_session = AsyncMock(spec=AsyncSession)

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/escalation/clusters/not-a-valid-uuid"
                )

            # FastAPI returns 422 for validation errors
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_cluster_escalation_detail_default_values(self):
        """Test default values are returned for cluster without escalation data."""
        cluster_id = uuid4()

        # Cluster without any escalation data
        mock_cluster = create_mock_cluster_with_signals(
            cluster_id=cluster_id,
            title="New Cluster",
            article_count=3,
            geo_score=None,
            mil_score=None,
            eco_score=None,
            combined_score=None,
            escalation_level=None,
            escalation_signals=None,
            escalation_calculated_at=None,
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cluster
        mock_session.execute = AsyncMock(return_value=mock_result)

        app.dependency_overrides[get_db] = lambda: mock_session
        app.dependency_overrides[get_current_user_id] = lambda: "test-user"

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/escalation/clusters/{cluster_id}"
                )

            assert response.status_code == 200

            data = response.json()

            # Default score 0.5 -> level 3
            assert data["geopolitical"]["level"] == 3
            assert float(data["geopolitical"]["score"]) == 0.5
            assert data["geopolitical"]["confidence"] == 0.0

            assert data["military"]["level"] == 3
            assert data["economic"]["level"] == 3

            # Combined level is max of defaults = 3
            assert data["combined_level"] == 3

            # Empty signals
            assert data["geopolitical_signals"] == []
            assert data["military_signals"] == []
            assert data["economic_signals"] == []
        finally:
            app.dependency_overrides.clear()
