# services/clustering-service/app/api/v1/batch_clusters.py
"""Batch Cluster API endpoints for topic discovery.

This module provides the Query API for batch-computed UMAP+HDBSCAN clusters,
enabling topic discovery and semantic search across news articles.

Endpoints:
- GET /topics         - List topic clusters from latest batch
- GET /topics/search  - Search clusters by keyword
- GET /topics/{id}    - Get cluster details with sample articles
- GET /topics/similar/{article_id} - Find clusters similar to an article
- POST /topics/{id}/feedback - Submit label correction feedback
- GET /topics/batches - List batch clustering runs (admin)

Note: These endpoints are separate from the real-time /clusters endpoints
which use single-pass clustering for burst detection.
"""

import logging
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding_service import get_embedding_service

from app.api.dependencies import get_current_user_id
from app.db.session import get_db
from app.schemas.batch_cluster import (
    ArticleTopicInfo,
    BatchInfo,
    BatchListResponse,
    FeedbackResponse,
    SimilarTopic,
    SimilarTopicsResponse,
    TopicDetail,
    TopicFeedbackRequest,
    TopicListResponse,
    TopicSearchResponse,
    TopicSearchResult,
    TopicSummary,
    TopicArticle,
)
from app.services.batch_cluster_repository import BatchClusterRepository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=TopicListResponse)
async def list_topics(
    min_size: int = Query(10, ge=1, le=1000, description="Minimum articles per cluster"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    batch_id: Optional[str] = Query(None, description="Specific batch ID (default: latest)"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    List topic clusters from the latest batch.

    Returns clusters sorted by article count (largest first).
    Filter by min_size to exclude small clusters.

    Examples:
        GET /topics?min_size=20&limit=20
        GET /topics?batch_id=abc-123
    """
    repo = BatchClusterRepository(db)

    # Parse batch_id if provided
    parsed_batch_id = UUID(batch_id) if batch_id else None

    clusters, total = await repo.list_clusters(
        batch_id=parsed_batch_id,
        min_size=min_size,
        limit=limit,
        offset=offset,
    )

    # Get batch ID for response (either provided or latest)
    actual_batch_id = parsed_batch_id
    if actual_batch_id is None and clusters:
        actual_batch_id = clusters[0].batch_id

    return TopicListResponse(
        topics=[
            TopicSummary(
                id=c.id,
                label=c.label,
                keywords=c.keywords.get("terms", []) if c.keywords else None,
                article_count=c.article_count,
                label_confidence=c.label_confidence,
            )
            for c in clusters
        ],
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(clusters) < total,
        batch_id=str(actual_batch_id) if actual_batch_id else None,
    )


@router.get("/search", response_model=TopicSearchResponse)
async def search_topics(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    mode: Literal["semantic", "keyword"] = Query("semantic", description="Search mode"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity (semantic mode)"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Search topic clusters by semantic similarity or keyword matching.

    **Semantic mode** (default): Embeds query and finds clusters with similar centroids.
    Uses OpenAI text-embedding-3-small for mathematical similarity in embedding space.

    **Keyword mode**: Searches article titles within clusters by string matching.
    Supports multiple keywords (space-separated, OR logic).

    Examples:
        GET /topics/search?q=federal reserve interest rates (semantic)
        GET /topics/search?q=bitcoin&mode=keyword (keyword fallback)
    """
    repo = BatchClusterRepository(db)
    batch_id = await repo.get_latest_batch_id()

    if mode == "semantic":
        # Semantic search using embeddings
        embedding_service = get_embedding_service()

        if not embedding_service.is_available():
            logger.warning("Semantic search unavailable, falling back to keyword mode")
            mode = "keyword"
        else:
            embedding = await embedding_service.embed_query(q)

            if embedding is None:
                logger.warning("Embedding failed, falling back to keyword mode")
                mode = "keyword"
            else:
                results = await repo.search_clusters_semantic(
                    query_embedding=embedding,
                    limit=limit,
                    min_similarity=min_similarity,
                )

                return TopicSearchResponse(
                    results=[
                        TopicSearchResult(
                            cluster_id=r["cluster_id"],
                            label=r["label"],
                            keywords=r["keywords"].get("terms", []) if r["keywords"] else None,
                            article_count=r["article_count"],
                            similarity=r["similarity"],
                        )
                        for r in results
                    ],
                    query=q,
                    mode="semantic",
                    batch_id=str(batch_id) if batch_id else None,
                )

    # Keyword mode (fallback or explicit)
    keywords = [kw.strip() for kw in q.split() if kw.strip()]

    if not keywords:
        raise HTTPException(status_code=400, detail="At least one keyword required")

    results = await repo.search_clusters_by_keyword(
        keywords=keywords,
        limit=limit,
    )

    return TopicSearchResponse(
        results=[
            TopicSearchResult(
                cluster_id=r["cluster_id"],
                label=r["label"],
                keywords=r["keywords"].get("terms", []) if r["keywords"] else None,
                article_count=r["article_count"],
                match_count=r["match_count"],
            )
            for r in results
        ],
        query=q,
        mode="keyword",
        batch_id=str(batch_id) if batch_id else None,
    )


@router.get("/batches", response_model=BatchListResponse)
async def list_batches(
    status: Optional[str] = Query(None, pattern="^(running|completed|failed)$"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    List batch clustering runs.

    Shows recent batch runs with their status and statistics.
    Useful for monitoring and debugging.

    Examples:
        GET /topics/batches
        GET /topics/batches?status=completed
    """
    repo = BatchClusterRepository(db)

    batches = await repo.list_batches(status=status, limit=limit)

    return BatchListResponse(
        batches=[
            BatchInfo(
                batch_id=b["batch_id"],
                status=b["status"],
                article_count=b["article_count"],
                cluster_count=b["cluster_count"],
                noise_count=b["noise_count"],
                csai_score=b["csai_score"],
                started_at=b["started_at"],
                completed_at=b["completed_at"],
            )
            for b in batches
        ]
    )


@router.get("/similar/{article_id}", response_model=SimilarTopicsResponse)
async def find_similar_topics(
    article_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Find topic clusters similar to an article.

    Uses the article's embedding to find clusters with similar centroids.
    Returns clusters sorted by cosine similarity (highest first).

    Args:
        article_id: UUID of the article
        limit: Maximum clusters to return

    Note: Requires the article to have an embedding in article_analysis table.
    """
    repo = BatchClusterRepository(db)

    # First, get the article's embedding from article_analysis
    embedding_query = """
        SELECT embedding
        FROM article_analysis
        WHERE article_id = :article_id
          AND embedding IS NOT NULL
        LIMIT 1
    """

    from sqlalchemy import text
    result = await db.execute(text(embedding_query), {"article_id": str(article_id)})
    row = result.first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Article {article_id} not found or has no embedding"
        )

    embedding = row.embedding
    if not embedding:
        raise HTTPException(
            status_code=404,
            detail=f"Article {article_id} has no embedding"
        )

    # Find similar clusters
    similar = await repo.find_similar_clusters(
        embedding=embedding,
        limit=limit,
    )

    batch_id = await repo.get_latest_batch_id()

    return SimilarTopicsResponse(
        topics=[
            SimilarTopic(
                cluster_id=s["cluster_id"],
                label=s["label"],
                keywords=s["keywords"].get("terms", []) if s["keywords"] else None,
                article_count=s["article_count"],
                similarity=s["similarity"],
            )
            for s in similar
        ],
        batch_id=str(batch_id) if batch_id else None,
    )


@router.get("/article/{article_id}", response_model=ArticleTopicInfo)
async def get_article_topic(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get the topic cluster for a specific article.

    Returns which cluster the article belongs to in the latest batch.

    Args:
        article_id: UUID of the article

    Raises:
        404: If article is not in any cluster (may be noise or not processed)
    """
    repo = BatchClusterRepository(db)

    info = await repo.get_article_cluster(article_id)

    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Article {article_id} not found in any topic cluster"
        )

    return ArticleTopicInfo(
        cluster_id=info["cluster_id"],
        label=info["label"],
        keywords=info["keywords"].get("terms", []) if info["keywords"] else None,
        article_count=info["article_count"],
        distance=info["distance"],
        batch_id=info["batch_id"],
    )


@router.get("/{cluster_id}", response_model=TopicDetail)
async def get_topic(
    cluster_id: int,
    sample_limit: int = Query(10, ge=1, le=50, description="Sample articles to include"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get topic cluster details with sample articles.

    Returns full cluster metadata and a sample of the most representative
    articles (sorted by distance to centroid).

    Args:
        cluster_id: ID of the cluster
        sample_limit: Number of sample articles to include

    Raises:
        404: If cluster not found
    """
    repo = BatchClusterRepository(db)

    cluster = await repo.get_cluster_by_id(cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail=f"Topic cluster {cluster_id} not found")

    # Get sample articles
    articles = await repo.get_cluster_articles(cluster_id, limit=sample_limit)

    return TopicDetail(
        id=cluster.id,
        label=cluster.label,
        keywords=cluster.keywords.get("terms", []) if cluster.keywords else None,
        article_count=cluster.article_count,
        label_confidence=cluster.label_confidence,
        batch_id=str(cluster.batch_id),
        cluster_idx=cluster.cluster_idx,
        created_at=cluster.created_at,
        sample_articles=[
            TopicArticle(
                article_id=a["article_id"],
                title=a["title"],
                url=a["url"],
                distance=a["distance"],
                published_at=a["published_at"],
                assigned_at=a["assigned_at"],
            )
            for a in articles
        ],
    )


@router.post("/{cluster_id}/feedback", response_model=FeedbackResponse)
async def submit_topic_feedback(
    cluster_id: int,
    feedback: TopicFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Submit feedback to correct a cluster's label.

    This immediately updates the cluster label and records the feedback
    for future learning.

    Args:
        cluster_id: ID of the cluster to update
        feedback: New label and confidence

    Raises:
        404: If cluster not found
    """
    repo = BatchClusterRepository(db)

    # Verify cluster exists
    cluster = await repo.get_cluster_by_id(cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail=f"Topic cluster {cluster_id} not found")

    # Record feedback
    old_value = {"label": cluster.label, "confidence": cluster.label_confidence}
    new_value = {"label": feedback.label, "confidence": feedback.confidence}

    feedback_id = await repo.submit_feedback(
        cluster_id=cluster_id,
        feedback_type="label_correction",
        old_value=old_value,
        new_value=new_value,
        created_by=user_id,
    )

    # Update the cluster label
    await repo.update_cluster_label(
        cluster_id=cluster_id,
        label=feedback.label,
        confidence=feedback.confidence,
    )

    logger.info(
        f"User {user_id} corrected cluster {cluster_id} label: "
        f"'{cluster.label}' -> '{feedback.label}'"
    )

    return FeedbackResponse(
        success=True,
        feedback_id=feedback_id,
        message=f"Label updated to '{feedback.label}'",
    )
