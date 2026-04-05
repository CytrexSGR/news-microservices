#!/usr/bin/env python3
"""
Article Entities Endpoint - Usage Examples

Demonstrates how to use the article entities endpoint in the knowledge-graph-service.
"""

import asyncio
import httpx
from typing import Optional


BASE_URL = "http://localhost:8111"


async def get_article_entities(
    article_id: str,
    entity_type: Optional[str] = None,
    limit: int = 50
):
    """
    Fetch entities extracted from an article.

    Args:
        article_id: Article identifier
        entity_type: Optional filter by entity type (PERSON, ORGANIZATION, etc.)
        limit: Maximum entities to return (1-200)

    Returns:
        Dict with article info and entities
    """
    async with httpx.AsyncClient() as client:
        params = {"limit": limit}
        if entity_type:
            params["entity_type"] = entity_type

        response = await client.get(
            f"{BASE_URL}/api/v1/graph/articles/{article_id}/entities",
            params=params
        )
        response.raise_for_status()
        return response.json()


async def get_article_info(article_id: str):
    """
    Get article metadata from knowledge graph.

    Args:
        article_id: Article identifier

    Returns:
        Dict with article info
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/graph/articles/{article_id}/info"
        )
        response.raise_for_status()
        return response.json()


async def example_basic_usage():
    """Example 1: Basic usage - fetch all entities."""
    print("=== Example 1: Fetch All Entities ===\n")

    article_id = "test-article-123"
    result = await get_article_entities(article_id)

    print(f"Article ID: {result['article_id']}")
    print(f"Article Title: {result['article_title']}")
    print(f"Total Entities: {result['total_entities']}")
    print(f"Query Time: {result['query_time_ms']}ms")

    if result['entities']:
        print("\nTop Entities:")
        for entity in result['entities'][:5]:
            print(f"  - {entity['name']} ({entity['type']})")
            print(f"    Confidence: {entity['confidence']:.2f}")
            print(f"    Mentions: {entity['mention_count']}")
    else:
        print("\nNo entities found (article not processed yet)")

    print("\n" + "-" * 60 + "\n")


async def example_filter_by_type():
    """Example 2: Filter by entity type."""
    print("=== Example 2: Filter by Entity Type (PERSON) ===\n")

    article_id = "test-article-123"
    result = await get_article_entities(article_id, entity_type="PERSON")

    print(f"Total PERSON entities: {result['total_entities']}")

    for entity in result['entities']:
        print(f"  - {entity['name']}")
        print(f"    Confidence: {entity['confidence']:.2f}")
        print(f"    Wikidata ID: {entity.get('wikidata_id', 'Not available')}")

    print("\n" + "-" * 60 + "\n")


async def example_limit_results():
    """Example 3: Limit number of results."""
    print("=== Example 3: Limit Results (Top 10) ===\n")

    article_id = "test-article-123"
    result = await get_article_entities(article_id, limit=10)

    print(f"Requested limit: 10")
    print(f"Entities returned: {result['total_entities']}")
    print(f"Query time: {result['query_time_ms']}ms")

    print("\n" + "-" * 60 + "\n")


async def example_article_info():
    """Example 4: Get article metadata."""
    print("=== Example 4: Article Metadata ===\n")

    article_id = "test-article-123"

    try:
        info = await get_article_info(article_id)

        print(f"Article ID: {info['article_id']}")
        print(f"Title: {info['title']}")
        print(f"URL: {info['url']}")
        print(f"Published: {info['published_date']}")
        print(f"Entity Count: {info['entity_count']}")
        print(f"Query Time: {info['query_time_ms']}ms")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"Article '{article_id}' not found in graph")
            print("(This is normal if the article hasn't been processed yet)")

    print("\n" + "-" * 60 + "\n")


async def example_error_handling():
    """Example 5: Error handling."""
    print("=== Example 5: Error Handling ===\n")

    # Test validation error (limit > 200)
    print("Testing validation error (limit > 200):")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/graph/articles/test/entities",
                params={"limit": 300}
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"  Status: {e.response.status_code}")
        print(f"  Error: Validation failed (expected)")

    # Test nonexistent article (returns empty list, not error)
    print("\nTesting nonexistent article:")
    result = await get_article_entities("nonexistent-article-999")
    print(f"  Status: 200 OK")
    print(f"  Entities: {result['total_entities']} (returns empty list)")

    print("\n" + "-" * 60 + "\n")


async def example_combined_filters():
    """Example 6: Combined filters."""
    print("=== Example 6: Combined Filters ===\n")

    article_id = "test-article-123"

    # Get top 5 organizations
    result = await get_article_entities(
        article_id,
        entity_type="ORGANIZATION",
        limit=5
    )

    print(f"Top 5 ORGANIZATION entities:")
    print(f"Total found: {result['total_entities']}")

    for i, entity in enumerate(result['entities'], 1):
        print(f"\n{i}. {entity['name']}")
        print(f"   Type: {entity['type']}")
        print(f"   Confidence: {entity['confidence']:.2%}")
        print(f"   Mentions: {entity['mention_count']}")
        if entity.get('wikidata_id'):
            print(f"   Wikidata: https://www.wikidata.org/wiki/{entity['wikidata_id']}")

    print("\n" + "-" * 60 + "\n")


async def example_entity_analysis():
    """Example 7: Entity analysis and statistics."""
    print("=== Example 7: Entity Analysis ===\n")

    article_id = "test-article-123"
    result = await get_article_entities(article_id, limit=200)

    if result['total_entities'] > 0:
        entities = result['entities']

        # Calculate statistics
        avg_confidence = sum(e['confidence'] for e in entities) / len(entities)
        total_mentions = sum(e['mention_count'] for e in entities)

        # Count by type
        type_counts = {}
        for entity in entities:
            entity_type = entity['type']
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

        print(f"Article: {result['article_title'] or 'Untitled'}")
        print(f"\nStatistics:")
        print(f"  Total entities: {len(entities)}")
        print(f"  Average confidence: {avg_confidence:.2%}")
        print(f"  Total mentions: {total_mentions}")

        print(f"\nEntity types:")
        for entity_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {entity_type}: {count}")

        # Find highest confidence entity
        top_entity = max(entities, key=lambda x: x['confidence'])
        print(f"\nHighest confidence entity:")
        print(f"  Name: {top_entity['name']}")
        print(f"  Type: {top_entity['type']}")
        print(f"  Confidence: {top_entity['confidence']:.2%}")

        # Find most mentioned entity
        top_mentioned = max(entities, key=lambda x: x['mention_count'])
        print(f"\nMost mentioned entity:")
        print(f"  Name: {top_mentioned['name']}")
        print(f"  Mentions: {top_mentioned['mention_count']}")

    else:
        print("No entities available for analysis")

    print("\n" + "-" * 60 + "\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Article Entities Endpoint - Usage Examples")
    print("=" * 60 + "\n")

    examples = [
        example_basic_usage,
        example_filter_by_type,
        example_limit_results,
        example_article_info,
        example_error_handling,
        example_combined_filters,
        example_entity_analysis,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}\n")

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
