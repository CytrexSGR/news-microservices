"""Add scrape failure tracking fields

Revision ID: 20251022_008
Revises: 20251021_007
Create Date: 2025-10-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251022_008'
down_revision = '20251021_007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add failure tracking fields to feeds table"""

    # Add scrape_failure_count column
    op.add_column('feeds', sa.Column(
        'scrape_failure_count',
        sa.Integer(),
        nullable=False,
        server_default='0'
    ))

    # Add scrape_last_failure_at column
    op.add_column('feeds', sa.Column(
        'scrape_last_failure_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))

    # Add scrape_disabled_reason column
    # Values: null (not disabled), "manual" (user disabled), "auto_threshold" (system disabled after 10 failures)
    op.add_column('feeds', sa.Column(
        'scrape_disabled_reason',
        sa.String(50),
        nullable=True
    ))

    # Create index for querying auto-disabled feeds
    op.create_index(
        'ix_feeds_scrape_disabled_reason',
        'feeds',
        ['scrape_disabled_reason']
    )


def downgrade() -> None:
    """Remove failure tracking fields"""

    # Drop index
    op.drop_index('ix_feeds_scrape_disabled_reason', table_name='feeds')

    # Drop columns
    op.drop_column('feeds', 'scrape_disabled_reason')
    op.drop_column('feeds', 'scrape_last_failure_at')
    op.drop_column('feeds', 'scrape_failure_count')
