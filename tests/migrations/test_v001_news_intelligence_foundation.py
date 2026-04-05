"""
Tests for V001 News Intelligence Foundation migration.

This test verifies:
1. All new columns exist in `feed_items`
2. All new tables exist (article_clusters, article_versions, publication_review_queue, sitrep_reports)
3. All new columns exist in `entity_aliases`
4. All check constraints work correctly
5. Migration history entry exists

Run with: pytest tests/migrations/test_v001_news_intelligence_foundation.py -v
"""
import pytest
import psycopg2
import os
from typing import Set, Optional


# Database connection configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://news_user:your_db_password@localhost:5432/news_mcp"
)


def parse_database_url(url: str) -> dict:
    """Parse DATABASE_URL into connection parameters."""
    # Handle postgresql:// format
    if url.startswith("postgresql://"):
        url = url[13:]  # Remove postgresql://

    # Split user:password@host:port/database
    user_pass, host_db = url.split("@")
    user, password = user_pass.split(":")

    if "/" in host_db:
        host_port, database = host_db.split("/")
    else:
        host_port = host_db
        database = "news_mcp"

    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host = host_port
        port = "5432"

    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "dbname": database,
    }


@pytest.fixture(scope="module")
def db_connection():
    """Create database connection for testing."""
    params = parse_database_url(DATABASE_URL)
    conn = psycopg2.connect(**params)
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def db_cursor(db_connection):
    """Create database cursor for testing."""
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


