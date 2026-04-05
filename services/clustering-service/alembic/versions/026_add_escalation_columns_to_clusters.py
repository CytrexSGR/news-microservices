"""Add escalation columns to article_clusters for Intelligence Interpretation Layer.

This migration adds escalation scoring columns to the article_clusters table:
- Domain-specific scores: geopolitical, military, economic (0.0000-1.0000)
- Combined score: weighted average across domains
- Escalation level: discrete 1-5 scale derived from combined score
- Escalation signals: JSONB with evidence and confidence details
- Calculation timestamp for cache invalidation

These columns enable real-time escalation monitoring and trend analysis
for the Intelligence Interpretation Layer (Phase 2).

Revision ID: 026
Revises: 025
Create Date: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add escalation columns to article_clusters table."""
    # Add domain-specific escalation scores (NUMERIC(5,4) for 0.0000-1.0000 precision)
    op.add_column('article_clusters', sa.Column(
        'escalation_geopolitical',
        sa.Numeric(5, 4),
        nullable=True,
        comment='Geopolitical escalation score (0.0000-1.0000)'
    ))

    op.add_column('article_clusters', sa.Column(
        'escalation_military',
        sa.Numeric(5, 4),
        nullable=True,
        comment='Military escalation score (0.0000-1.0000)'
    ))

    op.add_column('article_clusters', sa.Column(
        'escalation_economic',
        sa.Numeric(5, 4),
        nullable=True,
        comment='Economic escalation score (0.0000-1.0000)'
    ))

    # Add combined escalation score (weighted average)
    op.add_column('article_clusters', sa.Column(
        'escalation_combined',
        sa.Numeric(5, 4),
        nullable=True,
        comment='Combined escalation score (weighted average, 0.0000-1.0000)'
    ))

    # Add discrete escalation level (1-5 scale) with CHECK constraint
    op.add_column('article_clusters', sa.Column(
        'escalation_level',
        sa.Integer(),
        nullable=True,
        comment='Discrete escalation level (1=low, 5=critical)'
    ))

    # Add CHECK constraint for escalation_level (1-5 range)
    op.execute("""
        ALTER TABLE article_clusters
        ADD CONSTRAINT chk_escalation_level
        CHECK (escalation_level IS NULL OR (escalation_level >= 1 AND escalation_level <= 5))
    """)

    # Add JSONB column for escalation signals/evidence
    op.add_column('article_clusters', sa.Column(
        'escalation_signals',
        sa.dialects.postgresql.JSONB(),
        nullable=True,
        comment='Escalation evidence: {domain: {anchor_matches: [...], keywords: [...], confidence: float}}'
    ))

    # Add calculation timestamp for cache invalidation
    op.add_column('article_clusters', sa.Column(
        'escalation_calculated_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Timestamp of last escalation calculation'
    ))

    # Create indexes for efficient querying
    # Index on escalation_combined for trend analysis queries
    op.execute("""
        CREATE INDEX idx_article_clusters_escalation_combined
        ON article_clusters (escalation_combined DESC NULLS LAST)
        WHERE escalation_combined IS NOT NULL
    """)

    # Index on escalation_level for filtering by severity
    op.execute("""
        CREATE INDEX idx_article_clusters_escalation_level
        ON article_clusters (escalation_level)
        WHERE escalation_level IS NOT NULL
    """)

    # Add table comment update
    op.execute("""
        COMMENT ON COLUMN article_clusters.escalation_signals IS
        'JSON structure: {"geopolitical": {"anchor_similarity": 0.85, "top_anchors": [...], "keywords_matched": [...]}, ...}'
    """)


def downgrade() -> None:
    """Remove escalation columns from article_clusters table."""
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS idx_article_clusters_escalation_level")
    op.execute("DROP INDEX IF EXISTS idx_article_clusters_escalation_combined")

    # Drop CHECK constraint
    op.execute("ALTER TABLE article_clusters DROP CONSTRAINT IF EXISTS chk_escalation_level")

    # Drop columns
    op.drop_column('article_clusters', 'escalation_calculated_at')
    op.drop_column('article_clusters', 'escalation_signals')
    op.drop_column('article_clusters', 'escalation_level')
    op.drop_column('article_clusters', 'escalation_combined')
    op.drop_column('article_clusters', 'escalation_economic')
    op.drop_column('article_clusters', 'escalation_military')
    op.drop_column('article_clusters', 'escalation_geopolitical')
