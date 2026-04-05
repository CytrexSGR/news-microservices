"""Add content-analysis-v2 enable flag

Revision ID: 20251027_011
Revises: 20251022_010
Create Date: 2025-10-27

Adds enable_analysis_v2 boolean flag to replace granular V1 analysis flags.
The new content-analysis-v2 service handles all analysis decisions internally,
so only a single on/off toggle is needed per feed.

V1 flags (DEPRECATED but kept for backward compatibility):
- enable_categorization
- enable_finance_sentiment
- enable_geopolitical_sentiment
- enable_osint_analysis
- enable_summary
- enable_entity_extraction
- enable_topic_classification

V2 flag (NEW):
- enable_analysis_v2: Single toggle for entire content-analysis-v2 pipeline
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251027_011'
down_revision = '20251022_010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enable_analysis_v2 flag to feeds table."""
    op.add_column(
        'feeds',
        sa.Column('enable_analysis_v2', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Remove enable_analysis_v2 flag from feeds table."""
    op.drop_column('feeds', 'enable_analysis_v2')
