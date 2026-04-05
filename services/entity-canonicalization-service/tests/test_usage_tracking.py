# tests/test_usage_tracking.py
"""Tests for alias usage tracking."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.alias_store import AliasStore
from app.database.models import CanonicalEntity, EntityAlias


@pytest.fixture
def mock_session():
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def alias_store(mock_session):
    return AliasStore(mock_session)


class TestUsageTracking:
    """Tests for alias usage tracking."""

    @pytest.mark.asyncio
    async def test_increment_usage_on_exact_match(self, alias_store, mock_session):
        """Exact match increments usage count."""
        # Setup: alias with usage_count = 5
        existing_alias = EntityAlias(id=1, canonical_id=1, alias="USA", usage_count=5)
        canonical = CanonicalEntity(id=1, name="United States", type="LOCATION")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = canonical
        mock_result.scalars.return_value.first.return_value = existing_alias
        mock_session.execute.return_value = mock_result

        # Execute
        await alias_store.record_usage("USA")

        # Assert
        assert existing_alias.usage_count == 6

    @pytest.mark.asyncio
    async def test_get_top_aliases_by_usage(self, alias_store, mock_session):
        """Get aliases ordered by usage count."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            EntityAlias(alias="USA", usage_count=100),
            EntityAlias(alias="US", usage_count=50),
            EntityAlias(alias="United States", usage_count=25),
        ]
        mock_session.execute.return_value = mock_result

        aliases = await alias_store.get_top_aliases(canonical_id=1, limit=10)

        assert len(aliases) == 3
        assert aliases[0].usage_count >= aliases[1].usage_count

    @pytest.mark.asyncio
    async def test_get_most_used_entities(self, alias_store, mock_session):
        """Get entities ranked by total alias usage."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (CanonicalEntity(name="United States"), 500),  # Total usage
            (CanonicalEntity(name="Germany"), 300),
            (CanonicalEntity(name="France"), 200),
        ]
        mock_session.execute.return_value = mock_result

        entities = await alias_store.get_most_used_entities(entity_type="LOCATION", limit=10)

        assert len(entities) == 3
        assert entities[0][1] == 500

    @pytest.mark.asyncio
    async def test_decay_unused_aliases(self, alias_store, mock_session):
        """Aliases not used in X days get usage count decayed."""
        # This is for future ranking optimization
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        # Execute
        count = await alias_store.decay_stale_aliases(days_threshold=30, decay_factor=0.9)

        # Assert: execute was called with UPDATE query
        mock_session.execute.assert_called()
        assert count == 5
