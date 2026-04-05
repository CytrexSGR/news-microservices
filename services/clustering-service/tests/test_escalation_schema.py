"""Tests for escalation schema tables.

Validates that the escalation-related tables exist with correct columns
and constraints for the Intelligence Interpretation Layer:
- escalation_anchors: Reference anchors for escalation level detection
- article_clusters escalation columns: Domain scores and combined levels
- fmp_news_correlations: FMP regime / news escalation correlations
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.config import settings


@pytest_asyncio.fixture
async def db_engine() -> AsyncEngine:
    """Create a fresh engine for each test to avoid event loop issues."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_escalation_anchors_table_exists(db_engine: AsyncEngine):
    """Verify escalation_anchors table with correct columns."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'escalation_anchors' ORDER BY ordinal_position"
        ))
        columns = {row[0]: row[1] for row in result.fetchall()}

    # Core columns
    assert 'id' in columns, "id column missing"
    assert 'domain' in columns, "domain column missing"
    assert 'level' in columns, "level column missing"
    assert 'label' in columns, "label column missing"
    assert 'reference_text' in columns, "reference_text column missing"
    assert 'embedding' in columns, "embedding column missing"
    assert 'keywords' in columns, "keywords column missing"
    assert 'weight' in columns, "weight column missing"
    assert 'is_active' in columns, "is_active column missing"
    assert 'created_at' in columns, "created_at column missing"
    assert 'updated_at' in columns, "updated_at column missing"


@pytest.mark.asyncio
async def test_escalation_anchors_constraints(db_engine: AsyncEngine):
    """Verify CHECK constraints for domain and level."""
    async with db_engine.connect() as conn:
        # Test domain constraint - should reject invalid domain
        try:
            await conn.execute(text("""
                INSERT INTO escalation_anchors (domain, level, label, reference_text, embedding)
                VALUES ('invalid_domain', 1, 'test', 'test text',
                        (SELECT array_fill(0::real, ARRAY[1536])::vector))
            """))
            await conn.commit()
            # Should not reach here
            assert False, "Should have rejected invalid domain"
        except Exception as e:
            # Expected - constraint violation
            await conn.rollback()
            assert 'chk_anchor_domain' in str(e).lower() or 'check' in str(e).lower()

        # Test level constraint - should reject level outside 1-5
        try:
            await conn.execute(text("""
                INSERT INTO escalation_anchors (domain, level, label, reference_text, embedding)
                VALUES ('geopolitical', 6, 'test', 'test text',
                        (SELECT array_fill(0::real, ARRAY[1536])::vector))
            """))
            await conn.commit()
            assert False, "Should have rejected level > 5"
        except Exception as e:
            await conn.rollback()
            assert 'chk_anchor_level' in str(e).lower() or 'check' in str(e).lower()


@pytest.mark.asyncio
async def test_escalation_anchors_valid_insert(db_engine: AsyncEngine):
    """Verify valid data can be inserted."""
    async with db_engine.connect() as conn:
        # Insert valid record
        result = await conn.execute(text("""
            INSERT INTO escalation_anchors (domain, level, label, reference_text, embedding, keywords)
            VALUES ('geopolitical', 3, 'test_anchor', 'Test escalation reference text',
                    (SELECT array_fill(0.1::real, ARRAY[1536])::vector),
                    ARRAY['test', 'keyword'])
            RETURNING id, domain, level, label
        """))
        row = result.fetchone()
        await conn.commit()

        assert row is not None
        assert row[1] == 'geopolitical'
        assert row[2] == 3
        assert row[3] == 'test_anchor'

        # Cleanup
        await conn.execute(text(
            "DELETE FROM escalation_anchors WHERE label = 'test_anchor'"
        ))
        await conn.commit()


@pytest.mark.asyncio
async def test_escalation_anchors_indexes_exist(db_engine: AsyncEngine):
    """Verify required indexes exist."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'escalation_anchors'
        """))
        indexes = [row[0] for row in result.fetchall()]

    # Check for lookup index
    assert any('lookup' in idx for idx in indexes), "Lookup index missing"
    # Check for embedding index
    assert any('embedding' in idx for idx in indexes), "Embedding index missing"


@pytest.mark.asyncio
async def test_article_clusters_escalation_columns(db_engine: AsyncEngine):
    """Verify escalation columns added to article_clusters."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'article_clusters' AND column_name LIKE 'escalation_%'"
        ))
        columns = [row[0] for row in result.fetchall()]

    assert 'escalation_geopolitical' in columns
    assert 'escalation_military' in columns
    assert 'escalation_economic' in columns
    assert 'escalation_combined' in columns
    assert 'escalation_level' in columns
    assert 'escalation_signals' in columns
    assert 'escalation_calculated_at' in columns


