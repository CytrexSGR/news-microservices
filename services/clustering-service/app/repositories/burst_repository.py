"""Repository for burst alert database operations."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.burst_alert import BurstAlert

logger = logging.getLogger(__name__)


class BurstRepository:
    """
    Repository for burst alert persistence.

    Handles:
    - Recording burst detections for auditing
    - Checking cooldown periods from database
    - Marking alerts as sent
    - Querying recent alerts

    Attributes:
        session: SQLAlchemy async session
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def record_burst_alert(
        self,
        cluster_id: UUID,
        severity: str,
        velocity: int,
        window_minutes: int,
        alert_sent: bool = False,
    ) -> UUID:
        """
        Record a burst detection in the database.

        Args:
            cluster_id: UUID of the cluster with burst
            severity: Severity level (low, medium, high, critical)
            velocity: Articles per window when detected
            window_minutes: Detection window size
            alert_sent: Whether external alert was sent

        Returns:
            UUID of created alert record
        """
        alert = BurstAlert(
            id=uuid4(),
            cluster_id=cluster_id,
            severity=severity,
            velocity=velocity,
            window_minutes=window_minutes,
            alert_sent=alert_sent,
        )

        self.session.add(alert)
        await self.session.commit()

        logger.info(
            f"Recorded burst alert: cluster={cluster_id} severity={severity} "
            f"velocity={velocity}"
        )

        return alert.id

    async def get_recent_alerts(
        self,
        cluster_id: UUID,
        hours: int = 24
    ) -> List[BurstAlert]:
        """
        Get recent alerts for a cluster.

        Args:
            cluster_id: UUID of the cluster
            hours: Look back window in hours

        Returns:
            List of BurstAlert records
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(BurstAlert)
            .where(BurstAlert.cluster_id == cluster_id)
            .where(BurstAlert.detected_at >= cutoff)
            .order_by(BurstAlert.detected_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def is_in_cooldown(
        self,
        cluster_id: UUID,
        cooldown_minutes: int = 30
    ) -> bool:
        """
        Check if cluster has a recent alert (in cooldown).

        Args:
            cluster_id: UUID of the cluster
            cooldown_minutes: Cooldown period in minutes

        Returns:
            True if a sent alert exists within cooldown period
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)

        query = (
            select(BurstAlert)
            .where(BurstAlert.cluster_id == cluster_id)
            .where(BurstAlert.alert_sent == True)  # noqa: E712
            .where(BurstAlert.detected_at >= cutoff)
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def mark_alert_sent(self, alert_id: UUID) -> None:
        """
        Mark an alert as sent.

        Args:
            alert_id: UUID of the alert to update
        """
        alert = await self.session.get(BurstAlert, alert_id)
        if alert:
            alert.alert_sent = True
            alert.alert_sent_at = datetime.now(timezone.utc)
            await self.session.commit()
            logger.debug(f"Marked alert {alert_id} as sent")

    async def get_pending_alerts(self, limit: int = 100) -> List[BurstAlert]:
        """
        Get alerts that haven't been sent yet.

        Args:
            limit: Maximum alerts to return

        Returns:
            List of unsent BurstAlert records
        """
        query = (
            select(BurstAlert)
            .where(BurstAlert.alert_sent == False)  # noqa: E712
            .order_by(BurstAlert.detected_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())
