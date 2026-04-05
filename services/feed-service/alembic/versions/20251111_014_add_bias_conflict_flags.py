"""Add bias and conflict analysis flags

Revision ID: 20251111_014
Revises: 20251106_013
Create Date: 2025-11-11

Adds two missing boolean flags for Tier 2 specialist agent control:
- enable_bias: Enable BIAS_DETECTOR agent (bias detection and analysis)
- enable_conflict: Enable CONFLICT_EVENT_ANALYST agent (conflict and violence detection)

These flags complete the feed-level control for all 4 Tier 2 specialist agents:
- enable_finance_sentiment → FINANCIAL_ANALYST
- enable_geopolitical_sentiment → GEOPOLITICAL_ANALYST
- enable_bias → BIAS_DETECTOR (NEW)
- enable_conflict → CONFLICT_EVENT_ANALYST (NEW)

Background:
Prior to this migration, BIAS_DETECTOR and CONFLICT_EVENT_ANALYST were hardcoded
to always run in content-analysis-v2/app/pipeline/types.py. This migration adds
the database columns needed to implement per-feed control.

Related:
- /tmp/feature_flags_problem_analysis.md (root cause analysis)
- /tmp/feature_flags_complete_analysis.md (complete data flow analysis)
- services/content-analysis-v2/app/pipeline/orchestrator.py (will be updated to check these flags)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251111_014'
down_revision = '20251106_013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add bias and conflict analysis flags."""
    # Add enable_bias column
    op.add_column(
        'feeds',
        sa.Column('enable_bias', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add enable_conflict column
    op.add_column(
        'feeds',
        sa.Column('enable_conflict', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Remove bias and conflict analysis flags."""
    op.drop_column('feeds', 'enable_conflict')
    op.drop_column('feeds', 'enable_bias')
