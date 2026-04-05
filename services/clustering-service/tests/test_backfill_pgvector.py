"""Tests for the backfill_pgvector_centroids script.

Tests the core functions without requiring a database connection.
"""

import json
import pytest
import numpy as np
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from backfill_pgvector_centroids import (
    calculate_csai,
    get_csai_status,
    parse_centroid,
    parse_database_url,
    CSAI_STABLE_THRESHOLD,
)


class TestCalculateCSAI:
    """Tests for CSAI calculation function."""

    def test_csai_coherent_embedding(self):
        """CSAI should be high for coherent embeddings."""
        # A normalized random vector should have high self-correlation
        np.random.seed(42)
        coherent = np.random.randn(1536)
        coherent = coherent / np.linalg.norm(coherent)

        score = calculate_csai(coherent.tolist())

        # Coherent embeddings should have high CSAI (close to 1.0)
        assert score >= 0.90, f"Expected CSAI >= 0.90 for coherent embedding, got {score:.3f}"

    def test_csai_small_embedding(self):
        """CSAI returns 1.0 for embeddings smaller than 512D."""
        small = [0.1] * 256
        score = calculate_csai(small)
        assert score == 1.0

    def test_csai_zero_vector(self):
        """CSAI returns 0.0 for zero vectors."""
        zero = [0.0] * 1536
        score = calculate_csai(zero)
        assert score == 0.0

    def test_csai_range(self):
        """CSAI should always be between 0 and 1."""
        # Test with various random vectors
        np.random.seed(42)
        for _ in range(10):
            vec = np.random.randn(1536).tolist()
            score = calculate_csai(vec)
            assert 0.0 <= score <= 1.0, f"CSAI out of range: {score}"


class TestGetCSAIStatus:
    """Tests for CSAI status determination."""

    def test_stable_above_threshold(self):
        """Score >= threshold should return 'stable'."""
        assert get_csai_status(0.35) == "stable"
        assert get_csai_status(0.50) == "stable"
        assert get_csai_status(1.0) == "stable"

    def test_unstable_below_threshold(self):
        """Score < threshold should return 'unstable'."""
        assert get_csai_status(0.34) == "unstable"
        assert get_csai_status(0.10) == "unstable"
        assert get_csai_status(0.0) == "unstable"

    def test_threshold_value(self):
        """Threshold should be 0.35."""
        assert CSAI_STABLE_THRESHOLD == 0.35


class TestParseCentroid:
    """Tests for centroid parsing from various formats."""

    def test_parse_list(self):
        """Parse list of floats directly."""
        centroid = [0.1, 0.2, 0.3]
        result = parse_centroid(centroid)
        assert result == [0.1, 0.2, 0.3]

    def test_parse_list_integers(self):
        """Parse list with integers (should convert to float)."""
        centroid = [1, 2, 3]
        result = parse_centroid(centroid)
        assert result == [1.0, 2.0, 3.0]

    def test_parse_json_string(self):
        """Parse JSON string representation."""
        centroid = '[0.1, 0.2, 0.3]'
        result = parse_centroid(centroid)
        assert result == [0.1, 0.2, 0.3]

    def test_parse_dict_returns_none(self):
        """Parse dict should return None (unexpected format)."""
        centroid = {"values": [0.1, 0.2]}
        result = parse_centroid(centroid)
        assert result is None

    def test_parse_invalid_json(self):
        """Parse invalid JSON should return None."""
        centroid = "not valid json"
        result = parse_centroid(centroid)
        assert result is None

    def test_parse_none(self):
        """Parse None should return None."""
        result = parse_centroid(None)
        assert result is None


class TestParseDatabaseUrl:
    """Tests for DATABASE_URL parsing."""

    def test_full_url(self):
        """Parse complete PostgreSQL URL."""
        url = "postgresql://user:password@host:5432/dbname"
        result = parse_database_url(url)
        assert result["user"] == "user"
        assert result["password"] == "password"
        assert result["host"] == "host"
        assert result["port"] == 5432
        assert result["database"] == "dbname"

    def test_postgres_scheme(self):
        """Parse URL with postgres:// scheme."""
        url = "postgres://user:pass@localhost:5432/mydb"
        result = parse_database_url(url)
        assert result["user"] == "user"
        assert result["password"] == "pass"
        assert result["host"] == "localhost"
        assert result["database"] == "mydb"

    def test_default_port(self):
        """Default port should be 5432."""
        url = "postgresql://user:pass@host/dbname"
        result = parse_database_url(url)
        assert result["port"] == 5432

    def test_with_query_params(self):
        """URL with query params should ignore them for database name."""
        url = "postgresql://user:pass@host:5432/dbname?sslmode=require"
        result = parse_database_url(url)
        assert result["database"] == "dbname"

    def test_docker_compose_url(self):
        """Parse typical docker-compose URL."""
        url = "postgresql://postgres:postgres@postgres:5432/news_mcp"
        result = parse_database_url(url)
        assert result["user"] == "postgres"
        assert result["password"] == "postgres"
        assert result["host"] == "postgres"
        assert result["port"] == 5432
        assert result["database"] == "news_mcp"

    def test_asyncpg_url_format(self):
        """Parse postgresql+asyncpg:// format used by SQLAlchemy async."""
        url = "postgresql+asyncpg://news_user:news_secret@postgres:5432/news_db"
        result = parse_database_url(url)
        assert result["user"] == "news_user"
        assert result["password"] == "news_secret"
        assert result["host"] == "postgres"
        assert result["port"] == 5432
        assert result["database"] == "news_db"


class TestBackfillIntegration:
    """Integration-style tests (without actual database)."""

    def test_full_csai_pipeline(self):
        """Test complete CSAI calculation and status for a real-sized vector."""
        # Simulate a centroid from the database
        np.random.seed(123)
        centroid_list = np.random.randn(1536).tolist()

        # Parse it (simulating database retrieval)
        parsed = parse_centroid(centroid_list)
        assert parsed is not None
        assert len(parsed) == 1536

        # Calculate CSAI
        csai_score = calculate_csai(parsed)
        assert 0.0 <= csai_score <= 1.0

        # Get status
        status = get_csai_status(csai_score)
        assert status in ["stable", "unstable"]

    def test_json_round_trip(self):
        """Test parsing a JSON-serialized centroid (simulating JSONB)."""
        np.random.seed(456)
        original = np.random.randn(1536).tolist()

        # Simulate JSONB storage/retrieval
        json_str = json.dumps(original)
        parsed = parse_centroid(json_str)

        assert parsed is not None
        assert len(parsed) == 1536

        # Values should be close (floating point comparison)
        for orig, p in zip(original, parsed):
            assert abs(orig - p) < 1e-10
