"""
Knowledge Graph Enrichment API Endpoints

Admin-only endpoints for manual Knowledge Graph enrichment.
Provides analysis, tool execution, and enrichment application.
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.enrichment_service import EnrichmentService
from app.services.wikipedia_client import WikipediaClient
from app.services.neo4j_service import neo4j_service
from app.config import settings

router = APIRouter(prefix="/api/v1/graph/admin/enrichment", tags=["enrichment"])
logger = logging.getLogger(__name__)

# Initialize enrichment service with Wikipedia client
wikipedia_client = WikipediaClient(
    scraping_service_url=getattr(settings, 'SCRAPING_SERVICE_URL', 'http://news-scraping-service:8009')
)
enrichment_service = EnrichmentService(wikipedia_client=wikipedia_client)


# ===========================
# Request/Response Models
# ===========================

class AnalyzeRequest(BaseModel):
    """Enrichment analysis request"""
    analysis_type: str = Field(
        default="not_applicable_relationships",
        description="Type of analysis (currently only 'not_applicable_relationships')"
    )
    limit: int = Field(default=100, ge=1, le=500, description="Maximum candidates")
    min_occurrence: int = Field(default=5, ge=1, le=100, description="Minimum occurrence count")


class ExecuteToolRequest(BaseModel):
    """Tool execution request"""
    tool: str = Field(..., description="Tool to execute (wikipedia, research_perplexity, google_deep_research)")
    entity1: str = Field(..., description="First entity name")
    entity2: str = Field(..., description="Second entity name")
    language: str = Field(default="de", description="Language for Wikipedia tool (de, en)")
    # Additional tool-specific parameters can be added here


class ApplyEnrichmentRequest(BaseModel):
    """Enrichment application request"""
    entity1: str = Field(..., description="First entity name")
    entity2: str = Field(..., description="Second entity name")
    new_relationship_type: str = Field(..., description="New relationship type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    evidence: str = Field(..., description="Evidence/context for relationship")
    source: str = Field(default="manual_enrichment", description="Source of enrichment")


# ===========================
# API Endpoints
# ===========================

@router.post("/analyze")
async def analyze_for_enrichment(request: AnalyzeRequest):
    """
    Analyze Knowledge Graph for enrichment opportunities.

    Identifies entity pairs with NOT_APPLICABLE relationships that
    occur frequently and are candidates for enrichment.

    Returns:
        - candidates: List of entity pairs with suggested tools
        - summary: Statistics about enrichment opportunities

    Example:
        POST /api/v1/graph/admin/enrichment/analyze
        {
            "analysis_type": "not_applicable_relationships",
            "limit": 50,
            "min_occurrence": 10
        }

        Response:
        {
            "candidates": [
                {
                    "entity1": "Elon Musk",
                    "entity1_type": "PERSON",
                    "entity2": "Tesla",
                    "entity2_type": "ORGANIZATION",
                    "current_relationship": "NOT_APPLICABLE",
                    "occurrence_count": 47,
                    "suggested_tools": ["wikipedia", "research_perplexity"],
                    "context_samples": ["...CEO of Tesla...", "...founded Tesla..."]
                }
            ],
            "summary": {
                "total_candidates": 156,
                "by_entity_type": {"PERSON→ORGANIZATION": 89, ...},
                "top_patterns": [
                    {"pattern": "PERSON→ORGANIZATION", "count": 89}
                ]
            }
        }
    """
    try:
        if request.analysis_type != "not_applicable_relationships":
            raise HTTPException(
                status_code=400,
                detail=f"Unknown analysis type: {request.analysis_type}"
            )

        result = await enrichment_service.analyze_not_applicable_relationships(
            limit=request.limit,
            min_occurrence=request.min_occurrence
        )

        logger.info(
            f"Enrichment analysis: {len(result['candidates'])} candidates, "
            f"min_occurrence={request.min_occurrence}"
        )

        return result

    except Exception as e:
        logger.error(f"Enrichment analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enrichment analysis failed: {str(e)}"
        )


@router.post("/execute-tool")
async def execute_enrichment_tool(request: ExecuteToolRequest):
    """
    Execute enrichment tool for entity pair.

    Runs specified tool (Wikipedia, Research, Google Deep Research)
    to extract relationship information for an entity pair.

    Returns:
        - tool: Tool that was executed
        - success: Whether execution succeeded
        - data: Tool-specific data (article info, etc.)
        - suggestions: List of relationship suggestions with confidence

    Example:
        POST /api/v1/graph/admin/enrichment/execute-tool
        {
            "tool": "wikipedia",
            "entity1": "Elon Musk",
            "entity2": "Tesla",
            "language": "en"
        }

        Response:
        {
            "tool": "wikipedia",
            "success": true,
            "data": {
                "article_title": "Elon Musk",
                "article_url": "https://en.wikipedia.org/wiki/Elon_Musk",
                "extract": "Elon Reeve Musk is...",
                "infobox_fields": 12,
                "categories": ["21st-century American businesspeople", ...]
            },
            "suggestions": [
                {
                    "relationship_type": "CEO_of",
                    "confidence": 0.95,
                    "evidence": "Wikipedia infobox: CEO=Tesla",
                    "source": "wikipedia_infobox"
                },
                {
                    "relationship_type": "founded",
                    "confidence": 0.85,
                    "evidence": "Musk co-founded Tesla in 2003",
                    "source": "wikipedia_text"
                }
            ]
        }
    """
    try:
        if request.tool == "wikipedia":
            result = await enrichment_service.execute_wikipedia_tool(
                entity1=request.entity1,
                entity2=request.entity2,
                language=request.language
            )
        elif request.tool == "research_perplexity":
            raise HTTPException(
                status_code=501,
                detail="Research (Perplexity) tool not yet implemented. Use research-service API directly."
            )
        elif request.tool == "google_deep_research":
            raise HTTPException(
                status_code=501,
                detail="Google Deep Research tool not yet implemented. Manual import/export workflow."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown tool: {request.tool}. Available: wikipedia, research_perplexity, google_deep_research"
            )

        logger.info(
            f"Tool executed: {request.tool}, "
            f"entity1='{request.entity1}', entity2='{request.entity2}', "
            f"success={result.success}"
        )

        # Convert dataclass to dict
        return {
            "tool": result.tool,
            "success": result.success,
            "data": result.data,
            "suggestions": result.suggestions,
            "error": result.error
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}"
        )


@router.post("/apply")
async def apply_enrichment(request: ApplyEnrichmentRequest):
    """
    Apply enrichment to Knowledge Graph.

    Updates NOT_APPLICABLE relationships with specific relationship type
    based on user selection from tool suggestions.

    Returns:
        - updated_count: Number of relationships updated
        - relationship_exists: Whether relationship type exists in system
        - message: Success/warning message

    Example:
        POST /api/v1/graph/admin/enrichment/apply
        {
            "entity1": "Elon Musk",
            "entity2": "Tesla",
            "new_relationship_type": "CEO_of",
            "confidence": 0.95,
            "evidence": "Wikipedia infobox: CEO=Elon Musk",
            "source": "wikipedia_manual"
        }

        Response (if relationship type exists):
        {
            "updated_count": 47,
            "relationship_exists": true,
            "message": "Successfully updated 47 relationships",
            "new_relationship_type": "CEO_of",
            "entities": {
                "entity1": "Elon Musk",
                "entity2": "Tesla"
            }
        }

        Response (if relationship type missing):
        {
            "updated_count": 0,
            "relationship_exists": false,
            "message": "Relationship type 'CEO_of' does not exist in system. Add to RelationshipType enum first.",
            "action_required": "Add 'CEO_of' to content-analysis-service RelationshipType enum",
            "migration_needed": true
        }
    """
    try:
        result = await enrichment_service.apply_enrichment(
            entity1=request.entity1,
            entity2=request.entity2,
            new_relationship_type=request.new_relationship_type,
            confidence=request.confidence,
            evidence=request.evidence,
            source=request.source
        )

        logger.info(
            f"Enrichment applied: {request.entity1} → {request.entity2}, "
            f"type={request.new_relationship_type}, updated={result['updated_count']}"
        )

        return result

    except Exception as e:
        logger.error(f"Apply enrichment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply enrichment: {str(e)}"
        )


@router.get("/stats")
async def get_enrichment_stats():
    """
    Get enrichment statistics.

    Returns overall statistics about NOT_APPLICABLE relationships
    and enrichment opportunities.

    Example:
        GET /api/v1/graph/admin/enrichment/stats

        Response:
        {
            "total_not_applicable": 1041,
            "total_related_to": 1402,
            "enrichment_potential": 2443,
            "percentage_needs_enrichment": 59.8,
            "top_entity_type_patterns": [
                {"pattern": "PERSON→ORGANIZATION", "count": 312},
                {"pattern": "ORGANIZATION→LOCATION", "count": 189}
            ]
        }
    """
    try:
        # Query NOT_APPLICABLE count
        cypher_not_applicable = """
        MATCH ()-[r:NOT_APPLICABLE]->()
        RETURN count(r) AS count
        """

        not_applicable_result = await neo4j_service.execute_query(cypher_not_applicable)
        total_not_applicable = not_applicable_result[0]["count"] if not_applicable_result else 0

        # Query RELATED_TO count
        cypher_related_to = """
        MATCH ()-[r:RELATED_TO]->()
        RETURN count(r) AS count
        """

        related_to_result = await neo4j_service.execute_query(cypher_related_to)
        total_related_to = related_to_result[0]["count"] if related_to_result else 0

        # Query total relationships
        cypher_total = """
        MATCH ()-[r]->()
        RETURN count(r) AS count
        """

        total_result = await neo4j_service.execute_query(cypher_total)
        total_relationships = total_result[0]["count"] if total_result else 0

        # Query entity type patterns for NOT_APPLICABLE
        cypher_patterns = """
        MATCH (e1:Entity)-[r:NOT_APPLICABLE]->(e2:Entity)
        WITH e1.type AS entity1_type,
             e2.type AS entity2_type,
             count(r) AS count
        ORDER BY count DESC
        LIMIT 10
        RETURN entity1_type + '→' + entity2_type AS pattern, count
        """

        pattern_results = await neo4j_service.execute_query(cypher_patterns)
        top_patterns = [
            {"pattern": record["pattern"], "count": record["count"]}
            for record in pattern_results
        ]

        enrichment_potential = total_not_applicable + total_related_to
        percentage_needs_enrichment = (
            (enrichment_potential / total_relationships * 100)
            if total_relationships > 0 else 0
        )

        logger.info(
            f"Enrichment stats: {total_not_applicable} NOT_APPLICABLE, "
            f"{total_related_to} RELATED_TO, "
            f"{percentage_needs_enrichment:.1f}% needs enrichment"
        )

        return {
            "total_not_applicable": total_not_applicable,
            "total_related_to": total_related_to,
            "enrichment_potential": enrichment_potential,
            "total_relationships": total_relationships,
            "percentage_needs_enrichment": round(percentage_needs_enrichment, 1),
            "top_entity_type_patterns": top_patterns
        }

    except Exception as e:
        logger.error(f"Failed to get enrichment stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enrichment stats: {str(e)}"
        )
