"""Add feed source assessment fields

Revision ID: 20251018_004
Revises: 20251015_003
Create Date: 2025-10-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251018_004'
down_revision = '20251015_003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Feed Source Assessment columns
    op.add_column('feeds', sa.Column('assessment_status', sa.String(length=50), nullable=True))
    op.add_column('feeds', sa.Column('assessment_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('feeds', sa.Column('credibility_tier', sa.String(length=20), nullable=True))
    op.add_column('feeds', sa.Column('reputation_score', sa.Integer(), nullable=True))
    op.add_column('feeds', sa.Column('founded_year', sa.Integer(), nullable=True))
    op.add_column('feeds', sa.Column('organization_type', sa.String(length=100), nullable=True))
    op.add_column('feeds', sa.Column('political_bias', sa.String(length=50), nullable=True))
    op.add_column('feeds', sa.Column('editorial_standards', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('feeds', sa.Column('trust_ratings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('feeds', sa.Column('recommendation', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('feeds', sa.Column('assessment_summary', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove Feed Source Assessment columns
    op.drop_column('feeds', 'assessment_summary')
    op.drop_column('feeds', 'recommendation')
    op.drop_column('feeds', 'trust_ratings')
    op.drop_column('feeds', 'editorial_standards')
    op.drop_column('feeds', 'political_bias')
    op.drop_column('feeds', 'organization_type')
    op.drop_column('feeds', 'founded_year')
    op.drop_column('feeds', 'reputation_score')
    op.drop_column('feeds', 'credibility_tier')
    op.drop_column('feeds', 'assessment_date')
    op.drop_column('feeds', 'assessment_status')
