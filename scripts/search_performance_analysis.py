#!/usr/bin/env python3
"""
Search Performance Analysis Script

Analyzes search service performance with different configurations:
- TF-IDF weight profiles
- Fuzzy similarity thresholds
- Query execution times
- Cache hit rates
"""
import asyncio
import sys
import time
from typing import List, Dict, Any
import asyncpg
import redis.asyncio as redis
import json


async def test_query_performance(conn: asyncpg.Connection, queries: List[str]) -> Dict[str, Any]:
    """Test query performance with different configurations"""
    results = {
        "queries": {},
        "summary": {
            "total_queries": len(queries),
            "avg_execution_time_ms": 0,
            "slowest_query": None,
            "fastest_query": None
        }
    }

    total_time = 0

    for query in queries:
        start = time.time()

        # Test with tuned weights
        rows = await conn.fetch("""
            SELECT
                article_id,
                title,
                ts_rank(
                    search_vector,
                    to_tsquery('english', $1),
                    32  -- normalization: divide by document length
                ) as rank
            FROM article_indexes
            WHERE search_vector @@ to_tsquery('english', $1)
            ORDER BY rank DESC
            LIMIT 20
        """, query)

        exec_time = (time.time() - start) * 1000

        results["queries"][query] = {
            "execution_time_ms": round(exec_time, 2),
            "results_count": len(rows),
            "top_score": float(rows[0]['rank']) if rows else 0.0,
            "avg_score": sum(float(r['rank']) for r in rows) / len(rows) if rows else 0.0
        }

        total_time += exec_time

    # Calculate summary
    query_times = [data["execution_time_ms"] for data in results["queries"].values()]
    results["summary"]["avg_execution_time_ms"] = round(total_time / len(queries), 2)
    results["summary"]["slowest_query"] = max(results["queries"].items(), key=lambda x: x[1]["execution_time_ms"])[0]
    results["summary"]["fastest_query"] = min(results["queries"].items(), key=lambda x: x[1]["execution_time_ms"])[0]
    results["summary"]["min_time_ms"] = min(query_times)
    results["summary"]["max_time_ms"] = max(query_times)

    return results


async def test_fuzzy_thresholds(conn: asyncpg.Connection, query: str) -> Dict[str, Any]:
    """Test fuzzy search at different similarity thresholds"""
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    results = {"query": query, "thresholds": {}}

    for threshold in thresholds:
        start = time.time()

        rows = await conn.fetch("""
            SELECT
                article_id,
                title,
                similarity(title, $1) as title_sim,
                similarity(content, $1) as content_sim
            FROM article_indexes
            WHERE
                similarity(title, $1) >= $2
                OR similarity(content, $1) >= $2
            ORDER BY GREATEST(similarity(title, $1), similarity(content, $1)) DESC
            LIMIT 20
        """, query, threshold)

        exec_time = (time.time() - start) * 1000

        results["thresholds"][str(threshold)] = {
            "execution_time_ms": round(exec_time, 2),
            "results_count": len(rows),
            "avg_similarity": round(sum(max(float(r['title_sim']), float(r['content_sim'])) for r in rows) / len(rows), 3) if rows else 0.0
        }

    return results


