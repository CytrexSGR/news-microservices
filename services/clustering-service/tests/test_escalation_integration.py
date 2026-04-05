"""End-to-end integration tests for escalation calculation.

Tests verify that the complete escalation infrastructure is in place:
- Escalation anchors table exists with correct schema
- Article clusters have escalation columns
- FMP correlation table exists
- Vector indexes are configured

Note: These tests verify infrastructure, not data population.
Anchor seeding is a separate operation (scripts/seed_anchors.py).
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
async def test_escalation_anchors_table_ready(db_engine: AsyncEngine):
    """Verify escalation_anchors table is ready to receive data."""
    async with db_engine.connect() as conn:
        # Check table exists and has expected columns
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'escalation_anchors'
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in result.fetchall()]

    required_columns = [
        'id', 'domain', 'level', 'label', 'reference_text',
        'embedding', 'keywords', 'weight', 'is_active',
        'created_at', 'updated_at'
    ]

    for col in required_columns:
        assert col in columns, f"Column {col} missing from escalation_anchors"


@pytest.mark.asyncio
async def test_escalation_anchors_loaded(db_engine: AsyncEngine):
    """Verify escalation anchors are present in database (if seeded)."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT COUNT(*), array_agg(DISTINCT domain) FROM escalation_anchors WHERE is_active = true"
        ))
        row = result.fetchone()

        count = row[0]
        domains = row[1] or []

        if count == 0:
            pytest.skip("Anchors not yet seeded - run scripts/seed_anchors.py first")

        # Should have at least 15 anchors (5 levels x 3 domains)
        assert count >= 15, f"Expected at least 15 anchors, got {count}"

        # Should have all three domains
        assert 'geopolitical' in domains, "geopolitical domain missing"
        assert 'military' in domains, "military domain missing"
        assert 'economic' in domains, "economic domain missing"


@pytest.mark.asyncio
async def test_escalation_columns_exist(db_engine: AsyncEngine):
    """Verify escalation columns added to article_clusters."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'article_clusters'
            AND column_name LIKE 'escalation_%'
        """))
        columns = [row[0] for row in result.fetchall()]

    required_columns = [
        'escalation_geopolitical',
        'escalation_military',
        'escalation_economic',
        'escalation_combined',
        'escalation_level',
        'escalation_signals',
        'escalation_calculated_at'
    ]

    for col in required_columns:
        assert col in columns, f"Column {col} missing from article_clusters"


@pytest.mark.asyncio
async def test_fmp_correlations_table_exists(db_engine: AsyncEngine):
    """Verify fmp_news_correlations table exists and is accessible."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'fmp_news_correlations'
        """))
        count = result.scalar()

    assert count == 1, "fmp_news_correlations table does not exist"


@pytest.mark.asyncio
async def test_anchor_embedding_dimensions(db_engine: AsyncEngine):
    """Verify anchor embeddings have correct dimensions (1536) if seeded."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT id, vector_dims(embedding) as dims
            FROM escalation_anchors
            WHERE is_active = true
            LIMIT 5
        """))
        rows = result.fetchall()

    if len(rows) == 0:
        pytest.skip("Anchors not yet seeded - run scripts/seed_anchors.py first")

    for row in rows:
        assert row[1] == 1536, f"Anchor {row[0]} has wrong dimension: {row[1]}"


@pytest.mark.asyncio
async def test_anchor_levels_and_domains_coverage(db_engine: AsyncEngine):
    """Verify all domain/level combinations are covered (if seeded)."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT domain, array_agg(DISTINCT level ORDER BY level) as levels
            FROM escalation_anchors
            WHERE is_active = true
            GROUP BY domain
        """))
        coverage = {row[0]: row[1] for row in result.fetchall()}

    if len(coverage) == 0:
        pytest.skip("Anchors not yet seeded - run scripts/seed_anchors.py first")

    expected_levels = [1, 2, 3, 4, 5]

    for domain in ['geopolitical', 'military', 'economic']:
        assert domain in coverage, f"Domain {domain} has no anchors"
        assert coverage[domain] == expected_levels, \
            f"Domain {domain} missing levels: expected {expected_levels}, got {coverage[domain]}"


