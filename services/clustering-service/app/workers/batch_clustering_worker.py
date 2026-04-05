# services/clustering-service/app/workers/batch_clustering_worker.py
"""Celery worker for batch UMAP+HDBSCAN clustering.

Runs periodically to recompute high-quality topic clusters using:
1. Load all embeddings from article_analysis table
2. Apply UMAP dimensionality reduction (1536D -> 10D)
3. Run HDBSCAN clustering (automatic cluster detection)
4. Compute cluster centroids in original embedding space
5. Extract keywords per cluster using TF-IDF on titles
6. Store results in batch_clusters tables

This worker runs in parallel with the real-time Single-Pass clustering:
- Single-Pass: Handles real-time burst detection (ms latency)
- Batch: Provides high-quality topic taxonomy (1-2h interval)

Reference: docs/research/2026-01-05-csai-topic-discovery.md
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import numpy as np
from celery import Celery

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "batch_clustering",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # Don't prefetch batch tasks
    # Queue configuration
    task_default_queue="batch-clustering",
    task_routes={
        "app.workers.batch_clustering_worker.recompute_clusters": {"queue": "batch-clustering"},
    },
)

# Celery beat schedule for periodic execution
celery_app.conf.beat_schedule = {
    "recompute-clusters": {
        "task": "app.workers.batch_clustering_worker.recompute_clusters",
        "schedule": settings.BATCH_CLUSTERING_INTERVAL_HOURS * 3600,  # Convert hours to seconds
    },
}


async def _load_embeddings_from_db() -> List[Dict[str, Any]]:
    """
    Load all articles with embeddings from article_analysis table.

    Uses asyncpg for efficient bulk loading. The embeddings are stored
    as pgvector type which is returned as text representation.

    Returns:
        List of dicts with article_id, title, embedding, created_at
    """
    import asyncpg

    logger.info("Loading embeddings from database...")

    # Convert async DATABASE_URL to sync format for asyncpg
    # settings.DATABASE_URL is for SQLAlchemy (postgresql+asyncpg://...)
    # asyncpg needs postgresql://...
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(db_url)

    try:
        # Build query with optional limit for memory-constrained environments
        limit_clause = ""
        if settings.BATCH_MAX_ARTICLES > 0:
            limit_clause = f"ORDER BY fi.created_at DESC LIMIT {settings.BATCH_MAX_ARTICLES}"
            logger.info(f"Limiting to {settings.BATCH_MAX_ARTICLES} most recent articles")

        query = f"""
            SELECT
                aa.article_id,
                fi.title,
                aa.embedding::text as embedding_str,
                fi.created_at
            FROM article_analysis aa
            JOIN feed_items fi ON aa.article_id = fi.id
            WHERE aa.embedding IS NOT NULL
            {limit_clause}
        """

        rows = await conn.fetch(query)
        logger.info(f"Fetched {len(rows)} rows from database")

        articles = []
        parse_errors = 0

        for row in rows:
            try:
                # Parse pgvector text format: "[0.1,0.2,...]"
                emb_str = row["embedding_str"]
                if emb_str is None:
                    continue

                # Remove brackets and parse floats
                emb_str = emb_str.strip("[]")
                embedding = [float(x) for x in emb_str.split(",")]

                articles.append({
                    "article_id": str(row["article_id"]),
                    "title": row["title"] or "",
                    "embedding": embedding,
                    "created_at": row["created_at"],
                })
            except (ValueError, AttributeError) as e:
                parse_errors += 1
                if parse_errors <= 5:
                    logger.warning(f"Failed to parse embedding for article {row['article_id']}: {e}")

        if parse_errors > 0:
            logger.warning(f"Total embedding parse errors: {parse_errors}")

        logger.info(f"Loaded {len(articles)} articles with valid embeddings")
        if articles:
            logger.info(f"Embedding dimension: {len(articles[0]['embedding'])}")

        return articles

    finally:
        await conn.close()


def _run_umap_reduction(
    embeddings: np.ndarray,
    n_components: int,
    n_neighbors: int,
    min_dist: float,
) -> np.ndarray:
    """
    Reduce embedding dimensionality using UMAP.

    UMAP (Uniform Manifold Approximation and Projection) preserves
    local structure while reducing dimensionality, making clustering
    more effective in the reduced space.

    Args:
        embeddings: Original embeddings (n_samples, 1536)
        n_components: Target dimensions (default: 10)
        n_neighbors: UMAP neighborhood size (default: 15)
        min_dist: Minimum distance between points (default: 0.1)

    Returns:
        Reduced embeddings (n_samples, n_components)
    """
    import umap

    logger.info(
        f"Running UMAP reduction: {embeddings.shape[1]}D -> {n_components}D "
        f"(n_neighbors={n_neighbors}, min_dist={min_dist})"
    )

    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="cosine",
        random_state=42,
        verbose=False,
    )

    reduced = reducer.fit_transform(embeddings)
    logger.info(f"UMAP complete: {embeddings.shape} -> {reduced.shape}")

    return reduced


def _run_hdbscan_clustering(
    embeddings: np.ndarray,
    min_cluster_size: int,
) -> np.ndarray:
    """
    Cluster embeddings using HDBSCAN.

    HDBSCAN (Hierarchical Density-Based Spatial Clustering) automatically
    determines the number of clusters and identifies noise points.

    Args:
        embeddings: Reduced embeddings from UMAP
        min_cluster_size: Minimum points to form a cluster

    Returns:
        Cluster labels (-1 = noise)
    """
    import hdbscan

    logger.info(f"Running HDBSCAN clustering (min_cluster_size={min_cluster_size})...")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=5,
        metric="euclidean",
        cluster_selection_method="eom",
    )

    labels = clusterer.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    noise_pct = n_noise / len(labels) * 100

    logger.info(f"HDBSCAN complete: {n_clusters} clusters, {n_noise} noise points ({noise_pct:.1f}%)")

    return labels


def _compute_centroids(
    embeddings: np.ndarray,
    labels: np.ndarray,
) -> Dict[int, np.ndarray]:
    """
    Compute cluster centroids from original (full-dimensional) embeddings.

    The centroids are computed in the original 1536D space (not the
    UMAP-reduced space) to enable accurate similarity lookups.

    Args:
        embeddings: Original embeddings (n_samples, 1536)
        labels: Cluster labels from HDBSCAN

    Returns:
        Dict mapping cluster_idx -> centroid vector
    """
    logger.info("Computing cluster centroids in original embedding space...")

    centroids = {}
    unique_labels = set(labels)

    for label in unique_labels:
        if label == -1:  # Skip noise
            continue

        mask = labels == label
        cluster_embeddings = embeddings[mask]
        centroids[label] = np.mean(cluster_embeddings, axis=0)

    logger.info(f"Computed {len(centroids)} centroids")
    return centroids


def _extract_keywords(
    articles: List[Dict],
    labels: np.ndarray,
    cluster_idx: int,
    top_n: int = 5,
) -> List[str]:
    """
    Extract top keywords for a cluster using TF-IDF on article titles.

    Args:
        articles: List of article dicts with 'title' field
        labels: Cluster labels
        cluster_idx: Target cluster index
        top_n: Number of keywords to extract

    Returns:
        List of top keywords
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    # Get titles for this cluster
    cluster_titles = [
        articles[i]["title"]
        for i, label in enumerate(labels)
        if label == cluster_idx and articles[i]["title"]
    ]

    if len(cluster_titles) < 3:
        return []

    try:
        vectorizer = TfidfVectorizer(
            max_features=50,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,  # Require term in at least 2 docs
        )

        tfidf = vectorizer.fit_transform(cluster_titles)
        feature_names = vectorizer.get_feature_names_out()

        # Sum TF-IDF scores across all documents to find top terms
        scores = np.asarray(tfidf.sum(axis=0)).flatten()
        top_indices = scores.argsort()[-top_n:][::-1]

        return [feature_names[i] for i in top_indices]

    except Exception as e:
        logger.debug(f"Keyword extraction failed for cluster {cluster_idx}: {e}")
        return []


