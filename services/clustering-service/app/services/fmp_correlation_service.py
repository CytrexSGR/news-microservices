"""FMP Correlation Service.

Fetches FMP regime state and creates correlation alerts
between market regimes and news escalation levels.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.escalation import FMPNewsCorrelation, CorrelationType, FMPRegime

logger = logging.getLogger(__name__)


@dataclass
class RegimeState:
    """Current FMP regime state."""
    regime: str  # RISK_ON, RISK_OFF, TRANSITIONAL
    confidence: float  # 0.0-1.0
    vix_level: Optional[float] = None
    vix_change_24h: Optional[float] = None
    fear_greed_index: Optional[int] = None
    timestamp: Optional[datetime] = None


@dataclass
class CorrelationAlert:
    """Correlation between FMP regime and news escalation."""
    correlation_type: str  # CONFIRMATION, DIVERGENCE, EARLY_WARNING
    fmp_regime: str
    escalation_level: int
    confidence: float
    reasoning: str
    related_clusters: List[UUID]


class FMPCorrelationService:
    """Service for FMP regime correlation with news escalation."""

    # FMP service configuration
    DEFAULT_FMP_BASE_URL = "http://fmp-service:8113"
    REGIME_ENDPOINT = "/api/v1/market/regime"

    # Correlation thresholds
    DIVERGENCE_THRESHOLD = 2  # Level difference for divergence alert
    CONFIRMATION_THRESHOLD = 0.7  # Confidence threshold for confirmation

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        fmp_base_url: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """Initialize FMP correlation service.

        Args:
            session: AsyncSession for database operations (optional for testing)
            fmp_base_url: Base URL for FMP service (default: http://fmp-service:8113)
            http_client: Optional pre-configured HTTP client
        """
        self.session = session
        self.fmp_base_url = fmp_base_url or self.DEFAULT_FMP_BASE_URL
        self._http_client = http_client

    async def get_current_regime(self) -> Optional[RegimeState]:
        """Fetch current market regime from FMP service.

        Returns:
            RegimeState if successful, None if FMP service unavailable
        """
        try:
            client = self._get_http_client()
            should_close = self._http_client is None

            try:
                response = await client.get(
                    f"{self.fmp_base_url}{self.REGIME_ENDPOINT}",
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()

                return RegimeState(
                    regime=data.get("regime", "TRANSITIONAL"),
                    confidence=data.get("confidence", 0.5),
                    vix_level=data.get("vix_level"),
                    vix_change_24h=data.get("vix_change_24h"),
                    fear_greed_index=data.get("fear_greed_index"),
                    timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
                )
            finally:
                if should_close:
                    await client.aclose()
        except httpx.HTTPStatusError as e:
            logger.warning(f"FMP service returned error: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"FMP service unavailable: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching FMP regime: {e}")
            return None

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client:
            return self._http_client
        return httpx.AsyncClient(timeout=30.0)

    def analyze_correlation(
        self,
        regime: RegimeState,
        escalation_level: int,
        cluster_ids: List[UUID],
    ) -> Optional[CorrelationAlert]:
        """Analyze correlation between regime and escalation level.

        Correlation types:
        - CONFIRMATION: High escalation + RISK_OFF regime (market confirms news risk)
        - DIVERGENCE: High escalation + RISK_ON regime (market ignoring news risk)
        - EARLY_WARNING: Low escalation + RISK_OFF regime (market sees risk news doesn't)

        Args:
            regime: Current FMP regime state
            escalation_level: Current news escalation level (1-5)
            cluster_ids: Related cluster UUIDs

        Returns:
            CorrelationAlert if significant correlation detected, None otherwise
        """
        # Map regime to expected escalation level
        regime_expected_escalation = {
            "RISK_ON": 2,      # Risk-on = low escalation expected
            "RISK_OFF": 4,     # Risk-off = high escalation expected
            "TRANSITIONAL": 3  # Neutral
        }

        expected_level = regime_expected_escalation.get(regime.regime, 3)
        level_difference = escalation_level - expected_level

        # CONFIRMATION: High escalation + RISK_OFF or Low escalation + RISK_ON
        if regime.regime == "RISK_OFF" and escalation_level >= 4:
            return CorrelationAlert(
                correlation_type="CONFIRMATION",
                fmp_regime=regime.regime,
                escalation_level=escalation_level,
                confidence=min(1.0, regime.confidence * 0.8 + 0.2),
                reasoning=f"Market RISK_OFF aligns with high news escalation (level {escalation_level})",
                related_clusters=cluster_ids
            )

        if regime.regime == "RISK_ON" and escalation_level <= 2:
            return CorrelationAlert(
                correlation_type="CONFIRMATION",
                fmp_regime=regime.regime,
                escalation_level=escalation_level,
                confidence=min(1.0, regime.confidence * 0.8 + 0.2),
                reasoning=f"Market RISK_ON aligns with low news escalation (level {escalation_level})",
                related_clusters=cluster_ids
            )

        # DIVERGENCE: Significant mismatch between market and news
        if abs(level_difference) >= self.DIVERGENCE_THRESHOLD:
            if regime.regime == "RISK_ON" and escalation_level >= 4:
                return CorrelationAlert(
                    correlation_type="DIVERGENCE",
                    fmp_regime=regime.regime,
                    escalation_level=escalation_level,
                    confidence=min(1.0, 0.5 + abs(level_difference) * 0.15),
                    reasoning=f"Market RISK_ON but news shows high escalation (level {escalation_level}) - potential risk underpricing",
                    related_clusters=cluster_ids
                )

            if regime.regime == "RISK_OFF" and escalation_level <= 2:
                return CorrelationAlert(
                    correlation_type="DIVERGENCE",
                    fmp_regime=regime.regime,
                    escalation_level=escalation_level,
                    confidence=min(1.0, 0.5 + abs(level_difference) * 0.15),
                    reasoning=f"Market RISK_OFF but news shows low escalation (level {escalation_level}) - potential risk overpricing",
                    related_clusters=cluster_ids
                )

        # EARLY_WARNING: Market leading indicator
        if regime.regime == "RISK_OFF" and escalation_level == 3:
            return CorrelationAlert(
                correlation_type="EARLY_WARNING",
                fmp_regime=regime.regime,
                escalation_level=escalation_level,
                confidence=min(1.0, regime.confidence * 0.6),
                reasoning="Market showing RISK_OFF while news at neutral - potential early signal",
                related_clusters=cluster_ids
            )

        # No significant correlation
        return None

    async def create_correlation_record(
        self,
        alert: CorrelationAlert,
        metadata: Optional[dict] = None,
        ttl_hours: int = 24,
    ) -> FMPNewsCorrelation:
        """Persist correlation alert to database.

        Args:
            alert: CorrelationAlert to persist
            metadata: Additional context to store
            ttl_hours: Hours until alert expires

        Returns:
            Created FMPNewsCorrelation record

        Raises:
            ValueError: If session is not configured
        """
        if self.session is None:
            raise ValueError("Database session not configured")

        record = FMPNewsCorrelation(
            detected_at=datetime.now(),
            correlation_type=alert.correlation_type,
            fmp_regime=alert.fmp_regime,
            escalation_level=alert.escalation_level,
            confidence=Decimal(str(alert.confidence)),
            related_clusters=alert.related_clusters,
            extra_metadata=metadata or {"reasoning": alert.reasoning},
            expires_at=datetime.now() + timedelta(hours=ttl_hours),
            is_active=True,
        )

        self.session.add(record)
        await self.session.flush()

        return record

    async def get_active_alerts(
        self,
        limit: int = 10,
        correlation_type: Optional[str] = None,
    ) -> List[FMPNewsCorrelation]:
        """Get active correlation alerts.

        Args:
            limit: Maximum alerts to return
            correlation_type: Filter by type (optional)

        Returns:
            List of active FMPNewsCorrelation records

        Raises:
            ValueError: If session is not configured
        """
        if self.session is None:
            raise ValueError("Database session not configured")

        stmt = (
            select(FMPNewsCorrelation)
            .where(FMPNewsCorrelation.is_active == True)
            .where(FMPNewsCorrelation.expires_at > datetime.now())
            .order_by(FMPNewsCorrelation.detected_at.desc())
            .limit(limit)
        )

        if correlation_type:
            stmt = stmt.where(FMPNewsCorrelation.correlation_type == correlation_type)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
