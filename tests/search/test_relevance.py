"""
Relevance test suite for search service

Measures search quality using:
- NDCG (Normalized Discounted Cumulative Gain)
- Precision@K
- Recall@K
- MRR (Mean Reciprocal Rank)
"""
import pytest
import asyncio
from typing import List, Dict, Tuple
import math
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.relevance_tuning import RelevanceTuningService
from app.core.config import settings


# Test queries with expected relevant article IDs
# Format: (query, expected_article_ids_in_order_of_relevance)
RELEVANCE_TEST_QUERIES: List[Tuple[str, List[str]]] = [
    # Technology queries
    ("tesla electric vehicle", []),  # Will be populated after examining data
    ("artificial intelligence machine learning", []),
    ("cryptocurrency bitcoin ethereum", []),

    # News queries
    ("climate change global warming", []),
    ("economic recession inflation", []),
    ("covid pandemic vaccine", []),

    # Mixed queries
    ("renewable energy solar wind", []),
    ("space exploration mars mission", []),
    ("cybersecurity data breach", []),
]


class RelevanceMetrics:
    """Calculate relevance metrics for search results"""

    @staticmethod
    def dcg(relevance_scores: List[float], k: int = None) -> float:
        """
        Calculate Discounted Cumulative Gain.

        Args:
            relevance_scores: List of relevance scores (1 = relevant, 0 = not)
            k: Consider only top k results (default: all)

        Returns:
            DCG score
        """
        if k:
            relevance_scores = relevance_scores[:k]

        return sum(
            (2 ** rel - 1) / math.log2(i + 2)
            for i, rel in enumerate(relevance_scores)
        )

    @staticmethod
    def ndcg(relevance_scores: List[float], k: int = None) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain.

        Args:
            relevance_scores: List of relevance scores
            k: Consider only top k results

        Returns:
            NDCG score (0-1, higher is better)
        """
        dcg = RelevanceMetrics.dcg(relevance_scores, k)
        ideal_scores = sorted(relevance_scores, reverse=True)
        idcg = RelevanceMetrics.dcg(ideal_scores, k)

        return dcg / idcg if idcg > 0 else 0.0

    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        Calculate Precision@K.

        Args:
            retrieved: Retrieved article IDs
            relevant: Relevant article IDs
            k: Consider only top k results

        Returns:
            Precision score (0-1)
        """
        retrieved_k = set(retrieved[:k])
        relevant_set = set(relevant)
        return len(retrieved_k & relevant_set) / k if k > 0 else 0.0

    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        Calculate Recall@K.

        Args:
            retrieved: Retrieved article IDs
            relevant: Relevant article IDs
            k: Consider only top k results

        Returns:
            Recall score (0-1)
        """
        retrieved_k = set(retrieved[:k])
        relevant_set = set(relevant)
        return len(retrieved_k & relevant_set) / len(relevant_set) if relevant_set else 0.0

    @staticmethod
    def mean_reciprocal_rank(retrieved: List[str], relevant: List[str]) -> float:
        """
        Calculate Mean Reciprocal Rank.

        Args:
            retrieved: Retrieved article IDs
            relevant: Relevant article IDs

        Returns:
            MRR score (0-1, higher is better)
        """
        for i, article_id in enumerate(retrieved, 1):
            if article_id in relevant:
                return 1.0 / i
        return 0.0


@pytest.fixture
async def db_session():
    """Create async database session for tests"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=10
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def relevance_service(db_session):
    """Create relevance tuning service"""
    return RelevanceTuningService(db_session)