def _get_cluster_label(
    articles: List[Dict],
    labels: np.ndarray,
    cluster_idx: int,
    centroid: np.ndarray,
    embeddings: np.ndarray,
) -> str:
    """
    Generate a label for a cluster using the most representative article.

    The most representative article is the one closest to the centroid.

    Args:
        articles: List of article dicts
        labels: Cluster labels
        cluster_idx: Target cluster index
        centroid: Cluster centroid vector
        embeddings: Original embeddings

    Returns:
        Cluster label (truncated title of most representative article)
    """
    # Find articles in this cluster
    cluster_indices = [i for i, label in enumerate(labels) if label == cluster_idx]

    if not cluster_indices:
        return f"Cluster {cluster_idx}"

    # Find article closest to centroid (most representative)
    best_idx = None
    best_similarity = -1

    for idx in cluster_indices:
        article_emb = embeddings[idx]
        # Cosine similarity
        similarity = np.dot(article_emb, centroid) / (
            np.linalg.norm(article_emb) * np.linalg.norm(centroid)
        )
        if similarity > best_similarity:
            best_similarity = similarity
            best_idx = idx

    if best_idx is not None and articles[best_idx]["title"]:
        # Truncate to 100 chars
        return articles[best_idx]["title"][:100]

    return f"Cluster {cluster_idx}"


