"""Add admiralty code configuration tables

Revision ID: 20251021_007
Revises: 20251021_006
Create Date: 2025-10-21 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4

# revision identifiers, used by Alembic.
revision: str = '20251021_007'
down_revision: Union[str, None] = '20251021_006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add admiralty code configuration tables.

    Two tables:
    1. admiralty_code_thresholds - Configurable thresholds for A-F ratings
    2. quality_score_weights - Configurable weights for quality score calculation
    """

    # Create admiralty_code_thresholds table
    op.create_table(
        'admiralty_code_thresholds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('code', sa.String(1), nullable=False, unique=True),
        sa.Column('label', sa.String(50), nullable=False),
        sa.Column('min_score', sa.Integer, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create index on min_score for efficient lookups
    op.create_index('idx_admiralty_min_score', 'admiralty_code_thresholds', ['min_score'], postgresql_ops={'min_score': 'DESC'})

    # Insert default admiralty code thresholds
    op.execute("""
        INSERT INTO admiralty_code_thresholds (id, code, label, min_score, description, color) VALUES
        (gen_random_uuid(), 'A', 'Completely Reliable', 90, 'Score ≥ 90%: Premium sources with exceptional credibility, rigorous editorial standards, and consistently high trust ratings. Examples: Reuters, AP, established tier-1 news organizations.', 'green'),
        (gen_random_uuid(), 'B', 'Usually Reliable', 75, 'Score ≥ 75%: Trusted sources with strong credibility, solid editorial practices, and good trust ratings. Occasional minor issues but generally dependable.', 'blue'),
        (gen_random_uuid(), 'C', 'Fairly Reliable', 60, 'Score ≥ 60%: Moderate reliability with acceptable credibility. May have some bias or occasional quality issues. Suitable for general monitoring with verification.', 'yellow'),
        (gen_random_uuid(), 'D', 'Not Usually Reliable', 40, 'Score ≥ 40%: Limited reliability with questionable credibility or significant bias. Requires careful verification and cross-referencing with other sources.', 'orange'),
        (gen_random_uuid(), 'E', 'Unreliable', 20, 'Score ≥ 20%: Poor reliability with low credibility, poor editorial standards, or known misinformation history. Use with extreme caution.', 'red'),
        (gen_random_uuid(), 'F', 'Cannot Be Judged', 0, 'Score < 20% or new feed: Insufficient data for assessment, new source without established track record, or extremely low quality. Requires thorough evaluation before trust.', 'gray')
    """)

    # Create quality_score_weights table
    op.create_table(
        'quality_score_weights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('category', sa.String(50), nullable=False, unique=True),
        sa.Column('weight', sa.Numeric(5, 2), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('min_value', sa.Numeric(5, 2), nullable=False, server_default='0.00'),
        sa.Column('max_value', sa.Numeric(5, 2), nullable=False, server_default='1.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Insert default quality score weights
    op.execute("""
        INSERT INTO quality_score_weights (id, category, weight, description, min_value, max_value) VALUES
        (gen_random_uuid(), 'credibility', 0.40, 'Weight for credibility tier assessment (tier_1/tier_2/tier_3). Based on source reputation, longevity, and industry recognition.', 0.00, 1.00),
        (gen_random_uuid(), 'editorial', 0.25, 'Weight for editorial standards evaluation (fact-checking, corrections policy, source attribution). Reflects journalistic integrity.', 0.00, 1.00),
        (gen_random_uuid(), 'trust', 0.20, 'Weight for external trust ratings (NewsGuard, AllSides, MBFC). Independent third-party assessments of source reliability.', 0.00, 1.00),
        (gen_random_uuid(), 'health', 0.15, 'Weight for operational health metrics (uptime, response time, fetch success rate). Technical reliability of feed source.', 0.00, 1.00)
    """)

    # Add constraint to ensure weights sum to 1.00 (100%)
    op.create_check_constraint(
        'ck_quality_score_weights_range',
        'quality_score_weights',
        'weight >= min_value AND weight <= max_value'
    )


def downgrade() -> None:
    """Remove admiralty code configuration tables."""
    op.drop_table('quality_score_weights')
    op.drop_table('admiralty_code_thresholds')
