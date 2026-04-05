# tests/test_alias_store_enhanced.py
"""Tests for enhanced alias store with type-aware matching."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.alias_store import AliasStore
from app.database.models import CanonicalEntity, EntityAlias


@pytest.fixture
def mock_session():
    """Create mock async session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def alias_store(mock_session):
    """Create alias store with mock session."""
    return AliasStore(mock_session)


class TestFindByAliasType:
    """Tests for find_by_alias_type method."""

    @pytest.mark.asyncio
    async def test_find_ticker_exact_match(self, alias_store, mock_session):
        """Ticker aliases require exact match."""
        # Setup: AAPL ticker for Apple Inc.
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = CanonicalEntity(
            id=1, name="Apple Inc.", wikidata_id="Q312", type="ORGANIZATION"
        )
        mock_session.execute.return_value = mock_result

        # Execute
        result = await alias_store.find_by_alias_type("AAPL", alias_type="ticker")

        # Assert
        assert result is not None
        assert result.name == "Apple Inc."

    @pytest.mark.asyncio
    async def test_find_abbreviation_case_insensitive(self, alias_store, mock_session):
        """Abbreviation aliases are case-insensitive."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = CanonicalEntity(
            id=2, name="United States", wikidata_id="Q30", type="LOCATION"
        )
        mock_session.execute.return_value = mock_result

        # Execute - "usa" should match "USA" abbreviation
        result = await alias_store.find_by_alias_type("usa", alias_type="abbreviation")

        # Assert
        assert result is not None
        assert result.name == "United States"

    @pytest.mark.asyncio
    async def test_find_nickname_normalized(self, alias_store, mock_session):
        """Nickname aliases use normalized matching."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = CanonicalEntity(
            id=3, name="Donald Trump", wikidata_id="Q22686", type="PERSON"
        )
        mock_session.execute.return_value = mock_result

        # Execute - "The Donald" normalized should match
        result = await alias_store.find_by_alias_type("the donald", alias_type="nickname")

        # Assert
        assert result is not None
        assert result.name == "Donald Trump"

    @pytest.mark.asyncio
    async def test_find_no_match_returns_none(self, alias_store, mock_session):
        """No match returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await alias_store.find_by_alias_type("UNKNOWN", alias_type="ticker")

        assert result is None


class TestAddAliasWithType:
    """Tests for add_alias_with_type method."""

    @pytest.mark.asyncio
    async def test_add_ticker_alias(self, alias_store, mock_session):
        """Add ticker alias with proper normalization."""
        # Setup: find canonical entity returns entity, find_alias_by_value returns None
        find_canonical_result = MagicMock()
        find_canonical_result.scalar_one_or_none.return_value = CanonicalEntity(
            id=1, name="Apple Inc.", wikidata_id="Q312", type="ORGANIZATION"
        )

        find_alias_result = MagicMock()
        find_alias_result.scalar_one_or_none.return_value = None  # Alias does not exist yet

        mock_session.execute.side_effect = [find_canonical_result, find_alias_result]

        # Execute
        success = await alias_store.add_alias_with_type(
            canonical_name="Apple Inc.",
            entity_type="ORGANIZATION",
            new_alias="AAPL",
            alias_type="ticker",
            source="discovered"
        )

        # Assert
        assert success is True
        mock_session.add.assert_called_once()
        # Verify EntityAlias was created with correct fields
        added_alias = mock_session.add.call_args[0][0]
        assert added_alias.alias == "AAPL"
        assert added_alias.alias_type == "ticker"
        assert added_alias.alias_normalized == "aapl"
        assert added_alias.source == "discovered"

    @pytest.mark.asyncio
    async def test_add_alias_increments_usage_count_for_duplicate(self, alias_store, mock_session):
        """Adding existing alias increments usage count."""
        # Setup: alias already exists for same entity
        find_canonical_result = MagicMock()
        find_canonical_result.scalar_one_or_none.return_value = CanonicalEntity(
            id=1, name="Apple Inc.", wikidata_id="Q312", type="ORGANIZATION"
        )

        existing_alias = EntityAlias(
            id=100, canonical_id=1, alias="AAPL", usage_count=5
        )
        find_alias_result = MagicMock()
        find_alias_result.scalar_one_or_none.return_value = existing_alias

        mock_session.execute.side_effect = [find_canonical_result, find_alias_result]

        # Execute
        success = await alias_store.add_alias_with_type(
            canonical_name="Apple Inc.",
            entity_type="ORGANIZATION",
            new_alias="AAPL",
            alias_type="ticker",
            source="discovered"
        )

        # Assert: should succeed and increment usage count
        assert success is True
        assert existing_alias.usage_count == 6


class TestGetCandidateAliases:
    """Tests for get_candidate_aliases method with normalization."""

    @pytest.mark.asyncio
    async def test_get_normalized_candidates(self, alias_store, mock_session):
        """Get candidates returns normalized aliases."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("apple inc.",),
            ("microsoft corporation",),
            ("google llc",),
        ]
        mock_session.execute.return_value = mock_result

        # Execute
        candidates = await alias_store.get_candidate_aliases_normalized(
            entity_type="ORGANIZATION",
            limit=100
        )

        # Assert
        assert len(candidates) == 3
        assert "apple inc." in candidates
        assert all(c == c.lower() for c in candidates)

    @pytest.mark.asyncio
    async def test_get_candidates_by_alias_type(self, alias_store, mock_session):
        """Get candidates filtered by alias type."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("AAPL",),
            ("MSFT",),
            ("GOOGL",),
        ]
        mock_session.execute.return_value = mock_result

        # Execute
        candidates = await alias_store.get_candidate_aliases_by_type(
            entity_type="ORGANIZATION",
            alias_type="ticker",
            limit=100
        )

        # Assert
        assert len(candidates) == 3
        assert "AAPL" in candidates

    @pytest.mark.asyncio
    async def test_get_candidates_ordered_by_usage(self, alias_store, mock_session):
        """Get candidates ordered by usage count (most used first)."""
        mock_result = MagicMock()
        # Ordered by usage_count desc
        mock_result.all.return_value = [
            ("apple",),   # usage_count: 100
            ("google",),  # usage_count: 50
            ("microsoft",), # usage_count: 25
        ]
        mock_session.execute.return_value = mock_result

        candidates = await alias_store.get_candidate_aliases_normalized(
            entity_type="ORGANIZATION",
            order_by_usage=True
        )

        assert candidates[0] == "apple"


class TestFindByNormalizedAlias:
    """Tests for normalized alias lookup."""

    @pytest.mark.asyncio
    async def test_find_by_normalized_ignores_case(self, alias_store, mock_session):
        """Find by normalized matches regardless of case."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = CanonicalEntity(
            id=1, name="Apple Inc.", wikidata_id="Q312", type="ORGANIZATION"
        )
        mock_session.execute.return_value = mock_result

        # Execute with mixed case
        result = await alias_store.find_by_normalized("ApPlE iNc.")

        # Assert
        assert result is not None
        assert result.name == "Apple Inc."

    @pytest.mark.asyncio
    async def test_find_by_normalized_trims_whitespace(self, alias_store, mock_session):
        """Find by normalized handles extra whitespace."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = CanonicalEntity(
            id=1, name="Apple Inc.", wikidata_id="Q312", type="ORGANIZATION"
        )
        mock_session.execute.return_value = mock_result

        # Execute with extra whitespace
        result = await alias_store.find_by_normalized("  Apple Inc.  ")

        # Assert
        assert result is not None