def get_table_columns(cursor, table_name: str) -> Set[str]:
    """Get all column names for a table."""
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        AND table_schema = 'public'
    """, (table_name,))
    return {row[0] for row in cursor.fetchall()}


def get_table_exists(cursor, table_name: str) -> bool:
    """Check if a table exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_name = %s
            AND table_schema = 'public'
        )
    """, (table_name,))
    return cursor.fetchone()[0]


def get_constraint_exists(cursor, constraint_name: str) -> bool:
    """Check if a constraint exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = %s
        )
    """, (constraint_name,))
    return cursor.fetchone()[0]


def get_column_default(cursor, table_name: str, column_name: str) -> Optional[str]:
    """Get the default value for a column."""
    cursor.execute("""
        SELECT column_default
        FROM information_schema.columns
        WHERE table_name = %s
        AND column_name = %s
        AND table_schema = 'public'
    """, (table_name, column_name))
    result = cursor.fetchone()
    return result[0] if result else None


class TestV001NewsIntelligenceFoundation:
    """Test V001 migration: News Intelligence Foundation schema extensions."""

    # =========================================================================
    # 1. FEED_ITEMS NEW COLUMNS
    # =========================================================================

    def test_feed_items_new_columns_exist(self, db_cursor):
        """Verify all new feed_items columns exist."""
        columns = get_table_columns(db_cursor, 'feed_items')

        expected = {
            'version',
            'pub_status',
            'simhash_fingerprint',
            'cluster_id',
            'relevance_score'
        }

        missing = expected - columns
        assert not missing, f"Missing feed_items columns: {missing}"

    def test_feed_items_newsml_columns_exist(self, db_cursor):
        """Verify NewsML-G2 specific columns exist in feed_items."""
        columns = get_table_columns(db_cursor, 'feed_items')

        expected = {
            'version',
            'version_created_at',
            'pub_status',
            'is_correction',
            'corrects_article_id'
        }

        missing = expected - columns
        assert not missing, f"Missing NewsML-G2 columns: {missing}"

    def test_feed_items_clustering_columns_exist(self, db_cursor):
        """Verify clustering columns exist in feed_items."""
        columns = get_table_columns(db_cursor, 'feed_items')

        expected = {
            'cluster_id',
            'cluster_similarity',
            'cluster_assigned_at'
        }

        missing = expected - columns
        assert not missing, f"Missing clustering columns: {missing}"

    def test_feed_items_time_decay_columns_exist(self, db_cursor):
        """Verify time-decay columns exist in feed_items."""
        columns = get_table_columns(db_cursor, 'feed_items')

        expected = {
            'relevance_score',
            'relevance_calculated_at'
        }

        missing = expected - columns
        assert not missing, f"Missing time-decay columns: {missing}"

    def test_feed_items_version_default(self, db_cursor):
        """Verify version column has default value of 1."""
        default = get_column_default(db_cursor, 'feed_items', 'version')
        assert default is not None, "version column has no default"
        assert '1' in default, f"Expected default to contain '1', got: {default}"

    def test_feed_items_pub_status_default(self, db_cursor):
        """Verify pub_status column has default value of 'usable'."""
        default = get_column_default(db_cursor, 'feed_items', 'pub_status')
        assert default is not None, "pub_status column has no default"
        assert 'usable' in default, f"Expected default to contain 'usable', got: {default}"

    # =========================================================================
    # 2. NEW TABLES EXIST
    # =========================================================================

    def test_article_clusters_table_exists(self, db_cursor):
        """Verify article_clusters table exists."""
        assert get_table_exists(db_cursor, 'article_clusters'), \
            "article_clusters table does not exist"

    def test_article_clusters_columns(self, db_cursor):
        """Verify article_clusters has all required columns."""
        columns = get_table_columns(db_cursor, 'article_clusters')

        expected = {
            'id', 'title', 'summary', 'status', 'article_count',
            'first_seen_at', 'last_updated_at', 'centroid_vector',
            'tension_score', 'is_breaking', 'burst_detected_at',
            'primary_entities', 'created_at'
        }

        missing = expected - columns
        assert not missing, f"Missing article_clusters columns: {missing}"

    def test_article_versions_table_exists(self, db_cursor):
        """Verify article_versions table exists."""
        assert get_table_exists(db_cursor, 'article_versions'), \
            "article_versions table does not exist"

    def test_article_versions_columns(self, db_cursor):
        """Verify article_versions has all required columns."""
        columns = get_table_columns(db_cursor, 'article_versions')

        expected = {
            'id', 'article_id', 'version', 'pub_status', 'title',
            'content_hash', 'change_type', 'change_reason', 'created_at'
        }

        missing = expected - columns
        assert not missing, f"Missing article_versions columns: {missing}"

    def test_publication_review_queue_table_exists(self, db_cursor):
        """Verify publication_review_queue table exists."""
        assert get_table_exists(db_cursor, 'publication_review_queue'), \
            "publication_review_queue table does not exist"

    def test_publication_review_queue_columns(self, db_cursor):
        """Verify publication_review_queue has all required columns."""
        columns = get_table_columns(db_cursor, 'publication_review_queue')

        expected = {
            'id', 'article_id', 'target', 'content', 'risk_score',
            'risk_factors', 'status', 'reviewed_by', 'reviewed_at',
            'reviewer_notes', 'edited_content', 'created_at', 'expires_at'
        }

        missing = expected - columns
        assert not missing, f"Missing publication_review_queue columns: {missing}"

    def test_sitrep_reports_table_exists(self, db_cursor):
        """Verify sitrep_reports table exists."""
        assert get_table_exists(db_cursor, 'sitrep_reports'), \
            "sitrep_reports table does not exist"

    def test_sitrep_reports_columns(self, db_cursor):
        """Verify sitrep_reports has all required columns."""
        columns = get_table_columns(db_cursor, 'sitrep_reports')

        expected = {
            'id', 'report_date', 'report_type', 'title', 'content_markdown',
            'content_html', 'top_stories', 'key_entities', 'sentiment_summary',
            'emerging_signals', 'generation_model', 'generation_time_ms',
            'articles_analyzed', 'confidence_score', 'human_reviewed', 'created_at'
        }

        missing = expected - columns
        assert not missing, f"Missing sitrep_reports columns: {missing}"

    # =========================================================================
    # 3. ENTITY_ALIASES NEW COLUMNS
    # =========================================================================

    def test_entity_aliases_new_columns_exist(self, db_cursor):
        """Verify all new entity_aliases columns exist."""
        columns = get_table_columns(db_cursor, 'entity_aliases')

        expected = {
            'alias_normalized',
            'alias_type',
            'language',
            'confidence',
            'source',
            'is_active',
            'usage_count'
        }

        missing = expected - columns
        assert not missing, f"Missing entity_aliases columns: {missing}"

    def test_entity_aliases_alias_type_default(self, db_cursor):
        """Verify alias_type has default value of 'name'."""
        default = get_column_default(db_cursor, 'entity_aliases', 'alias_type')
        assert default is not None, "alias_type column has no default"
        assert 'name' in default, f"Expected default to contain 'name', got: {default}"

    def test_entity_aliases_confidence_default(self, db_cursor):
        """Verify confidence has default value of 1.0."""
        default = get_column_default(db_cursor, 'entity_aliases', 'confidence')
        assert default is not None, "confidence column has no default"
        assert '1' in str(default), f"Expected default to contain '1', got: {default}"

    def test_entity_aliases_is_active_default(self, db_cursor):
        """Verify is_active has default value of true."""
        default = get_column_default(db_cursor, 'entity_aliases', 'is_active')
        assert default is not None, "is_active column has no default"
        assert 'true' in default.lower(), f"Expected default to contain 'true', got: {default}"

    # =========================================================================
    # 4. CHECK CONSTRAINTS WORK CORRECTLY
    # =========================================================================

    def test_chk_pub_status_constraint_exists(self, db_cursor):
        """Verify chk_pub_status constraint exists."""
        assert get_constraint_exists(db_cursor, 'chk_pub_status'), \
            "chk_pub_status constraint does not exist"

    def test_chk_pub_status_allows_valid_values(self, db_cursor):
        """Verify chk_pub_status allows valid values."""
        # This test checks the constraint definition
        db_cursor.execute("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'chk_pub_status'
        """)
        result = db_cursor.fetchone()
        assert result is not None, "chk_pub_status constraint not found"
        constraint_def = result[0]

        # Verify all valid values are in the constraint
        assert 'usable' in constraint_def, "usable not in chk_pub_status"
        assert 'withheld' in constraint_def, "withheld not in chk_pub_status"
        assert 'canceled' in constraint_def, "canceled not in chk_pub_status"

    def test_chk_cluster_status_constraint_exists(self, db_cursor):
        """Verify chk_cluster_status constraint exists."""
        assert get_constraint_exists(db_cursor, 'chk_cluster_status'), \
            "chk_cluster_status constraint does not exist"

    def test_chk_cluster_status_allows_valid_values(self, db_cursor):
        """Verify chk_cluster_status allows valid values."""
        db_cursor.execute("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'chk_cluster_status'
        """)
        result = db_cursor.fetchone()
        assert result is not None, "chk_cluster_status constraint not found"
        constraint_def = result[0]

        assert 'active' in constraint_def, "active not in chk_cluster_status"
        assert 'archived' in constraint_def, "archived not in chk_cluster_status"
        assert 'merged' in constraint_def, "merged not in chk_cluster_status"

    def test_chk_version_change_type_constraint_exists(self, db_cursor):
        """Verify chk_version_change_type constraint exists."""
        assert get_constraint_exists(db_cursor, 'chk_version_change_type'), \
            "chk_version_change_type constraint does not exist"

    def test_chk_version_change_type_allows_valid_values(self, db_cursor):
        """Verify chk_version_change_type allows valid values."""
        db_cursor.execute("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'chk_version_change_type'
        """)
        result = db_cursor.fetchone()
        assert result is not None, "chk_version_change_type constraint not found"
        constraint_def = result[0]

        assert 'update' in constraint_def, "update not in chk_version_change_type"
        assert 'correction' in constraint_def, "correction not in chk_version_change_type"
        assert 'withdrawal' in constraint_def, "withdrawal not in chk_version_change_type"

    def test_chk_review_status_constraint_exists(self, db_cursor):
        """Verify chk_review_status constraint exists."""
        assert get_constraint_exists(db_cursor, 'chk_review_status'), \
            "chk_review_status constraint does not exist"

    def test_chk_review_status_allows_valid_values(self, db_cursor):
        """Verify chk_review_status allows valid values."""
        db_cursor.execute("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'chk_review_status'
        """)
        result = db_cursor.fetchone()
        assert result is not None, "chk_review_status constraint not found"
        constraint_def = result[0]

        expected_values = ['pending', 'approved', 'rejected', 'edited', 'auto_approved', 'blocked']
        for value in expected_values:
            assert value in constraint_def, f"{value} not in chk_review_status"

    def test_chk_alias_type_constraint_exists(self, db_cursor):
        """Verify chk_alias_type constraint exists."""
        assert get_constraint_exists(db_cursor, 'chk_alias_type'), \
            "chk_alias_type constraint does not exist"

    def test_chk_alias_type_allows_valid_values(self, db_cursor):
        """Verify chk_alias_type allows valid values."""
        db_cursor.execute("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'chk_alias_type'
        """)
        result = db_cursor.fetchone()
        assert result is not None, "chk_alias_type constraint not found"
        constraint_def = result[0]

        expected_values = ['name', 'ticker', 'abbreviation', 'nickname']
        for value in expected_values:
            assert value in constraint_def, f"{value} not in chk_alias_type"

    def test_chk_alias_source_constraint_exists(self, db_cursor):
        """Verify chk_alias_source constraint exists."""
        assert get_constraint_exists(db_cursor, 'chk_alias_source'), \
            "chk_alias_source constraint does not exist"

    def test_chk_alias_source_allows_valid_values(self, db_cursor):
        """Verify chk_alias_source allows valid values."""
        db_cursor.execute("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'chk_alias_source'
        """)
        result = db_cursor.fetchone()
        assert result is not None, "chk_alias_source constraint not found"
        constraint_def = result[0]

        expected_values = ['manual', 'discovered', 'wikidata']
        for value in expected_values:
            assert value in constraint_def, f"{value} not in chk_alias_source"

    def test_chk_alias_confidence_constraint_exists(self, db_cursor):
        """Verify chk_alias_confidence constraint exists."""
        assert get_constraint_exists(db_cursor, 'chk_alias_confidence'), \
            "chk_alias_confidence constraint does not exist"

    def test_chk_alias_confidence_range(self, db_cursor):
        """Verify chk_alias_confidence enforces 0-1 range."""
        db_cursor.execute("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conname = 'chk_alias_confidence'
        """)
        result = db_cursor.fetchone()
        assert result is not None, "chk_alias_confidence constraint not found"
        constraint_def = result[0]

        # Verify range check
        assert '>=' in constraint_def and '0' in constraint_def, \
            "chk_alias_confidence should check >= 0"
        assert '<=' in constraint_def and '1' in constraint_def, \
            "chk_alias_confidence should check <= 1"

    # =========================================================================
    # 5. MIGRATION HISTORY ENTRY EXISTS
    # =========================================================================

    def test_migration_history_table_exists(self, db_cursor):
        """Verify _migration_history table exists."""
        assert get_table_exists(db_cursor, '_migration_history'), \
            "_migration_history table does not exist"

    def test_migration_history_entry_exists(self, db_cursor):
        """Verify V001 migration entry exists in history."""
        db_cursor.execute("""
            SELECT migration_name, applied_at, checksum
            FROM _migration_history
            WHERE migration_name = 'V001__news_intelligence_foundation'
        """)
        result = db_cursor.fetchone()

        assert result is not None, \
            "V001__news_intelligence_foundation not found in _migration_history"

        migration_name, applied_at, checksum = result
        assert migration_name == 'V001__news_intelligence_foundation'
        assert applied_at is not None, "applied_at should not be null"
        assert checksum is not None, "checksum should not be null"

    def test_migration_history_has_correct_columns(self, db_cursor):
        """Verify _migration_history has required columns."""
        columns = get_table_columns(db_cursor, '_migration_history')

        expected = {'id', 'migration_name', 'applied_at', 'checksum'}
        missing = expected - columns
        assert not missing, f"Missing _migration_history columns: {missing}"


