"""
Ingestion Service

Handles inserting relationship triplets into Neo4j graph.
Uses idempotent MERGE queries to prevent duplicates.

CRITICAL FIX (2025-12-28): Entity Canonicalization Merge Strategy
- Problem: Entities with same wikidata_id were stored as separate nodes
  (e.g., "Trump", "Donald Trump", "President Trump" all Q16944413)
- Solution: MERGE by wikidata_id when available, fallback to name
- See: Entity Canonicalization Fix - Duplicate Entity Merging
"""

import logging
import time
import asyncio
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.services.neo4j_service import neo4j_service
from app.models.graph import Triplet, Entity, Relationship
from app.core.metrics import (
    kg_ingestion_triplets_total,
    kg_ingestion_duration_seconds,
    kg_ingestion_batch_size,
    kg_nodes_created_total,
    kg_relationships_created_total
)

logger = logging.getLogger(__name__)


def _build_entity_merge_query(
    entity_var: str,
    has_wikidata_id: bool,
    wikidata_id_param: str,
    name_param: str,
    type_param: str,
    entity_id_param: str
) -> str:
    """
    Build MERGE clause for entity based on whether wikidata_id is available.

    Strategy:
    - If wikidata_id is provided: MERGE by wikidata_id (canonical merge)
      This ensures "Trump", "Donald Trump", "President Trump" all merge to one node
    - If wikidata_id is NULL: MERGE by name (legacy behavior)

    Args:
        entity_var: Variable name (subject/object)
        has_wikidata_id: Whether entity has a wikidata_id
        wikidata_id_param: Parameter name for wikidata_id
        name_param: Parameter name for entity name
        type_param: Parameter name for entity type
        entity_id_param: Parameter name for entity_id

    Returns:
        Cypher MERGE clause string
    """
    if has_wikidata_id:
        # MERGE by wikidata_id - canonical merge strategy
        # This ensures all entity mentions with same wikidata_id are merged
        return f"""
    // Create or update {entity_var} entity (MERGE by wikidata_id - canonical)
    MERGE ({entity_var}:Entity {{wikidata_id: ${wikidata_id_param}}})
    ON CREATE SET
        {entity_var}.name = ${name_param},
        {entity_var}.entity_id = ${entity_id_param},
        {entity_var}.type = ${type_param},
        {entity_var}.created_at = datetime(),
        {entity_var}.last_seen = datetime(),
        {entity_var}.aliases = [${name_param}]
    ON MATCH SET
        {entity_var}.last_seen = datetime(),
        {entity_var}.type = ${type_param},
        {entity_var}.entity_id = COALESCE({entity_var}.entity_id, ${entity_id_param}),
        {entity_var}.aliases = CASE
            WHEN ${name_param} IN COALESCE({entity_var}.aliases, []) THEN {entity_var}.aliases
            ELSE COALESCE({entity_var}.aliases, []) + ${name_param}
        END
"""
    else:
        # MERGE by name - fallback for entities without wikidata_id
        return f"""
    // Create or update {entity_var} entity (MERGE by name - no wikidata_id)
    MERGE ({entity_var}:Entity {{name: ${name_param}}})
    ON CREATE SET
        {entity_var}.entity_id = ${entity_id_param},
        {entity_var}.type = ${type_param},
        {entity_var}.created_at = datetime(),
        {entity_var}.last_seen = datetime()
    ON MATCH SET
        {entity_var}.last_seen = datetime(),
        {entity_var}.type = ${type_param},
        {entity_var}.wikidata_id = COALESCE({entity_var}.wikidata_id, ${wikidata_id_param}),
        {entity_var}.entity_id = COALESCE({entity_var}.entity_id, ${entity_id_param})
"""