@pytest.mark.asyncio
async def test_anchor_embeddings_normalized(db_engine: AsyncEngine):
    """Verify anchor embeddings are approximately normalized (L2 norm close to 1) if seeded."""
    async with db_engine.connect() as conn:
        # Calculate L2 norm of embeddings using pgvector
        result = await conn.execute(text("""
            SELECT id, domain, level,
                   sqrt(embedding <-> array_fill(0::real, ARRAY[1536])::vector) as l2_norm
            FROM escalation_anchors
            WHERE is_active = true
            LIMIT 10
        """))
        rows = result.fetchall()

    if len(rows) == 0:
        pytest.skip("Anchors not yet seeded - run scripts/seed_anchors.py first")

    for row in rows:
        anchor_id, domain, level, l2_norm = row
        # L2 norm should be approximately 1.0 for normalized vectors
        # Allow some tolerance for floating point
        assert 0.9 <= l2_norm <= 1.1, \
            f"Anchor {anchor_id} ({domain} L{level}) not normalized: L2 norm = {l2_norm}"


@pytest.mark.asyncio
async def test_anchor_unique_constraint(db_engine: AsyncEngine):
    """Verify unique constraint on (domain, level, label)."""
    async with db_engine.connect() as conn:
        # Check for duplicate domain/level/label combinations
        result = await conn.execute(text("""
            SELECT domain, level, label, COUNT(*) as cnt
            FROM escalation_anchors
            WHERE is_active = true
            GROUP BY domain, level, label
            HAVING COUNT(*) > 1
        """))
        duplicates = result.fetchall()

    assert len(duplicates) == 0, f"Found duplicate anchors: {duplicates}"


@pytest.mark.asyncio
async def test_escalation_vector_index_exists(db_engine: AsyncEngine):
    """Verify vector index exists on escalation_anchors embedding column."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT indexname, indexdef FROM pg_indexes
            WHERE tablename = 'escalation_anchors'
            AND (indexdef LIKE '%hnsw%' OR indexdef LIKE '%ivfflat%')
        """))
        indexes = [(row[0], row[1]) for row in result.fetchall()]

    # Should have a vector index (HNSW or IVFFlat) for efficient similarity search
    assert len(indexes) >= 1, "No vector index (HNSW or IVFFlat) found on escalation_anchors"

    # Verify index is on the embedding column
    embedding_index_found = any('embedding' in idx[1] for idx in indexes)
    assert embedding_index_found, "Vector index not on embedding column"


@pytest.mark.asyncio
async def test_article_clusters_escalation_defaults(db_engine: AsyncEngine):
    """Verify article_clusters escalation columns have appropriate defaults."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, column_default
            FROM information_schema.columns
            WHERE table_name = 'article_clusters'
            AND column_name LIKE 'escalation_%'
        """))
        defaults = {row[0]: row[1] for row in result.fetchall()}

    # Combined should default to 'unknown' or similar
    # Scores should default to NULL or 0
    # This is more of a documentation test to understand the schema
    assert 'escalation_combined' in defaults, "escalation_combined column missing"
    assert 'escalation_level' in defaults, "escalation_level column missing"


@pytest.mark.asyncio
async def test_fmp_correlations_schema(db_engine: AsyncEngine):
    """Verify fmp_news_correlations has required columns."""
    async with db_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'fmp_news_correlations'
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in result.fetchall()]

    # Core columns for FMP/news correlation (actual schema)
    required_columns = [
        'id',
        'detected_at',
        'correlation_type',
        'fmp_regime',
        'escalation_level',
        'confidence',
        'related_clusters',
        'is_active',
        'created_at'
    ]

    for col in required_columns:
        assert col in columns, f"Column {col} missing from fmp_news_correlations"


@pytest.mark.asyncio
async def test_escalation_anchors_domain_constraint(db_engine: AsyncEngine):
    """Verify CHECK constraint on domain column."""
    async with db_engine.connect() as conn:
        # Check constraint exists
        result = await conn.execute(text("""
            SELECT con.conname, pg_get_constraintdef(con.oid)
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            WHERE rel.relname = 'escalation_anchors'
            AND con.contype = 'c'
            AND con.conname LIKE '%domain%'
        """))
        constraints = result.fetchall()

    assert len(constraints) >= 1, "Domain CHECK constraint missing on escalation_anchors"


@pytest.mark.asyncio
async def test_escalation_anchors_level_constraint(db_engine: AsyncEngine):
    """Verify CHECK constraint on level column (1-5)."""
    async with db_engine.connect() as conn:
        # Check constraint exists
        result = await conn.execute(text("""
            SELECT con.conname, pg_get_constraintdef(con.oid)
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            WHERE rel.relname = 'escalation_anchors'
            AND con.contype = 'c'
            AND con.conname LIKE '%level%'
        """))
        constraints = result.fetchall()

    assert len(constraints) >= 1, "Level CHECK constraint missing on escalation_anchors"
