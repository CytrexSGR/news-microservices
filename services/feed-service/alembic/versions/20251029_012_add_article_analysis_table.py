"""Add article_analysis table for storing analysis results from content-analysis-v2

Revision ID: 20251029_012
Revises: 20251029_009
Create Date: 2025-10-29 19:00:00.000000

This table stores analysis results received via analysis.completed events
from the content-analysis-v2 service. It serves as the single source of truth
for article analysis data, consumed by the frontend API.

Event Schema: /tmp/analysis_completed_event_schema.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251029_012'
down_revision = '20251029_009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create article_analysis table"""

    op.create_table(
        'article_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, comment='Foreign key to feed_items.id'),
        sa.Column('pipeline_version', sa.String(10), nullable=False, comment='Analysis pipeline version (e.g., "2.0")'),
        sa.Column('success', sa.Boolean(), nullable=False, comment='Whether analysis completed successfully'),

        # Analysis Results (JSONB for flexibility)
        sa.Column('triage_results', postgresql.JSONB, nullable=True, comment='Triage stage results (priority, category, topics)'),
        sa.Column('tier1_results', postgresql.JSONB, nullable=True, comment='Tier 1 foundation results (entities, topics, sentiment, summary)'),
        sa.Column('tier2_results', postgresql.JSONB, nullable=True, comment='Tier 2 specialist results (specialist agents output)'),
        sa.Column('tier3_results', postgresql.JSONB, nullable=True, comment='Tier 3 synthesis results (intelligence synthesis)'),

        # Relevance Scoring
        sa.Column('relevance_score', sa.Integer(), nullable=True, comment='Overall relevance score (0-100)'),
        sa.Column('score_breakdown', postgresql.JSONB, nullable=True, comment='Detailed score breakdown (impact, entity, source scores)'),

        # Execution Metrics
        sa.Column('metrics', postgresql.JSONB, nullable=True, comment='Execution metrics (cost, time, agents_run, agents_skipped)'),

        # Error Handling
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if analysis failed'),
        sa.Column('failed_agents', postgresql.ARRAY(sa.String()), nullable=True, comment='List of failed agent names'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='When analysis was first stored'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='When analysis was last updated'),
    )

    # Foreign key to feed_items
    op.create_foreign_key(
        'fk_article_analysis_article_id',
        'article_analysis',
        'feed_items',
        ['article_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Index for fast lookup by article_id (primary use case)
    op.create_index(
        'ix_article_analysis_article_id',
        'article_analysis',
        ['article_id']
    )

    # Index for filtering by success status
    op.create_index(
        'ix_article_analysis_success',
        'article_analysis',
        ['success']
    )

    # Index for filtering by pipeline version
    op.create_index(
        'ix_article_analysis_pipeline_version',
        'article_analysis',
        ['pipeline_version']
    )

    # Index for sorting by creation time
    op.create_index(
        'ix_article_analysis_created_at',
        'article_analysis',
        ['created_at']
    )

    # Partial index for failed analyses (for monitoring)
    op.create_index(
        'ix_article_analysis_failed',
        'article_analysis',
        ['success', 'created_at'],
        postgresql_where=sa.text("success = false")
    )


def downgrade() -> None:
    """Drop article_analysis table"""

    # Drop indexes
    op.drop_index('ix_article_analysis_failed', table_name='article_analysis')
    op.drop_index('ix_article_analysis_created_at', table_name='article_analysis')
    op.drop_index('ix_article_analysis_pipeline_version', table_name='article_analysis')
    op.drop_index('ix_article_analysis_success', table_name='article_analysis')
    op.drop_index('ix_article_analysis_article_id', table_name='article_analysis')

    # Drop foreign key
    op.drop_constraint('fk_article_analysis_article_id', 'article_analysis', type_='foreignkey')

    # Drop table
    op.drop_table('article_analysis')
