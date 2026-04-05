"""Add enable_osint_analysis flag to feeds

Revision ID: 20251015_003
Revises: 20251013_002
Create Date: 2025-10-15 16:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251015_003'
down_revision = '20251013_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enable_osint_analysis flag to feeds table."""
    op.add_column(
        'feeds',
        sa.Column('enable_osint_analysis', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Remove enable_osint_analysis flag from feeds table."""
    op.drop_column('feeds', 'enable_osint_analysis')
