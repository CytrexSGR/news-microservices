"""Add fmp_news_correlations table for FMP regime / news escalation correlations.

This migration creates the fmp_news_correlations table to store correlations
between FMP market regime states and news escalation levels. This enables
the Intelligence Interpretation Layer to detect patterns like:
- CONFIRMATION: News escalation confirms market regime signals
- DIVERGENCE: News escalation diverges from market expectations
- EARLY_WARNING: News may predict upcoming regime shifts

Correlation Types:
- CONFIRMATION: News sentiment matches market regime
- DIVERGENCE: News sentiment conflicts with market regime
- EARLY_WARNING: News precedes market regime change

FMP Regimes:
- RISK_ON: Markets in risk-on mode (bullish)
- RISK_OFF: Markets in risk-off mode (bearish/defensive)
- TRANSITIONAL: Markets transitioning between regimes

Revision ID: 027
Revises: 026
Create Date: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

# revision identifiers
revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create fmp_news_correlations table with indexes and constraints."""
    op.create_table(
        'fmp_news_correlations',
        # Primary key
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),

        # Core timestamp - when correlation was detected
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()'),
                  comment='Timestamp when correlation was detected'),

        # Correlation type with CHECK constraint
        sa.Column('correlation_type', sa.VARCHAR(20), nullable=False,
                  comment='Type of correlation: CONFIRMATION, DIVERGENCE, EARLY_WARNING'),

        # FMP regime with CHECK constraint
        sa.Column('fmp_regime', sa.VARCHAR(20), nullable=False,
                  comment='FMP market regime: RISK_ON, RISK_OFF, TRANSITIONAL'),

        # Escalation level (1-5 scale)
        sa.Column('escalation_level', sa.Integer(), nullable=True,
                  comment='News escalation level (1=low, 5=critical)'),

        # Confidence score (0.000-1.000)
        sa.Column('confidence', sa.Numeric(4, 3), nullable=True,
                  comment='Correlation confidence score (0.000-1.000)'),

        # Related clusters - array of UUIDs
        sa.Column('related_clusters', ARRAY(UUID(as_uuid=True)), nullable=True,
                  server_default='{}',
                  comment='Array of related article cluster UUIDs'),

        # Additional metadata
        sa.Column('metadata', JSONB(), nullable=True,
                  comment='Additional context: {vix_level, regime_score, signals, ...}'),

        # Alert TTL
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Expiration timestamp for alert TTL'),

        # Active flag for soft delete / filtering
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default='true',
                  comment='Whether this correlation is currently active'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()'),
                  comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()'),
                  comment='Record last update timestamp'),
    )

    # Add CHECK constraint for correlation_type
    op.execute("""
        ALTER TABLE fmp_news_correlations
        ADD CONSTRAINT chk_fmp_correlation_type
        CHECK (correlation_type IN ('CONFIRMATION', 'DIVERGENCE', 'EARLY_WARNING'))
    """)

    # Add CHECK constraint for fmp_regime
    op.execute("""
        ALTER TABLE fmp_news_correlations
        ADD CONSTRAINT chk_fmp_regime
        CHECK (fmp_regime IN ('RISK_ON', 'RISK_OFF', 'TRANSITIONAL'))
    """)

    # Add CHECK constraint for escalation_level (1-5)
    op.execute("""
        ALTER TABLE fmp_news_correlations
        ADD CONSTRAINT chk_fmp_escalation_level
        CHECK (escalation_level IS NULL OR (escalation_level >= 1 AND escalation_level <= 5))
    """)

    # Add CHECK constraint for confidence (0.000-1.000)
    op.execute("""
        ALTER TABLE fmp_news_correlations
        ADD CONSTRAINT chk_fmp_confidence
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
    """)

    # Create index for active correlations by type (partial index)
    op.execute("""
        CREATE INDEX idx_fmp_correlations_active_type
        ON fmp_news_correlations (correlation_type, detected_at DESC)
        WHERE is_active = true
    """)

    # Create index for regime lookups
    op.execute("""
        CREATE INDEX idx_fmp_correlations_regime
        ON fmp_news_correlations (fmp_regime, detected_at DESC)
    """)

    # Add trigger for updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_fmp_correlations_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER fmp_correlations_updated_at_trigger
        BEFORE UPDATE ON fmp_news_correlations
        FOR EACH ROW
        EXECUTE FUNCTION update_fmp_correlations_updated_at();
    """)


def downgrade() -> None:
    """Remove fmp_news_correlations table and related objects."""
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS fmp_correlations_updated_at_trigger ON fmp_news_correlations")
    op.execute("DROP FUNCTION IF EXISTS update_fmp_correlations_updated_at()")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_fmp_correlations_regime")
    op.execute("DROP INDEX IF EXISTS idx_fmp_correlations_active_type")

    # Drop table (constraints are automatically dropped with table)
    op.drop_table('fmp_news_correlations')
