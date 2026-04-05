# File: services/sitrep-service/app/services/review_client.py
"""
Review Client for HITL Integration.

HTTP client for submitting AI-generated SITREPs to the feed-service
review queue for risk scoring and human review.

Epic 2.3 Task 2.3.5: Integrate Risk Scoring with SITREP Generation

Usage:
    from app.services.review_client import get_review_client

    client = get_review_client()
    result = await client.submit_for_review(
        target_type="sitrep",
        target_id=str(sitrep.id),
        content=sitrep.executive_summary,
    )

    if result.status == "auto_approved":
        # Proceed with publication
    else:
        # Wait for human review
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ReviewResult:
    """Result from review submission."""

    id: str
    target_type: str
    target_id: str
    risk_score: float
    risk_level: str
    risk_factors: List[str]
    status: str
    error: Optional[str] = None

    @property
    def is_approved(self) -> bool:
        """Check if content is approved (auto or manually)."""
        return self.status in ("auto_approved", "approved", "edited")

    @property
    def requires_review(self) -> bool:
        """Check if content requires human review."""
        return self.status == "pending"


class ReviewClientError(Exception):
    """Exception raised when review client operations fail."""

    pass


class ReviewClient:
    """
    HTTP client for HITL review queue integration.

    Submits AI-generated content to feed-service for risk scoring
    and potential human review before publication.

    Attributes:
        base_url: Base URL of feed-service
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        """
        Initialize ReviewClient.

        Args:
            base_url: Feed service URL (default from settings)
            timeout: Request timeout in seconds (default from settings)
        """
        self.base_url = base_url or settings.FEED_SERVICE_URL
        self.timeout = timeout or settings.REVIEW_TIMEOUT_SECONDS
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client (lazy initialization)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=5.0),
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def submit_for_review(
        self,
        target_type: str,
        target_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None,
    ) -> ReviewResult:
        """
        Submit content to review queue for risk scoring.

        Sends content to feed-service /api/v1/review/submit endpoint.
        The feed-service calculates a risk score and either:
        - Auto-approves (risk < 0.3)
        - Adds to pending queue (risk >= 0.3)

        Args:
            target_type: Type of content (sitrep, summary, alert)
            target_id: UUID of the content
            content: Text content to analyze for risk
            metadata: Additional metadata (ai_generated, source, etc.)
            auth_token: Optional JWT token for authentication

        Returns:
            ReviewResult with risk score, factors, and status

        Raises:
            ReviewClientError: If submission fails
        """
        if not settings.REVIEW_ENABLED:
            logger.info("Review integration disabled, auto-approving")
            return ReviewResult(
                id="disabled",
                target_type=target_type,
                target_id=target_id,
                risk_score=0.0,
                risk_level="low",
                risk_factors=[],
                status="auto_approved",
            )

        client = await self._get_client()

        # Build request payload
        payload = {
            "target_type": target_type,
            "target_id": target_id,
            "content_preview": content[:5000] if content else "",
            "metadata": metadata or {"ai_generated": True, "source": "sitrep-service"},
        }

        # Build headers
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            logger.debug(f"Submitting {target_type}/{target_id} for review")

            response = await client.post(
                "/api/v1/review/submit",
                json=payload,
                headers=headers,
            )

            if response.status_code in (200, 201):
                data = response.json()
                result = ReviewResult(
                    id=data.get("id", ""),
                    target_type=data.get("target_type", target_type),
                    target_id=data.get("target_id", target_id),
                    risk_score=data.get("risk_score", 0.0),
                    risk_level=data.get("risk_level", "low"),
                    risk_factors=data.get("risk_factors", []),
                    status=data.get("status", "pending"),
                )

                logger.info(
                    f"Review submission successful: {target_type}/{target_id} -> "
                    f"score={result.risk_score}, status={result.status}"
                )
                return result

            else:
                error_msg = f"Review submission failed: HTTP {response.status_code}"
                logger.error(f"{error_msg}: {response.text}")
                raise ReviewClientError(error_msg)

        except httpx.TimeoutException as e:
            error_msg = f"Review submission timeout: {e}"
            logger.error(error_msg)
            raise ReviewClientError(error_msg) from e

        except httpx.RequestError as e:
            error_msg = f"Review submission request error: {e}"
            logger.error(error_msg)
            raise ReviewClientError(error_msg) from e

        except Exception as e:
            error_msg = f"Review submission unexpected error: {e}"
            logger.exception(error_msg)
            raise ReviewClientError(error_msg) from e

    async def check_review_status(
        self,
        item_id: str,
        auth_token: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Check status of a review item.

        Args:
            item_id: UUID of the review queue item
            auth_token: Optional JWT token

        Returns:
            Review item data or None if not found
        """
        if not settings.REVIEW_ENABLED:
            return None

        client = await self._get_client()

        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            response = await client.get(
                f"/api/v1/review/queue/{item_id}",
                headers=headers,
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.warning(
                    f"Review status check failed: HTTP {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Review status check error: {e}")
            return None


# Singleton instance
_client: Optional[ReviewClient] = None


def get_review_client() -> ReviewClient:
    """
    Get singleton ReviewClient instance.

    Returns:
        ReviewClient instance
    """
    global _client
    if _client is None:
        _client = ReviewClient()
    return _client


async def close_review_client() -> None:
    """Close the singleton review client."""
    global _client
    if _client:
        await _client.close()
        _client = None
