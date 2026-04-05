"""Add escalation_anchors table for Intelligence Interpretation Layer.

This table stores reference anchor points for each escalation level (1-5)
across three domains (geopolitical, military, economic). Each anchor has:
- Reference text that defines the escalation level semantics
- Pre-computed embedding (1536 dimensions) for similarity matching
- Keywords for heuristic fallback detection
- Weight for importance scoring

The table enables three-signal escalation scoring:
- 50% embedding similarity to anchor points
- 30% content analysis matching
- 20% keyword heuristics

Revision ID: 025
Revises: 024
Create Date: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

# revision identifiers
revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create escalation_anchors table with pgvector support."""
    # Ensure pgvector extension exists (should already be enabled)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create escalation_anchors table using raw SQL for pgvector column
    op.execute("""
        CREATE TABLE escalation_anchors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            domain VARCHAR(20) NOT NULL,
            level INTEGER NOT NULL,
            label VARCHAR(100) NOT NULL,
            reference_text TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            keywords TEXT[] DEFAULT '{}',
            weight NUMERIC(3, 2) DEFAULT 1.0,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

            -- Constraints
            CONSTRAINT chk_anchor_domain CHECK (domain IN ('geopolitical', 'military', 'economic')),
            CONSTRAINT chk_anchor_level CHECK (level BETWEEN 1 AND 5),
            CONSTRAINT uq_anchor_domain_level_label UNIQUE (domain, level, label)
        )
    """)

    # Create partial index for active anchor lookups by domain and level
    op.execute("""
        CREATE INDEX idx_escalation_anchors_lookup
        ON escalation_anchors (domain, level)
        WHERE is_active = true
    """)

    # Create IVFFlat index for fast embedding similarity search
    # lists=10 is appropriate for small tables (<1000 rows)
    op.execute("""
        CREATE INDEX idx_escalation_anchors_embedding
        ON escalation_anchors
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10)
    """)

    # Add comment for documentation
    op.execute("""
        COMMENT ON TABLE escalation_anchors IS
        'Reference anchor points for escalation level detection. Each anchor defines '
        'the semantic meaning of an escalation level (1-5) within a domain '
        '(geopolitical, military, economic) via reference text and pre-computed embeddings.'
    """)


def downgrade() -> None:
    """Remove escalation_anchors table and indexes."""
    op.execute("DROP INDEX IF EXISTS idx_escalation_anchors_embedding")
    op.execute("DROP INDEX IF EXISTS idx_escalation_anchors_lookup")
    op.execute("DROP TABLE IF EXISTS escalation_anchors")
