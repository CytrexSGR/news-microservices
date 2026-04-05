"""Tests for BurstRepository database operations."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.models.burst_alert import BurstAlert
from app.repositories.burst_repository import BurstRepository


class TestBurstRepository:
    """Tests for BurstRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def repo(self, mock_session):
        """Create repository with mock session."""
        return BurstRepository(mock_session)

    @pytest.mark.asyncio
    async def test_record_burst_alert(self, repo, mock_session):
        """Should persist burst alert to database."""
        cluster_id = uuid4()

        alert_id = await repo.record_burst_alert(
            cluster_id=cluster_id,
            severity="high",
            velocity=15,
            window_minutes=5,
            alert_sent=False,
        )

        assert alert_id is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        # Verify the alert object was created correctly
        added_alert = mock_session.add.call_args[0][0]
        assert added_alert.cluster_id == cluster_id
        assert added_alert.severity == "high"
        assert added_alert.velocity == 15
        assert added_alert.window_minutes == 5
        assert added_alert.alert_sent is False

    @pytest.mark.asyncio
    async def test_get_recent_alerts(self, repo, mock_session):
        """Should return recent alerts for a cluster."""
        cluster_id = uuid4()

        # Create mock alerts
        mock_alerts = [
            MagicMock(cluster_id=cluster_id, severity="medium", velocity=5 + i)
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_alerts
        mock_session.execute = AsyncMock(return_value=mock_result)

        alerts = await repo.get_recent_alerts(cluster_id, hours=1)

        assert len(alerts) == 3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_in_cooldown_no_alerts(self, repo, mock_session):
        """Should return False when no alerts exist."""
        cluster_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.is_in_cooldown(cluster_id, cooldown_minutes=30)

        assert result is False
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_in_cooldown_with_recent_alert(self, repo, mock_session):
        """Should return True when recent sent alert exists."""
        cluster_id = uuid4()

        mock_alert = MagicMock()
        mock_alert.alert_sent = True
        mock_alert.detected_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alert
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.is_in_cooldown(cluster_id, cooldown_minutes=30)

        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_alert_sent(self, repo, mock_session):
        """Should mark alert as sent."""
        alert_id = uuid4()

        mock_alert = MagicMock()
        mock_alert.alert_sent = False
        mock_alert.alert_sent_at = None
        mock_session.get = AsyncMock(return_value=mock_alert)

        await repo.mark_alert_sent(alert_id)

        assert mock_alert.alert_sent is True
        assert mock_alert.alert_sent_at is not None
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_alert_sent_not_found(self, repo, mock_session):
        """Should handle case where alert is not found."""
        alert_id = uuid4()

        mock_session.get = AsyncMock(return_value=None)

        # Should not raise exception
        await repo.mark_alert_sent(alert_id)

        # Commit should not be called when alert not found
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_pending_alerts(self, repo, mock_session):
        """Should return unsent alerts."""
        mock_alerts = [
            MagicMock(alert_sent=False, severity="high"),
            MagicMock(alert_sent=False, severity="critical"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_alerts
        mock_session.execute = AsyncMock(return_value=mock_result)

        alerts = await repo.get_pending_alerts(limit=100)

        assert len(alerts) == 2
        mock_session.execute.assert_called_once()
