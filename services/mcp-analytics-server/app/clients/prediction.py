"""HTTP client for prediction-service with circuit breaker protection."""

import httpx
import logging
from typing import Dict, Any, Optional, List

from ..config import settings
from ..resilience import (
    ResilientHTTPClient,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    HTTPCircuitBreakerError,
)
from ..cache import cache_manager

logger = logging.getLogger(__name__)


class PredictionClient:
    """Client for prediction-service (Port 8116) with circuit breaker."""

    def __init__(self):
        self.base_url = settings.prediction_url

        # Create circuit breaker configuration
        cb_config = CircuitBreakerConfig(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            success_threshold=2,
            timeout_seconds=settings.circuit_breaker_recovery_timeout,
            enable_metrics=True,
        )

        # Create resilient HTTP client with circuit breaker
        self.client = ResilientHTTPClient(
            name="prediction-service",
            base_url=self.base_url,
            config=cb_config,
            timeout=settings.http_timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def get_predictions(
        self,
        model_name: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get recent predictions from ML models.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            model_name: Filter by specific model (optional)
            limit: Number of predictions to return (max 100)

        Returns:
            List of predictions with confidence scores

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"limit": limit}
            if model_name:
                params["model_name"] = model_name

            response = await self.client.get("/api/v1/predictions/", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get predictions request failed: {e}")
            raise

    async def create_prediction(
        self,
        model_name: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create new prediction using specified model.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            model_name: Name of ML model to use
            input_data: Input features for prediction

        Returns:
            Prediction result with confidence score

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            payload = {
                "model_name": model_name,
                "input_data": input_data,
            }

            response = await self.client.post("/api/v1/predictions/", json=payload)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Create prediction request failed: {e}")
            raise

    async def get_features(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """
        Get feature data for a specific trading symbol.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            symbol: Trading symbol (e.g., "BTCUSD", "ETHUSD")

        Returns:
            Feature data including technical indicators, sentiment, etc.

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            response = await self.client.get(f"/api/v1/features/{symbol}")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get features request failed for {symbol}: {e}")
            raise

    async def get_indicators(
        self,
        symbol: str,
        timeframe: str = "1h",
    ) -> Dict[str, Any]:
        """
        Get technical indicators for a specific symbol.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            symbol: Trading symbol (e.g., "BTCUSD", "ETHUSD")
            timeframe: Timeframe for indicators (1m, 5m, 15m, 1h, 4h, 1d)

        Returns:
            Technical indicators (RSI, MACD, Bollinger Bands, etc.)

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"timeframe": timeframe}
            response = await self.client.get(
                f"/api/v1/indicators/{symbol}/current",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get indicators request failed for {symbol}: {e}")
            raise

    async def get_signals(
        self,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Get trading signals from prediction models.

        Circuit breaker protection: Fails fast during service outages.

        Args:
            symbol: Filter by trading symbol (optional)
            strategy: Filter by strategy name (optional)
            min_confidence: Minimum confidence threshold (0-1)

        Returns:
            Trading signals with buy/sell recommendations

        Raises:
            HTTPCircuitBreakerError: If circuit breaker is OPEN
            httpx.HTTPError: If request fails
        """
        try:
            params = {"min_confidence": min_confidence}
            if symbol:
                params["symbol"] = symbol
            if strategy:
                params["strategy"] = strategy

            response = await self.client.get("/api/v1/signals/", params=params)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get signals request failed: {e}")
            raise

    async def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """
        Get performance metrics for a specific model.

        Args:
            model_name: Name of the ML model

        Returns:
            Performance metrics (accuracy, precision, recall, etc.)
        """
        try:
            response = await self.client.get(f"/api/v1/performance/{model_name}")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get model performance request failed: {e}")
            raise

    async def get_model_drift(self, model_name: str) -> Dict[str, Any]:
        """
        Get model drift analysis to detect performance degradation.

        Args:
            model_name: Name of the ML model

        Returns:
            Drift analysis with statistical measures
        """
        try:
            response = await self.client.get(f"/api/v1/performance/{model_name}/drift")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get model drift request failed: {e}")
            raise

    async def get_consensus_alerts(self) -> Dict[str, Any]:
        """
        Get consensus alerts from multiple models.

        Returns:
            Alerts when multiple models agree on predictions
        """
        try:
            response = await self.client.get("/api/v1/consensus/alerts")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get consensus alerts request failed: {e}")
            raise

    async def get_regime_analysis(self) -> Dict[str, Any]:
        """
        Get market regime analysis (trending, ranging, volatile).

        Returns:
            Current market regime classification and confidence
        """
        try:
            response = await self.client.get("/api/v1/analytics/regime/analysis")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get regime analysis request failed: {e}")
            raise

    async def get_backtest_results(self, backtest_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get backtest results for strategies.

        Args:
            backtest_id: Specific backtest ID (optional, returns list if not provided)

        Returns:
            Backtest results with performance metrics
        """
        try:
            if backtest_id:
                response = await self.client.get(f"/api/v1/backtests/{backtest_id}")
            else:
                response = await self.client.get("/api/v1/backtests/")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get backtest results request failed: {e}")
            raise

    async def get_order_flow_data(self, symbol: str, data_type: str = "cvd") -> Dict[str, Any]:
        """
        Get order flow analysis data (CVD, Delta, Zones).

        Args:
            symbol: Trading symbol
            data_type: Type of order flow data (cvd, delta, zones)

        Returns:
            Order flow analysis data
        """
        try:
            response = await self.client.get(f"/api/v1/order-flow/{symbol}/{data_type}")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Get order flow data request failed: {e}")
            raise

    async def optimize_portfolio(self, symbols: List[str], constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize portfolio allocation using modern portfolio theory.

        Args:
            symbols: List of trading symbols
            constraints: Optional constraints (max_weight, min_weight, etc.)

        Returns:
            Optimal portfolio allocation with expected returns and risk
        """
        try:
            payload = {"symbols": symbols}
            if constraints:
                payload["constraints"] = constraints

            response = await self.client.post("/api/v1/signals/portfolio/optimize", json=payload)
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Optimize portfolio request failed: {e}")
            raise

    async def list_strategies(self) -> Dict[str, Any]:
        """
        List all available trading strategies.

        Returns:
            List of strategies with descriptions and parameters
        """
        try:
            response = await self.client.get("/api/v1/strategies/")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"List strategies request failed: {e}")
            raise

    async def validate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Validate a trading strategy configuration.

        Args:
            strategy_id: Strategy identifier

        Returns:
            Validation results with errors/warnings
        """
        try:
            response = await self.client.post(f"/api/v1/strategies/{strategy_id}/validate")
            response.raise_for_status()
            return response.json()
        except CircuitBreakerOpenError as e:
            logger.error(f"Circuit breaker OPEN for prediction-service: {e}")
            raise HTTPCircuitBreakerError(
                service="prediction-service",
                message="Service temporarily unavailable (circuit breaker OPEN)",
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"Validate strategy request failed: {e}")
            raise
