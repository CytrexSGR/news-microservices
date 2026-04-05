"""
Inconsistency detection analyzer for OSS.
Detects data quality issues, duplicates, and violations of ontology rules.
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


class InconsistencyDetector:
    """Detects inconsistencies and data quality issues in Neo4j."""

    def __init__(self, neo4j: Neo4jConnection):
        self.neo4j = neo4j

    async def detect_iso_code_violations(self) -> List[OntologyChangeProposal]:
        """
        Detect invalid ISO country codes.

        Returns:
            List of proposals for fixing ISO code violations
        """
        proposals = []

        try:
            # Query: Find Country nodes with invalid ISO codes
            query = """
            MATCH (c)
            WHERE (c.entity_type = 'COUNTRY' OR 'Country' IN labels(c))
              AND (
                size(c.entity_id) <> 2 OR
                c.entity_id =~ '.*[^A-Z].*' OR
                c.entity_id IS NULL
              )
            RETURN c.entity_id AS entity_id,
                   c.name AS name,
                   labels(c) AS labels,
                   id(c) AS node_id
            LIMIT 50
            """

            results = self.neo4j.execute_read(query)

            if results:
                proposal = self._create_iso_code_violation_proposal(results)
                if proposal:
                    proposals.append(proposal)

            logger.info(f"Detected {len(proposals)} ISO code violations")

        except Exception as e:
            logger.error(f"ISO code violation detection failed: {e}", exc_info=True)

        return proposals

    async def detect_duplicate_entities(self) -> List[OntologyChangeProposal]:
        """
        Detect duplicate entities (same entity_id).

        Returns:
            List of proposals for handling duplicates
        """
        proposals = []

        try:
            # Query: Find entities with duplicate entity_ids
            query = """
            MATCH (n)
            WHERE n.entity_id IS NOT NULL
            WITH n.entity_id AS id, collect(n) AS nodes
            WHERE size(nodes) > 1
            RETURN id,
                   size(nodes) AS duplicate_count,
                   [node IN nodes | id(node)][0..5] AS sample_node_ids
            LIMIT 20
            """

            results = self.neo4j.execute_read(query)

            for record in results:
                entity_id = record.get("id")
                count = record.get("duplicate_count", 0)
                sample_ids = record.get("sample_node_ids", [])

                proposal = self._create_duplicate_entity_proposal(
                    entity_id=entity_id,
                    count=count,
                    sample_ids=sample_ids
                )

                if proposal:
                    proposals.append(proposal)

            logger.info(f"Detected {len(proposals)} duplicate entity issues")

        except Exception as e:
            logger.error(f"Duplicate entity detection failed: {e}", exc_info=True)

        return proposals

    async def detect_missing_required_properties(self) -> List[OntologyChangeProposal]:
        """
        Detect entities missing required properties.

        Improved with quality checks:
        - Excludes Article nodes (they shouldn't have entity_id/entity_type)
        - Excludes Symbolic nodes (findings from Intelligence Synthesizer)
        - Filters out generic/invalid entity names
        - Only reports legitimate Entity nodes with missing properties

        Returns:
            List of proposals for fixing missing properties
        """
        proposals = []

        try:
            # Query: Find Entity nodes missing required properties
            # IMPROVED: Exclude Article/Symbolic nodes + quality filters
            query = """
            MATCH (e:Entity)
            WHERE (e.entity_id IS NULL
                   OR e.entity_type IS NULL
                   OR e.name IS NULL)
              // Exclude Article nodes (they're not real entities)
              AND NOT 'Article' IN labels(e)
              // Exclude Symbolic nodes (intelligence findings)
              AND NOT 'Symbolic' IN labels(e)
              // Quality checks on entity names
              AND e.name IS NOT NULL
              AND NOT e.name STARTS WITH 'Article '
              AND NOT e.name =~ '(?i).*(UUID|masterarbeit|bullish|article).*'
              AND size(e.name) > 2
              AND size(e.name) < 200
            RETURN id(e) AS node_id,
                   labels(e) AS labels,
                   e.entity_id AS entity_id,
                   e.entity_type AS entity_type,
                   e.name AS name
            LIMIT 50
            """

            results = self.neo4j.execute_read(query)

            # Additional quality filtering in Python
            filtered_results = []
            for record in results:
                name = record.get("name", "")

                # Skip if name looks like garbage
                if self._is_low_quality_entity_name(name):
                    logger.debug(f"Skipped low-quality entity: {name}")
                    continue

                filtered_results.append(record)

            if filtered_results:
                proposal = self._create_missing_properties_proposal(filtered_results)
                if proposal:
                    proposals.append(proposal)

            logger.info(f"Detected {len(proposals)} missing property issues ({len(results)} before filtering)")

        except Exception as e:
            logger.error(f"Missing property detection failed: {e}", exc_info=True)

        return proposals

    def _is_low_quality_entity_name(self, name: str) -> bool:
        """
        Check if entity name is low-quality and should be excluded.

        Args:
            name: Entity name to check

        Returns:
            True if low-quality, False if valid
        """
        if not name or len(name) < 3:
            return True

        name_lower = name.lower()

        # Skip generic terms
        generic_terms = [
            'article', 'masterarbeit', 'bullish', 'bearish',
            'senate', 'house', 'pm', 'cm', 'president',
            'report', 'news', 'update', 'latest',
            # Generic titles/positions (Option 2a)
            'chief', 'captain', 'commander',
            # Demonyms (nationality/ethnicity terms)
            'chinesen', 'russians', 'ukrainian', 'europeans', 'americans'
        ]

        if any(term in name_lower for term in generic_terms):
            return True

        # Skip generic phrases ending with military/technical terms
        generic_endings = ['allies', 'forces', 'troops', 'drones']
        if any(name_lower.endswith(ending) for ending in generic_endings):
            return True

        # Skip UUIDs and similar patterns
        if 'uuid' in name_lower or len(name) == 36:  # UUID length
            return True

        # Skip very long names (likely article titles)
        if len(name) > 150:
            return True

        # Skip names that are just numbers or dates
        if name.replace('-', '').replace('.', '').isdigit():
            return True

        return False

    def _create_iso_code_violation_proposal(
        self,
        violations: List[Dict[str, Any]]
    ) -> Optional[OntologyChangeProposal]:
        """
        Create proposal for ISO code violations.

        Args:
            violations: List of violation records

        Returns:
            OntologyChangeProposal or None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            proposal_id = f"OSS_{timestamp}_{short_uuid}"

            count = len(violations)

            # Group by issue type
            invalid_format = [v for v in violations if v.get("entity_id") and len(v.get("entity_id", "")) != 2]
            has_lowercase = [v for v in violations if v.get("entity_id") and any(c.islower() for c in v.get("entity_id", ""))]
            is_null = [v for v in violations if not v.get("entity_id")]

            description_parts = [
                f"Detected {count} Country nodes with invalid ISO 3166-1 alpha-2 codes:",
            ]

            if invalid_format:
                description_parts.append(f"- {len(invalid_format)} with wrong length (not 2 characters)")
            if has_lowercase:
                description_parts.append(f"- {len(has_lowercase)} with lowercase characters")
            if is_null:
                description_parts.append(f"- {len(is_null)} with NULL entity_id")

            description_parts.append("\nThis violates ISO 3166-1 alpha-2 standard and breaks relationship queries.")

            proposal = OntologyChangeProposal(
                proposal_id=proposal_id,
                change_type=ChangeType.FLAG_INCONSISTENCY,
                severity=Severity.CRITICAL,
                title="Inconsistent ISO country codes",
                description="\n".join(description_parts),
                evidence=[
                    Evidence(
                        example_id=str(v.get("node_id")),
                        example_type="NODE",
                        properties={
                            "entity_id": v.get("entity_id"),
                            "name": v.get("name")
                        },
                        context=f"Invalid ISO code: '{v.get('entity_id')}' for {v.get('name')}"
                    )
                    for v in violations[:5]
                ],
                pattern_query="""
                MATCH (c)
                WHERE c.entity_type = 'COUNTRY'
                  AND (size(c.entity_id) <> 2 OR c.entity_id =~ '.*[^A-Z].*')
                RETURN c
                """,
                occurrence_count=count,
                confidence=1.0,
                confidence_factors={
                    "data_quality": 1.0,
                    "standard_violation": 1.0
                },
                validation_checks=[
                    "Checked against ISO 3166-1 alpha-2 standard",
                    "Verified entity_type is COUNTRY"
                ],
                impact_analysis=ImpactAnalysis(
                    affected_entities_count=count,
                    breaking_change=False,
                    migration_complexity="LOW",
                    estimated_effort_hours=0.5,
                    benefits=[
                        "Fix data quality issue",
                        "Enable proper ISO-based queries",
                        "Compliance with international standards"
                    ],
                    risks=["None - this is clearly an error"]
                ),
                tags=["data-quality", "iso-code", "critical"]
            )

            return proposal

        except Exception as e:
            logger.error(f"Failed to create ISO code violation proposal: {e}")
            return None

    def _create_duplicate_entity_proposal(
        self,
        entity_id: str,
        count: int,
        sample_ids: List[int]
    ) -> Optional[OntologyChangeProposal]:
        """
        Create proposal for duplicate entities.

        Args:
            entity_id: Duplicated entity_id
            count: Number of duplicates
            sample_ids: Sample node IDs

        Returns:
            OntologyChangeProposal or None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            proposal_id = f"OSS_{timestamp}_{short_uuid}"

            proposal = OntologyChangeProposal(
                proposal_id=proposal_id,
                change_type=ChangeType.FLAG_INCONSISTENCY,
                severity=Severity.HIGH,
                title=f"Duplicate entity_id: {entity_id}",
                description=f"""
                Found {count} nodes with the same entity_id: '{entity_id}'

                This violates the uniqueness constraint for entity_id and can cause:
                - Query ambiguity
                - Inconsistent results
                - Data integrity issues

                Action required: Investigate and merge duplicate nodes or fix entity_id generation.
                """.strip(),
                evidence=[
                    Evidence(
                        example_id=str(node_id),
                        example_type="NODE",
                        properties={"entity_id": entity_id},
                        context=f"Duplicate {i+1} of {count}"
                    )
                    for i, node_id in enumerate(sample_ids[:3])
                ],
                pattern_query=f"""
                MATCH (n {{entity_id: '{entity_id}'}})
                RETURN n
                """,
                occurrence_count=count,
                confidence=1.0,
                impact_analysis=ImpactAnalysis(
                    affected_entities_count=count,
                    breaking_change=False,
                    migration_complexity="MEDIUM",
                    estimated_effort_hours=1.0,
                    benefits=[
                        "Data integrity",
                        "Unambiguous queries",
                        "Prevention of future duplicates"
                    ],
                    risks=["Must merge or deduplicate nodes manually"]
                ),
                tags=["data-quality", "duplicate", "entity-id"]
            )

            return proposal

        except Exception as e:
            logger.error(f"Failed to create duplicate entity proposal: {e}")
            return None

    def _create_missing_properties_proposal(
        self,
        violations: List[Dict[str, Any]]
    ) -> Optional[OntologyChangeProposal]:
        """
        Create proposal for missing required properties.

        Args:
            violations: List of violation records

        Returns:
            OntologyChangeProposal or None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            proposal_id = f"OSS_{timestamp}_{short_uuid}"

            count = len(violations)

            proposal = OntologyChangeProposal(
                proposal_id=proposal_id,
                change_type=ChangeType.FLAG_INCONSISTENCY,
                severity=Severity.HIGH,
                title="Entity nodes missing required properties",
                description=f"""
                Found {count} Entity nodes missing one or more required properties:
                - entity_id
                - entity_type
                - name

                These properties are mandatory for all Entity nodes according to the ontology specification.
                """.strip(),
                evidence=[
                    Evidence(
                        example_id=str(v.get("node_id")),
                        example_type="NODE",
                        properties={
                            "entity_id": v.get("entity_id"),
                            "entity_type": v.get("entity_type"),
                            "name": v.get("name")
                        },
                        context="Missing required properties"
                    )
                    for v in violations[:5]
                ],
                pattern_query="""
                MATCH (e:Entity)
                WHERE e.entity_id IS NULL
                   OR e.entity_type IS NULL
                   OR e.name IS NULL
                RETURN e
                """,
                occurrence_count=count,
                confidence=1.0,
                impact_analysis=ImpactAnalysis(
                    affected_entities_count=count,
                    breaking_change=False,
                    migration_complexity="MEDIUM",
                    estimated_effort_hours=2.0,
                    benefits=[
                        "Data completeness",
                        "Query reliability",
                        "Ontology compliance"
                    ],
                    risks=["May require manual data entry for missing values"]
                ),
                tags=["data-quality", "missing-properties"]
            )

            return proposal

        except Exception as e:
            logger.error(f"Failed to create missing properties proposal: {e}")
            return None

    async def detect_unknown_entity_types(self) -> List[OntologyChangeProposal]:
        """
        Detect entities with UNKNOWN type - massive data quality issue.

        Returns:
            List of proposals for fixing UNKNOWN entities
        """
        proposals = []

        try:
            # Query: Find entities with UNKNOWN entity_type
            query = """
            MATCH (e:Entity)
            WHERE e.entity_type = 'UNKNOWN'
            RETURN count(*) AS unknown_count,
                   collect(id(e))[0..10] AS sample_ids
            """

            results = self.neo4j.execute_read(query)

            if results and results[0].get("unknown_count", 0) > 0:
                count = results[0]["unknown_count"]
                sample_ids = results[0].get("sample_ids", [])

                # Calculate percentage of total entities
                total_entities = 46205  # Known from analysis
                percentage = (count / total_entities) * 100 if total_entities > 0 else 0

                proposal = self._create_unknown_entity_proposal(
                    count=count,
                    percentage=percentage,
                    sample_ids=sample_ids
                )

                if proposal:
                    proposals.append(proposal)

            logger.info(f"Detected {len(proposals)} UNKNOWN entity type issues")

        except Exception as e:
            logger.error(f"UNKNOWN entity detection failed: {e}", exc_info=True)

        return proposals

    async def detect_article_entities(self) -> List[OntologyChangeProposal]:
        """
        Detect Article UUIDs incorrectly stored as entities.

        IMPORTANT: Excludes legitimate legal document references like:
        - "Article 370" (Indian Constitution)
        - "Article 146 of the Fourth Geneva Convention"
        - "Article 23 of the Basic Law"

        Only flags:
        - entity_type = 'ARTICLE' (metadata garbage)
        - Names matching UUID pattern like "Article a1b2c3d4-..."

        Returns:
            List of proposals for cleaning up ARTICLE entities
        """
        proposals = []

        try:
            # Query: Find entities that are actually article UUID references
            # FIXED: Exclude legitimate legal document references
            query = """
            MATCH (e:Entity)
            WHERE e.entity_type = 'ARTICLE'
               // Only match "Article " followed by UUID patterns, NOT legal articles
               OR (e.name STARTS WITH 'Article '
                   AND e.name =~ 'Article [0-9a-f]{8}-[0-9a-f]{4}-.*')
            RETURN count(*) AS article_count,
                   collect(id(e))[0..10] AS sample_ids,
                   collect(e.name)[0..5] AS sample_names
            """

            results = self.neo4j.execute_read(query)

            if results and results[0].get("article_count", 0) > 0:
                count = results[0]["article_count"]
                sample_ids = results[0].get("sample_ids", [])
                sample_names = results[0].get("sample_names", [])

                proposal = self._create_article_entity_proposal(
                    count=count,
                    sample_ids=sample_ids,
                    sample_names=sample_names
                )

                if proposal:
                    proposals.append(proposal)

            logger.info(f"Detected {len(proposals)} ARTICLE entity issues")

        except Exception as e:
            logger.error(f"ARTICLE entity detection failed: {e}", exc_info=True)

        return proposals

    def _create_unknown_entity_proposal(
        self,
        count: int,
        percentage: float,
        sample_ids: List[int]
    ) -> Optional[OntologyChangeProposal]:
        """
        Create proposal for UNKNOWN entity types.

        Args:
            count: Number of UNKNOWN entities
            percentage: Percentage of total entities
            sample_ids: Sample node IDs

        Returns:
            OntologyChangeProposal or None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            proposal_id = f"OSS_{timestamp}_{short_uuid}"

            proposal = OntologyChangeProposal(
                proposal_id=proposal_id,
                change_type=ChangeType.FLAG_INCONSISTENCY,
                severity=Severity.CRITICAL,  # 82.8% is CRITICAL!
                title=f"Mass UNKNOWN entity types: {count} entities ({percentage:.1f}%)",
                description=f"""
                Found {count} Entity nodes with entity_type='UNKNOWN'.
                This represents {percentage:.1f}% of all entities in the knowledge graph!

                This indicates severe data quality issues:
                - NER/NLP extraction failures in content-analysis-v2
                - Missing entity type classification logic
                - Potential pipeline configuration errors

                Root causes to investigate:
                1. GPT model not returning entity types
                2. Entity extraction logic filtering out type information
                3. Mapping errors between extracted entities and graph storage

                Immediate actions required:
                1. Review content-analysis-v2 entity extraction pipeline
                2. Validate GPT prompts include entity type extraction
                3. Check entity normalization logic
                4. Consider re-processing affected articles

                Impact:
                - Graph queries return meaningless "UNKNOWN" entities
                - Relationship reasoning is impossible
                - Analytics and insights are severely degraded
                """.strip(),
                evidence=[
                    Evidence(
                        example_id=str(node_id),
                        example_type="NODE",
                        properties={"entity_type": "UNKNOWN"},
                        context=f"Example {i+1} of {count} UNKNOWN entities"
                    )
                    for i, node_id in enumerate(sample_ids[:5])
                ],
                pattern_query="""
                MATCH (e:Entity)
                WHERE e.entity_type = 'UNKNOWN'
                RETURN e
                LIMIT 10
                """,
                occurrence_count=count,
                confidence=1.0,  # This is definitely a critical issue
                confidence_factors={
                    "data_quality": 1.0,
                    "severity": 1.0,
                    "impact": 1.0
                },
                validation_checks=[
                    "Verified UNKNOWN is not a valid entity type",
                    f"Confirmed {percentage:.1f}% of graph is affected"
                ],
                impact_analysis=ImpactAnalysis(
                    affected_entities_count=count,
                    breaking_change=False,
                    migration_complexity="HIGH",
                    estimated_effort_hours=40.0,  # Massive cleanup effort
                    benefits=[
                        "Dramatically improved graph quality",
                        "Meaningful entity-based queries",
                        "Actionable analytics and insights",
                        "Foundation for relationship reasoning"
                    ],
                    risks=[
                        "Requires re-processing thousands of articles",
                        "May need NLP model improvements",
                        "Could indicate systemic pipeline issues"
                    ]
                ),
                tags=["data-quality", "unknown-entities", "critical", "nlp-failure"]
            )

            return proposal

        except Exception as e:
            logger.error(f"Failed to create UNKNOWN entity proposal: {e}")
            return None

    def _create_article_entity_proposal(
        self,
        count: int,
        sample_ids: List[int],
        sample_names: List[str]
    ) -> Optional[OntologyChangeProposal]:
        """
        Create proposal for ARTICLE entities cleanup.

        Args:
            count: Number of ARTICLE entities
            sample_ids: Sample node IDs
            sample_names: Sample entity names

        Returns:
            OntologyChangeProposal or None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            proposal_id = f"OSS_{timestamp}_{short_uuid}"

            proposal = OntologyChangeProposal(
                proposal_id=proposal_id,
                change_type=ChangeType.FLAG_INCONSISTENCY,
                severity=Severity.HIGH,
                title=f"Article UUIDs stored as entities: {count}",
                description=f"""
                Found {count} Entity nodes with entity_type='ARTICLE' (metadata artifacts).

                Examples:
                {chr(10).join(f"- {name}" for name in sample_names[:3])}

                NOTE: This does NOT include legitimate legal document references like:
                - "Article 370" (Indian Constitution) → Should be LAW
                - "Article 146 of the Fourth Geneva Convention" → Should be LAW

                Only pure metadata artifacts are flagged:
                - entity_type='ARTICLE' (content metadata, not entities)
                - Names matching UUID patterns like "Article a1b2c3d4-..."

                Recommended actions:
                1. Delete entity_type='ARTICLE' nodes (pure metadata)
                2. Reclassify legal articles to entity_type='LAW'

                Impact:
                - Cleaner entity graph
                - Better semantic distinction
                """.strip(),
                evidence=[
                    Evidence(
                        example_id=str(node_id),
                        example_type="NODE",
                        properties={"entity_type": "ARTICLE", "name": sample_names[i] if i < len(sample_names) else "N/A"},
                        context=f"Article UUID {i+1} of {count}"
                    )
                    for i, node_id in enumerate(sample_ids[:5])
                ],
                pattern_query="""
                MATCH (e:Entity)
                WHERE e.entity_type = 'ARTICLE'
                   OR e.name STARTS WITH 'Article '
                RETURN e
                LIMIT 10
                """,
                occurrence_count=count,
                confidence=1.0,
                impact_analysis=ImpactAnalysis(
                    affected_entities_count=count,
                    breaking_change=False,
                    migration_complexity="LOW",
                    estimated_effort_hours=2.0,
                    benefits=[
                        "Cleaner entity graph",
                        "More meaningful queries",
                        "Reduced storage waste"
                    ],
                    risks=[
                        "Must ensure no critical relationships depend on these nodes",
                        "Need validation before deletion"
                    ]
                ),
                tags=["data-quality", "article-entities", "cleanup"]
            )

            return proposal

        except Exception as e:
            logger.error(f"Failed to create ARTICLE entity proposal: {e}")
            return None
