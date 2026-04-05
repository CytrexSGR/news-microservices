"""
Pathfinding Service

Implements graph pathfinding algorithms using Neo4j Cypher queries.
"""

import logging
from typing import List, Optional
import time

from app.services.neo4j_service import neo4j_service
from app.models.pathfinding import PathNode, PathRelationship, PathResult

logger = logging.getLogger(__name__)


class PathfindingService:
    """Service for finding paths between entities in the knowledge graph."""

    @staticmethod
    async def find_paths(
        entity1: str,
        entity2: str,
        max_depth: int = 3,
        limit: int = 3,
        min_confidence: float = 0.5
    ) -> List[PathResult]:
        """
        Find paths between two entities using Neo4j shortestPath.

        Args:
            entity1: Source entity name
            entity2: Target entity name
            max_depth: Maximum path length (1-5 hops)
            limit: Maximum number of paths to return (1-10)
            min_confidence: Minimum relationship confidence (0.0-1.0)

        Returns:
            List of PathResult objects

        Example:
            paths = await pathfinding_service.find_paths(
                "Elon Musk",
                "Tesla",
                max_depth=3,
                limit=5
            )
        """
        start_time = time.time()

        # Build Cypher query with variable path length
        cypher = f"""
        MATCH path = allShortestPaths(
            (e1:Entity {{name: $entity1}})-[*1..{max_depth}]-(e2:Entity {{name: $entity2}})
        )
        WHERE all(r in relationships(path) WHERE r.confidence >= $min_confidence)
        WITH path, length(path) AS path_length
        ORDER BY path_length
        LIMIT $limit
        RETURN
            [node IN nodes(path) | {{name: node.name, type: node.type}}] AS nodes,
            [rel IN relationships(path) | {{
                type: type(rel),
                confidence: rel.confidence,
                evidence: rel.evidence
            }}] AS relationships,
            path_length
        """

        logger.info(
            f"Finding paths: {entity1} -> {entity2} "
            f"(max_depth={max_depth}, limit={limit}, min_confidence={min_confidence})"
        )

        try:
            results = await neo4j_service.execute_query(
                cypher,
                parameters={
                    "entity1": entity1,
                    "entity2": entity2,
                    "limit": limit,
                    "min_confidence": min_confidence
                }
            )

            paths = []
            for record in results:
                # Parse nodes
                nodes = [
                    PathNode(name=node["name"], type=node["type"])
                    for node in record["nodes"]
                ]

                # Parse relationships
                relationships = [
                    PathRelationship(
                        type=rel["type"],
                        confidence=rel["confidence"],
                        evidence=rel.get("evidence")
                    )
                    for rel in record["relationships"]
                ]

                path_result = PathResult(
                    length=record["path_length"],
                    nodes=nodes,
                    relationships=relationships
                )
                paths.append(path_result)

            query_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Found {len(paths)} paths in {query_time_ms}ms: "
                f"{entity1} -> {entity2}"
            )

            return paths

        except Exception as e:
            logger.error(f"Pathfinding query failed: {e}", exc_info=True)
            raise


# Global service instance
pathfinding_service = PathfindingService()