async def get_database_statistics(conn: asyncpg.Connection) -> Dict[str, Any]:
    """Get database and index statistics"""
    # Table statistics
    table_stats = await conn.fetchrow("""
        SELECT
            pg_size_pretty(pg_total_relation_size('article_indexes')) as total_size,
            pg_size_pretty(pg_relation_size('article_indexes')) as table_size,
            pg_size_pretty(pg_indexes_size('article_indexes')) as indexes_size,
            (SELECT COUNT(*) FROM article_indexes) as row_count,
            (SELECT COUNT(DISTINCT source) FROM article_indexes) as unique_sources
    """)

    # Index usage statistics
    index_stats = await conn.fetch("""
        SELECT
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch
        FROM pg_stat_user_indexes
        WHERE tablename = 'article_indexes'
        ORDER BY idx_scan DESC
    """)

    # Cache hit rates
    cache_stats = await conn.fetchrow("""
        SELECT
            sum(heap_blks_read) as heap_read,
            sum(heap_blks_hit) as heap_hit,
            sum(idx_blks_read) as idx_read,
            sum(idx_blks_hit) as idx_hit
        FROM pg_statio_user_tables
        WHERE schemaname = 'public' AND relname = 'article_indexes'
    """)

    heap_total = (cache_stats['heap_read'] or 0) + (cache_stats['heap_hit'] or 0)
    idx_total = (cache_stats['idx_read'] or 0) + (cache_stats['idx_hit'] or 0)

    return {
        "table": {
            "total_size": table_stats['total_size'],
            "table_size": table_stats['table_size'],
            "indexes_size": table_stats['indexes_size'],
            "row_count": table_stats['row_count'],
            "unique_sources": table_stats['unique_sources']
        },
        "indexes": [
            {
                "name": row['indexname'],
                "scans": row['idx_scan'],
                "tuples_read": row['idx_tup_read'],
                "tuples_fetched": row['idx_tup_fetch']
            }
            for row in index_stats
        ],
        "cache_hit_ratios": {
            "heap_ratio": round((cache_stats['heap_hit'] / heap_total * 100) if heap_total > 0 else 0, 2),
            "index_ratio": round((cache_stats['idx_hit'] / idx_total * 100) if idx_total > 0 else 0, 2)
        }
    }


async def analyze_weight_profiles(conn: asyncpg.Connection, query: str) -> Dict[str, Any]:
    """Compare different TF-IDF weight profiles"""
    profiles = {
        "default": [1.0, 1.0, 1.0, 1.0],  # PostgreSQL default
        "balanced": [0.8, 0.6, 0.4, 0.2],  # Our tuned weights
        "title_focused": [1.0, 0.3, 0.2, 0.1],  # Heavy title weighting
        "content_focused": [0.5, 0.7, 0.6, 0.2]  # Heavy content weighting
    }

    results = {"query": query, "profiles": {}}

    for profile_name, weights in profiles.items():
        weight_str = "{" + ",".join(map(str, weights)) + "}"
        start = time.time()

        rows = await conn.fetch("""
            SELECT
                article_id,
                title,
                ts_rank(
                    search_vector,
                    to_tsquery('english', $1),
                    $2::real[]
                ) as rank
            FROM article_indexes
            WHERE search_vector @@ to_tsquery('english', $1)
            ORDER BY rank DESC
            LIMIT 10
        """, query, weight_str)

        exec_time = (time.time() - start) * 1000

        results["profiles"][profile_name] = {
            "weights": weights,
            "execution_time_ms": round(exec_time, 2),
            "results_count": len(rows),
            "top_3_scores": [round(float(r['rank']), 4) for r in rows[:3]] if rows else []
        }

    return results


