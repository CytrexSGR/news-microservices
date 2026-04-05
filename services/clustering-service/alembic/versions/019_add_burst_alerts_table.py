"""Add burst_alerts table for tracking detected bursts.

Revision ID: 019
Revises: 018
Create Date: 2026-01-04

Epic 1.3: Enhanced Burst Detection

This table stores burst detection alerts with their severity, velocity,
and whether an external alert was sent. Used for:
- Auditing burst detection history
- Cooldown period tracking to prevent alert spam
- API endpoints for querying burst activity
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
# NOTE: down_revision set to None because older migrations (001-018) were
# applied before being tracked in this repository. The database already has
# these changes applied.
revision = '019'
down_revision = None  # Base migration for clustering-service
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create burst_alerts table."""
    op.create_table(
        'burst_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('cluster_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('velocity', sa.Integer(), nullable=False),
        sa.Column('window_minutes', sa.Integer(), nullable=False),
        sa.Column('alert_sent', sa.Boolean(), default=False, nullable=False),
        sa.Column('alert_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Index for cooldown queries: find recent sent alerts for a cluster
    op.create_index(
        'ix_burst_alerts_cluster_sent_detected',
        'burst_alerts',
        ['cluster_id', 'alert_sent', 'detected_at']
    )

    # Index for time-based queries
    op.create_index(
        'ix_burst_alerts_detected_at',
        'burst_alerts',
        ['detected_at']
    )

    # Check constraint for severity values
    op.create_check_constraint(
        'ck_burst_alerts_severity',
        'burst_alerts',
        "severity IN ('low', 'medium', 'high', 'critical')"
    )


def downgrade() -> None:
    """Drop burst_alerts table."""
    op.drop_constraint('ck_burst_alerts_severity', 'burst_alerts', type_='check')
    op.drop_index('ix_burst_alerts_detected_at', table_name='burst_alerts')
    op.drop_index('ix_burst_alerts_cluster_sent_detected', table_name='burst_alerts')
    op.drop_table('burst_alerts')
