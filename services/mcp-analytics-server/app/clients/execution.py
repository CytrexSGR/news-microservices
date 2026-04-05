"""HTTP client for execution-service with circuit breaker protection."""

import httpx
import logging
from typing import Dict, Any, Optional

from ..config import settings
from ..resilience import (
    ResilientHTTPClient,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    HTTPCircuitBreakerError,
)
from ..cache import cache_manager

logger = logging.getLogger(__name__)


class ExecutionClient:
    """Client for execution-service (Port 8120) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.execution_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="execution-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def get_positions(
        self,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all trading positions.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            status: Filter by position status (open, closed, all)

        Returns:
            List of positions with entry/exit prices, PnL, etc.

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {}
            if status:
                params["status"] = status

            response = await self.client.get("/api/v1/positions", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for execution-service: {e}")
            raise HTTPCircuitBreakerError(
                service="execution-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get positions request failed: {e}")
            raise

    async def get_portfolio(self) -> Dict[str, Any]:
        """
        Get portfolio overview with current holdings and performance.

        Circuit breaker protection: Fails fast during service outages.

        Returns:
            Portfolio data with current value, PnL, allocations

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/portfolio")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for execution-service: {e}")
            raise HTTPCircuitBreakerError(
                service="execution-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get portfolio request failed: {e}")
            raise

    async def get_execution_status(self) -> Dict[str, Any]:
        """
        Get execution service health and control status.

        Circuit breaker protection: Fails fast during service outages.

        Returns:
            Service status, kill switch state, active orders, etc.

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get("/api/v1/control/status")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for execution-service: {e}")
            raise HTTPCircuitBreakerError(
                service="execution-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get execution status request failed: {e}")
            raise

    async def get_portfolio_performance(self) -> Dict[str, Any]:
        """
        Get detailed portfolio performance metrics.

        Returns:
            Performance metrics including returns, volatility, Sharpe ratio, etc.
        """
        try:
            response = await self.client.get("/api/v1/portfolio/performance")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for execution-service: {e}")
            raise HTTPCircuitBreakerError(
                service="execution-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get portfolio performance request failed: {e}")
            raise

    async def close_position(self, position_id: str) -> Dict[str, Any]:
        """
        Close a specific trading position.

        Args:
            position_id: Position identifier

        Returns:
            Closed position details with final PnL
        """
        try:
            response = await self.client.post(f"/api/v1/positions/{position_id}/close")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for execution-service: {e}")
            raise HTTPCircuitBreakerError(
                service="execution-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Close position request failed: {e}")
            raise

    async def control_autotrade(self, action: str) -> Dict[str, Any]:
        """
        Control auto-trading system (start, stop, status).

        Args:
            action: Action to perform (start, stop, status)

        Returns:
            Auto-trading status and control confirmation
        """
        try:
            response = await self.client.post(f"/control/autotrade/{action}")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for execution-service: {e}")
            raise HTTPCircuitBreakerError(
                service="execution-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Control autotrade request failed: {e}")
            raise

    async def get_strategy_analytics(self) -> Dict[str, Any]:
        """
        Get analytics for all active trading strategies.

        Returns:
            Strategy performance metrics and statistics
        """
        try:
            response = await self.client.get("/api/v1/analytics/strategies")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for execution-service: {e}")
            raise HTTPCircuitBreakerError(
                service="execution-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get strategy analytics request failed: {e}")
            raise