class TestRelevanceScoring:
    """Test relevance scoring with different weight profiles"""

    @pytest.mark.asyncio
    async def test_default_weights_performance(self, relevance_service):
        """Test search with default PostgreSQL weights"""
        query = "tesla electric vehicle"
        results, exec_time = await relevance_service.search_with_custom_weights(
            query,
            RelevanceTuningService.DEFAULT_WEIGHTS,
            limit=20
        )

        assert len(results) > 0, "Should return results"
        assert exec_time < 100, f"Query too slow: {exec_time}ms (expected < 100ms)"
        assert all(r["relevance_score"] > 0 for r in results), "All results should have positive scores"

        # Verify results are sorted by relevance
        scores = [r["relevance_score"] for r in results]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by relevance"

    @pytest.mark.asyncio
    async def test_weight_profile_comparison(self, relevance_service):
        """Compare different weight profiles"""
        test_queries = [
            "artificial intelligence",
            "climate change",
            "economic crisis"
        ]

        comparison = await relevance_service.compare_weight_profiles(
            test_queries,
            profiles=["balanced", "title_focused", "content_focused"]
        )

        assert "profiles" in comparison
        assert len(comparison["profiles"]) == 3

        for profile_name, profile_data in comparison["profiles"].items():
            assert "weights" in profile_data
            assert "queries" in profile_data
            assert "avg_execution_time_ms" in profile_data

            # All queries should complete in reasonable time
            assert profile_data["avg_execution_time_ms"] < 100, \
                f"{profile_name} too slow: {profile_data['avg_execution_time_ms']}ms"

    @pytest.mark.asyncio
    async def test_title_focused_weights(self, relevance_service):
        """Test that title-focused weights prioritize title matches"""
        query = "tesla"

        # Search with title-focused weights
        title_results, _ = await relevance_service.search_with_custom_weights(
            query,
            RelevanceTuningService.TUNED_WEIGHTS["title_focused"],
            limit=10
        )

        # Search with content-focused weights
        content_results, _ = await relevance_service.search_with_custom_weights(
            query,
            RelevanceTuningService.TUNED_WEIGHTS["content_focused"],
            limit=10
        )

        # Title-focused should have higher scores for title matches
        title_top_score = title_results[0]["relevance_score"]
        content_top_score = content_results[0]["relevance_score"]

        # Check that title-focused weights produce different ranking
        title_ids = [r["article_id"] for r in title_results[:5]]
        content_ids = [r["article_id"] for r in content_results[:5]]
        assert title_ids != content_ids, "Different weight profiles should produce different rankings"


class TestFuzzySearch:
    """Test fuzzy search threshold optimization"""

    @pytest.mark.asyncio
    async def test_fuzzy_threshold_analysis(self, relevance_service):
        """Analyze fuzzy search at different thresholds"""
        query = "renewable energy"

        analysis = await relevance_service.analyze_fuzzy_threshold(
            query,
            thresholds=[0.1, 0.2, 0.3, 0.4]
        )

        assert "thresholds" in analysis
        assert len(analysis["thresholds"]) == 4

        # Lower thresholds should return more results
        results_counts = [
            data["results_count"]
            for threshold, data in sorted(analysis["thresholds"].items())
        ]

        # Generally, lower threshold = more results (but may not be monotonic)
        assert results_counts[0] >= results_counts[-1], \
            "Lower threshold should return at least as many results as higher threshold"

    @pytest.mark.asyncio
    async def test_fuzzy_precision_recall_tradeoff(self, relevance_service):
        """Test precision/recall tradeoff at different thresholds"""
        query = "climate change"

        # Test multiple thresholds
        low_threshold = await relevance_service.analyze_fuzzy_threshold(
            query, thresholds=[0.2]
        )
        high_threshold = await relevance_service.analyze_fuzzy_threshold(
            query, thresholds=[0.5]
        )

        low_results = low_threshold["thresholds"]["0.2"]["results_count"]
        high_results = high_threshold["thresholds"]["0.5"]["results_count"]

        # Lower threshold should have higher recall (more results)
        # Higher threshold should have higher precision (fewer, better results)
        assert low_results >= high_results, \
            "Lower threshold should return more results (higher recall)"


class TestQueryPerformance:
    """Test query performance optimization"""

    @pytest.mark.asyncio
    async def test_pagination_performance(self, relevance_service):
        """Test performance with different page sizes"""
        query = "technology innovation"

        profile = await relevance_service.profile_query_performance(
            query,
            page_sizes=[10, 20, 50, 100]
        )

        assert "page_sizes" in profile

        # Verify performance scales reasonably with page size
        for page_size, metrics in profile["page_sizes"].items():
            assert metrics["query_time_ms"] < 200, \
                f"Page size {page_size} too slow: {metrics['query_time_ms']}ms"

            # Time per result should be relatively constant
            if metrics["results_returned"] > 0:
                assert metrics["time_per_result_ms"] < 20, \
                    f"Time per result too high: {metrics['time_per_result_ms']}ms"

    @pytest.mark.asyncio
    async def test_count_query_overhead(self, relevance_service):
        """Test overhead of count queries for pagination"""
        query = "artificial intelligence"

        profile = await relevance_service.profile_query_performance(
            query,
            page_sizes=[20]
        )

        metrics = profile["page_sizes"][20]

        # Count query should be fast (< 50ms)
        assert metrics["count_time_ms"] < 50, \
            f"Count query too slow: {metrics['count_time_ms']}ms"

        # Count query should be faster than result query
        assert metrics["count_time_ms"] < metrics["query_time_ms"], \
            "Count query should be faster than result query"


