"""Tests for FMP Correlation Service.

Tests cover:
- RegimeState dataclass creation
- CorrelationAlert dataclass creation
- FMPCorrelationService initialization
- HTTP regime fetching with mocked responses
- Correlation analysis logic for all alert types
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import httpx

from app.services.fmp_correlation_service import (
    FMPCorrelationService,
    RegimeState,
    CorrelationAlert,
)


class TestRegimeState:
    """Tests for RegimeState dataclass."""

    def test_regime_state_creation_minimal(self):
        """Test creating RegimeState with minimal required fields."""
        state = RegimeState(regime="RISK_ON", confidence=0.8)

        assert state.regime == "RISK_ON"
        assert state.confidence == 0.8
        assert state.vix_level is None
        assert state.vix_change_24h is None
        assert state.fear_greed_index is None
        assert state.timestamp is None

    def test_regime_state_creation_full(self):
        """Test creating RegimeState with all fields."""
        ts = datetime.now()
        state = RegimeState(
            regime="RISK_OFF",
            confidence=0.95,
            vix_level=25.5,
            vix_change_24h=3.2,
            fear_greed_index=35,
            timestamp=ts,
        )

        assert state.regime == "RISK_OFF"
        assert state.confidence == 0.95
        assert state.vix_level == 25.5
        assert state.vix_change_24h == 3.2
        assert state.fear_greed_index == 35
        assert state.timestamp == ts

    def test_regime_state_transitional(self):
        """Test creating TRANSITIONAL regime state."""
        state = RegimeState(regime="TRANSITIONAL", confidence=0.5)

        assert state.regime == "TRANSITIONAL"
        assert state.confidence == 0.5


class TestCorrelationAlert:
    """Tests for CorrelationAlert dataclass."""

    def test_correlation_alert_creation(self):
        """Test creating CorrelationAlert with all fields."""
        cluster_ids = [uuid4(), uuid4()]
        alert = CorrelationAlert(
            correlation_type="CONFIRMATION",
            fmp_regime="RISK_OFF",
            escalation_level=4,
            confidence=0.85,
            reasoning="Market confirms news risk",
            related_clusters=cluster_ids,
        )

        assert alert.correlation_type == "CONFIRMATION"
        assert alert.fmp_regime == "RISK_OFF"
        assert alert.escalation_level == 4
        assert alert.confidence == 0.85
        assert alert.reasoning == "Market confirms news risk"
        assert alert.related_clusters == cluster_ids

    def test_correlation_alert_divergence(self):
        """Test creating DIVERGENCE alert."""
        alert = CorrelationAlert(
            correlation_type="DIVERGENCE",
            fmp_regime="RISK_ON",
            escalation_level=5,
            confidence=0.65,
            reasoning="Market ignoring high risk news",
            related_clusters=[],
        )

        assert alert.correlation_type == "DIVERGENCE"
        assert alert.fmp_regime == "RISK_ON"
        assert alert.escalation_level == 5

    def test_correlation_alert_early_warning(self):
        """Test creating EARLY_WARNING alert."""
        alert = CorrelationAlert(
            correlation_type="EARLY_WARNING",
            fmp_regime="RISK_OFF",
            escalation_level=3,
            confidence=0.5,
            reasoning="Market sees risk news doesn't yet show",
            related_clusters=[uuid4()],
        )

        assert alert.correlation_type == "EARLY_WARNING"
        assert alert.escalation_level == 3


class TestFMPCorrelationService:
    """Tests for FMPCorrelationService."""

    def test_init_default_url(self):
        """Test service uses default FMP URL."""
        service = FMPCorrelationService()

        assert service.fmp_base_url == "http://fmp-service:8113"
        assert service.session is None
        assert service._http_client is None

    def test_init_custom_url(self):
        """Test service accepts custom URL."""
        custom_url = "http://custom-fmp:9999"
        service = FMPCorrelationService(fmp_base_url=custom_url)

        assert service.fmp_base_url == custom_url

    def test_init_with_session(self):
        """Test service accepts database session."""
        mock_session = MagicMock()
        service = FMPCorrelationService(session=mock_session)

        assert service.session == mock_session

    def test_init_with_http_client(self):
        """Test service accepts pre-configured HTTP client."""
        mock_client = MagicMock()
        service = FMPCorrelationService(http_client=mock_client)

        assert service._http_client == mock_client

    @pytest.mark.asyncio
    async def test_get_current_regime_success(self):
        """Test successful regime fetch parses response correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "regime": "RISK_OFF",
            "confidence": 0.85,
            "vix_level": 28.5,
            "vix_change_24h": 5.2,
            "fear_greed_index": 25,
            "timestamp": "2026-01-22T10:30:00",
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()

        service = FMPCorrelationService(http_client=mock_client)
        regime = await service.get_current_regime()

        assert regime is not None
        assert regime.regime == "RISK_OFF"
        assert regime.confidence == 0.85
        assert regime.vix_level == 28.5
        assert regime.vix_change_24h == 5.2
        assert regime.fear_greed_index == 25
        assert regime.timestamp == datetime(2026, 1, 22, 10, 30, 0)

        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_regime_default_values(self):
        """Test regime fetch uses defaults for missing fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}  # Empty response

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()

        service = FMPCorrelationService(http_client=mock_client)
        regime = await service.get_current_regime()

        assert regime is not None
        assert regime.regime == "TRANSITIONAL"  # Default
        assert regime.confidence == 0.5  # Default

    @pytest.mark.asyncio
    async def test_get_current_regime_unavailable(self):
        """Test returns None when FMP service unavailable."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection refused"))

        service = FMPCorrelationService(http_client=mock_client)
        regime = await service.get_current_regime()

        assert regime is None

    @pytest.mark.asyncio
    async def test_get_current_regime_http_error(self):
        """Test returns None on HTTP error response."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        service = FMPCorrelationService(http_client=mock_client)
        regime = await service.get_current_regime()

        assert regime is None

    def test_analyze_correlation_confirmation_risk_off(self):
        """Test CONFIRMATION alert for RISK_OFF + high escalation."""
        service = FMPCorrelationService()
        cluster_ids = [uuid4(), uuid4()]
        regime = RegimeState(regime="RISK_OFF", confidence=0.9)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=4,  # High escalation
            cluster_ids=cluster_ids,
        )

        assert alert is not None
        assert alert.correlation_type == "CONFIRMATION"
        assert alert.fmp_regime == "RISK_OFF"
        assert alert.escalation_level == 4
        assert alert.confidence > 0.7
        assert "aligns with high news escalation" in alert.reasoning
        assert alert.related_clusters == cluster_ids

    def test_analyze_correlation_confirmation_risk_off_level_5(self):
        """Test CONFIRMATION alert for RISK_OFF + critical escalation."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_OFF", confidence=0.95)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=5,  # Critical escalation
            cluster_ids=[],
        )

        assert alert is not None
        assert alert.correlation_type == "CONFIRMATION"
        assert alert.escalation_level == 5

    def test_analyze_correlation_confirmation_risk_on(self):
        """Test CONFIRMATION alert for RISK_ON + low escalation."""
        service = FMPCorrelationService()
        cluster_ids = [uuid4()]
        regime = RegimeState(regime="RISK_ON", confidence=0.85)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=2,  # Low escalation
            cluster_ids=cluster_ids,
        )

        assert alert is not None
        assert alert.correlation_type == "CONFIRMATION"
        assert alert.fmp_regime == "RISK_ON"
        assert alert.escalation_level == 2
        assert "aligns with low news escalation" in alert.reasoning

    def test_analyze_correlation_confirmation_risk_on_level_1(self):
        """Test CONFIRMATION alert for RISK_ON + minimal escalation."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_ON", confidence=0.8)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=1,  # Minimal escalation
            cluster_ids=[],
        )

        assert alert is not None
        assert alert.correlation_type == "CONFIRMATION"

    def test_analyze_correlation_divergence_risk_on_high_escalation(self):
        """Test DIVERGENCE alert when RISK_ON but high escalation."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_ON", confidence=0.75)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=4,  # High escalation (expected: 2)
            cluster_ids=[uuid4()],
        )

        assert alert is not None
        assert alert.correlation_type == "DIVERGENCE"
        assert alert.fmp_regime == "RISK_ON"
        assert "potential risk underpricing" in alert.reasoning

    def test_analyze_correlation_divergence_risk_on_critical_escalation(self):
        """Test DIVERGENCE alert when RISK_ON but critical escalation."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_ON", confidence=0.6)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=5,  # Critical (3 levels above expected)
            cluster_ids=[],
        )

        assert alert is not None
        assert alert.correlation_type == "DIVERGENCE"
        # Higher level difference = higher confidence
        assert alert.confidence > 0.5

    def test_analyze_correlation_divergence_risk_off_low_escalation(self):
        """Test DIVERGENCE alert when RISK_OFF but low escalation."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_OFF", confidence=0.8)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=2,  # Low escalation (expected: 4)
            cluster_ids=[uuid4()],
        )

        assert alert is not None
        assert alert.correlation_type == "DIVERGENCE"
        assert alert.fmp_regime == "RISK_OFF"
        assert "potential risk overpricing" in alert.reasoning

    def test_analyze_correlation_early_warning(self):
        """Test EARLY_WARNING alert for RISK_OFF + neutral escalation."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_OFF", confidence=0.7)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=3,  # Neutral escalation
            cluster_ids=[uuid4(), uuid4()],
        )

        assert alert is not None
        assert alert.correlation_type == "EARLY_WARNING"
        assert alert.fmp_regime == "RISK_OFF"
        assert alert.escalation_level == 3
        assert "potential early signal" in alert.reasoning

    def test_analyze_correlation_no_alert_transitional(self):
        """Test no alert for TRANSITIONAL regime + neutral escalation."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="TRANSITIONAL", confidence=0.5)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=3,  # Neutral (matches expected for transitional)
            cluster_ids=[],
        )

        # No significant correlation
        assert alert is None

    def test_analyze_correlation_no_alert_slight_mismatch(self):
        """Test no alert for slight level mismatch (below threshold)."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_ON", confidence=0.8)

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=3,  # Only 1 level above expected (2)
            cluster_ids=[],
        )

        # Difference of 1 is below DIVERGENCE_THRESHOLD (2)
        assert alert is None

    def test_analyze_correlation_confidence_calculation(self):
        """Test confidence is properly bounded at 1.0."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_OFF", confidence=1.0)  # Max confidence

        alert = service.analyze_correlation(
            regime=regime,
            escalation_level=5,
            cluster_ids=[],
        )

        assert alert is not None
        assert alert.confidence <= 1.0  # Should not exceed 1.0