async def execute_with_retry(cypher: str, parameters: dict, max_retries: int = 3) -> Dict[str, Any]:
    """
    Execute Neo4j query with automatic retry on deadlock errors.

    Deadlocks are transient errors that occur when multiple transactions
    compete for the same nodes/relationships. Retrying usually succeeds.

    Args:
        cypher: Cypher query to execute
        parameters: Query parameters
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        Query result summary

    Raises:
        Exception: If all retries fail
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            return await neo4j_service.execute_write(cypher, parameters)
        except Exception as e:
            error_str = str(e)

            # Check if it's a deadlock error
            if "DeadlockDetected" in error_str or "deadlock" in error_str.lower():
                last_error = e

                if attempt < max_retries - 1:
                    # Exponential backoff: 50ms, 100ms, 200ms
                    wait_time = 0.05 * (2 ** attempt)
                    logger.warning(
                        f"Deadlock detected (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time*1000:.0f}ms..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"Deadlock persisted after {max_retries} attempts. "
                        f"Query: {cypher[:100]}..."
                    )
            else:
                # Not a deadlock - re-raise immediately
                raise

    # All retries failed
    raise last_error


class IngestionService:
    """Service for ingesting triplets into Neo4j."""

    async def ingest_triplet(
        self,
        triplet: Triplet
    ) -> Dict[str, Any]:
        """
        Ingest a single (subject)-[relationship]->(object) triplet into Neo4j.

        Uses idempotent MERGE operations:
        - If entities/relationships exist, updates last_seen and mention_count
        - If new, creates them with initial properties

        Args:
            triplet: Triplet to ingest

        Returns:
            Summary of changes made
        """
        start_time = time.time()

        try:
            # Extract wikidata_ids
            subject_wikidata_id = triplet.subject.properties.get("wikidata_id")
            object_wikidata_id = triplet.object.properties.get("wikidata_id")

            # Generate entity_id (deterministic hash of wikidata_id or name + type)
            if subject_wikidata_id:
                subject_entity_id = hashlib.md5(
                    f"wikidata:{subject_wikidata_id}".encode('utf-8')
                ).hexdigest()[:16]
            else:
                subject_entity_id = hashlib.md5(
                    f"{triplet.subject.name}:{triplet.subject.type}".encode('utf-8')
                ).hexdigest()[:16]

            if object_wikidata_id:
                object_entity_id = hashlib.md5(
                    f"wikidata:{object_wikidata_id}".encode('utf-8')
                ).hexdigest()[:16]
            else:
                object_entity_id = hashlib.md5(
                    f"{triplet.object.name}:{triplet.object.type}".encode('utf-8')
                ).hexdigest()[:16]

            # Build Cypher query dynamically based on wikidata_id availability
            # CRITICAL FIX (2025-12-28): MERGE by wikidata_id when available
            # This ensures "Trump", "Donald Trump", "President Trump" all merge to one node
            subject_merge = _build_entity_merge_query(
                entity_var="subject",
                has_wikidata_id=bool(subject_wikidata_id),
                wikidata_id_param="subject_wikidata_id",
                name_param="subject_name",
                type_param="subject_type",
                entity_id_param="subject_entity_id"
            )

            object_merge = _build_entity_merge_query(
                entity_var="object",
                has_wikidata_id=bool(object_wikidata_id),
                wikidata_id_param="object_wikidata_id",
                name_param="object_name",
                type_param="object_type",
                entity_id_param="object_entity_id"
            )

            # Build complete Cypher query
            cypher = f"""
            {subject_merge}
            WITH subject

            {object_merge}
            WITH subject, object

            // Create or update relationship
            MERGE (subject)-[rel:{{rel_type}}]->(object)
            ON CREATE SET
                rel.confidence = $confidence,
                rel.mention_count = 1,
                rel.created_at = datetime(),
                rel.evidence = $evidence,
                rel.source_url = $source_url,
                rel.article_id = $article_id,
                rel.sentiment_score = $sentiment_score,
                rel.sentiment_category = $sentiment_category,
                rel.sentiment_confidence = $sentiment_confidence
            ON MATCH SET
                rel.mention_count = rel.mention_count + 1,
                rel.last_seen = datetime(),
                rel.confidence = CASE
                    WHEN $confidence > rel.confidence THEN $confidence
                    ELSE rel.confidence
                END,
                rel.sentiment_score = COALESCE($sentiment_score, rel.sentiment_score),
                rel.sentiment_category = COALESCE($sentiment_category, rel.sentiment_category),
                rel.sentiment_confidence = COALESCE($sentiment_confidence, rel.sentiment_confidence)

            RETURN subject, rel, object
            """

            # Replace relationship type placeholder (Cypher doesn't allow parameterized relationship types)
            # CRITICAL: Normalize to UPPERCASE to prevent case-inconsistency duplicates
            # See: CLAUDE.md Critical Learning #31
            relationship_type_normalized = triplet.relationship.relationship_type.upper()
            cypher_final = cypher.replace("{rel_type}", relationship_type_normalized)

            parameters = {
                "subject_name": triplet.subject.name,
                "subject_type": triplet.subject.type,
                "subject_entity_id": subject_entity_id,
                "subject_wikidata_id": subject_wikidata_id,
                "object_name": triplet.object.name,
                "object_type": triplet.object.type,
                "object_entity_id": object_entity_id,
                "object_wikidata_id": object_wikidata_id,
                "confidence": triplet.relationship.confidence,
                "evidence": triplet.relationship.evidence,
                "source_url": triplet.relationship.source_url,
                "article_id": triplet.relationship.article_id,
                "sentiment_score": triplet.relationship.sentiment_score,
                "sentiment_category": triplet.relationship.sentiment_category,
                "sentiment_confidence": triplet.relationship.sentiment_confidence
            }

            summary = await execute_with_retry(cypher_final, parameters)

            # Record metrics
            duration = time.time() - start_time
            kg_ingestion_duration_seconds.observe(duration)
            kg_ingestion_triplets_total.labels(status='success').inc()

            # Record entity and relationship creation metrics
            if summary.get("nodes_created", 0) > 0:
                # Track by entity type (subject and object might be new)
                kg_nodes_created_total.labels(entity_type=triplet.subject.type).inc()
                if triplet.object.type != triplet.subject.type:
                    kg_nodes_created_total.labels(entity_type=triplet.object.type).inc()

            if summary.get("relationships_created", 0) > 0:
                kg_relationships_created_total.labels(
                    relationship_type=triplet.relationship.relationship_type
                ).inc()

            logger.debug(
                f"Ingested triplet in {duration:.3f}s: "
                f"({triplet.subject.name})-[{triplet.relationship.relationship_type}]->({triplet.object.name})"
            )

            return summary

        except Exception as e:
            # Record failure metrics
            duration = time.time() - start_time
            kg_ingestion_duration_seconds.observe(duration)
            kg_ingestion_triplets_total.labels(status='failed').inc()

            logger.error(f"Failed to ingest triplet in {duration:.3f}s: {e}", exc_info=True)
            raise

    async def ingest_triplets_batch(
        self,
        triplets: List[Triplet],
        article_id: str,
        source_url: str
    ) -> Dict[str, Any]:
        """
        Ingest multiple triplets from a single article.

        Args:
            triplets: List of triplets to ingest
            article_id: Source article ID
            source_url: Source article URL

        Returns:
            Aggregated summary of changes
        """
        # Record batch size
        kg_ingestion_batch_size.observe(len(triplets))

        total_summary = {
            "nodes_created": 0,
            "nodes_deleted": 0,
            "relationships_created": 0,
            "relationships_deleted": 0,
            "properties_set": 0,
            "triplets_processed": 0
        }

        for triplet in triplets:
            try:
                # Add article metadata to relationship
                triplet.relationship.article_id = article_id
                triplet.relationship.source_url = source_url

                summary = await self.ingest_triplet(triplet)

                # Aggregate counts
                total_summary["nodes_created"] += summary.get("nodes_created", 0)
                total_summary["relationships_created"] += summary.get("relationships_created", 0)
                total_summary["properties_set"] += summary.get("properties_set", 0)
                total_summary["triplets_processed"] += 1

            except Exception as e:
                logger.error(
                    f"Failed to ingest triplet from article {article_id}: {e}",
                    exc_info=True
                )
                # Continue with other triplets

        logger.info(
            f"Ingested {total_summary['triplets_processed']}/{len(triplets)} triplets from article {article_id}. "
            f"Created {total_summary['nodes_created']} nodes, {total_summary['relationships_created']} relationships."
        )

        return total_summary


# Global ingestion service instance
ingestion_service = IngestionService()
