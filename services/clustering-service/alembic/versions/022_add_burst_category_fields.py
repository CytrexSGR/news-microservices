"""Add category and title fields to burst_alerts.

Revision ID: 022
Revises: 021
Create Date: 2026-01-06

Adds category-based filtering support for burst alerts:
- title: Cluster title at detection time
- category: Content category (conflict, finance, etc.)
- tension_score: Story tension score
- growth_rate: Growth rate multiplier
- top_entities: Top entities in the cluster (JSONB)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add category and title fields to burst_alerts table."""
    # Add new columns
    op.add_column(
        "burst_alerts",
        sa.Column("title", sa.String(500), nullable=True),
    )
    op.add_column(
        "burst_alerts",
        sa.Column("category", sa.String(50), nullable=True),
    )
    op.add_column(
        "burst_alerts",
        sa.Column("tension_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "burst_alerts",
        sa.Column("growth_rate", sa.Float(), nullable=True),
    )
    op.add_column(
        "burst_alerts",
        sa.Column("top_entities", JSONB(), nullable=True),
    )

    # Add index on category for filtering performance
    op.create_index(
        "ix_burst_alerts_category",
        "burst_alerts",
        ["category"],
    )


def downgrade() -> None:
    """Remove category and title fields from burst_alerts table."""
    op.drop_index("ix_burst_alerts_category", table_name="burst_alerts")
    op.drop_column("burst_alerts", "top_entities")
    op.drop_column("burst_alerts", "growth_rate")
    op.drop_column("burst_alerts", "tension_score")
    op.drop_column("burst_alerts", "category")
    op.drop_column("burst_alerts", "title")
