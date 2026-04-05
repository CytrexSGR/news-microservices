"""Tests for entity fragmentation metrics."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.fragmentation_metrics import FragmentationMetrics


@pytest.fixture
def mock_session():
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    return session


@pytest.fixture
def metrics(mock_session):
    return FragmentationMetrics(mock_session)


class TestFragmentationMetrics:
    """Tests for fragmentation analysis."""

    @pytest.mark.asyncio
    async def test_calculate_fragmentation_score(self, metrics, mock_session):
        """Calculate fragmentation score for entity type."""
        # Setup: 100 entities, 250 aliases (2.5 avg aliases per entity)
        # Implementation makes two separate queries: one for entities, one for aliases
        entity_result = MagicMock()
        entity_result.scalar_one.return_value = 100  # total entities

        alias_result = MagicMock()
        alias_result.scalar_one.return_value = 250  # total aliases

        mock_session.execute.side_effect = [entity_result, alias_result]

        score = await metrics.calculate_fragmentation_score("ORGANIZATION")

        # Lower score = less fragmentation
        # Score = 1 / (aliases_per_entity) where 1.0 is ideal
        assert 0 < score <= 1.0
        assert score == pytest.approx(0.4, rel=0.1)  # 1/2.5 = 0.4

    @pytest.mark.asyncio
    async def test_find_potential_duplicates(self, metrics, mock_session):
        """Find entities that might be duplicates based on similarity."""
        # Mock returns entity tuples (id, name) that get fuzzy matched
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (1, "Apple Inc."),
            (2, "Apple Inc"),  # Similar to first
            (3, "Microsoft Corporation"),
            (4, "Microsoft Corp"),  # Similar to third
        ]
        mock_session.execute.return_value = mock_result

        duplicates = await metrics.find_potential_duplicates(
            entity_type="ORGANIZATION",
            threshold=0.90
        )

        # Should find similar pairs
        assert len(duplicates) >= 1
        assert duplicates[0]["similarity"] >= 0.90

    @pytest.mark.asyncio
    async def test_get_singleton_entities(self, metrics, mock_session):
        """Find entities with only 1 alias (high fragmentation risk)."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(name="Lonely Entity 1"),
            MagicMock(name="Lonely Entity 2"),
        ]
        mock_session.execute.return_value = mock_result

        singletons = await metrics.get_singleton_entities("ORGANIZATION")

        assert len(singletons) == 2

    @pytest.mark.asyncio
    async def test_generate_fragmentation_report(self, metrics, mock_session):
        """Generate comprehensive fragmentation report."""
        # Mock for calculate_fragmentation_score (2 calls)
        entity_count_result = MagicMock()
        entity_count_result.scalar_one.return_value = 100

        alias_count_result = MagicMock()
        alias_count_result.scalar_one.return_value = 250

        # Mock for entity/alias counts in generate_report (2 more calls)
        entity_count_result_2 = MagicMock()
        entity_count_result_2.scalar_one.return_value = 100

        alias_count_result_2 = MagicMock()
        alias_count_result_2.scalar_one.return_value = 250

        # Mock for get_singleton_entities
        singleton_result = MagicMock()
        singleton_result.scalars.return_value.all.return_value = []

        # Mock for find_potential_duplicates
        duplicates_result = MagicMock()
        duplicates_result.all.return_value = []

        mock_session.execute.side_effect = [
            entity_count_result,    # calculate_fragmentation_score entities
            alias_count_result,     # calculate_fragmentation_score aliases
            entity_count_result_2,  # generate_report entities
            alias_count_result_2,   # generate_report aliases
            singleton_result,       # get_singleton_entities
            duplicates_result,      # find_potential_duplicates
        ]

        report = await metrics.generate_report("ORGANIZATION")

        assert "fragmentation_score" in report
        assert "total_entities" in report
        assert "total_aliases" in report
        assert "avg_aliases_per_entity" in report
        assert "singleton_count" in report
        assert "potential_duplicates" in report
