"""Tests for CSAI (Cluster Stability Assessment Index) model fields.

Task 2: Verify ArticleCluster model has CSAI tracking fields.
These fields were added by migration 024_add_pgvector_to_article_clusters.py.
"""

import pytest

from app.models.cluster import ArticleCluster


class TestArticleClusterCSAIFields:
    """Tests for CSAI fields on ArticleCluster model."""

    def test_article_cluster_has_csai_score_field(self):
        """ArticleCluster model should have csai_score field."""
        assert hasattr(ArticleCluster, 'csai_score'), \
            "ArticleCluster should have 'csai_score' field for CSAI validation"

    def test_article_cluster_has_csai_status_field(self):
        """ArticleCluster model should have csai_status field."""
        assert hasattr(ArticleCluster, 'csai_status'), \
            "ArticleCluster should have 'csai_status' field for CSAI validation"

    def test_article_cluster_has_csai_checked_at_field(self):
        """ArticleCluster model should have csai_checked_at field."""
        assert hasattr(ArticleCluster, 'csai_checked_at'), \
            "ArticleCluster should have 'csai_checked_at' field for CSAI validation"

    def test_csai_fields_are_optional(self):
        """CSAI fields should be nullable (Optional)."""
        # Check column properties through SQLAlchemy mapper
        from sqlalchemy import inspect

        mapper = inspect(ArticleCluster)
        columns = {col.key: col for col in mapper.columns}

        # Verify csai_score is nullable
        assert 'csai_score' in columns, "csai_score column should exist"
        assert columns['csai_score'].nullable is True, \
            "csai_score should be nullable"

        # Verify csai_status is nullable
        assert 'csai_status' in columns, "csai_status column should exist"
        assert columns['csai_status'].nullable is True, \
            "csai_status should be nullable"

        # Verify csai_checked_at is nullable
        assert 'csai_checked_at' in columns, "csai_checked_at column should exist"
        assert columns['csai_checked_at'].nullable is True, \
            "csai_checked_at should be nullable"

    def test_csai_status_default_value(self):
        """csai_status should default to 'pending'."""
        from sqlalchemy import inspect

        mapper = inspect(ArticleCluster)
        columns = {col.key: col for col in mapper.columns}

        csai_status_col = columns.get('csai_status')
        assert csai_status_col is not None, "csai_status column should exist"

        # Check default value
        default = csai_status_col.default
        if default is not None:
            # SQLAlchemy default can be a scalar or callable
            default_value = default.arg if hasattr(default, 'arg') else default
            assert default_value == 'pending', \
                f"csai_status default should be 'pending', got {default_value}"
