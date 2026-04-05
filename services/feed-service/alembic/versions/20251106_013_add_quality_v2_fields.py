"""Add quality v2 fields to feeds table

Revision ID: 20251106_013
Revises: 20251029_012
Create Date: 2025-11-06

Adds comprehensive quality scoring fields for Feed Quality V2:
- quality_score_v2: Overall quality score (0-100) from comprehensive analysis
- quality_confidence: Confidence level (high, medium, low)
- quality_trend: Quality trend (improving, stable, declining)
- quality_calculated_at: Timestamp of last calculation
- article_quality_stats: JSONB with component breakdowns

These fields support the new Feed Quality Scoring Model V2 which combines:
- Article quality from content-analysis-v2
- Source credibility from research service
- Operational reliability from feed health
- Freshness & consistency from publishing patterns

See: docs/design/feed-quality-scoring-model.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251106_013'
down_revision = '20251029_012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Quality V2 fields to feeds table."""

    # Add quality_score_v2 - comprehensive quality score (0-100)
    op.add_column('feeds', sa.Column(
        'quality_score_v2',
        sa.Integer(),
        nullable=True,
        comment='Comprehensive quality score (0-100) from Quality V2 model'
    ))

    # Add quality_confidence - confidence level based on data completeness
    op.add_column('feeds', sa.Column(
        'quality_confidence',
        sa.String(length=20),
        nullable=True,
        comment='Confidence level: high, medium, low'
    ))

    # Add quality_trend - trend detection
    op.add_column('feeds', sa.Column(
        'quality_trend',
        sa.String(length=20),
        nullable=True,
        comment='Quality trend: improving, stable, declining, unknown'
    ))

    # Add quality_calculated_at - timestamp of last calculation
    op.add_column('feeds', sa.Column(
        'quality_calculated_at',
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment='Timestamp of last quality calculation'
    ))

    # Add article_quality_stats - component breakdowns and detailed metrics
    op.add_column('feeds', sa.Column(
        'article_quality_stats',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
        comment='Detailed quality component breakdowns (article, source, operational, freshness)'
    ))

    # Create index on quality_score_v2 for efficient sorting/filtering
    op.create_index(
        'idx_feeds_quality_score_v2',
        'feeds',
        ['quality_score_v2'],
        unique=False
    )

    # Create index on quality_calculated_at for efficient queries
    op.create_index(
        'idx_feeds_quality_calculated_at',
        'feeds',
        ['quality_calculated_at'],
        unique=False
    )

    # Create composite index for quality dashboard queries
    op.create_index(
        'idx_feeds_quality_dashboard',
        'feeds',
        ['quality_score_v2', 'quality_confidence', 'quality_trend'],
        unique=False
    )

    # Add check constraint for quality_score_v2 (0-100)
    op.create_check_constraint(
        'chk_quality_score_v2_range',
        'feeds',
        'quality_score_v2 >= 0 AND quality_score_v2 <= 100'
    )

    # Add check constraint for quality_confidence values
    op.create_check_constraint(
        'chk_quality_confidence_values',
        'feeds',
        "quality_confidence IN ('high', 'medium', 'low')"
    )

    # Add check constraint for quality_trend values
    op.create_check_constraint(
        'chk_quality_trend_values',
        'feeds',
        "quality_trend IN ('improving', 'stable', 'declining', 'unknown')"
    )


def downgrade() -> None:
    """Remove Quality V2 fields from feeds table."""

    # Drop check constraints
    op.drop_constraint('chk_quality_trend_values', 'feeds', type_='check')
    op.drop_constraint('chk_quality_confidence_values', 'feeds', type_='check')
    op.drop_constraint('chk_quality_score_v2_range', 'feeds', type_='check')

    # Drop indexes
    op.drop_index('idx_feeds_quality_dashboard', table_name='feeds')
    op.drop_index('idx_feeds_quality_calculated_at', table_name='feeds')
    op.drop_index('idx_feeds_quality_score_v2', table_name='feeds')

    # Drop columns
    op.drop_column('feeds', 'article_quality_stats')
    op.drop_column('feeds', 'quality_calculated_at')
    op.drop_column('feeds', 'quality_trend')
    op.drop_column('feeds', 'quality_confidence')
    op.drop_column('feeds', 'quality_score_v2')
