"""Add source_id to feed_items table

Links articles directly to Sources for unified source management.
This enables direct source-to-article relationships independent of
the legacy feeds table.

Revision ID: 20251227_017
Revises: 20251227_016
Create Date: 2025-12-27 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251227_017'
down_revision = '20251227_016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add source_id column to feed_items
    op.add_column(
        'feed_items',
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_feed_items_source_id',
        'feed_items',
        'sources',
        ['source_id'],
        ['id'],
        ondelete='SET NULL'  # Keep article if source is deleted
    )

    # Create index for efficient lookups
    op.create_index(
        'ix_feed_items_source_id',
        'feed_items',
        ['source_id']
    )

    # Create composite index for source + published_at queries
    op.create_index(
        'ix_feed_items_source_published',
        'feed_items',
        ['source_id', 'published_at'],
        postgresql_where=sa.text('source_id IS NOT NULL')
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_feed_items_source_published', table_name='feed_items')
    op.drop_index('ix_feed_items_source_id', table_name='feed_items')

    # Drop foreign key
    op.drop_constraint('fk_feed_items_source_id', 'feed_items', type_='foreignkey')

    # Drop column
    op.drop_column('feed_items', 'source_id')