@pytest.mark.asyncio
async def test_article_clusters_escalation_indexes(db_engine: AsyncEngine):
    """Verify escalation indexes exist on article_clusters."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'article_clusters' AND indexname LIKE '%escalation%'
        """))
        indexes = [row[0] for row in result.fetchall()]

    # Check for escalation-related indexes
    assert any('escalation_combined' in idx for idx in indexes), \
        "escalation_combined index missing"
    assert any('escalation_level' in idx for idx in indexes), \
        "escalation_level index missing"


@pytest.mark.asyncio
async def test_article_clusters_escalation_level_constraint(db_engine: AsyncEngine):
    """Verify escalation_level CHECK constraint (1-5)."""
    async with db_engine.connect() as conn:
        # Get any existing cluster ID to test update constraint
        result = await conn.execute(text(
            "SELECT id FROM article_clusters LIMIT 1"
        ))
        row = result.fetchone()

        if row:
            cluster_id = row[0]
            # Test invalid level - should reject level outside 1-5
            try:
                await conn.execute(text("""
                    UPDATE article_clusters
                    SET escalation_level = 6
                    WHERE id = :id
                """), {"id": cluster_id})
                await conn.commit()
                assert False, "Should have rejected escalation_level > 5"
            except Exception as e:
                await conn.rollback()
                assert 'chk_escalation_level' in str(e).lower() or 'check' in str(e).lower()


# =============================================================================
# Tests for fmp_news_correlations table (Migration 027)
# =============================================================================

