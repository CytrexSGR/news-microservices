"""Database Query Tools for NEXUS Agent.

Provides read-only access to articles, feeds, and analysis data.
Uses actual database schema: feed_items, feeds, article_analysis.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.base import BaseTool, ToolResult
from app.db.session import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


class ArticleSearchTool(BaseTool):
    """Search and retrieve articles from the database."""

    name: str = "article_search"
    description: str = (
        "Search for news articles in the database. "
        "Can search by title, content keywords, or date range. "
        "Returns article titles, descriptions, links, and publication dates."
    )

    async def execute(
        self,
        query: Optional[str] = None,
        days_back: int = 7,
        limit: int = 10,
        feed_id: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Search articles in the database (feed_items table).

        Args:
            query: Optional search term for title/content
            days_back: Number of days to look back (default 7)
            limit: Maximum results to return (default 10, max 50)
            feed_id: Optional filter by specific feed ID (UUID)
            **kwargs: Additional parameters (ignored)

        Returns:
            ToolResult with list of matching articles
        """
        # Validate limit
        limit = min(max(1, limit), 50)
        days_back = min(max(1, days_back), 90)

        try:
            async with AsyncSessionLocal() as session:
                # Build the query - using feed_items table
                sql_parts = [
                    """
                    SELECT
                        fi.id,
                        fi.title,
                        fi.link,
                        fi.published_at,
                        COALESCE(fi.description, LEFT(fi.content, 300)) as summary,
                        fi.author,
                        fi.source_type,
                        f.name as feed_name,
                        f.url as feed_url
                    FROM feed_items fi
                    LEFT JOIN feeds f ON fi.feed_id = f.id
                    WHERE fi.published_at >= :since_date
                    """
                ]
                params: Dict[str, Any] = {
                    "since_date": datetime.now(timezone.utc) - timedelta(days=days_back),
                    "limit": limit,
                }

                if query:
                    sql_parts.append(
                        "AND (fi.title ILIKE :query OR fi.description ILIKE :query OR fi.content ILIKE :query)"
                    )
                    params["query"] = f"%{query}%"

                if feed_id:
                    sql_parts.append("AND fi.feed_id = :feed_id")
                    params["feed_id"] = feed_id

                sql_parts.append("ORDER BY fi.published_at DESC LIMIT :limit")

                sql = " ".join(sql_parts)
                result = await session.execute(text(sql), params)
                rows = result.fetchall()

                articles = [
                    {
                        "id": str(row.id),
                        "title": row.title,
                        "link": row.link,
                        "published_at": row.published_at.isoformat() if row.published_at else None,
                        "summary": row.summary[:300] if row.summary else None,
                        "author": row.author,
                        "source_type": row.source_type,
                        "feed_name": row.feed_name,
                    }
                    for row in rows
                ]

                logger.info(
                    "article_search_success",
                    query=query,
                    days_back=days_back,
                    results_count=len(articles),
                )

                return ToolResult(
                    success=True,
                    data={
                        "articles": articles,
                        "total_count": len(articles),
                        "search_params": {
                            "query": query,
                            "days_back": days_back,
                            "limit": limit,
                            "feed_id": feed_id,
                        },
                    },
                    tool_name=self.name,
                )

        except Exception as exc:
            logger.error(
                "article_search_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Database error: {str(exc)}",
                tool_name=self.name,
            )


