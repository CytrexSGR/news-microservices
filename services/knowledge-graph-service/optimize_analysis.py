#!/usr/bin/env python3
"""
Knowledge Graph Service Optimization Analysis

Comprehensive analysis of Neo4j indexes, query performance, and schema optimization.
"""

import asyncio
import json
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any, Tuple
from neo4j import AsyncGraphDatabase, AsyncDriver
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeGraphOptimizer:
    """Analyze and optimize Neo4j knowledge graph performance."""

    def __init__(self, neo4j_uri: str, user: str, password: str):
        self.uri = neo4j_uri
        self.user = user
        self.password = password
        self.driver: AsyncDriver = None
        self.results = {}

    async def connect(self):
        """Connect to Neo4j."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=10
            )
            await self.driver.verify_connectivity()
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Neo4j."""
        if self.driver:
            await self.driver.close()
            logger.info("Disconnected from Neo4j")

    async def run_query(self, query: str, params: Dict = None) -> Tuple[List[Dict], float]:
        """Run a query and return results with timing."""
        start_time = time.time()
        async with self.driver.session() as session:
            result = await session.run(query, params or {})
            records = await result.data()
        elapsed_ms = (time.time() - start_time) * 1000
        return records, elapsed_ms

    async def analyze_indexes(self) -> Dict[str, Any]:
        """Analyze current indexes."""
        logger.info("Analyzing indexes...")

        try:
            query = "SHOW INDEXES"
            indexes, _ = await self.run_query(query)
        except Exception as e:
            logger.warning(f"Could not retrieve indexes: {e}")
            indexes = []

        analysis = {
            "total_indexes": len(indexes),
            "indexes": indexes,
            "recommendations": []
        }

        # Check for missing indexes
        index_names = [str(idx) for idx in indexes]
        
        if not any('Entity' in str(idx) and 'name' in str(idx) for idx in index_names):
            analysis["recommendations"].append({
                "type": "missing_index",
                "entity": "Entity",
                "property": "name",
                "cypher": "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "reason": "Index on Entity.name improves entity lookups by 10-50x"
            })

        if not any('Entity' in str(idx) and 'type' in str(idx) for idx in index_names):
            analysis["recommendations"].append({
                "type": "missing_index",
                "entity": "Entity",
                "property": "type",
                "cypher": "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                "reason": "Index on Entity.type improves type-based filtering by 5-20x"
            })

        return analysis

    async def analyze_schema(self) -> Dict[str, Any]:
        """Analyze graph schema and data distribution."""
        logger.info("Analyzing schema...")

        # Get node and relationship counts
        try:
            count_query = "MATCH (n) RETURN count(n) AS node_count"
            node_count_result, _ = await self.run_query(count_query)
            node_count = node_count_result[0]['node_count'] if node_count_result else 0

            rel_query = "MATCH ()-[r]->() RETURN count(r) AS rel_count"
            rel_count_result, _ = await self.run_query(rel_query)
            rel_count = rel_count_result[0]['rel_count'] if rel_count_result else 0

            entity_query = "MATCH (e:Entity) RETURN count(DISTINCT e.type) AS type_count"
            entity_result, _ = await self.run_query(entity_query)
            entity_count = entity_result[0]['type_count'] if entity_result else 0
        except Exception as e:
            logger.warning(f"Schema analysis error: {e}")
            return {"error": str(e), "recommendations": []}

        return {
            "total_nodes": node_count,
            "total_relationships": rel_count,
            "entity_types_count": entity_count,
            "recommendations": [
                {
                    "type": "high_cardinality",
                    "issue": "Large graph detected - optimize common query patterns",
                    "solution": "Ensure indexes on frequently filtered properties"
                },
                {
                    "type": "relationships",
                    "issue": "Relationship traversals can be expensive",
                    "solution": "Use confidence filtering (>= 0.5) to reduce result set"
                }
            ]
        }

    async def profile_common_queries(self) -> Dict[str, Any]:
        """Profile performance of common query patterns."""
        logger.info("Profiling common queries...")

        queries = {
            "entity_lookup": {
                "cypher": "MATCH (e:Entity) WHERE e.name CONTAINS 'Trump' RETURN e LIMIT 10",
                "description": "Entity name lookup (critical path)",
                "runs": 3
            },
            "entity_connections": {
                "cypher": """
                MATCH (source:Entity {name: 'Trump'})-[r]->(target:Entity)
                WHERE r.confidence >= 0.5
                RETURN target.name, type(r), r.confidence
                ORDER BY r.confidence DESC
                LIMIT 50
                """,
                "description": "Get entity connections with confidence filter",
                "runs": 3
            },
            "type_filter": {
                "cypher": """
                MATCH (e:Entity)
                WHERE e.type = 'PERSON'
                RETURN e.name, e.connection_count
                LIMIT 100
                """,
                "description": "Filter entities by type (supports analytics)",
                "runs": 3
            },
            "relationship_filter": {
                "cypher": """
                MATCH (source:Entity)-[r]->(target:Entity)
                WHERE r.confidence >= 0.8
                RETURN source.name, target.name, r.confidence
                LIMIT 100
                """,
                "description": "Filter relationships by high confidence",
                "runs": 3
            },
            "full_text_search": {
                "cypher": """
                MATCH (e:Entity)
                WHERE LOWER(e.name) CONTAINS LOWER('tesla')
                RETURN e.name, e.type
                LIMIT 20
                """,
                "description": "Full-text search on entity names",
                "runs": 3
            }
        }

        results = {}
        for query_name, query_info in queries.items():
            timings = []
            logger.info(f"  Profiling {query_name}...")

            for i in range(query_info["runs"]):
                try:
                    _, elapsed = await self.run_query(query_info["cypher"])
                    timings.append(elapsed)
                except Exception as e:
                    logger.warning(f"    Run {i+1} failed: {e}")

            if timings:
                results[query_name] = {
                    "description": query_info["description"],
                    "min_ms": min(timings),
                    "max_ms": max(timings),
                    "avg_ms": statistics.mean(timings),
                    "slow": max(timings) > 500
                }

        return results

    async def analyze_entity_canonicalization(self) -> Dict[str, Any]:
        """Analyze entity deduplication quality."""
        logger.info("Analyzing entity canonicalization...")

        try:
            # Check confidence distribution
            confidence_query = """
            MATCH ()-[r]->()
            WHERE r.confidence IS NOT NULL
            RETURN
                count(*) AS total,
                sum(CASE WHEN r.confidence >= 0.8 THEN 1 ELSE 0 END) AS high,
                sum(CASE WHEN r.confidence >= 0.5 AND r.confidence < 0.8 THEN 1 ELSE 0 END) AS medium,
                sum(CASE WHEN r.confidence < 0.5 THEN 1 ELSE 0 END) AS low
            """

            confidence, _ = await self.run_query(confidence_query)
            conf_data = confidence[0] if confidence else {}
        except Exception as e:
            logger.warning(f"Canonicalization analysis error: {e}")
            conf_data = {}

        return {
            "confidence_distribution": conf_data,
            "recommendations": [
                {
                    "type": "confidence_filtering",
                    "issue": "Ensure relationships are filtered by confidence",
                    "solution": "Use WHERE r.confidence >= 0.5 in graph queries"
                },
                {
                    "type": "entity_deduplication",
                    "issue": "Case-sensitive entity names may create duplicates",
                    "solution": "Normalize entity names to canonical form (title case)"
                }
            ]
        }

    async def run_optimization_analysis(self) -> Dict[str, Any]:
        """Run complete optimization analysis."""
        await self.connect()

        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "indexes": await self.analyze_indexes(),
                "schema": await self.analyze_schema(),
                "query_performance": await self.profile_common_queries(),
                "entity_canonicalization": await self.analyze_entity_canonicalization()
            }
        finally:
            await self.disconnect()


