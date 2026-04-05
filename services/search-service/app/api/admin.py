"""
Admin API endpoints for search service management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text, case
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.redis_client import get_redis_client
from app.services.indexing_service import IndexingService
from app.models.search import ArticleIndex, SearchHistory, SearchAnalytics
from app.workers.celery_app import celery_app

router = APIRouter()


@router.post("/reindex")
async def reindex_articles(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Reindex all articles from Feed Service.

    Requires authentication. This will:
    1. Delete all existing article indexes
    2. Fetch all articles from Feed Service
    3. Fetch sentiment/entity data from Content Analysis Service
    4. Create full-text search indexes

    Returns:
        Dict with reindex statistics
    """
    indexing_service = IndexingService(db)

    try:
        result = await indexing_service.reindex_all()
        return {
            "status": "success",
            "message": "Reindex completed successfully",
            "stats": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reindex failed: {str(e)}"
        )


@router.post("/sync")
async def sync_articles(
    batch_size: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Sync new articles from Feed Service.

    Requires authentication. This will:
    1. Fetch articles updated since last sync
    2. Index new articles
    3. Update existing articles

    Args:
        batch_size: Number of articles to fetch per batch (default: 100)

    Returns:
        Dict with sync statistics
    """
    indexing_service = IndexingService(db)

    try:
        result = await indexing_service.sync_articles(batch_size)
        return {
            "status": "success",
            "message": "Sync completed successfully",
            "stats": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/stats/index")
async def get_index_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get article index statistics.

    Returns:
        Dict with index statistics including:
        - Total indexed articles
        - Articles by source
        - Articles by sentiment
        - Index size estimate
        - Recent indexing activity
    """
    try:
        # Total indexed articles
        total_result = await db.execute(
            select(func.count(ArticleIndex.id))
        )
        total_indexed = total_result.scalar() or 0

        # Articles by source (top 10)
        source_result = await db.execute(
            select(
                ArticleIndex.source,
                func.count(ArticleIndex.id).label('count')
            )
            .group_by(ArticleIndex.source)
            .order_by(func.count(ArticleIndex.id).desc())
            .limit(10)
        )
        by_source = [
            {"source": row.source, "count": row.count}
            for row in source_result.all()
        ]

        # Articles by sentiment
        sentiment_result = await db.execute(
            select(
                ArticleIndex.sentiment,
                func.count(ArticleIndex.id).label('count')
            )
            .group_by(ArticleIndex.sentiment)
            .order_by(func.count(ArticleIndex.id).desc())
        )
        by_sentiment = [
            {"sentiment": row.sentiment or "unknown", "count": row.count}
            for row in sentiment_result.all()
        ]

        # Recent indexing activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_result = await db.execute(
            select(func.count(ArticleIndex.id))
            .where(ArticleIndex.indexed_at >= yesterday)
        )
        recent_indexed = recent_result.scalar() or 0

        # Database size estimate (PostgreSQL specific)
        size_result = await db.execute(
            text("SELECT pg_size_pretty(pg_total_relation_size('article_indexes'))")
        )
        index_size = size_result.scalar() or "Unknown"

        return {
            "total_indexed": total_indexed,
            "by_source": by_source,
            "by_sentiment": by_sentiment,
            "recent_24h": recent_indexed,
            "index_size": index_size,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get index statistics: {str(e)}"
        )


