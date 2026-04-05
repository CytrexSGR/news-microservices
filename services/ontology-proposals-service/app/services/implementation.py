"""
Ontology Proposal Implementation Service.

Executes Cypher scripts against Neo4j to implement accepted proposals.
"""
from neo4j import GraphDatabase, Driver
from typing import Dict, Any, Optional
import logging

from app.config import settings
from app.models.proposal import OntologyProposal
from app.utils.iso_codes import get_iso_code, validate_iso_code

logger = logging.getLogger(__name__)


class ProposalImplementationService:
    """Service for implementing accepted ontology proposals."""

    def __init__(self):
        """Initialize Neo4j driver."""
        self.driver: Optional[Driver] = None

    def _get_driver(self) -> Driver:
        """Get or create Neo4j driver."""
        if self.driver is None:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
        return self.driver

    def close(self):
        """Close Neo4j driver."""
        if self.driver:
            self.driver.close()
            self.driver = None

    def implement_proposal(self, proposal: OntologyProposal) -> Dict[str, Any]:
        """
        Implement a proposal based on its change_type.

        Args:
            proposal: The accepted proposal to implement

        Returns:
            Dict with implementation results

        Raises:
            ValueError: If change_type is not supported
            Exception: If implementation fails
        """
        if proposal.status != "ACCEPTED":
            raise ValueError(f"Proposal must be ACCEPTED, got {proposal.status}")

        # Route to specific implementation based on change_type
        if proposal.change_type == "FLAG_INCONSISTENCY":
            return self._fix_inconsistency(proposal)
        elif proposal.change_type == "NEW_ENTITY_TYPE":
            return self._add_entity_type(proposal)
        elif proposal.change_type == "NEW_RELATIONSHIP_TYPE":
            return self._add_relationship_type(proposal)
        elif proposal.change_type == "MODIFY_ENTITY_TYPE":
            return self._modify_entity_type(proposal)
        elif proposal.change_type == "MODIFY_RELATIONSHIP_TYPE":
            return self._modify_relationship_type(proposal)
        else:
            raise ValueError(f"Unsupported change_type: {proposal.change_type}")

    def _fix_inconsistency(self, proposal: OntologyProposal) -> Dict[str, Any]:
        """
        Fix inconsistencies (missing properties, invalid data).

        Handles different types of inconsistencies:
        - Missing required properties (entity_id, entity_type, name)
        - Invalid ISO country codes for COUNTRY entities
        - Duplicate entity_id values (merges duplicates into canonical node)
        """
        logger.info(f"Fixing inconsistency: {proposal.title}")

        driver = self._get_driver()
        results = {
            "nodes_fixed": 0,
            "properties_added": 0,
            "iso_codes_fixed": 0,
            "duplicates_merged": 0,
            "relationships_migrated": 0,
            "entities_deleted": 0,
            "errors": []
        }

        with driver.session(database=settings.NEO4J_DATABASE) as session:
            # Check if this is a duplicate entity_id proposal
            is_duplicate_proposal = (
                "duplicate" in proposal.title.lower() and
                "entity_id" in proposal.title.lower()
            )

            if is_duplicate_proposal:
                logger.info("Detected duplicate entity_id proposal - merging duplicates")
                return self._merge_duplicate_entities(proposal, session, results)

            # Check if this is an ISO code proposal
            is_iso_proposal = (
                "ISO" in proposal.title.upper() or
                "country code" in proposal.title.lower() or
                "iso 3166" in proposal.description.lower()
            )

            if is_iso_proposal:
                logger.info("Detected ISO country code proposal - fixing COUNTRY entity_ids")

                # Get all COUNTRY entities
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE e.entity_type = 'COUNTRY'
                    RETURN e.name as name, e.entity_id as current_id, id(e) as node_id
                """)

                countries_fixed = 0
                countries_failed = []

                for record in result:
                    name = record["name"]
                    current_id = record["current_id"]
                    node_id = record["node_id"]

                    # Get ISO code for country name
                    iso_code = get_iso_code(name)

                    if iso_code:
                        # Only update if current_id is not already a valid ISO code
                        if not validate_iso_code(current_id):
                            try:
                                session.run("""
                                    MATCH (e:Entity)
                                    WHERE id(e) = $node_id
                                    SET e.entity_id = $iso_code
                                """, node_id=node_id, iso_code=iso_code)
                                countries_fixed += 1
                                logger.info(f"Fixed: '{name}' → entity_id='{iso_code}' (was: '{current_id}')")
                            except Exception as e:
                                error_msg = f"Failed to update '{name}': {e}"
                                logger.error(error_msg)
                                results["errors"].append(error_msg)
                                countries_failed.append(name)
                        else:
                            logger.info(f"Skipped: '{name}' already has valid ISO code '{current_id}'")
                    else:
                        error_msg = f"No ISO code found for country: '{name}'"
                        logger.warning(error_msg)
                        results["errors"].append(error_msg)
                        countries_failed.append(name)

                results["iso_codes_fixed"] = countries_fixed
                results["nodes_fixed"] = countries_fixed

                if countries_failed:
                    logger.warning(f"Failed to fix {len(countries_failed)} countries: {countries_failed}")

                logger.info(f"ISO code fix complete: {countries_fixed} countries updated")
                return results

            # Check if this is an UNKNOWN entity type proposal
            is_unknown_proposal = (
                "UNKNOWN" in proposal.title.upper() and
                "entity type" in proposal.title.lower()
            )

            if is_unknown_proposal:
                logger.info("Detected UNKNOWN entity type proposal - reclassifying entities")

                # Reclassify UNKNOWN entities with intelligent pattern matching
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE e.entity_type = 'UNKNOWN'
                    SET e.entity_type = CASE
                        WHEN e.name =~ '.*[Pp]resident.*' OR e.name =~ '.*[Mm]inister.*' OR e.name =~ '.*CEO.*' THEN 'PERSON'
                        WHEN e.name IN ['United States', 'Japan', 'Australia', 'Russia', 'China', 'North Korea', 'Ukraine', 'Iran', 'Israel', 'Palestine', 'Saudi Arabia', 'Germany', 'France', 'UK', 'India', 'Pakistan'] THEN 'COUNTRY'
                        WHEN e.name =~ '.*Group$' OR e.name =~ '.*Organization$' OR e.name =~ '.*Corp.*' OR e.name =~ '.*Inc.*' THEN 'ORGANIZATION'
                        WHEN e.name =~ '.*City$' OR e.name =~ '.*Town$' OR e.name =~ '.*Region$' THEN 'LOCATION'
                        WHEN e.name =~ '^\\$[0-9]+.*' OR e.name =~ '.*billion.*' OR e.name =~ '.*million.*' THEN 'CURRENCY'
                        WHEN e.name STARTS WITH 'APT' THEN 'THREAT_ACTOR'
                        ELSE 'OTHER'
                    END
                    RETURN count(e) as count
                """)
                unknown_fixed = result.single()["count"]
                results["nodes_fixed"] = unknown_fixed
                results["properties_added"] = unknown_fixed

                logger.info(f"UNKNOWN entity reclassification complete: {unknown_fixed} entities updated")
                return results

            # Check if this is an Article UUID proposal
            is_article_uuid_proposal = (
                "Article" in proposal.title and
                "UUID" in proposal.title.upper() or
                "entity_type = 'ARTICLE'" in proposal.description or
                "Article " in proposal.description
            )

            if is_article_uuid_proposal:
                logger.info("Detected Article UUID proposal - deleting article reference entities")

                # Delete Article UUID entities (they are metadata artifacts, not semantic entities)
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE e.entity_type = 'ARTICLE' OR e.name STARTS WITH 'Article '
                    DETACH DELETE e
                    RETURN count(e) as count
                """)
                deleted_count = result.single()["count"]
                results["nodes_fixed"] = deleted_count
                results["entities_deleted"] = deleted_count

                logger.info(f"Article UUID deletion complete: {deleted_count} entities deleted")
                return results

            # Original inconsistency fixes (non-ISO, non-UNKNOWN, non-Article)
            # Fix missing entity_id
            result = session.run("""
                MATCH (e:Entity)
                WHERE e.entity_id IS NULL
                SET e.entity_id = randomUUID()
                RETURN count(e) as count
            """)
            count = result.single()["count"]
            results["properties_added"] += count
            logger.info(f"Fixed {count} entities with missing entity_id")

            # Fix missing entity_type (auto-classify)
            result = session.run("""
                MATCH (e:Entity)
                WHERE e.entity_type IS NULL AND e.name IS NOT NULL
                SET e.entity_type = CASE
                    WHEN e.name STARTS WITH "APT" THEN "THREAT_ACTOR"
                    WHEN e.name IN ["United States", "Japan", "Australia", "Russia", "China", "North Korea"] THEN "COUNTRY"
                    WHEN e.name =~ ".*Group$" OR e.name =~ ".*Organization$" THEN "ORGANIZATION"
                    ELSE "UNKNOWN"
                END
                RETURN count(e) as count
            """)
            count = result.single()["count"]
            results["properties_added"] += count
            logger.info(f"Fixed {count} entities with missing entity_type")

            # Count total nodes affected
            result = session.run("""
                MATCH (e:Entity)
                WHERE e.entity_id IS NOT NULL
                  AND e.entity_type IS NOT NULL
                  AND e.name IS NOT NULL
                RETURN count(e) as count
            """)
            results["nodes_fixed"] = result.single()["count"]

        return results

    def _merge_duplicate_entities(self, proposal: OntologyProposal, session, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge duplicate entities with same entity_id into a single canonical node.

        Strategy:
        1. Extract entity_id from proposal title (e.g., "Duplicate entity_id: US" → "US")
        2. Find all nodes with this entity_id
        3. Select canonical node (oldest = MIN node_id)
        4. Migrate all relationships from duplicates to canonical
        5. Delete duplicate nodes

        Args:
            proposal: The duplicate entity_id proposal
            session: Neo4j session
            results: Results dict to populate

        Returns:
            Dict with merge results
        """
        # Extract entity_id from title (format: "Duplicate entity_id: XX")
        import re
        match = re.search(r'entity_id:\s*(\w+)', proposal.title, re.IGNORECASE)
        if not match:
            error_msg = f"Could not extract entity_id from title: {proposal.title}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results

        duplicate_entity_id = match.group(1)
        logger.info(f"Merging duplicates for entity_id='{duplicate_entity_id}'")

        # Step 1: Find all nodes with this entity_id
        find_query = """
            MATCH (e:Entity)
            WHERE e.entity_id = $entity_id
            RETURN id(e) as node_id, e.name as name, e.entity_type as entity_type
            ORDER BY id(e)
        """
        result = session.run(find_query, entity_id=duplicate_entity_id)
        nodes = list(result)

        if len(nodes) <= 1:
            logger.info(f"No duplicates found for entity_id='{duplicate_entity_id}' (found {len(nodes)} nodes)")
            results["duplicates_merged"] = 0
            return results

        logger.info(f"Found {len(nodes)} nodes with entity_id='{duplicate_entity_id}'")

        # Step 2: Select canonical node (oldest = first in sorted list)
        canonical_node_id = nodes[0]["node_id"]
        canonical_name = nodes[0]["name"]
        duplicate_node_ids = [n["node_id"] for n in nodes[1:]]

        logger.info(f"Canonical node: {canonical_node_id} (name: '{canonical_name}')")
        logger.info(f"Duplicates to merge: {duplicate_node_ids}")

        # Step 3: Migrate relationships from each duplicate to canonical
        total_relationships_migrated = 0

        for dup_node_id in duplicate_node_ids:
            logger.info(f"Processing duplicate node {dup_node_id}...")

            # Migrate INCOMING relationships (other)-[r]->(duplicate)
            migrate_incoming_query = """
                MATCH (source)-[r]->(duplicate:Entity)
                WHERE id(duplicate) = $dup_id
                WITH source, duplicate, r, type(r) as rel_type, properties(r) as rel_props
                MATCH (canonical:Entity)
                WHERE id(canonical) = $canonical_id
                // Only create if relationship doesn't already exist
                MERGE (source)-[new_r:RELATED_TO]->(canonical)
                SET new_r = rel_props
                WITH r, count(new_r) as created
                DELETE r
                RETURN created
            """
            result = session.run(
                migrate_incoming_query,
                dup_id=dup_node_id,
                canonical_id=canonical_node_id
            )
            incoming_count = sum(record["created"] for record in result)
            logger.info(f"  Migrated {incoming_count} incoming relationships")

            # Migrate OUTGOING relationships (duplicate)-[r]->(other)
            migrate_outgoing_query = """
                MATCH (duplicate:Entity)-[r]->(target)
                WHERE id(duplicate) = $dup_id
                WITH duplicate, target, r, type(r) as rel_type, properties(r) as rel_props
                MATCH (canonical:Entity)
                WHERE id(canonical) = $canonical_id
                // Only create if relationship doesn't already exist
                MERGE (canonical)-[new_r:RELATED_TO]->(target)
                SET new_r = rel_props
                WITH r, count(new_r) as created
                DELETE r
                RETURN created
            """
            result = session.run(
                migrate_outgoing_query,
                dup_id=dup_node_id,
                canonical_id=canonical_node_id
            )
            outgoing_count = sum(record["created"] for record in result)
            logger.info(f"  Migrated {outgoing_count} outgoing relationships")

            total_relationships_migrated += incoming_count + outgoing_count

            # Step 4: Delete duplicate node (now safe, no relationships)
            delete_query = """
                MATCH (e:Entity)
                WHERE id(e) = $node_id
                DELETE e
                RETURN count(e) as deleted
            """
            result = session.run(delete_query, node_id=dup_node_id)
            deleted = result.single()["deleted"]
            logger.info(f"  Deleted duplicate node {dup_node_id}: {deleted} nodes removed")

        # Step 5: Update results
        results["duplicates_merged"] = len(duplicate_node_ids)
        results["relationships_migrated"] = total_relationships_migrated
        results["nodes_fixed"] = 1  # The canonical node is now the single source of truth

        logger.info(
            f"Merge complete: {results['duplicates_merged']} duplicates merged, "
            f"{results['relationships_migrated']} relationships migrated"
        )

        return results

    def _add_entity_type(self, proposal: OntologyProposal) -> Dict[str, Any]:
        """
        Add new entity type to ontology.

        For proposal: "Add :CyberActorGroup entity type"
        """
        logger.info(f"Adding entity type: {proposal.title}")

        driver = self._get_driver()
        results = {
            "constraint_created": False,
            "nodes_migrated": 0,
            "errors": []
        }

        with driver.session(database=settings.NEO4J_DATABASE) as session:
            # Create constraint for new entity type
            try:
                session.run("""
                    CREATE CONSTRAINT cyber_actor_group_id IF NOT EXISTS
                    FOR (c:CyberActorGroup) REQUIRE c.entity_id IS UNIQUE
                """)
                results["constraint_created"] = True
                logger.info("Created CyberActorGroup constraint")
            except Exception as e:
                logger.warning(f"Constraint may already exist: {e}")
                results["errors"].append(str(e))

            # Migrate existing ORGANIZATION nodes to CyberActorGroup
            result = session.run("""
                MATCH (o:ORGANIZATION)
                WHERE o.description CONTAINS "cyber group"
                   OR o.name STARTS WITH "APT"
                   OR o.name = "Lazarus Group"
                SET o:CyberActorGroup
                SET o.apt_number = CASE
                    WHEN o.name STARTS WITH "APT" THEN toInteger(substring(o.name, 3))
                    ELSE null
                END
                SET o.attribution = CASE
                    WHEN o.name = "APT28" OR o.name = "APT29" THEN "Russia"
                    WHEN o.name = "Lazarus Group" THEN "North Korea"
                    ELSE null
                END
                RETURN count(o) as count
            """)
            results["nodes_migrated"] = result.single()["count"]
            logger.info(f"Migrated {results['nodes_migrated']} nodes to CyberActorGroup")

        return results

    def _add_relationship_type(self, proposal: OntologyProposal) -> Dict[str, Any]:
        """Add new relationship type to ontology."""
        logger.info(f"Adding relationship type: {proposal.title}")
        # TODO: Implement based on specific proposal requirements
        return {"message": "Not yet implemented"}

    def _modify_entity_type(self, proposal: OntologyProposal) -> Dict[str, Any]:
        """Modify existing entity type."""
        logger.info(f"Modifying entity type: {proposal.title}")
        # TODO: Implement based on specific proposal requirements
        return {"message": "Not yet implemented"}

    def _modify_relationship_type(self, proposal: OntologyProposal) -> Dict[str, Any]:
        """Modify existing relationship type."""
        logger.info(f"Modifying relationship type: {proposal.title}")
        # TODO: Implement based on specific proposal requirements
        return {"message": "Not yet implemented"}


# Global instance
implementation_service = ProposalImplementationService()
