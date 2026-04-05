"""SQLAlchemy models for batch-computed UMAP+HDBSCAN clusters.

These models support the periodic batch clustering layer that runs in parallel
with Single-Pass clustering:
- Single-Pass: Real-time burst detection (existing ArticleCluster)
- Batch: High-quality topic discovery via UMAP+HDBSCAN (these models)

The batch clustering is recomputed every 1-2 hours using Celery, providing
stable topic groupings that can be searched and browsed.

Note: The `centroid_vec` column is a pgvector type (vector(1536)) that is
not directly mapped in SQLAlchemy. Use raw SQL for vector operations:
- Similarity search: `SELECT ... ORDER BY centroid_vec <=> :embedding::vector`
- Insert centroid: `UPDATE batch_clusters SET centroid_vec = :vec::vector WHERE id = :id`
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.cluster import Base


class ClusterBatch(Base):
    """
    Metadata for a batch clustering run.

    Each batch represents one complete UMAP+HDBSCAN computation over all
    article embeddings. Only the most recent completed batch is considered
    "active" for query operations.

    Status flow: running -> completed | failed
    """
    __tablename__ = "cluster_batches"

    batch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="running",
        nullable=False
    )
    article_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    cluster_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    noise_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    csai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    clusters: Mapped[list["BatchCluster"]] = relationship(
        "BatchCluster",
        back_populates="batch",
        cascade="all, delete-orphan"
    )


class BatchCluster(Base):
    """
    A cluster from batch UMAP+HDBSCAN computation.

    Unlike real-time ArticleCluster, these are recomputed periodically
    and provide high-quality semantic topic groupings. Each cluster has:
    - A unique index within its batch (cluster_idx)
    - An LLM-generated or user-corrected label
    - Extracted keywords for search
    - A pgvector centroid for similarity lookup (not mapped - use raw SQL)

    Note: The `centroid_vec` column (vector(1536)) is not mapped here.
    Access via raw SQL for pgvector operations.
    """
    __tablename__ = "batch_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cluster_batches.batch_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    cluster_idx: Mapped[int] = mapped_column(Integer, nullable=False)

    # Metadata (LLM-generated or user-corrected)
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    label_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Statistics
    article_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Note: centroid_vec is a pgvector column (vector(1536)), not mapped here.
    # Access via raw SQL:
    #   SELECT id, centroid_vec <=> :embedding::vector AS distance FROM batch_clusters
    #   UPDATE batch_clusters SET centroid_vec = :vec::vector WHERE id = :id

    # Relationships
    batch: Mapped["ClusterBatch"] = relationship(
        "ClusterBatch",
        back_populates="clusters"
    )
    article_assignments: Mapped[list["BatchArticleCluster"]] = relationship(
        "BatchArticleCluster",
        back_populates="cluster",
        cascade="all, delete-orphan"
    )
    feedback: Mapped[list["ClusterFeedback"]] = relationship(
        "ClusterFeedback",
        back_populates="cluster",
        cascade="all, delete-orphan"
    )


class BatchArticleCluster(Base):
    """
    Maps articles to batch clusters.

    Each article belongs to exactly one cluster per batch. Articles marked
    as "noise" by HDBSCAN (cluster_idx = -1) are not stored here.

    The distance_to_centroid field enables ranking articles within a cluster
    by their representativeness (lower distance = more representative).
    """
    __tablename__ = "batch_article_clusters"

    article_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    cluster_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("batch_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cluster_batches.batch_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    distance_to_centroid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    cluster: Mapped["BatchCluster"] = relationship(
        "BatchCluster",
        back_populates="article_assignments"
    )


class ClusterFeedback(Base):
    """
    User feedback for improving cluster labels and structure.

    Feedback types:
    - label_correction: User corrected the cluster label
    - merge: User suggested merging clusters (future)
    - split: User suggested splitting a cluster (future)
    - quality_rating: User rated cluster quality (future)

    Feedback is stored for learning and can be used to:
    1. Immediately update the cluster label
    2. Inform future batch clustering runs
    3. Train label generation models
    """
    __tablename__ = "cluster_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("batch_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    cluster: Mapped["BatchCluster"] = relationship(
        "BatchCluster",
        back_populates="feedback"
    )


class TopicProfile(Base):
    """
    Semantic topic profile for cluster matching.

    Instead of hardcoded categories (CONFLICT, FINANCE, etc.), topic profiles
    define semantic categories via descriptive text that gets embedded. Clusters
    are then matched to profiles by cosine similarity of their centroid vectors.

    Example usage:
    1. Create profile: name="finance", description_text="Financial markets, stocks, bonds..."
    2. Generate embedding from description_text via OpenAI
    3. Find matching clusters: SELECT ... WHERE centroid_vec <=> embedding_vec < threshold

    Note: The `embedding_vec` column (vector(1536)) is not mapped here.
    Access via raw SQL for pgvector operations:
        SELECT id, name, embedding_vec <=> :query_vec::vector AS distance
        FROM topic_profiles WHERE is_active = true
    """
    __tablename__ = "topic_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Matching configuration
    min_similarity: Mapped[float] = mapped_column(
        Float,
        server_default="0.40",
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
        nullable=False
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        nullable=False
    )

    # Note: embedding_vec is a pgvector column (vector(1536)), not mapped here.
    # Access via raw SQL:
    #   SELECT id, embedding_vec <=> :profile_vec::vector AS distance FROM batch_clusters
    #   UPDATE topic_profiles SET embedding_vec = :vec::vector WHERE id = :id

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
