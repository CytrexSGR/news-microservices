"""Add pgvector columns to article_clusters for CSAI validation.

Adds centroid_vec (pgvector) column for fast similarity search and
CSAI (Cluster Stability Assessment Index) tracking columns for
validating cluster quality at size milestones.

Revision ID: 024
Revises: 023
Create Date: 2026-01-06
"""

from alembic import op
import sqlalchemy as sa

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgvector extension (should already exist, but safe to check)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add pgvector centroid column
    # Using IF NOT EXISTS for idempotency
    op.execute("""
        ALTER TABLE article_clusters
        ADD COLUMN IF NOT EXISTS centroid_vec vector(1536)
    """)

    # Add CSAI tracking columns
    # These track cluster stability at size milestones (10, 25, 50, 100 articles)
    op.add_column(
        "article_clusters",
        sa.Column("csai_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "article_clusters",
        sa.Column(
            "csai_status",
            sa.String(20),
            nullable=True,
            server_default="pending",
        ),
    )
    op.add_column(
        "article_clusters",
        sa.Column("csai_checked_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create IVFFlat index for fast similarity search
    # Note: Cannot use CONCURRENTLY in a transaction, so we commit first
    # For production, consider running this separately
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_article_clusters_centroid_vec
        ON article_clusters USING ivfflat (centroid_vec vector_cosine_ops)
        WITH (lists = 100)
    """)

    # Create index for active cluster queries with CSAI status
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_article_clusters_active_csai
        ON article_clusters (status, csai_status, last_updated_at DESC)
        WHERE status = 'active'
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_article_clusters_active_csai")
    op.execute("DROP INDEX IF EXISTS idx_article_clusters_centroid_vec")
    op.drop_column("article_clusters", "csai_checked_at")
    op.drop_column("article_clusters", "csai_status")
    op.drop_column("article_clusters", "csai_score")
    op.execute("ALTER TABLE article_clusters DROP COLUMN IF EXISTS centroid_vec")