class FeedListTool(BaseTool):
    """List and search feeds in the system."""

    name: str = "feed_list"
    description: str = (
        "List available news feeds in the system. "
        "Shows feed names, URLs, status, health scores, and article counts."
    )

    async def execute(
        self,
        active_only: bool = True,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """
        List feeds from the database.

        Args:
            active_only: Only return active feeds (default True)
            limit: Maximum results (default 20, max 100)
            **kwargs: Additional parameters (ignored)

        Returns:
            ToolResult with list of feeds
        """
        limit = min(max(1, limit), 100)

        try:
            async with AsyncSessionLocal() as session:
                sql_parts = [
                    """
                    SELECT
                        f.id,
                        f.name,
                        f.url,
                        f.description,
                        f.is_active,
                        f.status,
                        f.health_score,
                        f.total_items,
                        f.items_last_24h,
                        f.last_fetched_at,
                        f.created_at
                    FROM feeds f
                    WHERE 1=1
                    """
                ]
                params: Dict[str, Any] = {"limit": limit}

                if active_only:
                    sql_parts.append("AND f.is_active = true")

                sql_parts.append(
                    "ORDER BY f.total_items DESC LIMIT :limit"
                )

                sql = " ".join(sql_parts)
                result = await session.execute(text(sql), params)
                rows = result.fetchall()

                feeds = [
                    {
                        "id": str(row.id),
                        "name": row.name,
                        "url": row.url,
                        "description": row.description,
                        "is_active": row.is_active,
                        "status": row.status,
                        "health_score": row.health_score,
                        "total_items": row.total_items,
                        "items_last_24h": row.items_last_24h,
                        "last_fetched_at": row.last_fetched_at.isoformat() if row.last_fetched_at else None,
                    }
                    for row in rows
                ]

                logger.info(
                    "feed_list_success",
                    active_only=active_only,
                    results_count=len(feeds),
                )

                return ToolResult(
                    success=True,
                    data={
                        "feeds": feeds,
                        "total_count": len(feeds),
                    },
                    tool_name=self.name,
                )

        except Exception as exc:
            logger.error(
                "feed_list_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Database error: {str(exc)}",
                tool_name=self.name,
            )


class ArticleAnalysisTool(BaseTool):
    """Retrieve article analysis data."""

    name: str = "article_analysis"
    description: str = (
        "Get analysis data for articles including relevance scores, "
        "triage results, and tiered analysis. Shows processing status and insights."
    )

    async def execute(
        self,
        article_id: Optional[str] = None,
        limit: int = 10,
        successful_only: bool = True,
        **kwargs,
    ) -> ToolResult:
        """
        Get article analysis from the database.

        Args:
            article_id: Specific article ID (UUID) to get analysis for
            limit: Maximum results if no article_id (default 10)
            successful_only: Only return successful analyses (default True)
            **kwargs: Additional parameters (ignored)

        Returns:
            ToolResult with analysis data
        """
        limit = min(max(1, limit), 50)

        try:
            async with AsyncSessionLocal() as session:
                if article_id:
                    sql = """
                        SELECT
                            aa.id,
                            aa.article_id,
                            fi.title as article_title,
                            fi.link as article_link,
                            aa.pipeline_version,
                            aa.success,
                            aa.relevance_score,
                            aa.score_breakdown,
                            aa.triage_results,
                            aa.tier1_results,
                            aa.tier2_results,
                            aa.tier3_results,
                            aa.metrics,
                            aa.error_message,
                            aa.created_at
                        FROM article_analysis aa
                        JOIN feed_items fi ON aa.article_id = fi.id
                        WHERE aa.article_id = :article_id
                    """
                    result = await session.execute(
                        text(sql), {"article_id": article_id}
                    )
                else:
                    sql_parts = [
                        """
                        SELECT
                            aa.id,
                            aa.article_id,
                            fi.title as article_title,
                            fi.link as article_link,
                            aa.pipeline_version,
                            aa.success,
                            aa.relevance_score,
                            aa.score_breakdown,
                            aa.triage_results,
                            aa.tier1_results,
                            aa.tier2_results,
                            aa.tier3_results,
                            aa.metrics,
                            aa.error_message,
                            aa.created_at
                        FROM article_analysis aa
                        JOIN feed_items fi ON aa.article_id = fi.id
                        WHERE 1=1
                        """
                    ]
                    params = {"limit": limit}

                    if successful_only:
                        sql_parts.append("AND aa.success = true")

                    sql_parts.append("ORDER BY aa.created_at DESC LIMIT :limit")

                    sql = " ".join(sql_parts)
                    result = await session.execute(text(sql), params)

                rows = result.fetchall()

                analyses = []
                for row in rows:
                    analysis = {
                        "id": str(row.id),
                        "article_id": str(row.article_id),
                        "article_title": row.article_title,
                        "article_link": row.article_link,
                        "pipeline_version": row.pipeline_version,
                        "success": row.success,
                        "relevance_score": row.relevance_score,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                    }

                    # Add JSONB fields if they have data
                    if row.score_breakdown:
                        analysis["score_breakdown"] = row.score_breakdown
                    if row.triage_results:
                        analysis["triage_summary"] = _summarize_triage(row.triage_results)
                    if row.tier1_results:
                        analysis["tier1_summary"] = _summarize_tier(row.tier1_results, "tier1")
                    if row.error_message:
                        analysis["error_message"] = row.error_message

                    analyses.append(analysis)

                logger.info(
                    "article_analysis_success",
                    article_id=article_id,
                    results_count=len(analyses),
                )

                return ToolResult(
                    success=True,
                    data={
                        "analyses": analyses,
                        "total_count": len(analyses),
                    },
                    tool_name=self.name,
                )

        except Exception as exc:
            logger.error(
                "article_analysis_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Database error: {str(exc)}",
                tool_name=self.name,
            )


def _summarize_triage(triage_results: dict) -> dict:
    """Extract key info from triage results JSONB."""
    summary = {}
    if isinstance(triage_results, dict):
        if "is_relevant" in triage_results:
            summary["is_relevant"] = triage_results["is_relevant"]
        if "relevance_score" in triage_results:
            summary["relevance_score"] = triage_results["relevance_score"]
        if "category" in triage_results:
            summary["category"] = triage_results["category"]
        if "confidence" in triage_results:
            summary["confidence"] = triage_results["confidence"]
    return summary


def _summarize_tier(tier_results: dict, tier_name: str) -> dict:
    """Extract key info from tier results JSONB."""
    summary = {}
    if isinstance(tier_results, dict):
        # Common fields across tiers
        for key in ["sentiment", "entities", "topics", "summary", "key_points"]:
            if key in tier_results:
                summary[key] = tier_results[key]
    return summary


class DatabaseStatsTool(BaseTool):
    """Get database statistics and counts."""

    name: str = "database_stats"
    description: str = (
        "Get statistics about the news database including article counts, "
        "feed counts, analysis counts, and recent activity metrics."
    )

    async def execute(self, **kwargs) -> ToolResult:
        """
        Get database statistics.

        Args:
            **kwargs: Additional parameters (ignored)

        Returns:
            ToolResult with database statistics
        """
        try:
            async with AsyncSessionLocal() as session:
                # Get counts from actual tables
                stats_sql = """
                    SELECT
                        (SELECT COUNT(*) FROM feed_items) as total_articles,
                        (SELECT COUNT(*) FROM feed_items
                         WHERE published_at >= NOW() - INTERVAL '24 hours') as articles_24h,
                        (SELECT COUNT(*) FROM feed_items
                         WHERE published_at >= NOW() - INTERVAL '7 days') as articles_7d,
                        (SELECT COUNT(*) FROM feeds) as total_feeds,
                        (SELECT COUNT(*) FROM feeds WHERE is_active = true) as active_feeds,
                        (SELECT COUNT(*) FROM article_analysis) as total_analyses,
                        (SELECT COUNT(*) FROM article_analysis WHERE success = true) as successful_analyses
                """
                result = await session.execute(text(stats_sql))
                row = result.fetchone()

                # Get top feeds by recent activity
                top_feeds_sql = """
                    SELECT f.name, COUNT(fi.id) as article_count
                    FROM feeds f
                    JOIN feed_items fi ON f.id = fi.feed_id
                    WHERE fi.published_at >= NOW() - INTERVAL '7 days'
                    GROUP BY f.id, f.name
                    ORDER BY article_count DESC
                    LIMIT 5
                """
                feeds_result = await session.execute(text(top_feeds_sql))
                top_feeds = [
                    {"feed": r.name, "count": r.article_count}
                    for r in feeds_result.fetchall()
                ]

                stats = {
                    "total_articles": row.total_articles,
                    "articles_last_24h": row.articles_24h,
                    "articles_last_7d": row.articles_7d,
                    "total_feeds": row.total_feeds,
                    "active_feeds": row.active_feeds,
                    "total_analyses": row.total_analyses,
                    "successful_analyses": row.successful_analyses,
                    "top_feeds_7d": top_feeds,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                logger.info("database_stats_success")

                return ToolResult(
                    success=True,
                    data=stats,
                    tool_name=self.name,
                )

        except Exception as exc:
            logger.error(
                "database_stats_error",
                error=str(exc),
            )
            return ToolResult(
                success=False,
                error=f"Database error: {str(exc)}",
                tool_name=self.name,
            )
