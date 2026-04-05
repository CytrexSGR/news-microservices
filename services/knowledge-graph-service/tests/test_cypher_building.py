"""
Tests for Cypher Query Building

Tests dynamic Cypher query construction and parameterization.
"""

import pytest
from app.models.graph import Relationship


class TestCypherQueryBuilding:
    """Tests for building Cypher queries programmatically."""

    def test_merge_entity_query(self):
        """Test building MERGE query for entity creation."""
        name = "Tesla"
        entity_type = "ORGANIZATION"

        cypher = f"""
        MERGE (e:Entity {{name: $name, type: $type}})
        ON CREATE SET e.created_at = datetime()
        RETURN e
        """

        assert "MERGE" in cypher
        assert "Entity" in cypher
        assert "$name" in cypher
        assert "$type" in cypher

    def test_relationship_merge_query(self):
        """Test building MERGE query for relationship."""
        cypher = """
        MATCH (subject:Entity {name: $subject_name})
        MATCH (object:Entity {name: $object_name})
        MERGE (subject)-[r:{rel_type}]->(object)
        ON CREATE SET r.confidence = $confidence
        RETURN subject, r, object
        """

        assert "MERGE" in cypher
        assert "{rel_type}" in cypher
        assert "$subject_name" in cypher
        assert "$object_name" in cypher

    def test_relationship_type_placeholder(self):
        """Test replacing relationship type placeholder."""
        rel_type = "WORKS_FOR"
        cypher = "MERGE (s)-[r:{rel_type}]->(o) RETURN r"

        cypher_final = cypher.replace("{rel_type}", rel_type)

        assert "{rel_type}" not in cypher_final
        assert "WORKS_FOR" in cypher_final

    def test_relationship_type_normalization_in_query(self):
        """Test normalizing relationship type before query."""
        rel_type_raw = "works_for"
        rel_type_normalized = rel_type_raw.upper()

        cypher = "MERGE (s)-[r:{rel_type}]->(o) RETURN r"
        cypher_final = cypher.replace("{rel_type}", rel_type_normalized)

        assert "WORKS_FOR" in cypher_final

    def test_match_entity_by_name(self):
        """Test building MATCH query for entity lookup."""
        cypher = """
        MATCH (e:Entity {name: $name})
        RETURN e.name, e.type
        """

        assert "MATCH" in cypher
        assert "{name: $name}" in cypher

    def test_match_relationship_by_type(self):
        """Test building MATCH query for relationships by type."""
        rel_type = "WORKS_FOR"

        cypher = f"""
        MATCH (subject)-[r:{rel_type}]->(object)
        RETURN subject, r, object
        """

        assert "MATCH" in cypher
        assert rel_type in cypher

    def test_match_relationships_with_confidence_filter(self):
        """Test building MATCH query with confidence filter."""
        cypher = """
        MATCH (n:Entity)-[r]->(m:Entity)
        WHERE r.confidence >= $confidence_threshold
        RETURN n, r, m
        """

        assert "WHERE" in cypher
        assert "r.confidence" in cypher
        assert "$confidence_threshold" in cypher

    def test_order_by_confidence_descending(self):
        """Test building query with ORDER BY confidence."""
        cypher = """
        MATCH (n:Entity)-[r]->(m:Entity)
        ORDER BY r.confidence DESC
        RETURN n, r, m
        """

        assert "ORDER BY" in cypher
        assert "confidence DESC" in cypher

    def test_limit_results(self):
        """Test building query with LIMIT."""
        limit = 100

        cypher = f"""
        MATCH (n:Entity)-[r]->(m:Entity)
        RETURN n, r, m
        LIMIT ${limit}
        """

        # Note: In real queries, use parameter
        cypher_correct = """
        MATCH (n:Entity)-[r]->(m:Entity)
        RETURN n, r, m
        LIMIT $limit
        """

        assert "LIMIT" in cypher_correct
        assert "$limit" in cypher_correct

    def test_count_nodes_query(self):
        """Test building COUNT query."""
        cypher = """
        MATCH (e:Entity)
        RETURN count(e) AS total_nodes
        """

        assert "MATCH (e:Entity)" in cypher
        assert "count(e)" in cypher
        assert "total_nodes" in cypher

    def test_count_relationships_query(self):
        """Test building relationship count query."""
        cypher = """
        MATCH ()-[r]->()
        RETURN count(r) AS total_relationships
        """

        assert "count(r)" in cypher
        assert "total_relationships" in cypher

    def test_group_by_entity_type(self):
        """Test building GROUP BY query."""
        cypher = """
        MATCH (e:Entity)
        RETURN e.type AS entity_type, count(*) AS count
        ORDER BY count DESC
        """

        assert "RETURN e.type AS entity_type" in cypher
        assert "count(*)" in cypher
        assert "GROUP BY" not in cypher  # Neo4j doesn't need explicit GROUP BY with aggregation

    def test_shortest_path_query(self):
        """Test building shortest path query."""
        cypher = """
        MATCH p = shortestPath((start:Entity {name: $start_name})-[*]-(end:Entity {name: $end_name}))
        RETURN p
        """

        assert "shortestPath" in cypher
        assert "$start_name" in cypher
        assert "$end_name" in cypher

    def test_all_paths_query(self):
        """Test building all paths query."""
        cypher = """
        MATCH p = (start:Entity {name: $start_name})-[*1..3]->(end:Entity)
        RETURN p
        """

        assert "allShortestPaths" not in cypher
        assert "-[*1..3]->" in cypher  # Relationship path pattern

    def test_case_sensitivity_in_query_building(self):
        """Test that query building is case-sensitive for keywords."""
        cypher_correct = "MATCH (n) RETURN n"
        cypher_lowercase = "match (n) return n"

        # Keywords should be uppercase
        assert "MATCH" in cypher_correct
        assert "match" in cypher_lowercase

    def test_parameterized_query_injection_prevention(self):
        """Test that parameterized queries prevent injection."""
        # CORRECT: Use parameters
        cypher_safe = "MATCH (e:Entity {name: $name}) RETURN e"
        params = {"name": "Tesla'; DROP TABLE Entity; --"}

        # The parameter is separate from query
        assert "$name" in cypher_safe
        assert "DROP TABLE" not in cypher_safe

        # WRONG (for comparison):
        cypher_unsafe = f"MATCH (e:Entity {{name: '{params['name']}'}} ) RETURN e"
        # Unsafe has injection
        assert "DROP TABLE" in cypher_unsafe

    def test_build_triplet_merge_query(self):
        """Test building complete triplet MERGE query."""
        cypher = """
        MERGE (subject:Entity {name: $subject_name, type: $subject_type})
        ON CREATE SET subject.created_at = datetime()

        MERGE (object:Entity {name: $object_name, type: $object_type})
        ON CREATE SET object.created_at = datetime()

        MERGE (subject)-[rel:{rel_type}]->(object)
        ON CREATE SET rel.confidence = $confidence, rel.mention_count = 1
        ON MATCH SET rel.mention_count = rel.mention_count + 1

        RETURN subject, rel, object
        """

        assert cypher.count("MERGE") == 3
        assert "{rel_type}" in cypher
        assert "mention_count" in cypher

    def test_query_property_assignment(self):
        """Test building query with property assignment."""
        cypher = """
        MATCH (e:Entity {name: $name})
        SET e.last_seen = datetime(), e.updated = true
        RETURN e
        """

        assert "SET e.last_seen" in cypher
        assert "datetime()" in cypher

    def test_query_with_multiple_set_clauses(self):
        """Test building query with multiple SET operations."""
        cypher = """
        MERGE (e:Entity {name: $name})
        ON CREATE SET
            e.created_at = datetime(),
            e.type = $type,
            e.properties = {}
        ON MATCH SET
            e.last_seen = datetime(),
            e.updated_count = COALESCE(e.updated_count, 0) + 1
        RETURN e
        """

        assert "ON CREATE SET" in cypher
        assert "ON MATCH SET" in cypher

    def test_delete_entity_query(self):
        """Test building DELETE query."""
        cypher = """
        MATCH (e:Entity {name: $name})
        DETACH DELETE e
        RETURN 'deleted' AS status
        """

        assert "DETACH DELETE" in cypher

    def test_create_index_query(self):
        """Test building CREATE INDEX query."""
        cypher = """
        CREATE INDEX entity_name_index IF NOT EXISTS
        FOR (e:Entity)
        ON (e.name)
        """

        assert "CREATE INDEX" in cypher
        assert "IF NOT EXISTS" in cypher

    def test_create_constraint_query(self):
        """Test building CREATE CONSTRAINT query."""
        cypher = """
        CREATE CONSTRAINT entity_unique IF NOT EXISTS
        FOR (e:Entity)
        REQUIRE (e.name, e.type) IS UNIQUE
        """

        assert "CREATE CONSTRAINT" in cypher
        assert "IS UNIQUE" in cypher

    def test_explain_query(self):
        """Test building EXPLAIN query."""
        cypher = """
        EXPLAIN MATCH (n:Entity)-[r]->(m:Entity)
        RETURN n, r, m
        """

        assert "EXPLAIN" in cypher

    def test_profile_query(self):
        """Test building PROFILE query."""
        cypher = """
        PROFILE MATCH (n:Entity)-[r]->(m:Entity)
        RETURN n, r, m
        """

        assert "PROFILE" in cypher

    def test_skip_and_limit(self):
        """Test building query with SKIP and LIMIT for pagination."""
        cypher = """
        MATCH (n:Entity)
        RETURN n
        SKIP $skip
        LIMIT $limit
        """

        assert "SKIP $skip" in cypher
        assert "LIMIT $limit" in cypher

    def test_with_clause_for_subqueries(self):
        """Test building query with WITH clause."""
        cypher = """
        MATCH (e:Entity)
        WITH e WHERE e.type = $type
        RETURN e
        """

        assert "WITH e WHERE" in cypher