async def _store_batch_results(
    batch_id: UUID,
    articles: List[Dict],
    labels: np.ndarray,
    centroids: Dict[int, np.ndarray],
    embeddings: np.ndarray,
) -> Tuple[int, int]:
    """
    Store batch clustering results in database.

    Creates:
    - cluster_batches record
    - batch_clusters records with centroids
    - batch_article_clusters mappings

    Args:
        batch_id: Unique batch identifier
        articles: List of article dicts
        labels: Cluster labels from HDBSCAN
        centroids: Cluster centroids
        embeddings: Original embeddings for distance calculation

    Returns:
        Tuple of (cluster_count, noise_count)
    """
    import asyncpg

    logger.info(f"Storing batch results for {batch_id}...")

    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)

    try:
        n_clusters = len(centroids)
        n_noise = list(labels).count(-1)

        # Create batch record
        await conn.execute(
            """
            INSERT INTO cluster_batches (batch_id, status, article_count, cluster_count, noise_count, started_at)
            VALUES ($1, 'running', $2, $3, $4, NOW())
            """,
            batch_id,
            len(articles),
            n_clusters,
            n_noise,
        )

        # Store clusters
        cluster_id_map = {}  # cluster_idx -> database id

        for cluster_idx, centroid in centroids.items():
            # Extract keywords
            keywords = _extract_keywords(articles, labels, cluster_idx)

            # Generate label
            label = _get_cluster_label(articles, labels, cluster_idx, centroid, embeddings)

            # Count articles in cluster
            article_count = sum(1 for l in labels if l == cluster_idx)

            # Convert centroid to pgvector format
            centroid_str = "[" + ",".join(str(float(f)) for f in centroid) + "]"

            # Convert keywords to JSON string for asyncpg
            import json
            keywords_json = json.dumps({"terms": keywords})

            # Insert cluster
            row = await conn.fetchrow(
                """
                INSERT INTO batch_clusters (batch_id, cluster_idx, label, keywords, article_count, centroid_vec)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6::vector)
                RETURNING id
                """,
                batch_id,
                cluster_idx,
                label,
                keywords_json,
                article_count,
                centroid_str,
            )

            cluster_id_map[cluster_idx] = row["id"]

        logger.info(f"Stored {len(cluster_id_map)} clusters")

        # Store article assignments (skip noise)
        assignments_stored = 0

        for i, (article, label) in enumerate(zip(articles, labels)):
            if label == -1:  # Skip noise
                continue

            cluster_db_id = cluster_id_map.get(label)
            if cluster_db_id is None:
                continue

            # Compute distance to centroid (cosine distance)
            article_emb = embeddings[i]
            centroid = centroids[label]
            similarity = np.dot(article_emb, centroid) / (
                np.linalg.norm(article_emb) * np.linalg.norm(centroid)
            )
            distance = 1 - similarity

            await conn.execute(
                """
                INSERT INTO batch_article_clusters (article_id, cluster_id, batch_id, distance_to_centroid)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (article_id) DO UPDATE
                SET cluster_id = $2, batch_id = $3, distance_to_centroid = $4, assigned_at = NOW()
                """,
                UUID(article["article_id"]),
                cluster_db_id,
                batch_id,
                float(distance),
            )
            assignments_stored += 1

        logger.info(f"Stored {assignments_stored} article assignments")

        # Mark batch complete
        await conn.execute(
            """
            UPDATE cluster_batches
            SET status = 'completed', completed_at = NOW()
            WHERE batch_id = $1
            """,
            batch_id,
        )

        return n_clusters, n_noise

    except Exception as e:
        # Mark batch as failed
        await conn.execute(
            """
            UPDATE cluster_batches
            SET status = 'failed', completed_at = NOW()
            WHERE batch_id = $1
            """,
            batch_id,
        )
        raise

    finally:
        await conn.close()


