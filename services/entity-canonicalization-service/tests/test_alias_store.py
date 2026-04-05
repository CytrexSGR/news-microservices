"""Tests for AliasStore service - Core logic tests."""
import pytest
import time
from app.services.alias_store import AliasStore
from app.database.models import CanonicalEntity, EntityAlias


class TestAliasStoreFindExact:
    """Tests for exact alias matching."""

    @pytest.mark.asyncio
    async def test_find_exact_existing_alias(self, db_session, sample_entity_alias):
        """Test finding entity by exact alias match."""
        store = AliasStore(db_session)

        result = await store.find_exact("USA")

        assert result is not None
        assert result.name == "United States"
        assert result.wikidata_id == "Q30"

    @pytest.mark.asyncio
    async def test_find_exact_nonexistent_alias(self, db_session):
        """Test finding non-existent alias returns None."""
        store = AliasStore(db_session)

        result = await store.find_exact("NonExistentAlias")

        assert result is None

    @pytest.mark.asyncio
    async def test_find_exact_case_sensitive(self, db_session, sample_entity_alias):
        """Test that exact match is case-sensitive."""
        store = AliasStore(db_session)

        result = await store.find_exact("usa")  # lowercase

        assert result is None


class TestAliasStoreFindByName:
    """Tests for finding canonical entities by name."""

    @pytest.mark.asyncio
    async def test_find_by_name_existing(self, db_session, sample_canonical_entity):
        """Test finding canonical entity by name and type."""
        store = AliasStore(db_session)

        result = await store.find_by_name("United States", "LOCATION")

        assert result is not None
        assert result.id == sample_canonical_entity.id
        assert result.name == "United States"

    @pytest.mark.asyncio
    async def test_find_by_name_wrong_type(self, db_session, sample_canonical_entity):
        """Test finding entity with wrong type returns None."""
        store = AliasStore(db_session)

        result = await store.find_by_name("United States", "PERSON")

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_name_nonexistent(self, db_session):
        """Test finding non-existent entity returns None."""
        store = AliasStore(db_session)

        result = await store.find_by_name("NonExistent", "LOCATION")

        assert result is None


class TestAliasStoreGetByType:
    """Tests for getting entities by type."""

    @pytest.mark.asyncio
    async def test_get_by_type_existing(self, db_session, sample_canonical_entity):
        """Test getting entities by type."""
        store = AliasStore(db_session)

        results = await store.get_by_type("LOCATION")

        assert len(results) == 1
        assert results[0].name == "United States"

    @pytest.mark.asyncio
    async def test_get_by_type_empty(self, db_session):
        """Test getting entities by type with no matches."""
        store = AliasStore(db_session)

        results = await store.get_by_type("PERSON")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_by_type_multiple(self, db_session):
        """Test getting multiple entities of same type."""
        store = AliasStore(db_session)

        # Create multiple entities
        entity1 = CanonicalEntity(name="France", wikidata_id="Q142", type="LOCATION")
        entity2 = CanonicalEntity(name="Germany", wikidata_id="Q183", type="LOCATION")
        db_session.add(entity1)
        db_session.add(entity2)
        await db_session.commit()

        results = await store.get_by_type("LOCATION")

        assert len(results) == 2
        names = [e.name for e in results]
        assert "France" in names
        assert "Germany" in names


class TestAliasStoreGetCandidateNames:
    """Tests for getting candidate names."""

    @pytest.mark.asyncio
    async def test_get_candidate_names(self, db_session, sample_canonical_entity):
        """Test getting candidate names for similarity matching."""
        store = AliasStore(db_session)

        candidates = await store.get_candidate_names("LOCATION")

        assert len(candidates) == 1
        assert "United States" in candidates

    @pytest.mark.asyncio
    async def test_get_candidate_names_empty(self, db_session):
        """Test getting candidate names with no matches."""
        store = AliasStore(db_session)

        candidates = await store.get_candidate_names("PERSON")

        assert len(candidates) == 0


