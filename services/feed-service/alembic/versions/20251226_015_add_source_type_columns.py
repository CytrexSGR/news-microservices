"""Add source_type, source_metadata, parent_article_id to feed_items

Enables multiple source types beyond RSS feeds:
- rss (default, existing behavior)
- perplexity_research (AI-generated background research)
- scraping (web scraping results)
- manual (manually added content)
- api_* (various API sources)

Revision ID: 20251226_015
Revises: 20251111_014
Create Date: 2025-12-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '20251226_015'
down_revision = '20251111_014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add source_type column with default 'rss' for existing rows
    op.add_column(
        'feed_items',
        sa.Column(
            'source_type',
            sa.String(50),
            nullable=False,
            server_default='rss',
            comment='Source type: rss, perplexity_research, scraping, manual, api_*'
        )
    )

    # 2. Add source_metadata for extra information (model, cost, query, etc.)
    op.add_column(
        'feed_items',
        sa.Column(
            'source_metadata',
            JSONB,
            nullable=True,
            server_default='{}',
            comment='Source-specific metadata (e.g., model, cost, query for perplexity)'
        )
    )

    # 3. Add parent_article_id for linking research to original articles
    op.add_column(
        'feed_items',
        sa.Column(
            'parent_article_id',
            sa.UUID(),
            sa.ForeignKey('feed_items.id', ondelete='SET NULL'),
            nullable=True,
            comment='References original article for research/derived content'
        )
    )

    # 4. Make feed_id nullable for non-RSS sources
    op.alter_column(
        'feed_items',
        'feed_id',
        existing_type=sa.UUID(),
        nullable=True
    )

    # 5. Add check constraint: feed_id required for RSS, optional for others
    op.execute("""
        ALTER TABLE feed_items
        ADD CONSTRAINT chk_feed_id_required_for_rss
        CHECK (
            (source_type = 'rss' AND feed_id IS NOT NULL)
            OR source_type != 'rss'
        )
    """)

    # 6. Create indexes for efficient filtering
    op.create_index(
        'idx_feed_items_source_type',
        'feed_items',
        ['source_type']
    )

    op.create_index(
        'idx_feed_items_parent_article_id',
        'feed_items',
        ['parent_article_id']
    )

    # 7. Composite index for finding research by parent + type
    op.create_index(
        'idx_feed_items_parent_source',
        'feed_items',
        ['parent_article_id', 'source_type'],
        postgresql_where=sa.text("parent_article_id IS NOT NULL")
    )

    # 8. Add comment to table
    op.execute("""
        COMMENT ON TABLE feed_items IS
        'Articles from various sources: RSS feeds, Perplexity research, scraping, etc.'
    """)


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_feed_items_parent_source', table_name='feed_items')
    op.drop_index('idx_feed_items_parent_article_id', table_name='feed_items')
    op.drop_index('idx_feed_items_source_type', table_name='feed_items')

    # Remove check constraint
    op.execute("""
        ALTER TABLE feed_items
        DROP CONSTRAINT IF EXISTS chk_feed_id_required_for_rss
    """)

    # Make feed_id NOT NULL again (will fail if NULL values exist!)
    op.alter_column(
        'feed_items',
        'feed_id',
        existing_type=sa.UUID(),
        nullable=False
    )

    # Remove columns
    op.drop_column('feed_items', 'parent_article_id')
    op.drop_column('feed_items', 'source_metadata')
    op.drop_column('feed_items', 'source_type')
