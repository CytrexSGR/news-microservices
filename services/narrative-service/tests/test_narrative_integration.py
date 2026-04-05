"""
Integration Tests for Narrative Service
Tests narrative generation with real scenarios, caching, error handling
"""
import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime
import time

# Sample test articles
SAMPLE_ARTICLES = {
    "political": """
    The government announced new reforms to address economic inequality.
    Progressive leaders praised the initiative as essential for justice and fairness.
    Conservative critics warned about government overreach and increased spending.
    The proposal aims to support vulnerable communities through expanded healthcare
    and education programs.
    """,
    "crisis": """
    Natural disaster strikes coastal region, devastating communities.
    Thousands suffer from the catastrophic impact of the hurricane.
    Emergency services struggle to reach victims in the hardest-hit areas.
    International aid organizations mobilize to provide relief and support.
    Local heroes emerge as brave volunteers risk their lives to save neighbors.
    """,
    "conflict": """
    Tensions escalate between rival nations over disputed territory.
    Military buildup raises fears of armed conflict in the region.
    Diplomatic efforts fail as both sides refuse to compromise.
    International community calls for peaceful resolution of the crisis.
    Economic sanctions threatened if aggression continues.
    """,
    "short": "This text is too short",
}


@pytest.fixture
def api_url():
    """Base URL for narrative service"""
    return "http://localhost:8119/api/v1/narrative"


