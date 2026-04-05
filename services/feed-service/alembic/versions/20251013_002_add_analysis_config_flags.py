"""Add analysis configuration flags

Revision ID: 20251013_002
Revises: 20251013_001
Create Date: 2025-10-13 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251013_002'
down_revision = None  # Changed from '20251013_001' - this is now the initial migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feeds table with all columns
    op.create_table(
        'feeds',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fetch_interval', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('last_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_modified', sa.String(100), nullable=True),
        sa.Column('etag', sa.String(100), nullable=True),
        sa.Column('health_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('items_last_24h', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scrape_full_content', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('scrape_method', sa.String(50), nullable=False, server_default='auto'),
        sa.Column('enable_categorization', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enable_finance_sentiment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enable_geopolitical_sentiment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enable_osint_analysis', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index('ix_feeds_url', 'feeds', ['url'])


def downgrade() -> None:
    # Drop the entire feeds table
    op.drop_index('ix_feeds_url', 'feeds')
    op.drop_table('feeds')