async def main():
    """Run the optimization analysis."""
    optimizer = KnowledgeGraphOptimizer(
        neo4j_uri="bolt://neo4j:7687",
        user="neo4j",
        password="neo4j_password_2024"
    )

    results = await optimizer.run_optimization_analysis()

    # Save results to file
    output_file = "/app/optimization_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Optimization analysis saved to {output_file}")

    # Print summary
    print("\n" + "="*80)
    print("KNOWLEDGE GRAPH OPTIMIZATION ANALYSIS SUMMARY")
    print("="*80)

    print("\n1. INDEX ANALYSIS:")
    print(f"   Total Indexes: {results['indexes']['total_indexes']}")
    print(f"   Recommendations: {len(results['indexes']['recommendations'])}")
    for rec in results['indexes']['recommendations'][:3]:
        print(f"     - {rec['entity']}.{rec['property']}: {rec['reason']}")

    print("\n2. QUERY PERFORMANCE (avg/max time):")
    for name, metrics in sorted(results['query_performance'].items(),
                               key=lambda x: x[1].get('max_ms', 0), reverse=True):
        status = "SLOW" if metrics.get('slow') else "OK"
        print(f"     {name:30s}: {metrics['avg_ms']:7.1f}ms / {metrics['max_ms']:7.1f}ms [{status}]")

    print("\n3. SCHEMA ANALYSIS:")
    schema = results['schema']
    if 'error' not in schema:
        print(f"   Total Nodes: {schema.get('total_nodes', 'N/A')}")
        print(f"   Total Relationships: {schema.get('total_relationships', 'N/A')}")
        print(f"   Entity Types: {schema.get('entity_types_count', 'N/A')}")

    print("\n4. ENTITY CANONICALIZATION:")
    canon = results['entity_canonicalization']
    conf = canon.get('confidence_distribution', {})
    if conf:
        print(f"   Confidence Distribution:")
        print(f"     - High (≥0.8): {conf.get('high', 0)}")
        print(f"     - Medium (0.5-0.8): {conf.get('medium', 0)}")
        print(f"     - Low (<0.5): {conf.get('low', 0)}")

    print("\n" + "="*80)
    print(f"Full results saved to: {output_file}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
