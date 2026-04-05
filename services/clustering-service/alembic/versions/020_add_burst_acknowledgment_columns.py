"""Add acknowledgment columns to burst_alerts table.

Revision ID: 020
Revises: 019
Create Date: 2026-01-04

Epic 1.3: Enhanced Burst Detection - Task 6

Adds columns to support acknowledging burst alerts through the API:
- acknowledged: Boolean flag indicating if alert was reviewed
- acknowledged_at: Timestamp of acknowledgment
- acknowledged_by: User ID who acknowledged the alert
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add acknowledgment columns to burst_alerts."""
    op.add_column(
        'burst_alerts',
        sa.Column('acknowledged', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'burst_alerts',
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'burst_alerts',
        sa.Column('acknowledged_by', sa.String(100), nullable=True)
    )

    # Index for querying active (unacknowledged) bursts
    op.create_index(
        'ix_burst_alerts_acknowledged',
        'burst_alerts',
        ['acknowledged', 'detected_at']
    )


def downgrade() -> None:
    """Remove acknowledgment columns from burst_alerts."""
    op.drop_index('ix_burst_alerts_acknowledged', table_name='burst_alerts')
    op.drop_column('burst_alerts', 'acknowledged_by')
    op.drop_column('burst_alerts', 'acknowledged_at')
    op.drop_column('burst_alerts', 'acknowledged')