class TestFMPCorrelationServiceDatabase:
    """Tests for database operations (require mocked session)."""

    @pytest.mark.asyncio
    async def test_create_correlation_record_no_session(self):
        """Test create_correlation_record raises error without session."""
        service = FMPCorrelationService()  # No session
        alert = CorrelationAlert(
            correlation_type="CONFIRMATION",
            fmp_regime="RISK_OFF",
            escalation_level=4,
            confidence=0.8,
            reasoning="Test",
            related_clusters=[],
        )

        with pytest.raises(ValueError, match="Database session not configured"):
            await service.create_correlation_record(alert)

    @pytest.mark.asyncio
    async def test_get_active_alerts_no_session(self):
        """Test get_active_alerts raises error without session."""
        service = FMPCorrelationService()  # No session

        with pytest.raises(ValueError, match="Database session not configured"):
            await service.get_active_alerts()

    @pytest.mark.asyncio
    async def test_create_correlation_record_with_session(self):
        """Test create_correlation_record creates and flushes record."""
        mock_session = AsyncMock()
        service = FMPCorrelationService(session=mock_session)

        alert = CorrelationAlert(
            correlation_type="DIVERGENCE",
            fmp_regime="RISK_ON",
            escalation_level=5,
            confidence=0.7,
            reasoning="Test divergence",
            related_clusters=[uuid4()],
        )

        record = await service.create_correlation_record(
            alert=alert,
            metadata={"custom": "data"},
            ttl_hours=48,
        )

        # Verify session operations
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

        # Verify record attributes
        assert record.correlation_type == "DIVERGENCE"
        assert record.fmp_regime == "RISK_ON"
        assert record.escalation_level == 5
        assert record.confidence == Decimal("0.7")
        assert record.is_active is True
        assert record.extra_metadata == {"custom": "data"}
        # TTL should be 48 hours from now
        assert record.expires_at > datetime.now() + timedelta(hours=47)

    @pytest.mark.asyncio
    async def test_create_correlation_record_default_metadata(self):
        """Test create_correlation_record uses reasoning as default metadata."""
        mock_session = AsyncMock()
        service = FMPCorrelationService(session=mock_session)

        alert = CorrelationAlert(
            correlation_type="EARLY_WARNING",
            fmp_regime="RISK_OFF",
            escalation_level=3,
            confidence=0.5,
            reasoning="Test early warning reasoning",
            related_clusters=[],
        )

        record = await service.create_correlation_record(alert)

        # Default metadata should contain reasoning
        assert record.extra_metadata == {"reasoning": "Test early warning reasoning"}

    @pytest.mark.asyncio
    async def test_get_active_alerts_with_session(self):
        """Test get_active_alerts queries correctly."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = FMPCorrelationService(session=mock_session)
        alerts = await service.get_active_alerts(limit=5)

        mock_session.execute.assert_called_once()
        assert alerts == []

    @pytest.mark.asyncio
    async def test_get_active_alerts_with_type_filter(self):
        """Test get_active_alerts applies correlation_type filter."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = FMPCorrelationService(session=mock_session)
        await service.get_active_alerts(
            limit=10,
            correlation_type="DIVERGENCE",
        )

        mock_session.execute.assert_called_once()
        # The query should include the type filter (verified by call)


