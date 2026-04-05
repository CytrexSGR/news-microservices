# services/clustering-service/app/api/v1/clusters.py
"""Cluster API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.db.session import get_db
from app.schemas.cluster import (
    ArticleClusterRequest,
    ArticleClusterResponse,
    ClusterArticle,
    ClusterArticlesResponse,
    ClusterDetail,
    ClusterListResponse,
    ClusterSummary,
    PaginationMeta,
)
from app.services.cluster_repository import ClusterRepository
from app.services.clustering import ClusteringService
from app.services.event_publisher import get_event_publisher

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/articles", response_model=ArticleClusterResponse)
async def assign_article_to_cluster(
    request: ArticleClusterRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Assign an article to a cluster.

    If no matching cluster exists, creates a new one.
    """
    repo = ClusterRepository(db)
    clustering_service = ClusteringService()

    # Get active clusters
    active_clusters = await repo.get_active_clusters()

    # Find matching cluster
    match = clustering_service.find_matching_cluster(
        embedding=request.embedding,
        active_clusters=active_clusters,
    )

    # Prepare entities
    entities = None
    if request.entities:
        entities = [e.model_dump() for e in request.entities[:5]]

    if match:
        cluster_id = match["cluster_id"]
        similarity = match["similarity"]

        cluster_data = next(
            (c for c in active_clusters if c["id"] == cluster_id),
            None
        )
        if cluster_data is None:
            raise HTTPException(status_code=500, detail="Cluster not found")

        new_count = cluster_data["article_count"] + 1
        new_centroid = clustering_service.update_centroid(
            current_centroid=cluster_data["centroid"],
            new_vector=request.embedding,
            article_count=new_count,
        )

        await repo.update_cluster(
            cluster_id=cluster_id,
            new_centroid=new_centroid,
            new_article_count=new_count,
            entities=entities,
        )

        return ArticleClusterResponse(
            cluster_id=cluster_id,
            is_new_cluster=False,
            similarity_score=similarity,
            cluster_article_count=new_count,
        )

    else:
        cluster_id = await repo.create_cluster(
            title=request.title,
            centroid_vector=request.embedding,
            first_article_id=request.article_id,
            entities=entities,
        )

        return ArticleClusterResponse(
            cluster_id=cluster_id,
            is_new_cluster=True,
            similarity_score=1.0,
            cluster_article_count=1,
        )


@router.get("", response_model=ClusterListResponse)
async def list_clusters(
    status: str = Query("active", pattern="^(active|archived|all)$"),
    min_articles: int = Query(2, ge=1),
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    List clusters with pagination.

    Args:
        status: Filter by cluster status
        min_articles: Minimum article count
        hours: Time window in hours
        limit: Page size
        offset: Page offset
    """
    repo = ClusterRepository(db)

    clusters, total = await repo.get_clusters_paginated(
        status=status,
        min_articles=min_articles,
        hours=hours,
        limit=limit,
        offset=offset,
    )

    return ClusterListResponse(
        clusters=[
            ClusterSummary(
                id=c.id,
                title=c.title,
                article_count=c.article_count,
                status=c.status,
                tension_score=c.tension_score,
                is_breaking=c.is_breaking,
                first_seen_at=c.first_seen_at,
                last_updated_at=c.last_updated_at,
            )
            for c in clusters
        ],
        pagination={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(clusters) < total,
        },
    )


@router.get("/{cluster_id}", response_model=ClusterDetail)
async def get_cluster(
    cluster_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get cluster details by ID."""
    repo = ClusterRepository(db)
    cluster = await repo.get_cluster_by_id(cluster_id)

    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")

    return ClusterDetail(
        id=cluster.id,
        title=cluster.title,
        article_count=cluster.article_count,
        status=cluster.status,
        tension_score=cluster.tension_score,
        is_breaking=cluster.is_breaking,
        first_seen_at=cluster.first_seen_at,
        last_updated_at=cluster.last_updated_at,
        summary=cluster.summary,
        centroid_vector=cluster.centroid_vector,
        primary_entities=cluster.primary_entities,
        burst_detected_at=cluster.burst_detected_at,
    )


@router.get("/{cluster_id}/articles", response_model=ClusterArticlesResponse)
async def get_cluster_articles(
    cluster_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get articles belonging to a cluster.

    Args:
        cluster_id: Cluster UUID
        limit: Page size (max 100)
        offset: Page offset

    Returns:
        Paginated list of articles in the cluster
    """
    repo = ClusterRepository(db)

    # Verify cluster exists
    cluster = await repo.get_cluster_by_id(cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")

    articles, total = await repo.get_cluster_articles(
        cluster_id=cluster_id,
        limit=limit,
        offset=offset,
    )

    return ClusterArticlesResponse(
        cluster_id=cluster_id,
        articles=[ClusterArticle(**a) for a in articles],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(articles) < total,
        ),
    )