@router.get("/stats/queries")
async def get_query_statistics(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Get search query statistics.

    Args:
        limit: Number of top queries to return (default: 20)

    Returns:
        Dict with query statistics including:
        - Top queries by frequency
        - Recent search activity
        - Average results per query
    """
    try:
        # Top queries from search_analytics
        top_queries_result = await db.execute(
            select(
                SearchAnalytics.query,
                func.sum(SearchAnalytics.hits).label('total_hits')
            )
            .group_by(SearchAnalytics.query)
            .order_by(func.sum(SearchAnalytics.hits).desc())
            .limit(limit)
        )
        top_queries = [
            {"query": row.query, "hits": row.total_hits}
            for row in top_queries_result.all()
        ]

        # Total searches (from history)
        total_result = await db.execute(
            select(func.count(SearchHistory.id))
        )
        total_searches = total_result.scalar() or 0

        # Searches in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_result = await db.execute(
            select(func.count(SearchHistory.id))
            .where(SearchHistory.created_at >= yesterday)
        )
        recent_searches = recent_result.scalar() or 0

        # Average results count
        avg_result = await db.execute(
            select(func.avg(SearchHistory.results_count))
        )
        avg_results = float(avg_result.scalar() or 0)

        return {
            "top_queries": top_queries,
            "total_searches": total_searches,
            "recent_24h": recent_searches,
            "avg_results_per_query": round(avg_results, 2),
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get query statistics: {str(e)}"
        )


@router.get("/stats/cache")
async def get_cache_statistics():
    """
    Get Redis cache statistics.

    Returns:
        Dict with cache statistics including:
        - Total keys
        - Memory usage
        - Hit/miss rate (if available)
        - Cache info
    """
    try:
        redis_client = await get_redis_client()

        # Get Redis info
        info = await redis_client.info('stats')
        memory_info = await redis_client.info('memory')

        # Get number of keys (search-related)
        keys_count = await redis_client.dbsize()

        # Calculate hit rate if stats available
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total_requests = hits + misses
        hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_keys": keys_count,
            "memory_used": memory_info.get('used_memory_human', 'Unknown'),
            "memory_peak": memory_info.get('used_memory_peak_human', 'Unknown'),
            "hit_rate_percent": round(hit_rate, 2),
            "total_hits": hits,
            "total_misses": misses,
            "evicted_keys": info.get('evicted_keys', 0),
            "expired_keys": info.get('expired_keys', 0),
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.get("/stats/celery")
async def get_celery_statistics():
    """
    Get Celery worker statistics.

    Returns:
        Dict with Celery statistics including:
        - Active workers
        - Registered tasks
        - Queue sizes
        - Worker health
    """
    try:
        # Get active workers
        inspect = celery_app.control.inspect()

        # Active workers
        active_workers = inspect.active()
        worker_count = len(active_workers) if active_workers else 0

        # Registered tasks
        registered_tasks = inspect.registered()
        task_count = 0
        if registered_tasks:
            for worker, tasks in registered_tasks.items():
                task_count = len(tasks)
                break  # Just count from first worker

        # Stats from workers
        stats = inspect.stats()
        worker_stats = []
        if stats:
            for worker_name, worker_stat in stats.items():
                worker_stats.append({
                    "worker": worker_name,
                    "pool": worker_stat.get('pool', {}).get('max-concurrency', 0),
                    "total_tasks": worker_stat.get('total', {})
                })

        # Queue sizes (requires broker inspection)
        # Note: This is a simplified version, actual queue size needs broker-specific logic
        reserved = inspect.reserved()
        reserved_count = 0
        if reserved:
            for worker, tasks in reserved.items():
                reserved_count += len(tasks)

        return {
            "active_workers": worker_count,
            "registered_tasks": task_count,
            "reserved_tasks": reserved_count,
            "worker_stats": worker_stats,
            "status": "healthy" if worker_count > 0 else "no_workers",
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Celery statistics: {str(e)}"
        )


@router.get("/stats/performance")
async def get_performance_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get search performance statistics.

    Returns:
        Dict with performance metrics including:
        - Average query execution time
        - Slowest queries
        - Query distribution by result count
    """
    try:
        # For now, we don't have execution time tracking in the database
        # This would require adding an execution_time column to SearchHistory
        # Returning placeholder data for frontend compatibility

        # Most popular queries (as a proxy for performance-critical queries)
        popular_queries_result = await db.execute(
            select(
                SearchAnalytics.query,
                SearchAnalytics.hits
            )
            .order_by(SearchAnalytics.hits.desc())
            .limit(10)
        )
        slow_queries = [
            {"query": row.query, "hits": row.hits}
            for row in popular_queries_result.all()
        ]

        # Placeholder avg time (would need execution_time column)
        avg_time = 0.0

        # Query distribution by result count
        distribution_result = await db.execute(
            select(
                case(
                    (SearchHistory.results_count == 0, '0 results'),
                    (SearchHistory.results_count.between(1, 10), '1-10 results'),
                    (SearchHistory.results_count.between(11, 50), '11-50 results'),
                    (SearchHistory.results_count.between(51, 100), '51-100 results'),
                    else_='100+ results'
                ).label('range'),
                func.count(SearchHistory.id).label('count')
            )
            .group_by(text('range'))
        )
        distribution = [
            {"range": row.range, "count": row.count}
            for row in distribution_result.all()
        ]

        return {
            "avg_execution_time_ms": round(avg_time, 2),
            "slowest_queries": slow_queries,
            "result_distribution": distribution,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance statistics: {str(e)}"
        )