class TestAliasStoreStoreCanonical:
    """Tests for storing canonical entities."""

    @pytest.mark.asyncio
    async def test_store_canonical_basic(self, db_session):
        """Test storing a basic canonical entity."""
        store = AliasStore(db_session)

        result = await store.store_canonical(
            name="Barack Obama",
            wikidata_id="Q76",
            entity_type="PERSON",
            aliases=[]
        )

        assert result is not None
        assert result.name == "Barack Obama"
        assert result.wikidata_id == "Q76"
        assert result.type == "PERSON"

    @pytest.mark.asyncio
    async def test_store_canonical_with_aliases(self, db_session):
        """Test storing canonical entity with aliases."""
        store = AliasStore(db_session)

        result = await store.store_canonical(
            name="United States",
            wikidata_id="Q30",
            entity_type="LOCATION",
            aliases=["USA", "US", "United States of America"]
        )

        assert result is not None
        assert result.name == "United States"

        # Check aliases were created
        aliases = await store.get_aliases(result.id)
        assert len(aliases) == 3
        alias_texts = [a.alias for a in aliases]
        assert "USA" in alias_texts
        assert "US" in alias_texts

    @pytest.mark.asyncio
    @pytest.mark.memory
    async def test_store_canonical_batch_performance(self, db_session):
        """Test batch insert performance (Task 402 - should be < 500ms for 10 items)."""
        store = AliasStore(db_session)

        # Create entity with 10 aliases
        aliases = [f"alias_{i}" for i in range(10)]

        start_time = time.time()
        result = await store.store_canonical(
            name="Performance Test Entity",
            wikidata_id="Q999",
            entity_type="TEST",
            aliases=aliases
        )
        duration_ms = (time.time() - start_time) * 1000

        assert result is not None
        assert duration_ms < 500, f"Batch insert took {duration_ms:.1f}ms (expected < 500ms)"

        # Verify all aliases were created
        stored_aliases = await store.get_aliases(result.id)
        assert len(stored_aliases) == 10

    @pytest.mark.asyncio
    async def test_store_canonical_duplicate_returns_existing(self, db_session, sample_canonical_entity):
        """Test storing duplicate canonical entity returns existing."""
        store = AliasStore(db_session)

        result = await store.store_canonical(
            name="United States",
            wikidata_id="Q30",
            entity_type="LOCATION",
            aliases=[]
        )

        assert result is not None
        assert result.id == sample_canonical_entity.id

    @pytest.mark.asyncio
    async def test_store_canonical_filters_canonical_name_from_aliases(self, db_session):
        """Test that canonical name is filtered out from aliases list."""
        store = AliasStore(db_session)

        result = await store.store_canonical(
            name="Test Entity",
            wikidata_id="Q123",
            entity_type="TEST",
            aliases=["Test Entity", "Alias 1", "Alias 2"]  # Includes canonical name
        )

        # Should only create 2 aliases (canonical name filtered out)
        aliases = await store.get_aliases(result.id)
        assert len(aliases) == 2
        alias_texts = [a.alias for a in aliases]
        assert "Alias 1" in alias_texts
        assert "Alias 2" in alias_texts
        assert "Test Entity" not in alias_texts  # Canonical name not in aliases

    @pytest.mark.asyncio
    async def test_store_canonical_handles_duplicate_aliases_gracefully(self, db_session):
        """Test handling of duplicate aliases during batch insert."""
        store = AliasStore(db_session)

        # First entity with alias
        await store.store_canonical(
            name="Entity 1",
            wikidata_id="Q1",
            entity_type="TEST",
            aliases=["shared_alias"]
        )

        # Second entity with same alias (should handle gracefully)
        result = await store.store_canonical(
            name="Entity 2",
            wikidata_id="Q2",
            entity_type="TEST",
            aliases=["shared_alias", "unique_alias"]
        )

        # Should successfully create entity, even if some aliases fail
        assert result is not None
        assert result.name == "Entity 2"


class TestAliasStoreAddAlias:
    """Tests for adding aliases to existing entities."""

    @pytest.mark.asyncio
    async def test_add_alias_success(self, db_session, sample_canonical_entity):
        """Test adding a new alias to existing entity."""
        store = AliasStore(db_session)

        success = await store.add_alias("United States", "LOCATION", "US")

        assert success is True

        # Verify alias was added
        entity = await store.find_exact("US")
        assert entity is not None
        assert entity.name == "United States"

    @pytest.mark.asyncio
    async def test_add_alias_entity_not_found(self, db_session):
        """Test adding alias to non-existent entity."""
        store = AliasStore(db_session)

        success = await store.add_alias("NonExistent", "LOCATION", "NewAlias")

        assert success is False

    @pytest.mark.asyncio
    async def test_add_alias_already_exists_same_entity(self, db_session, sample_entity_alias):
        """Test adding alias that already exists for same entity."""
        store = AliasStore(db_session)

        success = await store.add_alias("United States", "LOCATION", "USA")

        assert success is True  # Should return True (idempotent)

    @pytest.mark.asyncio
    async def test_add_alias_already_exists_different_entity(self, db_session, sample_entity_alias):
        """Test adding alias that already exists for different entity."""
        store = AliasStore(db_session)

        # Create another entity
        entity2 = CanonicalEntity(name="Another Entity", wikidata_id="Q999", type="LOCATION")
        db_session.add(entity2)
        await db_session.commit()

        # Try to add alias that belongs to different entity
        success = await store.add_alias("Another Entity", "LOCATION", "USA")

        assert success is False


class TestAliasStoreGetAliases:
    """Tests for getting aliases."""

    @pytest.mark.asyncio
    async def test_get_aliases_existing(self, db_session, sample_canonical_entity, sample_entity_alias):
        """Test getting aliases for existing entity."""
        store = AliasStore(db_session)

        aliases = await store.get_aliases(sample_canonical_entity.id)

        assert len(aliases) == 1
        assert aliases[0].alias == "USA"

    @pytest.mark.asyncio
    async def test_get_aliases_empty(self, db_session, sample_canonical_entity):
        """Test getting aliases for entity with no aliases."""
        store = AliasStore(db_session)

        # Delete the sample alias first
        aliases_to_delete = await store.get_aliases(sample_canonical_entity.id)
        for alias in aliases_to_delete:
            await db_session.delete(alias)
        await db_session.commit()

        aliases = await store.get_aliases(sample_canonical_entity.id)

        assert len(aliases) == 0