@pytest.mark.asyncio
class TestNarrativeAnalysis:
    """Test narrative frame detection and bias analysis"""

    async def test_analyze_political_text(self, api_url):
        """Test analysis of political article"""
        async with AsyncClient() as client:
            response = await client.post(
                f"{api_url}/analyze/text",
                params={
                    "text": SAMPLE_ARTICLES["political"],
                    "source": "TestNews"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "frames" in data
            assert "bias" in data
            assert "text_length" in data
            assert "analyzed_at" in data

            # Check frames detected
            assert isinstance(data["frames"], list)
            assert len(data["frames"]) > 0

            # Should detect some political frames
            frame_types = [f["frame_type"] for f in data["frames"]]
            # Could include: solution, conflict, economic
            assert any(ft in ["solution", "conflict", "economic"] for ft in frame_types)

            # Check bias analysis
            bias = data["bias"]
            assert "bias_score" in bias
            assert "bias_label" in bias
            assert "sentiment" in bias
            assert bias["bias_label"] in ["left", "center-left", "center", "center-right", "right"]

    async def test_analyze_crisis_text(self, api_url):
        """Test analysis of crisis/disaster article"""
        async with AsyncClient() as client:
            response = await client.post(
                f"{api_url}/analyze/text",
                params={
                    "text": SAMPLE_ARTICLES["crisis"],
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect victim and hero frames
            frame_types = [f["frame_type"] for f in data["frames"]]
            assert "victim" in frame_types or "hero" in frame_types

            # Check entities extracted
            for frame in data["frames"]:
                assert "entities" in frame
                # Crisis articles should mention locations
                if frame["frame_type"] == "victim":
                    assert "confidence" in frame
                    assert 0.0 <= frame["confidence"] <= 1.0

    async def test_analyze_conflict_text(self, api_url):
        """Test analysis of conflict article"""
        async with AsyncClient() as client:
            response = await client.post(
                f"{api_url}/analyze/text",
                params={
                    "text": SAMPLE_ARTICLES["conflict"],
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect threat or conflict frames
            frame_types = [f["frame_type"] for f in data["frames"]]
            assert "threat" in frame_types or "conflict" in frame_types

    async def test_text_too_short_error(self, api_url):
        """Test error handling for text too short"""
        async with AsyncClient() as client:
            response = await client.post(
                f"{api_url}/analyze/text",
                params={
                    "text": SAMPLE_ARTICLES["short"],
                }
            )

            assert response.status_code == 400
            error = response.json()
            assert "detail" in error


@pytest.mark.asyncio
class TestCaching:
    """Test caching behavior"""

    async def test_cache_performance(self, api_url):
        """Test that caching improves performance"""
        async with AsyncClient() as client:
            text = SAMPLE_ARTICLES["political"]

            # First request (cache miss)
            start = time.time()
            response1 = await client.post(
                f"{api_url}/analyze/text",
                params={"text": text}
            )
            duration_uncached = time.time() - start

            assert response1.status_code == 200
            data1 = response1.json()
            assert data1.get("from_cache") == False

            # Second request (cache hit)
            start = time.time()
            response2 = await client.post(
                f"{api_url}/analyze/text",
                params={"text": text}
            )
            duration_cached = time.time() - start

            assert response2.status_code == 200
            data2 = response2.json()
            assert data2.get("from_cache") == True

            # Cached request should be much faster
            # Typically: 150ms → 3-5ms (30-50x faster)
            assert duration_cached < duration_uncached / 10

            # Results should be identical
            assert data1["frames"] == data2["frames"]
            assert data1["bias"] == data2["bias"]

    async def test_cache_stats(self, api_url):
        """Test cache statistics endpoint"""
        async with AsyncClient() as client:
            response = await client.get(f"{api_url}/cache/stats")

            assert response.status_code == 200
            stats = response.json()

            assert "cache_enabled" in stats
            if stats["cache_enabled"]:
                assert "total_keys" in stats
                assert "hit_rate" in stats


@pytest.mark.asyncio
class TestConcurrency:
    """Test concurrent request handling"""

    async def test_concurrent_analysis(self, api_url):
        """Test handling multiple concurrent requests"""
        async with AsyncClient() as client:
            # Create 10 concurrent requests
            tasks = []
            for i in range(10):
                text = SAMPLE_ARTICLES["political"] + f" Request {i}"
                task = client.post(
                    f"{api_url}/analyze/text",
                    params={"text": text}
                )
                tasks.append(task)

            # Execute concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            assert success_count >= 8  # Allow some failures due to rate limiting

    async def test_parallel_frame_and_bias(self, api_url):
        """Test that frame detection and bias analysis run in parallel"""
        async with AsyncClient() as client:
            text = SAMPLE_ARTICLES["conflict"]

            # Clear cache first
            await client.post(f"{api_url}/cache/clear")

            # Time the analysis
            start = time.time()
            response = await client.post(
                f"{api_url}/analyze/text",
                params={"text": text}
            )
            duration = time.time() - start

            assert response.status_code == 200
            # With parallel execution, should be faster than sequential
            # Typical: 80-120ms for parallel vs 150-200ms sequential
            assert duration < 0.2  # 200ms


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and retry logic"""

    async def test_empty_text_error(self, api_url):
        """Test error for empty text"""
        async with AsyncClient() as client:
            response = await client.post(
                f"{api_url}/analyze/text",
                params={"text": ""}
            )

            assert response.status_code == 400

    async def test_invalid_parameters(self, api_url):
        """Test error handling for invalid parameters"""
        async with AsyncClient() as client:
            # Invalid days parameter
            response = await client.get(
                f"{api_url}/overview",
                params={"days": 100}  # Max is 30
            )

            assert response.status_code == 422  # Validation error

    async def test_missing_required_field(self, api_url):
        """Test error for missing required field"""
        async with AsyncClient() as client:
            # Missing text parameter
            response = await client.post(f"{api_url}/analyze/text")

            assert response.status_code == 422


@pytest.mark.asyncio
class TestOverview:
    """Test narrative overview endpoint"""

    async def test_get_overview_default(self, api_url):
        """Test overview with default parameters"""
        async with AsyncClient() as client:
            response = await client.get(f"{api_url}/overview")

            assert response.status_code == 200
            data = response.json()

            # Check structure
            assert "total_frames" in data
            assert "total_clusters" in data
            assert "frame_distribution" in data
            assert "bias_distribution" in data
            assert "avg_bias_score" in data
            assert "avg_sentiment" in data
            assert "top_narratives" in data

            # Check types
            assert isinstance(data["total_frames"], int)
            assert isinstance(data["frame_distribution"], dict)
            assert isinstance(data["top_narratives"], list)

    async def test_overview_caching(self, api_url):
        """Test that overview results are cached"""
        async with AsyncClient() as client:
            # First request
            start = time.time()
            response1 = await client.get(f"{api_url}/overview?days=7")
            duration_uncached = time.time() - start

            # Second request (should be cached)
            start = time.time()
            response2 = await client.get(f"{api_url}/overview?days=7")
            duration_cached = time.time() - start

            assert response1.status_code == 200
            assert response2.status_code == 200

            # Cached should be much faster
            assert duration_cached < duration_uncached / 10


@pytest.mark.asyncio
class TestPerformance:
    """Performance benchmarks"""

    async def test_response_time_target(self, api_url):
        """Test that response time meets <2s target"""
        async with AsyncClient() as client:
            text = SAMPLE_ARTICLES["political"]

            # Measure response time
            start = time.time()
            response = await client.post(
                f"{api_url}/analyze/text",
                params={"text": text}
            )
            duration = time.time() - start

            assert response.status_code == 200
            # Target: <2s (without cache)
            assert duration < 2.0

    async def test_bulk_analysis_performance(self, api_url):
        """Test performance with multiple articles"""
        async with AsyncClient() as client:
            articles = [
                SAMPLE_ARTICLES["political"],
                SAMPLE_ARTICLES["crisis"],
                SAMPLE_ARTICLES["conflict"],
            ]

            # Analyze all in parallel
            start = time.time()
            tasks = [
                client.post(f"{api_url}/analyze/text", params={"text": text})
                for text in articles
            ]
            responses = await asyncio.gather(*tasks)
            duration = time.time() - start

            # All should succeed
            assert all(r.status_code == 200 for r in responses)

            # Should process 3 articles in <3 seconds
            assert duration < 3.0


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
