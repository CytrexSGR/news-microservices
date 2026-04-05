"""Add web crawler support: feed_type, crawl fields, crawl_sessions table

Revision ID: 018_web_crawler
Revises: 20260126_add_etf_table
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '018_web_crawler'
down_revision = '20260126_add_etf_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add feed_type to feeds table
    op.add_column('feeds', sa.Column('feed_type', sa.String(10), server_default='rss', nullable=False))
    op.create_index('ix_feeds_feed_type', 'feeds', ['feed_type'])

    # Add crawl columns to feed_items
    op.add_column('feed_items', sa.Column('depth', sa.Integer(), server_default='0', nullable=True))
    op.add_column('feed_items', sa.Column('parent_item_id', UUID(as_uuid=True), nullable=True))
    op.add_column('feed_items', sa.Column('crawl_session_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_feed_items_parent_item', 'feed_items', 'feed_items',
        ['parent_item_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_feed_items_crawl_session_id', 'feed_items', ['crawl_session_id'])

    # Create crawl_sessions table
    op.create_table(
        'crawl_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('feed_id', UUID(as_uuid=True), sa.ForeignKey('feeds.id', ondelete='CASCADE'), nullable=True),
        sa.Column('seed_url', sa.Text(), nullable=False),
        sa.Column('topic', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('pages_scraped', sa.Integer(), server_default='0', nullable=False),
        sa.Column('visited_urls', JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, server_default='{}'),
    )
    op.create_index('ix_crawl_sessions_status', 'crawl_sessions', ['status'])
    op.create_index('ix_crawl_sessions_feed_id', 'crawl_sessions', ['feed_id'])


def downgrade() -> None:
    op.drop_index('ix_feeds_feed_type')
    op.drop_index('ix_feed_items_crawl_session_id')
    op.drop_index('ix_crawl_sessions_feed_id')
    op.drop_index('ix_crawl_sessions_status')
    op.drop_table('crawl_sessions')
    op.drop_constraint('fk_feed_items_parent_item', 'feed_items', type_='foreignkey')
    op.drop_column('feed_items', 'crawl_session_id')
    op.drop_column('feed_items', 'parent_item_id')
    op.drop_column('feed_items', 'depth')
    op.drop_column('feeds', 'feed_type')