class TestAliasStoreGetStats:
    """Tests for statistics retrieval."""

    @pytest.mark.asyncio
    async def test_get_stats_basic(self, db_session, sample_canonical_entity, sample_entity_alias):
        """Test getting basic statistics."""
        store = AliasStore(db_session)

        total_entities, total_aliases, wikidata_linked = await store.get_stats()

        assert total_entities == 1
        assert total_aliases == 1
        assert wikidata_linked == 1  # sample_canonical_entity has wikidata_id

    @pytest.mark.asyncio
    async def test_get_stats_empty_database(self, db_session):
        """Test statistics with empty database."""
        store = AliasStore(db_session)

        total_entities, total_aliases, wikidata_linked = await store.get_stats()

        assert total_entities == 0
        assert total_aliases == 0
        assert wikidata_linked == 0

    @pytest.mark.asyncio
    async def test_get_stats_entities_without_wikidata(self, db_session):
        """Test statistics with entities without Wikidata IDs."""
        store = AliasStore(db_session)

        # Create entity without wikidata_id
        entity = CanonicalEntity(
            name="Unknown Entity",
            wikidata_id=None,
            type="OTHER"
        )
        db_session.add(entity)
        await db_session.commit()

        total_entities, total_aliases, wikidata_linked = await store.get_stats()

        assert total_entities == 1
        assert wikidata_linked == 0


class TestAliasStoreGetDetailedStats:
    """Tests for detailed statistics retrieval."""

    @pytest.mark.asyncio
    async def test_get_detailed_stats_basic(self, db_session, sample_canonical_entity, sample_entity_alias):
        """Test getting detailed statistics."""
        store = AliasStore(db_session)

        stats = await store.get_detailed_stats()

        assert stats["total_canonical_entities"] == 1
        assert stats["total_aliases"] == 1
        assert stats["wikidata_linked"] == 1
        assert stats["wikidata_coverage_percent"] == 100.0
        assert stats["deduplication_ratio"] == 1.0
        assert "entity_type_distribution" in stats
        assert "top_entities_by_aliases" in stats
        assert "entities_without_qid" in stats
        assert stats["entities_without_qid"] == 0

    @pytest.mark.asyncio
    async def test_get_detailed_stats_entity_type_distribution(self, db_session):
        """Test entity type distribution in detailed stats."""
        store = AliasStore(db_session)

        # Create entities of different types
        entities = [
            CanonicalEntity(name="Person 1", wikidata_id="Q1", type="PERSON"),
            CanonicalEntity(name="Person 2", wikidata_id="Q2", type="PERSON"),
            CanonicalEntity(name="Org 1", wikidata_id="Q3", type="ORGANIZATION"),
        ]
        for entity in entities:
            db_session.add(entity)
        await db_session.commit()

        stats = await store.get_detailed_stats()

        assert stats["entity_type_distribution"]["PERSON"] == 2
        assert stats["entity_type_distribution"]["ORGANIZATION"] == 1

    @pytest.mark.asyncio
    async def test_get_detailed_stats_deduplication_ratio(self, db_session):
        """Test deduplication ratio calculation."""
        store = AliasStore(db_session)

        # Create entity with multiple aliases
        entity = CanonicalEntity(name="Test Entity", wikidata_id="Q1", type="TEST")
        db_session.add(entity)
        await db_session.flush()

        # Add 5 aliases
        for i in range(5):
            alias = EntityAlias(canonical_id=entity.id, alias=f"alias_{i}")
            db_session.add(alias)
        await db_session.commit()

        stats = await store.get_detailed_stats()

        # Deduplication ratio = total_aliases / total_entities
        assert stats["deduplication_ratio"] == 5.0

    @pytest.mark.asyncio
    async def test_get_detailed_stats_top_entities(self, db_session):
        """Test top entities by alias count."""
        store = AliasStore(db_session)

        # Create entity with many aliases
        entity = CanonicalEntity(name="Popular Entity", wikidata_id="Q1", type="TEST")
        db_session.add(entity)
        await db_session.flush()

        # Add 10 aliases
        for i in range(10):
            alias = EntityAlias(canonical_id=entity.id, alias=f"alias_{i}")
            db_session.add(alias)
        await db_session.commit()

        stats = await store.get_detailed_stats()

        # Should include in top entities
        assert len(stats["top_entities_by_aliases"]) > 0
        top_entity = stats["top_entities_by_aliases"][0]
        assert top_entity["canonical_name"] == "Popular Entity"
        assert top_entity["alias_count"] == 10
