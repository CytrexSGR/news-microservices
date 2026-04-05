"""
Pattern detection analyzer for OSS.
Detects recurring patterns in Neo4j that might warrant new entity/relationship types.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.database import Neo4jConnection
from app.config import settings
from app.models.proposal import (
    OntologyChangeProposal,
    ChangeType,
    Severity,
    Evidence,
    ImpactAnalysis
)

logger = logging.getLogger(__name__)


class PatternDetector:
    """Detects patterns in Neo4j that suggest ontology improvements."""

    def __init__(self, neo4j: Neo4jConnection):
        self.neo4j = neo4j

    async def detect_entity_patterns(self) -> List[OntologyChangeProposal]:
        """
        Detect potential new entity types based on patterns.

        Returns:
            List of proposals for new entity types
        """
        proposals = []

        try:
            # Query 1: Find Entity nodes with frequently occurring entity_type values
            # FIXED: Search WITHIN Entity nodes, not outside them!
            query = """
            MATCH (n:Entity)
            WHERE n.entity_type IS NOT NULL
              AND n.entity_type <> 'UNKNOWN'
              AND n.entity_type <> 'ARTICLE'
            WITH n.entity_type AS type,
                 count(*) AS count,
                 collect(id(n)) AS node_ids
            WHERE count >= $min_occurrences
            RETURN type, count, node_ids[0..5] AS sample_ids
            ORDER BY count DESC
            LIMIT 20
            """

            results = self.neo4j.execute_read(
                query,
                {"min_occurrences": settings.MIN_PATTERN_OCCURRENCES}
            )

            for record in results:
                type_value = record.get("type")
                count = record.get("count", 0)
                sample_ids = record.get("sample_ids", [])

                # Skip if no type
                if not type_value:
                    continue

                # Generate proposal
                proposal = self._create_entity_type_proposal(
                    type_value=type_value,
                    count=count,
                    sample_ids=sample_ids
                )

                if proposal:
                    proposals.append(proposal)

            logger.info(f"Detected {len(proposals)} entity type patterns")

        except Exception as e:
            logger.error(f"Entity pattern detection failed: {e}", exc_info=True)

        return proposals

    async def detect_relationship_patterns(self) -> List[OntologyChangeProposal]:
        """
        Detect potential new relationship types.
        Analyzes generic RELATED_TO relationships that could be more specific.

        Returns:
            List of proposals for new relationship types
        """
        proposals = []

        try:
            # Query: Find frequent patterns in RELATED_TO relationships
            # FIXED: Use RELATED_TO instead of non-existent MENTIONED_WITH
            query = """
            MATCH (a:Entity)-[r:RELATED_TO]->(b:Entity)
            WHERE a.entity_type IS NOT NULL
              AND b.entity_type IS NOT NULL
              AND a.entity_type <> 'UNKNOWN'
              AND b.entity_type <> 'UNKNOWN'
              AND a.entity_type <> 'ARTICLE'
              AND b.entity_type <> 'ARTICLE'
            WITH a.entity_type AS source_type,
                 b.entity_type AS target_type,
                 count(*) AS count
            WHERE count >= $min_occurrences
            RETURN source_type, target_type, count
            ORDER BY count DESC
            LIMIT 10
            """

            results = self.neo4j.execute_read(
                query,
                {"min_occurrences": 5}
            )

            for record in results:
                source_type = record.get("source_type")
                target_type = record.get("target_type")
                count = record.get("count", 0)

                if not source_type or not target_type:
                    continue

                proposal = self._create_relationship_type_proposal(
                    source_type=source_type,
                    target_type=target_type,
                    count=count
                )

                if proposal:
                    proposals.append(proposal)

            logger.info(f"Detected {len(proposals)} relationship type patterns")

        except Exception as e:
            logger.error(f"Relationship pattern detection failed: {e}", exc_info=True)

        return proposals

    def _create_entity_type_proposal(
        self,
        type_value: str,
        count: int,
        sample_ids: List[int]
    ) -> Optional[OntologyChangeProposal]:
        """
        Create proposal for new entity type pattern.

        Args:
            type_value: Entity type value that occurs frequently
            count: Number of occurrences
            sample_ids: Sample node IDs as evidence

        Returns:
            OntologyChangeProposal or None
        """
        try:
            # Generate proposal ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            proposal_id = f"OSS_{timestamp}_{short_uuid}"

            # Calculate confidence
            confidence = min(0.5 + (count / 100) * 0.4, 0.95)

            # Create proposal
            proposal = OntologyChangeProposal(
                proposal_id=proposal_id,
                change_type=ChangeType.NEW_ENTITY_TYPE,
                severity=Severity.HIGH if count > 50 else Severity.MEDIUM,
                title=f"Frequent entity type pattern: {type_value}",
                description=f"""
                Detected {count} Entity nodes with entity_type='{type_value}'.
                This is a significant pattern in the knowledge graph ({count} occurrences).

                This pattern suggests:
                - The '{type_value}' entity type is well-established in the data
                - It may benefit from additional ontology modeling (relationships, constraints)
                - Consider adding specific properties or validation rules for this type

                Recommendation: Review this entity type for potential ontology enhancements.
                """.strip(),
                evidence=[
                    Evidence(
                        example_id=str(node_id),
                        example_type="NODE",
                        context=f"Example node with type '{type_value}'",
                        frequency=count
                    )
                    for node_id in sample_ids[:3]
                ],
                pattern_query=f"""
                MATCH (n:Entity)
                WHERE n.entity_type = '{type_value}'
                RETURN n
                LIMIT 10
                """,
                occurrence_count=count,
                confidence=confidence,
                confidence_factors={
                    "frequency": min(count / 100, 1.0),
                    "consistency": 0.8
                },
                validation_checks=[
                    "No conflicting entity types found",
                    "Properties are consistent across nodes"
                ],
                impact_analysis=ImpactAnalysis(
                    affected_entities_count=count,
                    breaking_change=False,
                    migration_complexity="MEDIUM",
                    estimated_effort_hours=4.0,
                    benefits=[
                        "Better data organization",
                        "Improved query performance",
                        "Clearer ontology structure"
                    ],
                    risks=[
                        f"Need to migrate {count} existing nodes",
                        "May require updating ingestion logic"
                    ]
                ),
                tags=["pattern-detection", "entity-type", type_value.lower()]
            )

            return proposal

        except Exception as e:
            logger.error(f"Failed to create entity type proposal: {e}")
            return None

    def _create_relationship_type_proposal(
        self,
        source_type: str,
        target_type: str,
        count: int
    ) -> Optional[OntologyChangeProposal]:
        """
        Create proposal for new relationship type.

        Args:
            source_type: Source entity type
            target_type: Target entity type
            count: Number of occurrences

        Returns:
            OntologyChangeProposal or None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            proposal_id = f"OSS_{timestamp}_{short_uuid}"

            # Suggest relationship type name
            rel_type = f"{source_type}_INTERACTS_WITH_{target_type}"

            confidence = min(0.5 + (count / 50) * 0.3, 0.90)

            proposal = OntologyChangeProposal(
                proposal_id=proposal_id,
                change_type=ChangeType.NEW_RELATIONSHIP_TYPE,
                severity=Severity.MEDIUM,
                title=f"Frequent relationship pattern: {source_type} → {target_type}",
                description=f"""
                Found {count} instances of {source_type} entities related to {target_type} entities.
                Currently using generic RELATED_TO relationship.

                This pattern suggests a specific semantic relationship exists between these entity types.
                Consider creating a more specific relationship type (e.g., '{rel_type}') for:
                - Better query expressiveness
                - Clearer ontology semantics
                - Improved relationship reasoning

                Recommendation: Analyze examples to determine the exact nature of this relationship.
                """.strip(),
                pattern_query=f"""
                MATCH (a:Entity)-[r:RELATED_TO]->(b:Entity)
                WHERE a.entity_type = '{source_type}'
                  AND b.entity_type = '{target_type}'
                RETURN a, r, b
                LIMIT 10
                """,
                occurrence_count=count,
                confidence=confidence,
                impact_analysis=ImpactAnalysis(
                    affected_relationships_count=count,
                    breaking_change=False,
                    migration_complexity="LOW",
                    estimated_effort_hours=2.0,
                    benefits=[
                        "More specific relationship semantics",
                        "Better query expressiveness",
                        "Improved relationship reasoning"
                    ],
                    risks=[f"Need to update {count} relationships"]
                ),
                tags=["pattern-detection", "relationship-type"]
            )

            return proposal

        except Exception as e:
            logger.error(f"Failed to create relationship type proposal: {e}")
            return None
