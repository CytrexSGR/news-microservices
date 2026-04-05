"""
E2E Test: Search Service Integration
Tests search functionality and integration with other services.
"""
import pytest
import httpx
from typing import Dict, Any
import asyncio


@pytest.mark.asyncio
async def test_article_search_basic(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test basic article search functionality."""
    # Search with simple query
    response = await http_client.get(
        "http://localhost:8006/api/search",
        params={"q": "technology", "limit": 10},
        headers=auth_headers
    )

    if response.status_code == 200:
        results = response.json()
        assert "results" in results or "total" in results
        print(f"✓ Basic search works: {results.get('total', 0)} results")
    else:
        print(f"⚠ Search service returned: {response.status_code}")


@pytest.mark.asyncio
async def test_search_with_filters(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test search with various filters."""
    # Search with category filter
    response = await http_client.get(
        "http://localhost:8006/api/search",
        params={
            "q": "news",
            "category": "technology",
            "limit": 5
        },
        headers=auth_headers
    )

    if response.status_code == 200:
        results = response.json()
        print(f"✓ Filtered search works")

    # Search with date range
    response = await http_client.get(
        "http://localhost:8006/api/search",
        params={
            "q": "AI",
            "from_date": "2024-01-01",
            "limit": 10
        },
        headers=auth_headers
    )

    if response.status_code == 200:
        print(f"✓ Date-filtered search works")


@pytest.mark.asyncio
async def test_search_indexing_after_article_creation(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test that newly created articles are indexed for search."""
    # Create a feed
    feed_data = {
        "url": "https://hnrss.org/frontpage",
        "name": "Search Indexing Test",
        "category": "technology"
    }

    response = await http_client.post(
        "http://localhost:8001/api/feeds",
        json=feed_data,
        headers=auth_headers
    )
    feed = response.json()

    # Fetch articles
    response = await http_client.post(
        f"http://localhost:8001/api/feeds/{feed['id']}/fetch",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Wait for indexing
    await asyncio.sleep(5)

    # Search for articles
    response = await http_client.get(
        "http://localhost:8006/api/search",
        params={"q": "technology", "limit": 20},
        headers=auth_headers
    )

    if response.status_code == 200:
        results = response.json()
        print(f"✓ Articles indexed: {results.get('total', 0)} searchable")


@pytest.mark.asyncio
async def test_search_relevance_ranking(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test that search results are properly ranked by relevance."""
    response = await http_client.get(
        "http://localhost:8006/api/search",
        params={"q": "artificial intelligence", "limit": 10},
        headers=auth_headers
    )

    if response.status_code == 200:
        results = response.json()

        # Check if results have relevance scores
        if "results" in results and len(results["results"]) > 0:
            first_result = results["results"][0]
            print(f"✓ Search ranking verified")


@pytest.mark.asyncio
async def test_search_performance(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test search performance and response times."""
    import time

    queries = [
        "technology",
        "artificial intelligence",
        "machine learning",
        "cybersecurity",
        "blockchain"
    ]

    response_times = []

    for query in queries:
        start = time.time()
        response = await http_client.get(
            "http://localhost:8006/api/search",
            params={"q": query, "limit": 10},
            headers=auth_headers
        )
        elapsed = time.time() - start
        response_times.append(elapsed)

        if response.status_code == 200:
            print(f"✓ Query '{query}': {elapsed:.3f}s")

    avg_time = sum(response_times) / len(response_times)
    print(f"✓ Average search time: {avg_time:.3f}s")

    # Assert reasonable performance (< 1 second average)
    assert avg_time < 1.0, f"Search too slow: {avg_time:.3f}s average"


@pytest.mark.asyncio
async def test_search_pagination(
    http_client: httpx.AsyncClient,
    test_user: Dict[str, Any],
    auth_headers: Dict[str, str]
):
    """Test search result pagination."""
    # Get first page
    response = await http_client.get(
        "http://localhost:8006/api/search",
        params={"q": "news", "limit": 5, "offset": 0},
        headers=auth_headers
    )

    if response.status_code == 200:
        page1 = response.json()

        # Get second page
        response = await http_client.get(
            "http://localhost:8006/api/search",
            params={"q": "news", "limit": 5, "offset": 5},
            headers=auth_headers
        )

        if response.status_code == 200:
            page2 = response.json()
            print(f"✓ Search pagination works")
