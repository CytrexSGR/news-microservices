"""Add event_outbox table for transactional event publishing

Revision ID: 20251029_009
Revises: 20251022_008
Create Date: 2025-10-29 17:00:00.000000

Implements Outbox Pattern to guarantee at-least-once event delivery.
Events are stored in outbox table in same transaction as domain changes,
then published to RabbitMQ by separate processor.

This solves the "orphaned article" problem where article.created events
could be lost if RabbitMQ publish failed after DB commit.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251029_009'
down_revision = '20251027_011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create event_outbox table"""

    op.create_table(
        'event_outbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_type', sa.String(100), nullable=False, comment='Event type (e.g., article.created, feed.updated)'),
        sa.Column('payload', postgresql.JSONB, nullable=False, comment='Event payload data'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='pending, published, failed'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='When event was created'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True, comment='When event was successfully published to RabbitMQ'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0', comment='Number of publish attempts'),
        sa.Column('last_error', sa.Text(), nullable=True, comment='Last error message if publish failed'),
        sa.Column('correlation_id', sa.String(100), nullable=True, comment='Optional correlation ID for tracking'),
    )

    # Index for fast lookup of pending events (used by outbox processor)
    op.create_index(
        'ix_outbox_pending',
        'event_outbox',
        ['status', 'created_at'],
        postgresql_where=sa.text("status = 'pending'")
    )

    # Index for monitoring failed events
    op.create_index(
        'ix_outbox_failed',
        'event_outbox',
        ['status', 'retry_count'],
        postgresql_where=sa.text("status = 'failed'")
    )

    # Index for correlation tracking
    op.create_index(
        'ix_outbox_correlation',
        'event_outbox',
        ['correlation_id'],
        postgresql_where=sa.text("correlation_id IS NOT NULL")
    )


def downgrade() -> None:
    """Drop event_outbox table"""

    # Drop indexes
    op.drop_index('ix_outbox_correlation', table_name='event_outbox')
    op.drop_index('ix_outbox_failed', table_name='event_outbox')
    op.drop_index('ix_outbox_pending', table_name='event_outbox')

    # Drop table
    op.drop_table('event_outbox')
