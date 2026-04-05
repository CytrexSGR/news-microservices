# File: services/sitrep-service/tests/test_review_client.py
"""
Tests for ReviewClient HITL integration.

Epic 2.3 Task 2.3.5: Integrate Risk Scoring with SITREP Generation

Tests the ReviewClient that submits AI-generated SITREPs to
feed-service for risk scoring and human review.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx


# =============================================================================
# Test: ReviewClient Submission
# =============================================================================


class TestReviewClientSubmission:
    """Tests for ReviewClient.submit_for_review()."""

    @pytest.mark.asyncio
    async def test_submit_high_risk_content_returns_pending(self):
        """Test that high-risk content submission returns pending status."""
        from app.services.review_client import ReviewClient

        client = ReviewClient(base_url="http://test:8101")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": str(uuid4()),
            "target_type": "sitrep",
            "target_id": str(uuid4()),
            "risk_score": 0.75,
            "risk_level": "high",
            "risk_factors": ["legal_language", "allegations"],
            "status": "pending",
        }

        with patch.object(
            httpx.AsyncClient,
            "post",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.submit_for_review(
                target_type="sitrep",
                target_id=str(uuid4()),
                content="Lawsuit filed alleging fraud at major company.",
            )

            assert result.status == "pending"
            assert result.risk_score >= 0.3
            assert result.requires_review is True
            assert result.is_approved is False

        await client.close()

    @pytest.mark.asyncio
    async def test_submit_low_risk_content_returns_auto_approved(self):
        """Test that low-risk content is auto-approved."""
        from app.services.review_client import ReviewClient

        client = ReviewClient(base_url="http://test:8101")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": str(uuid4()),
            "target_type": "sitrep",
            "target_id": str(uuid4()),
            "risk_score": 0.0,
            "risk_level": "low",
            "risk_factors": [],
            "status": "auto_approved",
        }

        with patch.object(
            httpx.AsyncClient,
            "post",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.submit_for_review(
                target_type="sitrep",
                target_id=str(uuid4()),
                content="Today's weather is sunny and clear.",
            )

            assert result.status == "auto_approved"
            assert result.risk_score < 0.3
            assert result.requires_review is False
            assert result.is_approved is True

        await client.close()

    @pytest.mark.asyncio
    async def test_submit_with_metadata(self):
        """Test submission with custom metadata."""
        from app.services.review_client import ReviewClient

        client = ReviewClient(base_url="http://test:8101")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": str(uuid4()),
            "target_type": "sitrep",
            "target_id": str(uuid4()),
            "risk_score": 0.5,
            "risk_level": "medium",
            "risk_factors": ["financial_data"],
            "status": "pending",
        }

        captured_request = None

        async def capture_post(*args, **kwargs):
            nonlocal captured_request
            captured_request = kwargs
            return mock_response

        with patch.object(
            httpx.AsyncClient,
            "post",
            side_effect=capture_post,
        ):
            await client.submit_for_review(
                target_type="sitrep",
                target_id=str(uuid4()),
                content="Company reported earnings.",
                metadata={
                    "ai_generated": True,
                    "source": "sitrep-service",
                    "report_type": "daily",
                },
            )

            assert captured_request is not None
            payload = captured_request.get("json", {})
            assert payload["metadata"]["source"] == "sitrep-service"
            assert payload["metadata"]["report_type"] == "daily"

        await client.close()

    @pytest.mark.asyncio
    async def test_submit_truncates_long_content(self):
        """Test that content longer than 5000 chars is truncated."""
        from app.services.review_client import ReviewClient

        client = ReviewClient(base_url="http://test:8101")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": str(uuid4()),
            "target_type": "sitrep",
            "target_id": str(uuid4()),
            "risk_score": 0.1,
            "risk_level": "low",
            "risk_factors": [],
            "status": "auto_approved",
        }

        captured_request = None

        async def capture_post(*args, **kwargs):
            nonlocal captured_request
            captured_request = kwargs
            return mock_response

        with patch.object(
            httpx.AsyncClient,
            "post",
            side_effect=capture_post,
        ):
            long_content = "A" * 10000  # 10,000 chars
            await client.submit_for_review(
                target_type="sitrep",
                target_id=str(uuid4()),
                content=long_content,
            )

            payload = captured_request.get("json", {})
            assert len(payload["content_preview"]) <= 5000

        await client.close()


# =============================================================================
# Test: ReviewClient Error Handling
# =============================================================================


class TestReviewClientErrorHandling:
    """Tests for ReviewClient error handling."""

    @pytest.mark.asyncio
    async def test_timeout_raises_exception(self):
        """Test that timeout raises ReviewClientError."""
        from app.services.review_client import ReviewClient, ReviewClientError

        client = ReviewClient(base_url="http://test:8101", timeout=0.1)

        with patch.object(
            httpx.AsyncClient,
            "post",
            side_effect=httpx.TimeoutException("Request timeout"),
        ):
            with pytest.raises(ReviewClientError) as exc_info:
                await client.submit_for_review(
                    target_type="sitrep",
                    target_id=str(uuid4()),
                    content="Test content",
                )

            assert "timeout" in str(exc_info.value).lower()

        await client.close()

    @pytest.mark.asyncio
    async def test_http_error_raises_exception(self):
        """Test that HTTP errors raise ReviewClientError."""
        from app.services.review_client import ReviewClient, ReviewClientError

        client = ReviewClient(base_url="http://test:8101")

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(
            httpx.AsyncClient,
            "post",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ReviewClientError) as exc_info:
                await client.submit_for_review(
                    target_type="sitrep",
                    target_id=str(uuid4()),
                    content="Test content",
                )

            assert "500" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_connection_error_raises_exception(self):
        """Test that connection errors raise ReviewClientError."""
        from app.services.review_client import ReviewClient, ReviewClientError

        client = ReviewClient(base_url="http://test:8101")

        with patch.object(
            httpx.AsyncClient,
            "post",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with pytest.raises(ReviewClientError) as exc_info:
                await client.submit_for_review(
                    target_type="sitrep",
                    target_id=str(uuid4()),
                    content="Test content",
                )

            assert "error" in str(exc_info.value).lower()

        await client.close()


# =============================================================================
# Test: ReviewClient Disabled Mode
# =============================================================================


class TestReviewClientDisabled:
    """Tests for ReviewClient when review is disabled."""

    @pytest.mark.asyncio
    async def test_disabled_returns_auto_approved(self):
        """Test that disabled review returns auto-approved status."""
        from app.services.review_client import ReviewClient

        with patch("app.services.review_client.settings") as mock_settings:
            mock_settings.REVIEW_ENABLED = False
            mock_settings.FEED_SERVICE_URL = "http://test:8101"
            mock_settings.REVIEW_TIMEOUT_SECONDS = 10.0

            client = ReviewClient()

            result = await client.submit_for_review(
                target_type="sitrep",
                target_id=str(uuid4()),
                content="This would normally be high-risk content with lawsuit allegations.",
            )

            assert result.status == "auto_approved"
            assert result.is_approved is True
            assert result.id == "disabled"

            await client.close()


# =============================================================================
# Test: ReviewResult Properties
# =============================================================================


class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_is_approved_with_auto_approved(self):
        """Test is_approved returns True for auto_approved status."""
        from app.services.review_client import ReviewResult

        result = ReviewResult(
            id="test",
            target_type="sitrep",
            target_id="test-id",
            risk_score=0.1,
            risk_level="low",
            risk_factors=[],
            status="auto_approved",
        )

        assert result.is_approved is True
        assert result.requires_review is False

    def test_is_approved_with_approved(self):
        """Test is_approved returns True for approved status."""
        from app.services.review_client import ReviewResult

        result = ReviewResult(
            id="test",
            target_type="sitrep",
            target_id="test-id",
            risk_score=0.5,
            risk_level="medium",
            risk_factors=["ai_generated"],
            status="approved",
        )

        assert result.is_approved is True

    def test_is_approved_with_edited(self):
        """Test is_approved returns True for edited status."""
        from app.services.review_client import ReviewResult

        result = ReviewResult(
            id="test",
            target_type="sitrep",
            target_id="test-id",
            risk_score=0.6,
            risk_level="medium",
            risk_factors=["financial_data"],
            status="edited",
        )

        assert result.is_approved is True

    def test_requires_review_with_pending(self):
        """Test requires_review returns True for pending status."""
        from app.services.review_client import ReviewResult

        result = ReviewResult(
            id="test",
            target_type="sitrep",
            target_id="test-id",
            risk_score=0.8,
            risk_level="high",
            risk_factors=["legal_language", "allegations"],
            status="pending",
        )

        assert result.requires_review is True
        assert result.is_approved is False

    def test_not_approved_with_rejected(self):
        """Test is_approved returns False for rejected status."""
        from app.services.review_client import ReviewResult

        result = ReviewResult(
            id="test",
            target_type="sitrep",
            target_id="test-id",
            risk_score=0.9,
            risk_level="high",
            risk_factors=["legal_language"],
            status="rejected",
        )

        assert result.is_approved is False
        assert result.requires_review is False


# =============================================================================
# Test: Singleton Pattern
# =============================================================================


class TestReviewClientSingleton:
    """Tests for singleton pattern."""

    def test_get_review_client_returns_same_instance(self):
        """Test that get_review_client returns the same instance."""
        from app.services import review_client as rc

        # Reset singleton
        rc._client = None

        client1 = rc.get_review_client()
        client2 = rc.get_review_client()

        assert client1 is client2

        # Cleanup
        rc._client = None

    @pytest.mark.asyncio
    async def test_close_review_client_clears_singleton(self):
        """Test that close_review_client clears the singleton."""
        from app.services import review_client as rc

        # Reset and get client
        rc._client = None
        client = rc.get_review_client()
        assert rc._client is not None

        # Close should clear it
        await rc.close_review_client()
        assert rc._client is None
