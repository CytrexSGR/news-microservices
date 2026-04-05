"""Add scraping enhancements: threshold config and metadata

Revision ID: 20251022_010
Revises: 20251022_008
Create Date: 2025-10-22 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251022_010'
down_revision = '20251022_008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add configurable failure threshold and metadata fields"""

    # 1. Add scrape_failure_threshold to feeds table
    op.add_column('feeds', sa.Column(
        'scrape_failure_threshold',
        sa.Integer(),
        nullable=False,
        server_default='5'
    ))

    # 2. Add scraped_metadata to feed_items table (for newspaper4k extras)
    op.add_column('feed_items', sa.Column(
        'scraped_metadata',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True
    ))

    # 3. Create GIN index for JSONB column (efficient JSON queries)
    op.create_index(
        'idx_feed_items_scraped_metadata',
        'feed_items',
        ['scraped_metadata'],
        postgresql_using='gin'
    )

    # 4. Migrate existing scrape_method values
    # Change 'auto' and 'httpx' to 'newspaper4k' (new default)
    op.execute("""
        UPDATE feeds
        SET scrape_method = 'newspaper4k'
        WHERE scrape_method IN ('auto', 'httpx')
    """)


def downgrade() -> None:
    """Remove scraping enhancements"""

    # Drop index
    op.drop_index('idx_feed_items_scraped_metadata', table_name='feed_items')

    # Drop columns
    op.drop_column('feed_items', 'scraped_metadata')
    op.drop_column('feeds', 'scrape_failure_threshold')

    # Revert scrape_method changes (optional, data loss)
    # op.execute("UPDATE feeds SET scrape_method = 'auto' WHERE scrape_method = 'newspaper4k'")
