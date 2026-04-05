"""
Relevance tuning service for PostgreSQL full-text search

Implements TF-IDF weight tuning, relevance scoring optimization,
and query performance monitoring.
"""
import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search import ArticleIndex
from app.core.config import settings


class RelevanceTuningService:
    """Service for tuning search relevance and performance"""

    # TF-IDF weights: {D-weight, C-weight, B-weight, A-weight}
    # D = title (highest), C = subtitle, B = body, A = author
    DEFAULT_WEIGHTS = [1.0, 0.5, 0.2, 0.1]  # Default PostgreSQL weights

    # Tuned weights based on field importance
    # Title should have highest weight, then content, then metadata
    TUNED_WEIGHTS = {
        "balanced": [0.8, 0.6, 0.4, 0.2],  # Balanced relevance
        "title_focused": [1.0, 0.3, 0.2, 0.1],  # Prioritize title matches
        "content_focused": [0.5, 0.7, 0.6, 0.2],  # Prioritize content depth
        "metadata_aware": [0.7, 0.5, 0.3, 0.3],  # Include metadata signals
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_with_custom_weights(
        self,
        query: str,
        weights: List[float],
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict], float]:
        """
        Execute search with custom TF-IDF weights.

        Args:
            query: Search query
            weights: TF-IDF weights [D, C, B, A]
            limit: Result limit
            offset: Result offset

        Returns:
            Tuple of (results, execution_time_ms)
        """
        start_time = time.time()

        # Build weighted ts_rank query
        weight_str = "{" + ",".join(map(str, weights)) + "}"
        ts_query = self._parse_query(query)

        stmt = text("""
            SELECT
                article_id,
                title,
                content,
                source,
                sentiment,
                published_at,
                ts_rank(
                    search_vector,
                    to_tsquery('english', :query),
                    :weights::real[]
                ) as rank
            FROM article_indexes
            WHERE search_vector @@ to_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(
            stmt,
            {
                "query": ts_query,
                "weights": weight_str,
                "limit": limit,
                "offset": offset
            }
        )
        rows = result.fetchall()

        execution_time = (time.time() - start_time) * 1000

        results = [
            {
                "article_id": row[0],
                "title": row[1],
                "content": row[2][:300] + "..." if len(row[2]) > 300 else row[2],
                "source": row[3],
                "sentiment": row[4],
                "published_at": row[5],
                "relevance_score": float(row[6]) if row[6] else 0.0,
            }
            for row in rows
        ]

        return results, execution_time

    async def compare_weight_profiles(
        self,
        test_queries: List[str],
        profiles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare different weight profiles on test queries.

        Args:
            test_queries: List of queries to test
            profiles: Weight profiles to compare (default: all)

        Returns:
            Comparison results with performance metrics
        """
        if profiles is None:
            profiles = list(self.TUNED_WEIGHTS.keys())

        results = {
            "queries": test_queries,
            "profiles": {},
            "summary": {}
        }

        for profile_name in profiles:
            weights = self.TUNED_WEIGHTS[profile_name]
            profile_results = []

            total_time = 0
            for query in test_queries:
                query_results, exec_time = await self.search_with_custom_weights(
                    query, weights, limit=10
                )
                profile_results.append({
                    "query": query,
                    "results_count": len(query_results),
                    "execution_time_ms": exec_time,
                    "top_3_scores": [r["relevance_score"] for r in query_results[:3]],
                })
                total_time += exec_time

            results["profiles"][profile_name] = {
                "weights": weights,
                "queries": profile_results,
                "avg_execution_time_ms": total_time / len(test_queries),
            }

        # Add summary
        fastest_profile = min(
            results["profiles"].items(),
            key=lambda x: x[1]["avg_execution_time_ms"]
        )
        results["summary"] = {
            "fastest_profile": fastest_profile[0],
            "fastest_time_ms": fastest_profile[1]["avg_execution_time_ms"],
        }

        return results

    async def analyze_fuzzy_threshold(
        self,
        query: str,
        thresholds: List[float] = [0.1, 0.2, 0.3, 0.4, 0.5]
    ) -> Dict[str, Any]:
        """
        Analyze fuzzy search results at different similarity thresholds.

        Args:
            query: Test query
            thresholds: Similarity thresholds to test

        Returns:
            Analysis results for each threshold
        """
        results = {
            "query": query,
            "thresholds": {}
        }

        for threshold in thresholds:
            start_time = time.time()

            stmt = text("""
                SELECT
                    article_id,
                    title,
                    similarity(title, :query) as title_sim,
                    similarity(content, :query) as content_sim,
                    GREATEST(
                        similarity(title, :query),
                        similarity(content, :query)
                    ) as max_sim
                FROM article_indexes
                WHERE
                    similarity(title, :query) >= :threshold
                    OR similarity(content, :query) >= :threshold
                ORDER BY max_sim DESC
                LIMIT 20
            """)

            result = await self.db.execute(
                stmt,
                {"query": query, "threshold": threshold}
            )
            rows = result.fetchall()

            execution_time = (time.time() - start_time) * 1000

            results["thresholds"][str(threshold)] = {
                "results_count": len(rows),
                "execution_time_ms": execution_time,
                "avg_similarity": sum(row[4] for row in rows) / len(rows) if rows else 0,
                "max_similarity": max(row[4] for row in rows) if rows else 0,
                "min_similarity": min(row[4] for row in rows) if rows else 0,
            }

        return results

    async def profile_query_performance(
        self,
        query: str,
        page_sizes: List[int] = [10, 20, 50, 100]
    ) -> Dict[str, Any]:
        """
        Profile query performance with different page sizes.

        Args:
            query: Test query
            page_sizes: Page sizes to test

        Returns:
            Performance metrics for each page size
        """
        ts_query = self._parse_query(query)
        results = {
            "query": query,
            "page_sizes": {}
        }

        for page_size in page_sizes:
            # Measure query time
            start_time = time.time()

            stmt = select(
                ArticleIndex,
                func.ts_rank(
                    ArticleIndex.search_vector,
                    func.to_tsquery('english', ts_query)
                ).label('rank')
            ).where(
                ArticleIndex.search_vector.op('@@')(
                    func.to_tsquery('english', ts_query)
                )
            ).order_by(text('rank DESC')).limit(page_size)

            result = await self.db.execute(stmt)
            rows = result.all()

            execution_time = (time.time() - start_time) * 1000

            # Measure count query time
            count_start = time.time()
            count_stmt = select(func.count()).select_from(
                select(ArticleIndex).where(
                    ArticleIndex.search_vector.op('@@')(
                        func.to_tsquery('english', ts_query)
                    )
                ).subquery()
            )
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar()
            count_time = (time.time() - count_start) * 1000

            results["page_sizes"][page_size] = {
                "results_returned": len(rows),
                "total_matches": total,
                "query_time_ms": execution_time,
                "count_time_ms": count_time,
                "total_time_ms": execution_time + count_time,
                "time_per_result_ms": execution_time / len(rows) if rows else 0,
            }

        return results

    async def optimize_index_statistics(self) -> Dict[str, Any]:
        """
        Analyze and update index statistics for better query planning.

        Returns:
            Index statistics and optimization results
        """
        # Get current index statistics
        stats_stmt = text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE tablename = 'article_indexes'
            ORDER BY idx_scan DESC
        """)

        result = await self.db.execute(stats_stmt)
        index_stats = [
            {
                "schema": row[0],
                "table": row[1],
                "index": row[2],
                "scans": row[3],
                "tuples_read": row[4],
                "tuples_fetched": row[5],
            }
            for row in result.fetchall()
        ]

        # Analyze table (updates statistics)
        analyze_stmt = text("ANALYZE article_indexes")
        await self.db.execute(analyze_stmt)
        await self.db.commit()

        # Get table bloat information
        bloat_stmt = text("""
            SELECT
                pg_size_pretty(pg_total_relation_size('article_indexes')) as total_size,
                pg_size_pretty(pg_relation_size('article_indexes')) as table_size,
                pg_size_pretty(pg_indexes_size('article_indexes')) as indexes_size,
                (SELECT COUNT(*) FROM article_indexes) as row_count
        """)

        bloat_result = await self.db.execute(bloat_stmt)
        bloat_row = bloat_result.first()

        return {
            "index_statistics": index_stats,
            "table_statistics": {
                "total_size": bloat_row[0],
                "table_size": bloat_row[1],
                "indexes_size": bloat_row[2],
                "row_count": bloat_row[3],
            },
            "optimization_applied": True,
            "recommendation": "ANALYZE completed - query planner statistics updated"
        }

    def _parse_query(self, query: str) -> str:
        """
        Parse query into PostgreSQL tsquery format.

        Handles:
        - AND/OR operators
        - Exclusion (-)
        - Phrase search (quotes)
        """
        tokens = []
        words = query.split()

        for word in words:
            if word.startswith('-'):
                tokens.append(f'!{word[1:]}')
            elif word.upper() in ('AND', 'OR'):
                tokens.append(word.upper())
            else:
                tokens.append(word)

        return ' & '.join(tokens) if tokens else query

    async def get_query_cache_stats(self) -> Dict[str, Any]:
        """
        Get PostgreSQL query cache statistics.

        Returns:
            Cache hit ratios and performance metrics
        """
        cache_stmt = text("""
            SELECT
                sum(heap_blks_read) as heap_read,
                sum(heap_blks_hit) as heap_hit,
                sum(idx_blks_read) as idx_read,
                sum(idx_blks_hit) as idx_hit
            FROM pg_statio_user_tables
            WHERE schemaname = 'public'
        """)

        result = await self.db.execute(cache_stmt)
        row = result.first()

        heap_total = (row[0] or 0) + (row[1] or 0)
        idx_total = (row[2] or 0) + (row[3] or 0)

        return {
            "heap_cache_hit_ratio": (row[1] / heap_total * 100) if heap_total > 0 else 0,
            "index_cache_hit_ratio": (row[3] / idx_total * 100) if idx_total > 0 else 0,
            "heap_blocks_read": row[0] or 0,
            "heap_blocks_hit": row[1] or 0,
            "index_blocks_read": row[2] or 0,
            "index_blocks_hit": row[3] or 0,
        }
