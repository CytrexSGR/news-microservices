"""
Tests for Graph Traversal Operations

Tests paths, neighbors, and graph walking algorithms.
"""

import pytest
from app.models.graph import Entity, Relationship, Triplet, GraphNode, GraphEdge, GraphResponse
from typing import List, Dict


class TestGraphTraversal:
    """Tests for graph traversal operations."""

    def test_build_simple_triplet(self, sample_entity_person, sample_entity_organization, sample_relationship):
        """Test building a simple triplet."""
        triplet = Triplet(
            subject=sample_entity_person,
            relationship=sample_relationship,
            object=sample_entity_organization
        )

        assert triplet.subject.name == "Elon Musk"
        assert triplet.relationship.relationship_type == "WORKS_FOR"
        assert triplet.object.name == "Tesla"

    def test_triplet_with_different_relationship_types(self, sample_entity_person, sample_entity_organization):
        """Test triplets with various relationship types."""
        relationships = [
            Relationship(
                subject="Elon Musk",
                subject_type="PERSON",
                relationship_type="WORKS_FOR",
                object="Tesla",
                object_type="ORGANIZATION",
                confidence=0.95
            ),
            Relationship(
                subject="Elon Musk",
                subject_type="PERSON",
                relationship_type="FOUNDED",
                object="Tesla",
                object_type="ORGANIZATION",
                confidence=0.95
            ),
            Relationship(
                subject="Elon Musk",
                subject_type="PERSON",
                relationship_type="OWNS",
                object="Tesla",
                object_type="ORGANIZATION",
                confidence=0.95
            )
        ]

        for rel in relationships:
            triplet = Triplet(
                subject=sample_entity_person,
                relationship=rel,
                object=sample_entity_organization
            )
            assert triplet.relationship.relationship_type in ["WORKS_FOR", "FOUNDED", "OWNS"]

    def test_find_entity_connections(self):
        """Test finding all connections for an entity."""
        # Simulate an entity with multiple connections
        entity_name = "Tesla"

        # Mock query results
        connections = [
            {"target": "Elon Musk", "type": "WORKS_FOR", "confidence": 0.95},
            {"target": "United States", "type": "LOCATED_IN", "confidence": 0.99},
            {"target": "Gigafactory", "type": "OWNS", "confidence": 0.9},
        ]

        # Filter connections for entity
        entity_connections = [c for c in connections if c]

        assert len(entity_connections) == 3
        assert entity_connections[0]["target"] == "Elon Musk"

    def test_find_incoming_relationships(self):
        """Test finding incoming relationships to an entity."""
        # Mock relationships pointing TO Tesla
        incoming = [
            {"source": "Elon Musk", "type": "WORKS_FOR", "target": "Tesla"},
            {"source": "SpaceX", "type": "COMPETES_WITH", "target": "Tesla"},
            {"source": "United States", "type": "CONTAINS", "target": "Tesla"}
        ]

        # Filter incoming for target "Tesla"
        tesla_incoming = [r for r in incoming if r["target"] == "Tesla"]

        assert len(tesla_incoming) == 3

    def test_find_outgoing_relationships(self):
        """Test finding outgoing relationships from an entity."""
        # Mock relationships FROM Tesla
        outgoing = [
            {"source": "Tesla", "type": "LOCATED_IN", "target": "United States"},
            {"source": "Tesla", "type": "EMPLOYS", "target": "Elon Musk"},
            {"source": "Tesla", "type": "MANUFACTURES", "target": "Model S"}
        ]

        # Filter outgoing for source "Tesla"
        tesla_outgoing = [r for r in outgoing if r["source"] == "Tesla"]

        assert len(tesla_outgoing) == 3

    def test_traverse_to_neighbors(self):
        """Test traversing to immediate neighbors."""
        # Build a simple graph structure
        graph = {
            "Tesla": {
                "neighbors": [
                    {"name": "Elon Musk", "type": "PERSON"},
                    {"name": "United States", "type": "LOCATION"},
                    {"name": "SpaceX", "type": "ORGANIZATION"}
                ]
            }
        }

        neighbors = graph["Tesla"]["neighbors"]

        assert len(neighbors) == 3
        assert neighbors[0]["name"] == "Elon Musk"

    def test_traverse_two_hops(self):
        """Test traversing two hops (entity -> entity -> entity)."""
        # Tesla -> Elon Musk -> University
        path = [
            {"entity": "Tesla", "type": "ORGANIZATION"},
            {"entity": "Elon Musk", "type": "PERSON"},
            {"entity": "University of Pennsylvania", "type": "ORGANIZATION"}
        ]

        assert len(path) == 3
        assert path[0]["entity"] == "Tesla"
        assert path[2]["entity"] == "University of Pennsylvania"

    def test_find_path_between_entities(self):
        """Test finding shortest path between two entities."""
        # Simplified BFS for path finding
        graph = {
            "A": ["B", "C"],
            "B": ["A", "D"],
            "C": ["A"],
            "D": ["B"]
        }

        def find_path(graph: Dict, start: str, end: str) -> List[str]:
            """Simple BFS path finder."""
            visited = set()
            queue = [(start, [start])]

            while queue:
                node, path = queue.pop(0)
                if node == end:
                    return path

                if node not in visited:
                    visited.add(node)
                    for neighbor in graph.get(node, []):
                        queue.append((neighbor, path + [neighbor]))

            return []

        path = find_path(graph, "A", "D")

        assert len(path) == 3
        assert path == ["A", "B", "D"]

    def test_count_relationships_per_entity(self):
        """Test counting relationships per entity."""
        relationships = [
            {"subject": "Tesla", "object": "Elon Musk"},
            {"subject": "Tesla", "object": "United States"},
            {"subject": "Tesla", "object": "Gigafactory"},
            {"subject": "Elon Musk", "object": "SpaceX"}
        ]

        # Count relationships per entity
        entity_counts = {}
        for rel in relationships:
            entity_counts[rel["subject"]] = entity_counts.get(rel["subject"], 0) + 1

        assert entity_counts["Tesla"] == 3
        assert entity_counts["Elon Musk"] == 1

    def test_detect_bidirectional_relationships(self):
        """Test detecting bidirectional relationships."""
        relationships = [
            {"source": "A", "target": "B", "type": "KNOWS"},
            {"source": "B", "target": "A", "type": "KNOWS"},
            {"source": "C", "target": "D", "type": "KNOWS"}
        ]

        # Find bidirectional pairs
        pairs = set()
        for rel in relationships:
            pairs.add((min(rel["source"], rel["target"]), max(rel["source"], rel["target"])))

        bidirectional = []
        for pair in pairs:
            count = sum(1 for rel in relationships if
                       (rel["source"] == pair[0] and rel["target"] == pair[1]) or
                       (rel["source"] == pair[1] and rel["target"] == pair[0]))
            if count == 2:
                bidirectional.append(pair)

        assert len(bidirectional) == 1
        assert ("A", "B") in bidirectional

    def test_filter_by_relationship_confidence_in_path(self):
        """Test filtering paths by confidence threshold."""
        path = [
            {"source": "A", "target": "B", "confidence": 0.95},
            {"source": "B", "target": "C", "confidence": 0.4},
            {"source": "C", "target": "D", "confidence": 0.9}
        ]

        # Filter path by confidence >= 0.5
        high_confidence_path = [r for r in path if r["confidence"] >= 0.5]

        assert len(high_confidence_path) == 2
        assert high_confidence_path[1]["source"] == "C"

    def test_find_common_neighbors(self):
        """Test finding common neighbors between two entities."""
        entity1_neighbors = {"Elon Musk", "United States", "Gigafactory"}
        entity2_neighbors = {"Elon Musk", "United States", "PayPal"}

        common = entity1_neighbors & entity2_neighbors

        assert len(common) == 2
        assert "Elon Musk" in common
        assert "United States" in common

    def test_distance_between_entities(self):
        """Test calculating distance (hop count) between entities."""
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["D"]
        }

        def bfs_distance(graph: Dict, start: str, end: str) -> int:
            """Calculate distance using BFS."""
            if start == end:
                return 0

            visited = {start}
            queue = [(start, 0)]

            while queue:
                node, dist = queue.pop(0)
                for neighbor in graph.get(node, []):
                    if neighbor == end:
                        return dist + 1
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))

            return -1

        distance = bfs_distance(graph, "A", "D")

        assert distance == 3

    def test_get_all_entity_types_in_path(self):
        """Test extracting entity types from a path."""
        path = [
            {"name": "Tesla", "type": "ORGANIZATION"},
            {"name": "Elon Musk", "type": "PERSON"},
            {"name": "United States", "type": "LOCATION"}
        ]

        types = [node["type"] for node in path]

        assert types == ["ORGANIZATION", "PERSON", "LOCATION"]

    def test_graph_response_model(self):
        """Test GraphResponse model creation."""
        nodes = [
            GraphNode(name="Tesla", type="ORGANIZATION", connection_count=3),
            GraphNode(name="Elon Musk", type="PERSON", connection_count=2)
        ]

        edges = [
            GraphEdge(source="Tesla", target="Elon Musk", relationship_type="WORKS_FOR", confidence=0.95)
        ]

        response = GraphResponse(
            nodes=nodes,
            edges=edges,
            total_nodes=2,
            total_edges=1,
            query_time_ms=42
        )

        assert response.total_nodes == 2
        assert response.total_edges == 1
        assert len(response.nodes) == 2
        assert response.nodes[0].connection_count == 3

    def test_graph_node_connection_count(self):
        """Test GraphNode connection count."""
        node = GraphNode(
            name="Tesla",
            type="ORGANIZATION",
            connection_count=5
        )

        assert node.connection_count == 5

    def test_graph_edge_confidence(self):
        """Test GraphEdge confidence."""
        edge = GraphEdge(
            source="A",
            target="B",
            relationship_type="KNOWS",
            confidence=0.85,
            mention_count=3
        )

        assert edge.confidence == 0.85
        assert edge.mention_count == 3
