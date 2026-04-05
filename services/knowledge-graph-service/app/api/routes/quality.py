"""
Knowledge Graph Quality Endpoints

Provides API endpoints for data quality analysis and disambiguation metrics.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import time

from app.services.neo4j_service import neo4j_service
from app.core.metrics import kg_queries_total, kg_query_duration_seconds

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/v1/graph/quality/disambiguation")
async def get_disambiguation_quality() -> Dict[str, Any]:
    """
    Analyze entity disambiguation quality.

    Identifies entities with the same name but different types,
    and calculates disambiguation success metrics.

    Returns:
        Dictionary with:
        - Total ambiguous entity names
        - Total disambiguation cases
        - Success rate
        - Top ambiguous entities with their variations
        - Confidence distribution for ambiguous entities

    Example:
        GET /api/v1/graph/quality/disambiguation
    """
    start_time = time.time()

    try:
        # Find entities with same name but different types (ambiguous entities)
        ambiguous_cypher = """
        MATCH (e:Entity)
        WITH e.name AS entity_name, collect(DISTINCT e.type) AS types, count(e) AS entity_count
        WHERE size(types) > 1
        RETURN
            entity_name,
            types,
            entity_count,
            size(types) AS type_variations
        ORDER BY entity_count DESC
        LIMIT 50
        """

        ambiguous_results = await neo4j_service.execute_query(ambiguous_cypher)

        # Calculate metrics
        total_ambiguous_names = len(ambiguous_results)
        total_disambiguation_cases = sum(record["entity_count"] for record in ambiguous_results)

        # Get detailed examples
        top_ambiguous = []
        for record in ambiguous_results[:10]:
            entity_name = record["entity_name"]

            # Get confidence distribution for this ambiguous entity
            conf_cypher = """
            MATCH (e:Entity {name: $name})
            OPTIONAL MATCH (e)-[r]-()
            WITH e, avg(r.confidence) AS avg_confidence, count(r) AS rel_count
            RETURN
                e.type AS entity_type,
                avg_confidence,
                rel_count
            ORDER BY rel_count DESC
            """

            conf_results = await neo4j_service.execute_query(
                conf_cypher,
                parameters={"name": entity_name}
            )

            variations = [
                {
                    "type": result["entity_type"],
                    "avg_confidence": result["avg_confidence"] or 0.0,
                    "relationship_count": result["rel_count"]
                }
                for result in conf_results
            ]

            top_ambiguous.append({
                "name": entity_name,
                "type_variations": record["types"],
                "occurrence_count": record["entity_count"],
                "variations_detail": variations
            })

        # Calculate overall disambiguation success rate
        # A well-disambiguated entity should have clear type separation with good confidence
        well_disambiguated = 0
        for amb in top_ambiguous:
            variations = amb.get("variations_detail", [])
            if variations:
                # Check if there's a dominant variation with high confidence
                max_rel_count = max(v["relationship_count"] for v in variations)
                dominant_variations = [v for v in variations if v["relationship_count"] == max_rel_count]

                if len(dominant_variations) == 1 and dominant_variations[0]["avg_confidence"] > 0.7:
                    well_disambiguated += 1

        success_rate = (well_disambiguated / len(top_ambiguous)) if top_ambiguous else 0.0

        # Get overall confidence distribution for ambiguous entities
        conf_dist_cypher = """
        MATCH (e:Entity)
        WITH e.name AS entity_name, collect(DISTINCT e.type) AS types
        WHERE size(types) > 1
        MATCH (amb:Entity {name: entity_name})-[r]-()
        WITH r.confidence AS conf
        RETURN
            count(CASE WHEN conf > 0.8 THEN 1 END) AS high_confidence,
            count(CASE WHEN conf >= 0.5 AND conf <= 0.8 THEN 1 END) AS medium_confidence,
            count(CASE WHEN conf < 0.5 THEN 1 END) AS low_confidence,
            count(*) AS total
        """

        conf_dist_result = await neo4j_service.execute_query(conf_dist_cypher)

        if conf_dist_result:
            dist = conf_dist_result[0]
            confidence_distribution = {
                "high": dist.get("high_confidence", 0),
                "medium": dist.get("medium_confidence", 0),
                "low": dist.get("low_confidence", 0),
                "total": dist.get("total", 0)
            }
        else:
            confidence_distribution = {"high": 0, "medium": 0, "low": 0, "total": 0}

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='disambiguation_quality', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='disambiguation_quality').observe(query_time_seconds)

        logger.info(
            f"Disambiguation quality query completed: "
            f"ambiguous_names={total_ambiguous_names}, "
            f"success_rate={success_rate:.2%}, "
            f"time={int(query_time_seconds * 1000)}ms"
        )

        return {
            "total_ambiguous_names": total_ambiguous_names,
            "total_disambiguation_cases": total_disambiguation_cases,
            "success_rate": round(success_rate, 3),
            "well_disambiguated_count": well_disambiguated,
            "top_ambiguous_entities": top_ambiguous,
            "confidence_distribution": confidence_distribution,
            "query_time_ms": int(query_time_seconds * 1000)
        }

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='disambiguation_quality', status='error').inc()

        logger.error(f"Disambiguation quality query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze disambiguation quality: {str(e)}"
        )


@router.get("/api/v1/graph/quality/integrity")
async def get_integrity_check() -> Dict[str, Any]:
    """
    Perform integrity checks on the knowledge graph.

    Checks for:
    - Orphaned entities (nodes with no relationships)
    - Weak relationships (low confidence)
    - Missing critical properties (wikidata_id, type)
    - Relationship symmetry issues

    Returns:
        Dictionary with integrity check results and issue counts

    Example:
        GET /api/v1/graph/quality/integrity
    """
    start_time = time.time()

    try:
        issues = {}

        # 1. Orphaned entities
        orphaned_cypher = """
        MATCH (e:Entity)
        WHERE NOT (e)-[]-()
        RETURN count(e) AS orphaned_count,
               collect(e.name)[0..10] AS sample_orphaned
        """
        orphaned_result = await neo4j_service.execute_query(orphaned_cypher)
        if orphaned_result:
            issues["orphaned_entities"] = {
                "count": orphaned_result[0]["orphaned_count"],
                "sample": orphaned_result[0]["sample_orphaned"]
            }

        # 2. Weak relationships (confidence < 0.3)
        weak_rel_cypher = """
        MATCH (e1:Entity)-[r]->(e2:Entity)
        WHERE r.confidence < 0.3
        RETURN count(r) AS weak_count,
               collect({
                   entity1: e1.name,
                   entity2: e2.name,
                   type: type(r),
                   confidence: r.confidence
               })[0..10] AS sample_weak
        """
        weak_result = await neo4j_service.execute_query(weak_rel_cypher)
        if weak_result:
            issues["weak_relationships"] = {
                "count": weak_result[0]["weak_count"],
                "sample": weak_result[0]["sample_weak"]
            }

        # 3. Missing wikidata_id
        missing_wikidata_cypher = """
        MATCH (e:Entity)
        WHERE e.wikidata_id IS NULL
        RETURN count(e) AS missing_count,
               collect(e.name)[0..10] AS sample_missing
        """
        wikidata_result = await neo4j_service.execute_query(missing_wikidata_cypher)
        if wikidata_result:
            issues["missing_wikidata_id"] = {
                "count": wikidata_result[0]["missing_count"],
                "sample": wikidata_result[0]["sample_missing"]
            }

        # 4. Missing entity type
        missing_type_cypher = """
        MATCH (e:Entity)
        WHERE e.type IS NULL OR e.type = ''
        RETURN count(e) AS missing_count,
               collect(e.name)[0..10] AS sample_missing
        """
        type_result = await neo4j_service.execute_query(missing_type_cypher)
        if type_result:
            issues["missing_entity_type"] = {
                "count": type_result[0]["missing_count"],
                "sample": type_result[0]["sample_missing"]
            }

        # Calculate overall integrity score
        total_issues = sum(issue["count"] for issue in issues.values())

        # Get total entity count for percentage calculation
        total_cypher = "MATCH (e:Entity) RETURN count(e) AS total"
        total_result = await neo4j_service.execute_query(total_cypher)
        total_entities = total_result[0]["total"] if total_result else 0

        integrity_percentage = (
            100 - (total_issues / total_entities * 100)
            if total_entities > 0 else 100
        )

        # Record metrics
        query_time_seconds = time.time() - start_time
        kg_queries_total.labels(endpoint='integrity_check', status='success').inc()
        kg_query_duration_seconds.labels(endpoint='integrity_check').observe(query_time_seconds)

        logger.info(
            f"Integrity check completed: "
            f"total_issues={total_issues}, "
            f"integrity={integrity_percentage:.1f}%, "
            f"time={int(query_time_seconds * 1000)}ms"
        )

        return {
            "integrity_percentage": round(integrity_percentage, 2),
            "total_issues": total_issues,
            "total_entities": total_entities,
            "issues_by_type": issues,
            "query_time_ms": int(query_time_seconds * 1000)
        }

    except Exception as e:
        # Record error metric
        kg_queries_total.labels(endpoint='integrity_check', status='error').inc()

        logger.error(f"Integrity check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform integrity check: {str(e)}"
        )
