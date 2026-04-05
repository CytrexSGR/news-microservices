# File: services/feed-service/tests/test_alert_webhook.py
"""
Tests for the Alert Webhook Service.

Epic 2.3 Task 2.3.6: n8n Webhook for Review Alerts

Tests the AlertWebhook service that sends notifications to n8n
when high-risk items (risk_score >= 0.7) are added to the review queue.
"""

import httpx
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestAlertWebhook:
    """Test AlertWebhook service for high-risk item notifications."""

    @pytest.mark.asyncio
    async def test_send_high_risk_alert_success(self):
        """Test sending alert for high-risk review item succeeds."""
        from app.services.alert_webhook import AlertWebhook

        webhook = AlertWebhook(webhook_url="http://n8n:5678/webhook/review-alert")

        with patch("app.services.alert_webhook.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await webhook.send_high_risk_alert(
                item_id=str(uuid4()),
                risk_score=0.85,
                risk_level="HIGH",
                flags=["ai_generated", "legal_language"],
                content_preview="Breaking: Lawsuit filed alleging fraud...",
            )

            assert result is True
            mock_client.post.assert_called_once()

            # Verify payload structure
            call_args = mock_client.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            assert payload is not None
            assert "item_id" in payload
            assert payload["risk_score"] == 0.85
            assert payload["risk_level"] == "HIGH"
            assert "ai_generated" in payload["flags"]
            assert "legal_language" in payload["flags"]
            assert "content_preview" in payload
            assert "timestamp" in payload

    @pytest.mark.asyncio
    async def test_send_alert_handles_timeout(self):
        """Test that timeout is handled gracefully (logs and returns False)."""
        import httpx
        from app.services.alert_webhook import AlertWebhook

        webhook = AlertWebhook(webhook_url="http://n8n:5678/webhook/review-alert")

        # Patch the entire httpx module's AsyncClient as a context manager
        async def mock_context_manager(*args, **kwargs):
            class MockClient:
                async def post(self, *args, **kwargs):
                    raise httpx.TimeoutException("timeout")

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

            return MockClient()

        with patch.object(httpx, "AsyncClient", side_effect=mock_context_manager):
            result = await webhook.send_high_risk_alert(
                item_id=str(uuid4()),
                risk_score=0.9,
                risk_level="HIGH",
                flags=["allegations"],
                content_preview="Test content",
            )

            # Should return False but not raise exception
            assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_handles_http_error(self):
        """Test that HTTP errors are handled gracefully."""
        import httpx
        from app.services.alert_webhook import AlertWebhook

        webhook = AlertWebhook(webhook_url="http://n8n:5678/webhook/review-alert")

        # Patch the entire httpx module's AsyncClient as a context manager
        async def mock_context_manager(*args, **kwargs):
            class MockClient:
                async def post(self, *args, **kwargs):
                    error_response = httpx.Response(
                        500, request=httpx.Request("POST", "http://test")
                    )
                    raise httpx.HTTPStatusError(
                        "error", request=None, response=error_response
                    )

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

            return MockClient()

        with patch.object(httpx, "AsyncClient", side_effect=mock_context_manager):
            result = await webhook.send_high_risk_alert(
                item_id=str(uuid4()),
                risk_score=0.75,
                risk_level="HIGH",
                flags=["financial_data"],
                content_preview="Test content",
            )

            # Should return False but not raise exception
            assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_when_disabled(self):
        """Test that no alert is sent when webhook URL is not configured."""
        from app.services.alert_webhook import AlertWebhook

        # Empty or None webhook URL should skip sending
        webhook = AlertWebhook(webhook_url=None)

        # No HTTP call should be made
        with patch("app.services.alert_webhook.httpx.AsyncClient") as mock_client_class:
            result = await webhook.send_high_risk_alert(
                item_id=str(uuid4()),
                risk_score=0.9,
                risk_level="HIGH",
                flags=["test"],
                content_preview="Test",
            )

            # Should return False (skipped) without calling HTTP client
            assert result is False
            mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_payload_structure(self):
        """Test that webhook payload contains all required fields."""
        from app.services.alert_webhook import AlertWebhook

        webhook = AlertWebhook(webhook_url="http://n8n:5678/webhook/review-alert")
        item_id = str(uuid4())

        with patch("app.services.alert_webhook.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            await webhook.send_high_risk_alert(
                item_id=item_id,
                risk_score=0.82,
                risk_level="HIGH",
                flags=["ai_generated", "unverified_claims"],
                content_preview="Sources say the company is under investigation...",
            )

            # Extract the payload from the call
            call_args = mock_client.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")

            # Verify required fields
            assert payload["item_id"] == item_id
            assert payload["risk_score"] == 0.82
            assert payload["risk_level"] == "HIGH"
            assert payload["flags"] == ["ai_generated", "unverified_claims"]
            assert "Sources say" in payload["content_preview"]
            assert "timestamp" in payload
            assert payload["source"] == "feed-service-review"
            assert payload["alert_type"] == "high_risk_review_item"

    @pytest.mark.asyncio
    async def test_content_preview_truncation(self):
        """Test that long content previews are truncated."""
        from app.services.alert_webhook import AlertWebhook

        webhook = AlertWebhook(webhook_url="http://n8n:5678/webhook/review-alert")

        # Create a very long content preview (> 500 chars)
        long_content = "A" * 1000

        with patch("app.services.alert_webhook.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            await webhook.send_high_risk_alert(
                item_id=str(uuid4()),
                risk_score=0.75,
                risk_level="HIGH",
                flags=["test"],
                content_preview=long_content,
            )

            call_args = mock_client.post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")

            # Content should be truncated to max 500 chars
            assert len(payload["content_preview"]) <= 500


class TestAlertWebhookIntegration:
    """Integration tests for AlertWebhook with review submission."""

    @pytest.mark.asyncio
    async def test_should_send_alert_for_high_risk(self):
        """Verify alert is triggered for risk_score >= 0.7."""
        from app.services.alert_webhook import should_send_alert

        assert should_send_alert(0.7) is True
        assert should_send_alert(0.85) is True
        assert should_send_alert(1.0) is True

    @pytest.mark.asyncio
    async def test_should_not_send_alert_for_lower_risk(self):
        """Verify no alert for risk_score < 0.7."""
        from app.services.alert_webhook import should_send_alert

        assert should_send_alert(0.0) is False
        assert should_send_alert(0.3) is False
        assert should_send_alert(0.5) is False
        assert should_send_alert(0.69) is False
