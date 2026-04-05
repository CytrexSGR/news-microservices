"""Tests for AlertWebhookService."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.alert_webhook import AlertWebhookService, WebhookPayload
from app.services.burst_detection import BurstSeverity


class TestAlertWebhookService:
    """Tests for AlertWebhookService."""

    @pytest.fixture
    def service(self):
        """Create service with test webhook URL."""
        return AlertWebhookService(
            webhook_url="http://n8n:5678/webhook/burst-alert"
        )

    def test_build_payload(self, service):
        """Should build correct webhook payload."""
        cluster_id = uuid4()

        payload = service.build_payload(
            cluster_id=cluster_id,
            cluster_title="Breaking: Market Crash",
            severity=BurstSeverity.CRITICAL,
            velocity=25,
            top_entities=["S&P 500", "NASDAQ", "Federal Reserve"],
        )

        assert payload.cluster_id == str(cluster_id)
        assert payload.severity == "critical"
        assert payload.velocity == 25
        assert "S&P 500" in payload.top_entities
        assert payload.recommended_action == "immediate_review"

    @pytest.mark.asyncio
    async def test_send_alert_success(self, service):
        """Should send webhook and return True on success."""
        cluster_id = uuid4()

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await service.send_alert(
                cluster_id=cluster_id,
                cluster_title="Test Alert",
                severity=BurstSeverity.HIGH,
                velocity=15,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_alert_failure(self, service):
        """Should return False on webhook failure."""
        cluster_id = uuid4()

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await service.send_alert(
                cluster_id=cluster_id,
                cluster_title="Test Alert",
                severity=BurstSeverity.HIGH,
                velocity=15,
            )

            assert result is False