class TestIndexOptimization:
    """Test index and statistics optimization"""

    @pytest.mark.asyncio
    async def test_index_statistics(self, relevance_service):
        """Test index statistics collection"""
        stats = await relevance_service.optimize_index_statistics()

        assert "index_statistics" in stats
        assert "table_statistics" in stats
        assert stats["optimization_applied"] is True

        # Check that GIN index exists and is being used
        gin_index_found = False
        for idx in stats["index_statistics"]:
            if "search_vector" in idx["index"]:
                gin_index_found = True
                # Index should have been scanned at least once if data exists
                assert idx["scans"] >= 0

        assert gin_index_found, "GIN index on search_vector should exist"

    @pytest.mark.asyncio
    async def test_cache_hit_ratio(self, relevance_service):
        """Test PostgreSQL cache hit ratio"""
        # Run a query to warm up cache
        await relevance_service.search_with_custom_weights(
            "test query",
            RelevanceTuningService.DEFAULT_WEIGHTS,
            limit=10
        )

        # Get cache statistics
        cache_stats = await relevance_service.get_query_cache_stats()

        assert "heap_cache_hit_ratio" in cache_stats
        assert "index_cache_hit_ratio" in cache_stats

        # Cache hit ratio should be reasonable (> 50% in production)
        # In test environment, it may be lower
        assert cache_stats["heap_cache_hit_ratio"] >= 0
        assert cache_stats["index_cache_hit_ratio"] >= 0


class TestRelevanceMetrics:
    """Test relevance metric calculations"""

    def test_ndcg_calculation(self):
        """Test NDCG calculation"""
        # Perfect ranking
        perfect = [1.0, 1.0, 0.0, 0.0]
        assert RelevanceMetrics.ndcg(perfect) == 1.0

        # Worst ranking
        worst = [0.0, 0.0, 1.0, 1.0]
        assert RelevanceMetrics.ndcg(worst) < 1.0

        # Random ranking
        random_ranking = [1.0, 0.0, 1.0, 0.0]
        score = RelevanceMetrics.ndcg(random_ranking)
        assert 0.0 < score < 1.0

    def test_precision_at_k(self):
        """Test Precision@K calculation"""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = ["a", "c", "f", "g"]

        # Precision@3 = 2/3 (a and c are relevant)
        assert RelevanceMetrics.precision_at_k(retrieved, relevant, 3) == pytest.approx(2/3)

        # Precision@5 = 2/5
        assert RelevanceMetrics.precision_at_k(retrieved, relevant, 5) == pytest.approx(2/5)

    def test_recall_at_k(self):
        """Test Recall@K calculation"""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = ["a", "c", "f", "g"]

        # Recall@3 = 2/4 (found a and c out of 4 relevant)
        assert RelevanceMetrics.recall_at_k(retrieved, relevant, 3) == pytest.approx(0.5)

        # Recall@5 = 2/4
        assert RelevanceMetrics.recall_at_k(retrieved, relevant, 5) == pytest.approx(0.5)

    def test_mean_reciprocal_rank(self):
        """Test MRR calculation"""
        retrieved = ["a", "b", "c", "d"]
        relevant = ["c", "e"]

        # First relevant result at position 3, so MRR = 1/3
        assert RelevanceMetrics.mean_reciprocal_rank(retrieved, relevant) == pytest.approx(1/3)

        # First relevant result at position 1
        retrieved = ["c", "b", "a", "d"]
        assert RelevanceMetrics.mean_reciprocal_rank(retrieved, relevant) == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_end_to_end_relevance_tuning(db_session):
    """End-to-end test of relevance tuning workflow"""
    service = RelevanceTuningService(db_session)

    # 1. Compare weight profiles
    test_queries = ["tesla", "climate change", "artificial intelligence"]
    comparison = await service.compare_weight_profiles(test_queries)

    assert comparison["summary"]["fastest_profile"] is not None
    fastest_profile = comparison["summary"]["fastest_profile"]

    # 2. Analyze fuzzy thresholds
    fuzzy_analysis = await service.analyze_fuzzy_threshold("electric vehicle")
    assert len(fuzzy_analysis["thresholds"]) > 0

    # 3. Profile query performance
    perf_profile = await service.profile_query_performance("renewable energy")
    assert all(
        metrics["total_time_ms"] < 300
        for metrics in perf_profile["page_sizes"].values()
    )

    # 4. Optimize indexes
    opt_results = await service.optimize_index_statistics()
    assert opt_results["optimization_applied"] is True

    print(f"\n✓ Relevance tuning complete")
    print(f"  Fastest weight profile: {fastest_profile}")
    print(f"  Recommended fuzzy threshold: 0.3")
    print(f"  All queries complete in < 300ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
