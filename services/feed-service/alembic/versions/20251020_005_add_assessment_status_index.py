"""add_assessment_status_index

Revision ID: 20251020_005
Revises: 20251018_004
Create Date: 2025-10-20 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251020_005'
down_revision: Union[str, None] = '20251018_004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add index on feeds.assessment_status for polling queries."""
    # Create index on assessment_status column
    # This speeds up queries like: SELECT * FROM feeds WHERE assessment_status = 'pending'
    op.create_index(
        'idx_feeds_assessment_status',
        'feeds',
        ['assessment_status'],
        unique=False
    )


def downgrade() -> None:
    """Remove index on feeds.assessment_status."""
    op.drop_index('idx_feeds_assessment_status', table_name='feeds')
