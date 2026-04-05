#!/usr/bin/env python3
"""
Pathfinding Example Script

Demonstrates how to use the Knowledge Graph pathfinding endpoint.
"""

import asyncio
import httpx
from typing import Optional, List, Dict, Any


class PathfindingClient:
    """Client for Knowledge Graph pathfinding API."""

    def __init__(self, base_url: str = "http://localhost:8111"):
        self.base_url = base_url

    async def find_path(
        self,
        entity1: str,
        entity2: str,
        max_depth: int = 3,
        limit: int = 3,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        Find paths between two entities.

        Args:
            entity1: Source entity name
            entity2: Target entity name
            max_depth: Maximum path length (1-5)
            limit: Maximum number of paths (1-10)
            min_confidence: Minimum relationship confidence (0.0-1.0)

        Returns:
            Pathfinding response dictionary
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/graph/path/{entity1}/{entity2}",
                params={
                    "max_depth": max_depth,
                    "limit": limit,
                    "min_confidence": min_confidence
                }
            )
            response.raise_for_status()
            return response.json()

    def print_paths(self, result: Dict[str, Any]):
        """
        Pretty print pathfinding results.

        Args:
            result: Pathfinding response dictionary
        """
        print(f"\n{'='*80}")
        print(f"Pathfinding: {result['entity1']} → {result['entity2']}")
        print(f"{'='*80}")
        print(f"Max Depth: {result['max_depth']}")
        print(f"Paths Found: {result['total_paths_found']}")
        print(f"Shortest Path: {result['shortest_path_length']} hops")
        print(f"Query Time: {result['query_time_ms']}ms")
        print()

        if not result['paths']:
            print("❌ No paths found between these entities")
            return

        for i, path in enumerate(result['paths'], 1):
            print(f"\n{'─'*80}")
            print(f"Path {i} (Length: {path['length']} hops)")
            print(f"{'─'*80}")

            # Print path visualization
            for j, node in enumerate(path['nodes']):
                # Print node
                print(f"\n  [{node['type']}] {node['name']}")

                # Print relationship to next node
                if j < len(path['relationships']):
                    rel = path['relationships'][j]
                    print(f"    ↓ {rel['type']} (confidence: {rel['confidence']:.2f})")
                    if rel.get('evidence'):
                        print(f"    💬 \"{rel['evidence'][:80]}...\"" if len(rel['evidence']) > 80 else f"    💬 \"{rel['evidence']}\"")

        print(f"\n{'='*80}\n")


async def example_basic():
    """Example: Basic pathfinding query."""
    print("\n### Example 1: Basic Pathfinding ###")

    client = PathfindingClient()
    result = await client.find_path("Trump", "Tesla")
    client.print_paths(result)


async def example_custom_params():
    """Example: Custom parameters."""
    print("\n### Example 2: Custom Parameters ###")

    client = PathfindingClient()
    result = await client.find_path(
        "Trump",
        "Tesla",
        max_depth=4,
        limit=5,
        min_confidence=0.7
    )
    client.print_paths(result)


async def example_no_path():
    """Example: No path found."""
    print("\n### Example 3: No Path Found ###")

    client = PathfindingClient()
    result = await client.find_path("NonExistentEntity", "Tesla")
    client.print_paths(result)


async def example_shortest_path():
    """Example: Find shortest path between entities."""
    print("\n### Example 4: Shortest Path Analysis ###")

    client = PathfindingClient()

    # Test multiple entity pairs
    pairs = [
        ("Trump", "Tesla"),
        ("Trump", "Biden"),
        ("Musk", "Tesla"),
    ]

    for entity1, entity2 in pairs:
        result = await client.find_path(entity1, entity2, max_depth=4, limit=1)
        if result['paths']:
            path = result['paths'][0]
            print(f"{entity1} → {entity2}: {path['length']} hops ({result['query_time_ms']}ms)")
            print(f"  Path: {' → '.join(node['name'] for node in path['nodes'])}")
        else:
            print(f"{entity1} → {entity2}: No path found")


async def example_relationship_types():
    """Example: Analyze relationship types in paths."""
    print("\n### Example 5: Relationship Type Analysis ###")

    client = PathfindingClient()
    result = await client.find_path("Trump", "Tesla", limit=10)

    if result['paths']:
        # Count relationship types
        rel_types: Dict[str, int] = {}
        for path in result['paths']:
            for rel in path['relationships']:
                rel_type = rel['type']
                rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        print(f"Relationship types in {len(result['paths'])} paths:")
        for rel_type, count in sorted(rel_types.items(), key=lambda x: -x[1]):
            print(f"  {rel_type}: {count}")


async def example_confidence_analysis():
    """Example: Analyze confidence scores."""
    print("\n### Example 6: Confidence Analysis ###")

    client = PathfindingClient()
    result = await client.find_path("Trump", "Tesla", limit=10)

    if result['paths']:
        # Analyze confidence scores
        all_confidences = []
        for path in result['paths']:
            path_confidences = [rel['confidence'] for rel in path['relationships']]
            avg_confidence = sum(path_confidences) / len(path_confidences)
            all_confidences.extend(path_confidences)

            print(f"Path {path['length']} hops: avg confidence = {avg_confidence:.2f}")

        overall_avg = sum(all_confidences) / len(all_confidences)
        print(f"\nOverall average confidence: {overall_avg:.2f}")
        print(f"Min confidence: {min(all_confidences):.2f}")
        print(f"Max confidence: {max(all_confidences):.2f}")


async def main():
    """Run all examples."""
    examples = [
        ("Basic Pathfinding", example_basic),
        ("Custom Parameters", example_custom_params),
        ("No Path Found", example_no_path),
        ("Shortest Path Analysis", example_shortest_path),
        ("Relationship Type Analysis", example_relationship_types),
        ("Confidence Analysis", example_confidence_analysis),
    ]

    for name, func in examples:
        try:
            print(f"\n{'#'*80}")
            print(f"# {name}")
            print(f"{'#'*80}")
            await func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║      Knowledge Graph Pathfinding Examples                      ║
    ║                                                                 ║
    ║  This script demonstrates various pathfinding use cases        ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())

    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  Examples completed!                                            ║
    ║                                                                 ║
    ║  Try running individual examples:                               ║
    ║    python pathfinding_example.py                                ║
    ║                                                                 ║
    ║  Or use the API directly:                                       ║
    ║    curl 'http://localhost:8111/api/v1/graph/path/Trump/Tesla'  ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
