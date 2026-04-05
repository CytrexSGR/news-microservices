"""Add batch clustering tables for UMAP+HDBSCAN clusters.

Revision ID: 021
Revises: 020
Create Date: 2026-01-05

Epic 2: Batch + Query Clustering Architecture

This migration adds tables for periodic batch-recomputed UMAP+HDBSCAN clusters:
- cluster_batches: Metadata for each batch clustering run
- batch_clusters: Individual clusters with pgvector centroids for similarity search
- batch_article_clusters: Article-to-cluster mapping for each batch
- cluster_feedback: User feedback for label corrections

The batch clustering runs in parallel with the existing Single-Pass clustering:
- Single-Pass: Real-time burst detection (existing)
- Batch: High-quality topic discovery (new)

Uses pgvector for efficient nearest-neighbor centroid lookup.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create batch clustering tables with pgvector support."""
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Batch metadata table - must be created first for foreign key references
    op.create_table(
        'cluster_batches',
        sa.Column('batch_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('status', sa.String(20), server_default='running', nullable=False),
        sa.Column('article_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('cluster_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('noise_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('csai_score', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Index for finding latest completed batch
    op.create_index(
        'ix_cluster_batches_status_completed',
        'cluster_batches',
        ['status', 'completed_at']
    )

    # Batch clustering results table
    op.create_table(
        'batch_clusters',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('batch_id', UUID(as_uuid=True), sa.ForeignKey('cluster_batches.batch_id', ondelete='CASCADE'), nullable=False),
        sa.Column('cluster_idx', sa.Integer(), nullable=False),

        # Metadata (LLM-generated or user-corrected)
        sa.Column('label', sa.String(255), nullable=True),
        sa.Column('label_confidence', sa.Float(), nullable=True),
        sa.Column('keywords', JSONB, nullable=True),

        # Statistics
        sa.Column('article_count', sa.Integer(), server_default='0', nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        # Unique constraint: one cluster per index per batch
        sa.UniqueConstraint('batch_id', 'cluster_idx', name='uq_batch_cluster_idx')
    )

    # Index on batch_id for filtering clusters by batch
    op.create_index('ix_batch_clusters_batch_id', 'batch_clusters', ['batch_id'])

    # Add pgvector column for cluster centroids (text-embedding-3-small = 1536 dimensions)
    # Using raw SQL because SQLAlchemy doesn't natively support pgvector types
    op.execute("ALTER TABLE batch_clusters ADD COLUMN centroid_vec vector(1536)")

    # IVFFlat index for efficient cosine similarity search
    # lists=100 is appropriate for datasets up to ~100k vectors
    op.execute(
        "CREATE INDEX idx_batch_clusters_centroid ON batch_clusters "
        "USING ivfflat (centroid_vec vector_cosine_ops) WITH (lists = 100)"
    )

    # Article-to-batch-cluster mapping
    op.create_table(
        'batch_article_clusters',
        sa.Column('article_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('cluster_id', sa.Integer(), sa.ForeignKey('batch_clusters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_id', UUID(as_uuid=True), sa.ForeignKey('cluster_batches.batch_id', ondelete='CASCADE'), nullable=False),
        sa.Column('distance_to_centroid', sa.Float(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Index for looking up articles by cluster
    op.create_index('ix_batch_article_clusters_cluster', 'batch_article_clusters', ['cluster_id'])

    # Index for filtering by batch
    op.create_index('ix_batch_article_clusters_batch', 'batch_article_clusters', ['batch_id'])

    # Cluster feedback for learning and label corrections
    op.create_table(
        'cluster_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('cluster_id', sa.Integer(), sa.ForeignKey('batch_clusters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),  # label_correction, merge, split
        sa.Column('old_value', JSONB, nullable=True),
        sa.Column('new_value', JSONB, nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Index for querying feedback by cluster
    op.create_index('ix_cluster_feedback_cluster', 'cluster_feedback', ['cluster_id'])

    # Index for querying feedback by type
    op.create_index('ix_cluster_feedback_type', 'cluster_feedback', ['feedback_type'])

    # Check constraint for valid feedback types
    op.create_check_constraint(
        'ck_cluster_feedback_type',
        'cluster_feedback',
        "feedback_type IN ('label_correction', 'merge', 'split', 'quality_rating')"
    )

    # Check constraint for valid batch status values
    op.create_check_constraint(
        'ck_cluster_batches_status',
        'cluster_batches',
        "status IN ('running', 'completed', 'failed')"
    )


def downgrade() -> None:
    """Drop batch clustering tables."""
    # Drop constraints first
    op.drop_constraint('ck_cluster_feedback_type', 'cluster_feedback', type_='check')
    op.drop_constraint('ck_cluster_batches_status', 'cluster_batches', type_='check')

    # Drop indexes
    op.drop_index('ix_cluster_feedback_type', table_name='cluster_feedback')
    op.drop_index('ix_cluster_feedback_cluster', table_name='cluster_feedback')
    op.drop_index('ix_batch_article_clusters_batch', table_name='batch_article_clusters')
    op.drop_index('ix_batch_article_clusters_cluster', table_name='batch_article_clusters')
    op.execute("DROP INDEX IF EXISTS idx_batch_clusters_centroid")
    op.drop_index('ix_batch_clusters_batch_id', table_name='batch_clusters')
    op.drop_index('ix_cluster_batches_status_completed', table_name='cluster_batches')

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('cluster_feedback')
    op.drop_table('batch_article_clusters')
    op.drop_table('batch_clusters')
    op.drop_table('cluster_batches')
