"""Add extended analysis configuration flags

Revision ID: 20251021_006
Revises: 20251020_005
Create Date: 2025-10-21

Adds three new boolean flags for extended auto-analysis configuration:
- enable_summary: Enable automatic article summarization and key facts extraction
- enable_entity_extraction: Enable entity extraction (persons, organizations, locations)
- enable_topic_classification: Enable topic classification and keyword extraction

These flags complement the existing analysis flags:
- enable_categorization (6 predefined categories)
- enable_finance_sentiment
- enable_geopolitical_sentiment
- enable_osint_analysis
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251021_006'
down_revision = '20251020_005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new analysis configuration flags."""
    # Add enable_summary column
    op.add_column(
        'feeds',
        sa.Column('enable_summary', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add enable_entity_extraction column
    op.add_column(
        'feeds',
        sa.Column('enable_entity_extraction', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add enable_topic_classification column
    op.add_column(
        'feeds',
        sa.Column('enable_topic_classification', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Remove analysis configuration flags."""
    op.drop_column('feeds', 'enable_topic_classification')
    op.drop_column('feeds', 'enable_entity_extraction')
    op.drop_column('feeds', 'enable_summary')
