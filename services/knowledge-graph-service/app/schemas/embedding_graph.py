"""
Extended Neo4j schema for embedding-derived graph signals.

New node types:
- NarrativeCluster: time-windowed article clusters = emergent narratives
- TimePoint: temporal anchors for sentiment shifts

New edge types:
- SIMILAR_TO (Article->Article): cosine_score > threshold
- SHIFTS_SENTIMENT (Entity->TimePoint): sentiment trajectory
- PART_OF_NARRATIVE (Article->NarrativeCluster): cluster membership
- CO_MENTIONED (Entity->Entity): co-occurrence in articles, weighted by count
"""


class EmbeddingGraphSchema:
    """Schema definitions for embedding-derived graph signals in Neo4j."""

    def get_setup_queries(self) -> list[str]:
        """Return Cypher queries to create constraints and indexes."""
        return [
            "CREATE CONSTRAINT narrative_cluster_id IF NOT EXISTS FOR (n:NarrativeCluster) REQUIRE n.cluster_id IS UNIQUE",
            "CREATE CONSTRAINT timepoint_id IF NOT EXISTS FOR (t:TimePoint) REQUIRE t.id IS UNIQUE",
            "CREATE INDEX similar_to_score IF NOT EXISTS FOR ()-[r:SIMILAR_TO]-() ON (r.cosine_score)",
            "CREATE INDEX narrative_membership IF NOT EXISTS FOR ()-[r:PART_OF_NARRATIVE]-() ON (r.joined_at)",
            "CREATE INDEX co_mentioned_weight IF NOT EXISTS FOR ()-[r:CO_MENTIONED]-() ON (r.weight)",
            "CREATE INDEX sentiment_shift IF NOT EXISTS FOR ()-[r:SHIFTS_SENTIMENT]-() ON (r.delta)",
        ]

    def create_similarity_edge_query(self) -> str:
        """Return Cypher query to create SIMILAR_TO edges between articles."""
        return """
        MATCH (a:Article {article_id: $article_id_a})
        MATCH (b:Article {article_id: $article_id_b})
        MERGE (a)-[r:SIMILAR_TO]->(b)
        SET r.cosine_score = $cosine_score, r.computed_at = datetime()
        """

    def create_narrative_cluster_query(self) -> str:
        """Return Cypher query to create NarrativeCluster nodes and link articles."""
        return """
        MERGE (nc:NarrativeCluster {cluster_id: $cluster_id})
        SET nc.label = $label, nc.article_count = $article_count,
            nc.first_seen = $first_seen, nc.last_seen = $last_seen,
            nc.centroid_category = $centroid_category
        WITH nc
        UNWIND $article_ids AS aid
        MATCH (a:Article {article_id: aid})
        MERGE (a)-[:PART_OF_NARRATIVE]->(nc)
        """

    def create_co_mentioned_query(self) -> str:
        """Return Cypher query to create CO_MENTIONED edges between entities."""
        return """
        MATCH (e1:Entity {name: $entity_a})
        MATCH (e2:Entity {name: $entity_b})
        MERGE (e1)-[r:CO_MENTIONED]->(e2)
        ON CREATE SET r.weight = 1, r.first_seen = datetime()
        ON MATCH SET r.weight = r.weight + 1
        SET r.last_seen = datetime()
        """

    def create_sentiment_shift_query(self) -> str:
        """Return Cypher query to create SHIFTS_SENTIMENT edges."""
        return """
        MATCH (e:Entity {name: $entity_name})
        MERGE (t:TimePoint {id: $timepoint_id})
        SET t.timestamp = datetime($timestamp)
        MERGE (e)-[r:SHIFTS_SENTIMENT]->(t)
        SET r.polarity = $polarity, r.intensity = $intensity,
            r.delta = $delta, r.article_count = $article_count
        """
