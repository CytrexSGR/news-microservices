"""SQLAlchemy models for Knowledge Graph Service."""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class KnowledgeGraphEvent(Base):
    """
    Event logging for knowledge graph operations.

    Tracks enrichment operations, relationship changes, and manual edits
    to provide audit trail and historical analysis capabilities.
    """

    __tablename__ = "knowledge_graph_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # enrichment_applied, relationship_created, etc.

    # Entity information
    entity1_name = Column(String(255), nullable=False, index=True)
    entity2_name = Column(String(255), nullable=True, index=True)
    relationship_type = Column(String(100), nullable=True)

    # Change tracking
    old_confidence = Column(Float, nullable=True)
    new_confidence = Column(Float, nullable=True)
    old_relationship_type = Column(String(100), nullable=True)

    # Enrichment metadata
    enrichment_source = Column(String(100), nullable=True)  # wikipedia, perplexity, manual
    enrichment_summary = Column(Text, nullable=True)  # Brief description of what changed

    # User tracking (for manual operations)
    user_id = Column(String(100), nullable=True)

    # Additional context
    event_metadata = Column(Text, nullable=True)  # JSON string for additional data

    # Indexes for common queries
    __table_args__ = (
        Index("idx_event_type_timestamp", "event_type", "timestamp"),
        Index("idx_entity1_timestamp", "entity1_name", "timestamp"),
        Index("idx_enrichment_source", "enrichment_source", "timestamp"),
    )

    def __repr__(self):
        return f"<KnowledgeGraphEvent(id={self.id}, type='{self.event_type}', entity1='{self.entity1_name}', timestamp={self.timestamp})>"


class GraphQualitySnapshot(Base):
    """
    Daily snapshots of graph quality metrics.

    Tracks quality metrics over time to enable trend analysis and
    identify data quality improvements or regressions.
    """

    __tablename__ = "graph_quality_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(DateTime, default=datetime.utcnow, nullable=False, unique=True, index=True)

    # Graph size metrics
    total_nodes = Column(Integer, default=0, nullable=False)
    total_relationships = Column(Integer, default=0, nullable=False)

    # Quality metrics
    not_applicable_count = Column(Integer, default=0, nullable=False)
    not_applicable_ratio = Column(Float, default=0.0, nullable=False)

    high_confidence_count = Column(Integer, default=0, nullable=False)  # confidence > 0.8
    medium_confidence_count = Column(Integer, default=0, nullable=False)  # 0.5 <= confidence <= 0.8
    low_confidence_count = Column(Integer, default=0, nullable=False)  # confidence < 0.5

    # Data completeness
    orphaned_entities_count = Column(Integer, default=0, nullable=False)
    entities_with_wikidata = Column(Integer, default=0, nullable=False)
    wikidata_coverage_ratio = Column(Float, default=0.0, nullable=False)

    # Composite quality score (0-100)
    quality_score = Column(Float, default=0.0, nullable=False)

    # Enrichment tracking
    total_enrichments = Column(Integer, default=0, nullable=False)
    enrichments_this_period = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<GraphQualitySnapshot(date={self.snapshot_date}, score={self.quality_score}, nodes={self.total_nodes})>"