class TestForeignKeyConstraints:
    """Test foreign key constraints created by V001 migration."""

    def test_fk_feed_items_corrects_exists(self, db_cursor):
        """Verify fk_feed_items_corrects foreign key exists."""
        assert get_constraint_exists(db_cursor, 'fk_feed_items_corrects'), \
            "fk_feed_items_corrects constraint does not exist"

    def test_fk_feed_items_cluster_exists(self, db_cursor):
        """Verify fk_feed_items_cluster foreign key exists."""
        assert get_constraint_exists(db_cursor, 'fk_feed_items_cluster'), \
            "fk_feed_items_cluster constraint does not exist"

    def test_fk_version_article_exists(self, db_cursor):
        """Verify fk_version_article foreign key exists."""
        assert get_constraint_exists(db_cursor, 'fk_version_article'), \
            "fk_version_article constraint does not exist"

    def test_fk_review_article_exists(self, db_cursor):
        """Verify fk_review_article foreign key exists."""
        assert get_constraint_exists(db_cursor, 'fk_review_article'), \
            "fk_review_article constraint does not exist"


class TestIndexes:
    """Test indexes created by V001 migration."""

    def _index_exists(self, cursor, index_name: str) -> bool:
        """Check if an index exists."""
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE indexname = %s
            )
        """, (index_name,))
        return cursor.fetchone()[0]

    def test_idx_feed_items_simhash_exists(self, db_cursor):
        """Verify idx_feed_items_simhash index exists."""
        assert self._index_exists(db_cursor, 'idx_feed_items_simhash'), \
            "idx_feed_items_simhash index does not exist"

    def test_idx_feed_items_pub_status_exists(self, db_cursor):
        """Verify idx_feed_items_pub_status index exists."""
        assert self._index_exists(db_cursor, 'idx_feed_items_pub_status'), \
            "idx_feed_items_pub_status index does not exist"

    def test_idx_feed_items_relevance_exists(self, db_cursor):
        """Verify idx_feed_items_relevance index exists."""
        assert self._index_exists(db_cursor, 'idx_feed_items_relevance'), \
            "idx_feed_items_relevance index does not exist"

    def test_idx_feed_items_cluster_exists(self, db_cursor):
        """Verify idx_feed_items_cluster index exists."""
        assert self._index_exists(db_cursor, 'idx_feed_items_cluster'), \
            "idx_feed_items_cluster index does not exist"

    def test_idx_clusters_active_updated_exists(self, db_cursor):
        """Verify idx_clusters_active_updated index exists."""
        assert self._index_exists(db_cursor, 'idx_clusters_active_updated'), \
            "idx_clusters_active_updated index does not exist"

    def test_idx_entity_aliases_normalized_exists(self, db_cursor):
        """Verify idx_entity_aliases_normalized index exists."""
        assert self._index_exists(db_cursor, 'idx_entity_aliases_normalized'), \
            "idx_entity_aliases_normalized index does not exist"