class TestIntegrationPatterns:
    """Tests for expected integration patterns."""

    def test_regime_to_escalation_mapping(self):
        """Verify regime-to-expected-escalation mapping."""
        service = FMPCorrelationService()

        # Access internal mapping indirectly through analyze_correlation
        # RISK_ON expects level 2, RISK_OFF expects level 4, TRANSITIONAL expects level 3

        # RISK_ON at level 2 = confirmation (matches expected)
        regime_on = RegimeState(regime="RISK_ON", confidence=0.8)
        alert = service.analyze_correlation(regime_on, 2, [])
        assert alert is not None
        assert alert.correlation_type == "CONFIRMATION"

        # RISK_OFF at level 4 = confirmation (matches expected)
        regime_off = RegimeState(regime="RISK_OFF", confidence=0.8)
        alert = service.analyze_correlation(regime_off, 4, [])
        assert alert is not None
        assert alert.correlation_type == "CONFIRMATION"

    def test_divergence_threshold_boundary(self):
        """Test divergence only triggers at threshold."""
        service = FMPCorrelationService()
        regime = RegimeState(regime="RISK_ON", confidence=0.8)

        # Level 3 is only 1 above expected (2) - no divergence
        alert_below = service.analyze_correlation(regime, 3, [])
        assert alert_below is None

        # Level 4 is 2 above expected - triggers divergence
        alert_at = service.analyze_correlation(regime, 4, [])
        assert alert_at is not None
        assert alert_at.correlation_type == "DIVERGENCE"

    def test_service_can_be_used_without_database(self):
        """Verify service works for analysis without database session."""
        service = FMPCorrelationService()  # No session

        regime = RegimeState(regime="RISK_OFF", confidence=0.9)
        alert = service.analyze_correlation(regime, 5, [uuid4()])

        # Analysis works without database
        assert alert is not None
        assert alert.correlation_type == "CONFIRMATION"
