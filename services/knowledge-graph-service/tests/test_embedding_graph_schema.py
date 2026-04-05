"""Tests for embedding-derived graph schema."""
import pytest


class TestEmbeddingGraphSchema:
    """Test suite for EmbeddingGraphSchema."""

    def _get_schema(self):
        from app.schemas.embedding_graph import EmbeddingGraphSchema
        return EmbeddingGraphSchema()

    def test_schema_creates_similarity_index(self):
        schema = self._get_schema()
        cypher = schema.get_setup_queries()
        assert any("SIMILAR_TO" in q for q in cypher)
        assert any("cosine_score" in q for q in cypher)

    def test_schema_creates_narrative_cluster_node(self):
        schema = self._get_schema()
        cypher = schema.get_setup_queries()
        assert any("NarrativeCluster" in q for q in cypher)

    def test_schema_creates_timepoint_constraint(self):
        schema = self._get_schema()
        cypher = schema.get_setup_queries()
        assert any("TimePoint" in q for q in cypher)

    def test_setup_queries_count(self):
        schema = self._get_schema()
        cypher = schema.get_setup_queries()
        assert len(cypher) == 6

    def test_similarity_edge_query(self):
        schema = self._get_schema()
        query = schema.create_similarity_edge_query()
        assert "SIMILAR_TO" in query
        assert "$article_id_a" in query
        assert "$article_id_b" in query
        assert "$cosine_score" in query

    def test_narrative_cluster_query(self):
        schema = self._get_schema()
        query = schema.create_narrative_cluster_query()
        assert "NarrativeCluster" in query
        assert "PART_OF_NARRATIVE" in query
        assert "$cluster_id" in query
        assert "$article_ids" in query

    def test_co_mentioned_query(self):
        schema = self._get_schema()
        query = schema.create_co_mentioned_query()
        assert "CO_MENTIONED" in query
        assert "r.weight" in query
        assert "$entity_a" in query
        assert "$entity_b" in query

    def test_sentiment_shift_query(self):
        schema = self._get_schema()
        query = schema.create_sentiment_shift_query()
        assert "SHIFTS_SENTIMENT" in query
        assert "$polarity" in query
        assert "$intensity" in query
        assert "$delta" in query
        assert "TimePoint" in query
