"""SQLAlchemy models for geolocation data."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Country(Base):
    """Country with geographic boundaries stored as GeoJSON."""

    __tablename__ = "countries"

    iso_code = Column(String(2), primary_key=True)
    name = Column(String(100), nullable=False)
    name_de = Column(String(100))
    region = Column(String(50))
    subregion = Column(String(50))
    centroid_lon = Column(Float)
    centroid_lat = Column(Float)
    boundary = Column(JSONB)  # GeoJSON MultiPolygon
    created_at = Column(DateTime, default=datetime.utcnow)


class ArticleLocation(Base):
    """Mapping between articles and countries."""

    __tablename__ = "article_locations"

    id = Column(PGUUID, primary_key=True)
    article_id = Column(PGUUID, nullable=False)
    country_code = Column(String(2), ForeignKey("countries.iso_code"))
    confidence = Column(Float, default=1.0)
    source = Column(String(20), default="entity_extraction")
    created_at = Column(DateTime, default=datetime.utcnow)


class CountryStats(Base):
    """Cached statistics per country."""

    __tablename__ = "country_stats"

    country_code = Column(String(2), ForeignKey("countries.iso_code"), primary_key=True)
    article_count_24h = Column(Integer, default=0)
    article_count_7d = Column(Integer, default=0)
    article_count_30d = Column(Integer, default=0)
    avg_impact_score = Column(Float)
    dominant_category = Column(String(50))
    last_article_at = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
