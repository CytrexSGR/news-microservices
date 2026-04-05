"""
Database query monitoring and optimization

Features:
- Query performance tracking
- Slow query detection
- Query plan analysis
- Automatic index recommendations
"""
import time
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from collections import defaultdict

logger = structlog.get_logger()


class QueryMonitor:
    """
    Monitor database query performance

    Tracks:
    - Query execution times
    - Slow queries
    - Query frequency
    - Query patterns
    """

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time_ms": 0.0,
            "min_time_ms": float('inf'),
            "max_time_ms": 0.0,
            "slow_queries": []
        })
        self.current_queries: Dict[int, Dict[str, Any]] = {}

    def start_query(self, query_id: int, statement: str):
        """Record query start"""
        self.current_queries[query_id] = {
            "statement": statement,
            "start_time": time.time()
        }

    def end_query(self, query_id: int):
        """Record query end and collect metrics"""
        if query_id not in self.current_queries:
            return

        query_info = self.current_queries.pop(query_id)
        statement = query_info["statement"]
        duration_ms = (time.time() - query_info["start_time"]) * 1000

        # Normalize query (remove values for grouping)
        normalized_query = self._normalize_query(statement)

        # Update statistics
        stats = self.query_stats[normalized_query]
        stats["count"] += 1
        stats["total_time_ms"] += duration_ms
        stats["min_time_ms"] = min(stats["min_time_ms"], duration_ms)
        stats["max_time_ms"] = max(stats["max_time_ms"], duration_ms)

        # Track slow queries
        if duration_ms > self.slow_query_threshold_ms:
            stats["slow_queries"].append({
                "statement": statement,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Keep only last 10 slow queries per pattern
            if len(stats["slow_queries"]) > 10:
                stats["slow_queries"] = stats["slow_queries"][-10:]

            logger.warning(
                "slow_query_detected",
                query=statement[:200],
                duration_ms=duration_ms,
                threshold_ms=self.slow_query_threshold_ms
            )

    def _normalize_query(self, statement: str) -> str:
        """
        Normalize query for grouping

        Removes:
        - Specific values (123, 'string')
        - Extra whitespace
        - Comments

        This groups similar queries together for statistics
        """
        import re

        # Remove comments
        normalized = re.sub(r'--.*$', '', statement, flags=re.MULTILINE)
        normalized = re.sub(r'/\*.*?\*/', '', normalized, flags=re.DOTALL)

        # Replace string literals
        normalized = re.sub(r"'[^']*'", "'?'", normalized)

        # Replace numbers
        normalized = re.sub(r'\b\d+\b', '?', normalized)

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return normalized[:500]  # Limit length

    def get_statistics(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        stats_list = []

        for query, stats in self.query_stats.items():
            avg_time_ms = stats["total_time_ms"] / stats["count"] if stats["count"] > 0 else 0

            stats_list.append({
                "query": query[:200],
                "executions": stats["count"],
                "total_time_ms": round(stats["total_time_ms"], 2),
                "avg_time_ms": round(avg_time_ms, 2),
                "min_time_ms": round(stats["min_time_ms"], 2),
                "max_time_ms": round(stats["max_time_ms"], 2),
                "slow_query_count": len(stats["slow_queries"])
            })

        # Sort by total time (most expensive first)
        stats_list.sort(key=lambda x: x["total_time_ms"], reverse=True)

        return {
            "total_queries": sum(s["count"] for s in self.query_stats.values()),
            "unique_patterns": len(self.query_stats),
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "top_queries": stats_list[:20]
        }

    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        all_slow = []

        for query_pattern, stats in self.query_stats.items():
            for slow_query in stats["slow_queries"]:
                all_slow.append({
                    **slow_query,
                    "pattern": query_pattern[:200]
                })

        # Sort by duration
        all_slow.sort(key=lambda x: x["duration_ms"], reverse=True)

        return all_slow[:limit]

    def reset_statistics(self):
        """Reset all statistics"""
        self.query_stats.clear()
        self.current_queries.clear()
        logger.info("query_statistics_reset")


# Global monitor instance
_query_monitor: Optional[QueryMonitor] = None


def get_query_monitor() -> QueryMonitor:
    """Get or create global query monitor"""
    global _query_monitor
    if _query_monitor is None:
        _query_monitor = QueryMonitor()
    return _query_monitor


def setup_query_monitoring(engine: Engine):
    """
    Setup query monitoring on SQLAlchemy engine

    Args:
        engine: SQLAlchemy engine instance
    """
    monitor = get_query_monitor()

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Called before query execution"""
        query_id = id(context)
        monitor.start_query(query_id, statement)

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Called after query execution"""
        query_id = id(context)
        monitor.end_query(query_id)

    logger.info("query_monitoring_enabled", threshold_ms=monitor.slow_query_threshold_ms)


async def analyze_query_plan(db_session, query: str) -> Dict[str, Any]:
    """
    Analyze PostgreSQL query execution plan

    Args:
        db_session: Database session
        query: SQL query to analyze

    Returns:
        Query plan analysis with recommendations
    """
    try:
        # Get query plan
        result = db_session.execute(text(f"EXPLAIN (FORMAT JSON, ANALYZE) {query}"))
        plan = result.scalar()

        # Extract key information
        plan_info = plan[0]["Plan"]

        return {
            "query": query[:200],
            "total_cost": plan_info.get("Total Cost"),
            "actual_time_ms": plan_info.get("Actual Total Time"),
            "rows": plan_info.get("Actual Rows"),
            "node_type": plan_info.get("Node Type"),
            "full_plan": plan
        }

    except Exception as e:
        logger.error(
            "query_plan_analysis_failed",
            error=str(e),
            exc_info=True
        )
        return {
            "error": str(e)
        }


def recommend_indexes(query_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Recommend database indexes based on query patterns

    Analyzes slow queries and suggests indexes
    """
    recommendations = []

    for query_info in query_stats.get("top_queries", []):
        query = query_info["query"].lower()

        # Look for common patterns
        if "where" in query and "=" in query:
            # Extract table and column names (simplified)
            import re
            table_match = re.search(r'from\s+(\w+)', query)
            where_match = re.search(r'where\s+(\w+)\s*=', query)

            if table_match and where_match:
                table = table_match.group(1)
                column = where_match.group(1)

                recommendations.append({
                    "type": "index",
                    "table": table,
                    "column": column,
                    "reason": f"Frequent WHERE clause on {table}.{column}",
                    "sql": f"CREATE INDEX idx_{table}_{column} ON {table}({column});",
                    "impact": "high" if query_info["avg_time_ms"] > 100 else "medium"
                })

        if "order by" in query:
            # Suggest index for ORDER BY
            order_match = re.search(r'order\s+by\s+(\w+)', query)
            if order_match:
                column = order_match.group(1)
                recommendations.append({
                    "type": "index",
                    "reason": f"ORDER BY on {column}",
                    "note": "Consider composite index if combined with WHERE clause"
                })

        if "join" in query:
            # Suggest indexes on join columns
            recommendations.append({
                "type": "index",
                "reason": "JOIN operation detected",
                "note": "Ensure foreign key columns are indexed"
            })

    # Deduplicate and sort by impact
    unique_recommendations = []
    seen = set()

    for rec in recommendations:
        key = f"{rec.get('table', '')}_{rec.get('column', '')}"
        if key not in seen:
            seen.add(key)
            unique_recommendations.append(rec)

    return unique_recommendations[:10]  # Top 10 recommendations


@contextmanager
def query_timer(operation_name: str):
    """
    Context manager for timing database operations

    Usage:
        with query_timer("fetch_user_metrics"):
            result = db.query(...)
    """
    start = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        logger.debug(
            "query_operation_completed",
            operation=operation_name,
            duration_ms=round(duration_ms, 2)
        )
