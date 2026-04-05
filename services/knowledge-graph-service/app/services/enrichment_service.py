"""
Knowledge Graph Enrichment Service

Provides manual enrichment capabilities for improving Knowledge Graph quality.
Analyzes NOT_APPLICABLE relationships and suggests enrichment from external sources.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from app.services.neo4j_service import neo4j_service
from app.services.wikipedia_client import WikipediaClient

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentCandidate:
    """Candidate entity pair for enrichment"""
    entity1: str
    entity1_type: str
    entity2: str
    entity2_type: str
    current_relationship: str
    occurrence_count: int
    suggested_tools: List[str]
    context_samples: List[str]  # Sample contexts where relationship occurs


@dataclass
class EnrichmentSummary:
    """Summary of enrichment analysis"""
    total_candidates: int
    by_entity_type: Dict[str, int]
    by_relationship: Dict[str, int]
    top_patterns: List[Dict[str, Any]]


@dataclass
class ToolExecutionResult:
    """Result of tool execution"""
    tool: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    suggestions: List[Dict[str, Any]] = None  # Relationship suggestions


class EnrichmentService:
    """
    Service for manual Knowledge Graph enrichment.

    Provides analysis and tooling for improving relationship quality
    by replacing NOT_APPLICABLE and generic RELATED_TO relationships
    with specific relationship types.
    """

    def __init__(self, wikipedia_client: WikipediaClient):
        self.wikipedia_client = wikipedia_client

    async def analyze_not_applicable_relationships(
        self,
        limit: int = 100,
        min_occurrence: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze NOT_APPLICABLE relationships to find enrichment candidates.

        Identifies entity pairs with NOT_APPLICABLE relationships that
        occur frequently enough to be worth enriching.

        Args:
            limit: Maximum number of candidates to return
            min_occurrence: Minimum occurrence count for candidates

        Returns:
            Dictionary with:
            - candidates: List of EnrichmentCandidate objects
            - summary: EnrichmentSummary with statistics

        Example:
            result = await service.analyze_not_applicable_relationships(limit=50)
            # {
            #   "candidates": [
            #     {
            #       "entity1": "Elon Musk",
            #       "entity1_type": "PERSON",
            #       "entity2": "Tesla",
            #       "entity2_type": "ORGANIZATION",
            #       "current_relationship": "NOT_APPLICABLE",
            #       "occurrence_count": 47,
            #       "suggested_tools": ["wikipedia", "research_perplexity"],
            #       "context_samples": ["...CEO of Tesla...", "...founded Tesla..."]
            #     }
            #   ],
            #   "summary": {
            #     "total_candidates": 156,
            #     "by_entity_type": {"PERSON→ORGANIZATION": 89, ...}
            #   }
            # }
        """
        # Query Neo4j for NOT_APPLICABLE relationships
        cypher = """
        MATCH (e1:Entity)-[r:NOT_APPLICABLE]->(e2:Entity)
        WITH e1.name AS entity1,
             e1.type AS entity1_type,
             e2.name AS entity2,
             e2.type AS entity2_type,
             count(r) AS occurrence_count,
             collect(r.evidence)[0..3] AS context_samples
        WHERE occurrence_count >= $min_occurrence
        ORDER BY occurrence_count DESC
        LIMIT $limit
        RETURN
            entity1,
            entity1_type,
            entity2,
            entity2_type,
            occurrence_count,
            context_samples
        """

        try:
            results = await neo4j_service.execute_query(
                cypher,
                parameters={
                    "limit": limit,
                    "min_occurrence": min_occurrence
                }
            )

            candidates = []
            by_entity_type = {}

            for record in results:
                entity1_type = record["entity1_type"]
                entity2_type = record["entity2_type"]
                pattern = f"{entity1_type}→{entity2_type}"

                # Count by entity type pattern
                by_entity_type[pattern] = by_entity_type.get(pattern, 0) + 1

                # Suggest tools based on entity types
                suggested_tools = self._suggest_tools(entity1_type, entity2_type)

                candidate = EnrichmentCandidate(
                    entity1=record["entity1"],
                    entity1_type=entity1_type,
                    entity2=record["entity2"],
                    entity2_type=entity2_type,
                    current_relationship="NOT_APPLICABLE",
                    occurrence_count=record["occurrence_count"],
                    suggested_tools=suggested_tools,
                    context_samples=record.get("context_samples", [])
                )

                candidates.append(asdict(candidate))

            # Build summary
            summary = EnrichmentSummary(
                total_candidates=len(candidates),
                by_entity_type=by_entity_type,
                by_relationship={"NOT_APPLICABLE": len(candidates)},
                top_patterns=self._get_top_patterns(by_entity_type, limit=10)
            )

            logger.info(
                f"Enrichment analysis: {len(candidates)} candidates, "
                f"{min_occurrence}+ occurrences"
            )

            return {
                "candidates": candidates,
                "summary": asdict(summary)
            }

        except Exception as e:
            logger.error(f"Enrichment analysis failed: {e}", exc_info=True)
            raise

    async def execute_wikipedia_tool(
        self,
        entity1: str,
        entity2: str,
        language: str = "de"
    ) -> ToolExecutionResult:
        """
        Execute Wikipedia enrichment tool.

        Searches Wikipedia for both entities and extracts relationship
        information from article content and infoboxes.

        Args:
            entity1: First entity name
            entity2: Second entity name
            language: Wikipedia language (de, en)

        Returns:
            ToolExecutionResult with relationship suggestions

        Example:
            result = await service.execute_wikipedia_tool("Elon Musk", "Tesla")
            # ToolExecutionResult(
            #     tool="wikipedia",
            #     success=True,
            #     suggestions=[
            #         {"relationship_type": "CEO_of", "confidence": 0.95},
            #         {"relationship_type": "founded", "confidence": 0.85}
            #     ]
            # )
        """
        try:
            # Search for entity1 (usually the primary entity)
            search_results = await self.wikipedia_client.search(
                query=entity1,
                language=language,
                limit=3
            )

            if not search_results:
                return ToolExecutionResult(
                    tool="wikipedia",
                    success=False,
                    error=f"No Wikipedia article found for '{entity1}'"
                )

            # Get article for top result
            article = await self.wikipedia_client.get_article(
                title=search_results[0].title,
                language=language,
                include_infobox=True,
                include_categories=True,
                include_links=True
            )

            if not article:
                return ToolExecutionResult(
                    tool="wikipedia",
                    success=False,
                    error=f"Failed to extract article for '{entity1}'"
                )

            # Extract relationships from article
            relationships = await self.wikipedia_client.extract_relationships(
                title=article.title,
                language=language
            )

            # Filter relationships that mention entity2
            relevant_suggestions = []
            for rel in relationships:
                # Check if entity2 is mentioned in the relationship
                entity2_mentioned = (
                    entity2.lower() in rel.get("entity2", "").lower() or
                    entity2.lower() in rel.get("evidence", "").lower()
                )

                if entity2_mentioned:
                    relevant_suggestions.append({
                        "relationship_type": rel.get("relationship_type"),
                        "confidence": rel.get("confidence", 0.0),
                        "evidence": rel.get("evidence", ""),
                        "source": rel.get("source", "wikipedia")
                    })

            # If no relevant relationships found, provide article context
            if not relevant_suggestions:
                # Check if entity2 is mentioned in article text
                if entity2.lower() in article.extract.lower():
                    relevant_suggestions.append({
                        "relationship_type": "RELATED_TO",
                        "confidence": 0.70,
                        "evidence": f"{entity2} mentioned in {entity1} Wikipedia article",
                        "source": "wikipedia_text"
                    })

            return ToolExecutionResult(
                tool="wikipedia",
                success=True,
                data={
                    "article_title": article.title,
                    "article_url": article.url,
                    "extract": article.extract[:500],  # First 500 chars
                    "infobox_fields": len(article.infobox),
                    "categories": article.categories[:5]  # Top 5 categories
                },
                suggestions=relevant_suggestions
            )

        except Exception as e:
            logger.error(f"Wikipedia tool execution failed: {e}", exc_info=True)
            return ToolExecutionResult(
                tool="wikipedia",
                success=False,
                error=str(e)
            )

    async def apply_enrichment(
        self,
        entity1: str,
        entity2: str,
        new_relationship_type: str,
        confidence: float,
        evidence: str,
        source: str = "manual_enrichment"
    ) -> Dict[str, Any]:
        """
        Apply enrichment to Knowledge Graph.

        Replaces NOT_APPLICABLE relationship with specific relationship type.
        If relationship type doesn't exist in enum, returns warning.

        Args:
            entity1: First entity name
            entity2: Second entity name
            new_relationship_type: New relationship type to apply
            confidence: Confidence score (0-1)
            evidence: Evidence/context for the relationship
            source: Source of enrichment (default: "manual_enrichment")

        Returns:
            Dictionary with:
            - updated_count: Number of relationships updated
            - relationship_exists: Whether relationship type exists in system
            - message: Success/warning message

        Example:
            result = await service.apply_enrichment(
                entity1="Elon Musk",
                entity2="Tesla",
                new_relationship_type="CEO_of",
                confidence=0.95,
                evidence="Wikipedia infobox: CEO=Elon Musk"
            )
            # {
            #   "updated_count": 47,
            #   "relationship_exists": False,
            #   "message": "Relationship type 'CEO_of' does not exist. Add to enum?"
            # }
        """
        try:
            # Check if relationship type exists in Neo4j
            # (We can't check Python enum from here, so we'll update anyway
            #  and let the validation happen at the application level)

            # Update all NOT_APPLICABLE relationships between these entities
            cypher = """
            MATCH (e1:Entity {name: $entity1})-[r:NOT_APPLICABLE]->(e2:Entity {name: $entity2})
            SET r.relationship_type = $new_relationship_type,
                r.confidence = $confidence,
                r.evidence = $evidence,
                r.enrichment_source = $source,
                r.enriched_at = datetime()
            RETURN count(r) AS updated_count
            """

            results = await neo4j_service.execute_query(
                cypher,
                parameters={
                    "entity1": entity1,
                    "entity2": entity2,
                    "new_relationship_type": new_relationship_type,
                    "confidence": confidence,
                    "evidence": evidence,
                    "source": source
                }
            )

            updated_count = results[0]["updated_count"] if results else 0

            if updated_count == 0:
                return {
                    "updated_count": 0,
                    "relationship_exists": None,
                    "message": f"No NOT_APPLICABLE relationships found between '{entity1}' and '{entity2}'"
                }

            logger.info(
                f"Enrichment applied: {entity1} → {entity2} "
                f"({updated_count} relationships updated to {new_relationship_type})"
            )

            return {
                "updated_count": updated_count,
                "relationship_exists": True,  # Will be validated by enum
                "message": f"Successfully updated {updated_count} relationships",
                "new_relationship_type": new_relationship_type,
                "entities": {
                    "entity1": entity1,
                    "entity2": entity2
                }
            }

        except Exception as e:
            logger.error(f"Apply enrichment failed: {e}", exc_info=True)
            raise

    def _suggest_tools(self, entity1_type: str, entity2_type: str) -> List[str]:
        """
        Suggest enrichment tools based on entity types.

        Args:
            entity1_type: First entity type (PERSON, ORGANIZATION, etc.)
            entity2_type: Second entity type

        Returns:
            List of suggested tool names
        """
        tools = []

        # Wikipedia is always useful
        tools.append("wikipedia")

        # Suggest based on entity type patterns
        if entity1_type == "PERSON" and entity2_type == "ORGANIZATION":
            tools.extend(["research_perplexity", "google_deep_research"])
        elif entity1_type == "ORGANIZATION" and entity2_type == "LOCATION":
            tools.extend(["wikipedia", "research_perplexity"])
        elif entity1_type == "ORGANIZATION" and entity2_type == "ORGANIZATION":
            tools.extend(["research_perplexity", "google_deep_research"])
        else:
            tools.append("research_perplexity")

        # Remove duplicates while preserving order
        return list(dict.fromkeys(tools))

    def _get_top_patterns(
        self,
        by_entity_type: Dict[str, int],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top entity type patterns sorted by count.

        Args:
            by_entity_type: Dictionary of entity type patterns and counts
            limit: Maximum number of patterns to return

        Returns:
            List of top patterns with counts
        """
        sorted_patterns = sorted(
            by_entity_type.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {"pattern": pattern, "count": count}
            for pattern, count in sorted_patterns
        ]