async def _recompute_clusters_async() -> Dict[str, Any]:
    """
    Async implementation of batch clustering.

    Full pipeline:
    1. Load embeddings from article_analysis
    2. Run UMAP dimensionality reduction
    3. Run HDBSCAN clustering
    4. Compute centroids
    5. Extract keywords
    6. Store results

    Returns:
        Dict with batch_id, cluster_count, noise_count, article_count
    """
    batch_id = uuid4()
    logger.info(f"Starting batch clustering run: {batch_id}")

    start_time = datetime.now(timezone.utc)

    # Step 1: Load embeddings
    articles = await _load_embeddings_from_db()

    if len(articles) < 100:
        logger.warning(f"Only {len(articles)} articles with embeddings, skipping batch")
        return {
            "batch_id": str(batch_id),
            "status": "skipped",
            "reason": f"Insufficient articles ({len(articles)})",
        }

    embeddings = np.array([a["embedding"] for a in articles])
    logger.info(f"Loaded {len(articles)} articles with {embeddings.shape[1]}D embeddings")

    # Step 2: UMAP reduction
    reduced = _run_umap_reduction(
        embeddings,
        n_components=settings.BATCH_UMAP_COMPONENTS,
        n_neighbors=settings.BATCH_UMAP_NEIGHBORS,
        min_dist=settings.BATCH_UMAP_MIN_DIST,
    )

    # Step 3: HDBSCAN clustering
    labels = _run_hdbscan_clustering(
        reduced,
        min_cluster_size=settings.BATCH_MIN_CLUSTER_SIZE,
    )

    # Step 4: Compute centroids (in original space)
    centroids = _compute_centroids(embeddings, labels)

    # Step 5 & 6: Store results (includes keyword extraction)
    n_clusters, n_noise = await _store_batch_results(
        batch_id=batch_id,
        articles=articles,
        labels=labels,
        centroids=centroids,
        embeddings=embeddings,
    )

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(
        f"Batch clustering complete: batch_id={batch_id}, "
        f"clusters={n_clusters}, noise={n_noise}, duration={duration:.1f}s"
    )

    return {
        "batch_id": str(batch_id),
        "status": "completed",
        "cluster_count": n_clusters,
        "noise_count": n_noise,
        "article_count": len(articles),
        "duration_seconds": duration,
    }


@celery_app.task(bind=True, name="app.workers.batch_clustering_worker.recompute_clusters")
def recompute_clusters(self) -> Dict[str, Any]:
    """
    Celery task: Recompute all topic clusters using UMAP+HDBSCAN.

    This task runs every BATCH_CLUSTERING_INTERVAL_HOURS (default: 2h).
    It can also be triggered manually via:
        recompute_clusters.delay()

    Returns:
        Dict with batch results (batch_id, cluster_count, etc.)
    """
    import asyncio

    logger.info("Celery task started: recompute_clusters")

    try:
        # Run async pipeline in sync context
        result = asyncio.run(_recompute_clusters_async())
        logger.info(f"Celery task completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Celery task failed: {e}", exc_info=True)
        raise


# Export for manual triggering
__all__ = ["celery_app", "recompute_clusters"]