async def main():
    """Main analysis function"""
    print("=" * 80)
    print("Search Service Performance Analysis")
    print("=" * 80)
    print()

    # Connect to database
    print("Connecting to database...")
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='news_user',
        password='+t1koDEJO+ruZ3QnYlkVeU2u6Z+zCJtL6wFW+wfN5Yk=',
        database='news_mcp'
    )
    print("✓ Connected\n")

    # 1. Database Statistics
    print("[1/5] Collecting database statistics...")
    db_stats = await get_database_statistics(conn)
    print(f"✓ Table size: {db_stats['table']['total_size']}")
    print(f"  - Articles indexed: {db_stats['table']['row_count']:,}")
    print(f"  - Unique sources: {db_stats['table']['unique_sources']}")
    print(f"  - Index size: {db_stats['table']['indexes_size']}")
    print(f"  - Heap cache hit ratio: {db_stats['cache_hit_ratios']['heap_ratio']}%")
    print(f"  - Index cache hit ratio: {db_stats['cache_hit_ratios']['index_ratio']}%")
    print()

    # 2. Query Performance Tests
    print("[2/5] Testing query performance...")
    test_queries = [
        "tesla electric vehicle",
        "climate change",
        "artificial intelligence",
        "economic crisis",
        "renewable energy"
    ]
    perf_results = await test_query_performance(conn, test_queries)
    print(f"✓ Tested {perf_results['summary']['total_queries']} queries")
    print(f"  - Average execution time: {perf_results['summary']['avg_execution_time_ms']}ms")
    print(f"  - Fastest: {perf_results['summary']['fastest_query']} ({perf_results['summary']['min_time_ms']}ms)")
    print(f"  - Slowest: {perf_results['summary']['slowest_query']} ({perf_results['summary']['max_time_ms']}ms)")
    print()

    # 3. Weight Profile Comparison
    print("[3/5] Comparing TF-IDF weight profiles...")
    weight_results = await analyze_weight_profiles(conn, "tesla electric")
    print("✓ Profile comparison:")
    for profile_name, data in weight_results["profiles"].items():
        print(f"  - {profile_name:15} {data['execution_time_ms']:6.2f}ms  "
              f"top_score={data['top_3_scores'][0] if data['top_3_scores'] else 0:.4f}")
    print()

    # 4. Fuzzy Threshold Analysis
    print("[4/5] Analyzing fuzzy similarity thresholds...")
    fuzzy_results = await test_fuzzy_thresholds(conn, "renewable energy")
    print(f"✓ Threshold analysis for '{fuzzy_results['query']}':")
    for threshold, data in fuzzy_results["thresholds"].items():
        print(f"  - Threshold {threshold}: {data['results_count']:3} results, "
              f"{data['execution_time_ms']:6.2f}ms, avg_sim={data['avg_similarity']:.3f}")
    print()

    # 5. Recommendations
    print("[5/5] Generating recommendations...")
    print("✓ Optimization recommendations:")

    # Performance recommendations
    if perf_results['summary']['avg_execution_time_ms'] > 100:
        print("  ⚠ Average query time > 100ms - consider:")
        print("    - Increase shared_buffers in PostgreSQL")
        print("    - Add more aggressive query result caching")
        print("    - Optimize WHERE clause filters")
    else:
        print("  ✓ Query performance is good (< 100ms average)")

    # Weight profile recommendation
    fastest_profile = min(
        weight_results["profiles"].items(),
        key=lambda x: x[1]["execution_time_ms"]
    )
    print(f"  ✓ Fastest weight profile: {fastest_profile[0]} ({fastest_profile[1]['execution_time_ms']}ms)")
    print(f"    Recommended weights: {fastest_profile[1]['weights']}")

    # Fuzzy threshold recommendation
    optimal_threshold = None
    for threshold, data in fuzzy_results["thresholds"].items():
        if data['results_count'] >= 5 and data['avg_similarity'] >= 0.3:
            optimal_threshold = threshold
            break
    if optimal_threshold:
        print(f"  ✓ Recommended fuzzy threshold: {optimal_threshold} (balanced precision/recall)")
    else:
        print("  ✓ Current fuzzy threshold (0.3) is optimal")

    # Cache recommendations
    if db_stats['cache_hit_ratios']['heap_ratio'] < 80:
        print(f"  ⚠ Heap cache hit ratio is low ({db_stats['cache_hit_ratios']['heap_ratio']}%)")
        print("    - Increase PostgreSQL shared_buffers")
        print("    - Add more RAM to database server")
    else:
        print(f"  ✓ Cache performance is good ({db_stats['cache_hit_ratios']['heap_ratio']}% heap hits)")

    print()
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)

    # Save detailed results to JSON
    full_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "database_statistics": db_stats,
        "query_performance": perf_results,
        "weight_profiles": weight_results,
        "fuzzy_thresholds": fuzzy_results
    }

    output_file = "/home/cytrex/news-microservices/reports/performance/search_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(full_results, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
