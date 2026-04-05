"""SQLAlchemy models for entity canonicalization."""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Index, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class CanonicalEntity(Base):
    """Canonical entity definition."""

    __tablename__ = "canonical_entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    wikidata_id = Column(String(50), nullable=True, index=True)
    type = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    aliases = relationship("EntityAlias", back_populates="canonical", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_canonical_name_type", "name", "type", unique=True),
    )

    def __repr__(self):
        return f"<CanonicalEntity(id={self.id}, name='{self.name}', type='{self.type}')>"


class EntityAlias(Base):
    """Entity alias mapping with fuzzy matching support."""

    __tablename__ = "entity_aliases"

    id = Column(Integer, primary_key=True, index=True)
    canonical_id = Column(Integer, ForeignKey("canonical_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    alias = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # === Fuzzy Matching Support (News Intelligence) ===
    alias_normalized = Column(String(255), nullable=True)  # Normalized alias (lowercase, trimmed)
    alias_type = Column(String(50), default='name')  # name, ticker, abbreviation, nickname
    language = Column(String(10), default='en')  # ISO language code
    confidence = Column(Float, default=1.0)  # Confidence score 0-1
    source = Column(String(50), default='manual')  # manual, discovered, wikidata
    is_active = Column(Boolean, default=True)  # Active flag for soft-delete
    usage_count = Column(Integer, default=0)  # Usage frequency tracking

    # Relationships
    canonical = relationship("CanonicalEntity", back_populates="aliases")

    # Indexes for fuzzy matching
    __table_args__ = (
        Index("idx_entity_aliases_normalized", "alias_normalized"),
        Index("idx_entity_aliases_type", "alias_type"),
        Index("idx_entity_aliases_source", "source"),
    )

    def __repr__(self):
        return f"<EntityAlias(alias='{self.alias}', canonical_id={self.canonical_id}, type='{self.alias_type}')>"


class CanonicalizationStat(Base):
    """Daily canonicalization statistics."""

    __tablename__ = "canonicalization_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False, unique=True, index=True)
    total_entities = Column(Integer, default=0, nullable=False)
    total_aliases = Column(Integer, default=0, nullable=False)
    wikidata_linked = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<CanonicalizationStat(date={self.date}, entities={self.total_entities})>"


class EntityMergeEvent(Base):
    """Entity merge event tracking."""

    __tablename__ = "entity_merge_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)  # 'merge', 'alias_added'
    entity_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    canonical_id = Column(Integer, ForeignKey("canonical_entities.id"), nullable=True)
    merge_method = Column(String(50), nullable=True)  # 'exact', 'fuzzy', 'semantic', 'wikidata'
    confidence = Column(Float, nullable=True)
    source_entity = Column(String(255), nullable=True)
    target_entity = Column(String(255), nullable=True)
    event_metadata = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_merge_event_type", "event_type"),
        Index("idx_merge_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<EntityMergeEvent(id={self.id}, source='{self.source_entity}', target='{self.target_entity}')>"