@pytest.mark.asyncio
async def test_fmp_correlations_table_exists(db_engine: AsyncEngine):
    """Verify fmp_news_correlations table exists with correct columns."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'fmp_news_correlations' ORDER BY ordinal_position"
        ))
        columns = {row[0]: row[1] for row in result.fetchall()}

    # Core columns
    assert 'id' in columns, "id column missing"
    assert 'detected_at' in columns, "detected_at column missing"
    assert 'correlation_type' in columns, "correlation_type column missing"
    assert 'fmp_regime' in columns, "fmp_regime column missing"
    assert 'escalation_level' in columns, "escalation_level column missing"
    assert 'confidence' in columns, "confidence column missing"
    assert 'related_clusters' in columns, "related_clusters column missing"
    assert 'metadata' in columns, "metadata column missing"
    assert 'expires_at' in columns, "expires_at column missing"
    assert 'is_active' in columns, "is_active column missing"
    assert 'created_at' in columns, "created_at column missing"
    assert 'updated_at' in columns, "updated_at column missing"


@pytest.mark.asyncio
async def test_fmp_correlations_constraints(db_engine: AsyncEngine):
    """Test CHECK constraints for correlation_type and fmp_regime."""
    async with db_engine.connect() as conn:
        # Test invalid correlation_type - should reject
        try:
            await conn.execute(text("""
                INSERT INTO fmp_news_correlations (correlation_type, fmp_regime)
                VALUES ('INVALID_TYPE', 'RISK_ON')
            """))
            await conn.commit()
            assert False, "Should have rejected invalid correlation_type"
        except Exception as e:
            await conn.rollback()
            assert 'chk_fmp_correlation_type' in str(e).lower() or 'check' in str(e).lower()

        # Test invalid fmp_regime - should reject
        try:
            await conn.execute(text("""
                INSERT INTO fmp_news_correlations (correlation_type, fmp_regime)
                VALUES ('CONFIRMATION', 'INVALID_REGIME')
            """))
            await conn.commit()
            assert False, "Should have rejected invalid fmp_regime"
        except Exception as e:
            await conn.rollback()
            assert 'chk_fmp_regime' in str(e).lower() or 'check' in str(e).lower()

        # Test invalid escalation_level (outside 1-5)
        try:
            await conn.execute(text("""
                INSERT INTO fmp_news_correlations (correlation_type, fmp_regime, escalation_level)
                VALUES ('CONFIRMATION', 'RISK_ON', 6)
            """))
            await conn.commit()
            assert False, "Should have rejected escalation_level > 5"
        except Exception as e:
            await conn.rollback()
            assert 'chk_fmp_escalation_level' in str(e).lower() or 'check' in str(e).lower()

        # Test invalid confidence (outside 0-1)
        try:
            await conn.execute(text("""
                INSERT INTO fmp_news_correlations (correlation_type, fmp_regime, confidence)
                VALUES ('CONFIRMATION', 'RISK_ON', 1.5)
            """))
            await conn.commit()
            assert False, "Should have rejected confidence > 1"
        except Exception as e:
            await conn.rollback()
            assert 'chk_fmp_confidence' in str(e).lower() or 'check' in str(e).lower()


@pytest.mark.asyncio
async def test_fmp_correlations_valid_insert(db_engine: AsyncEngine):
    """Verify valid data can be inserted and retrieved."""
    async with db_engine.connect() as conn:
        # Insert valid record with all fields
        result = await conn.execute(text("""
            INSERT INTO fmp_news_correlations (
                correlation_type, fmp_regime, escalation_level,
                confidence, related_clusters, metadata, is_active
            )
            VALUES (
                'EARLY_WARNING', 'TRANSITIONAL', 4,
                0.875, ARRAY[]::uuid[], '{"vix_level": 25.5, "notes": "test"}'::jsonb, true
            )
            RETURNING id, correlation_type, fmp_regime, escalation_level, confidence, is_active
        """))
        row = result.fetchone()
        await conn.commit()

        assert row is not None
        assert row[1] == 'EARLY_WARNING'
        assert row[2] == 'TRANSITIONAL'
        assert row[3] == 4
        assert float(row[4]) == 0.875
        assert row[5] is True

        inserted_id = row[0]

        # Cleanup
        await conn.execute(text(
            "DELETE FROM fmp_news_correlations WHERE id = :id"
        ), {"id": inserted_id})
        await conn.commit()


@pytest.mark.asyncio
async def test_fmp_correlations_indexes(db_engine: AsyncEngine):
    """Verify required indexes exist on fmp_news_correlations table."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'fmp_news_correlations'
        """))
        indexes = [row[0] for row in result.fetchall()]

    # Check for required indexes
    assert any('active_type' in idx for idx in indexes), \
        "idx_fmp_correlations_active_type index missing"
    assert any('regime' in idx for idx in indexes), \
        "idx_fmp_correlations_regime index missing"


@pytest.mark.asyncio
async def test_fmp_correlations_all_valid_types(db_engine: AsyncEngine):
    """Verify all valid correlation_type and fmp_regime values are accepted."""
    async with db_engine.connect() as conn:
        valid_types = ['CONFIRMATION', 'DIVERGENCE', 'EARLY_WARNING']
        valid_regimes = ['RISK_ON', 'RISK_OFF', 'TRANSITIONAL']
        inserted_ids = []

        # Test all combinations
        for corr_type in valid_types:
            for regime in valid_regimes:
                result = await conn.execute(text("""
                    INSERT INTO fmp_news_correlations (correlation_type, fmp_regime)
                    VALUES (:corr_type, :regime)
                    RETURNING id
                """), {"corr_type": corr_type, "regime": regime})
                row = result.fetchone()
                inserted_ids.append(row[0])
        await conn.commit()

        # Verify all 9 combinations were inserted
        assert len(inserted_ids) == 9

        # Cleanup
        for id_ in inserted_ids:
            await conn.execute(text(
                "DELETE FROM fmp_news_correlations WHERE id = :id"
            ), {"id": id_})
        await conn.commit()
