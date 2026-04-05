"""Pydantic schemas for API responses."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class CountryBase(BaseModel):
    """Base country schema."""

    iso_code: str
    name: str
    name_de: Optional[str] = None
    region: Optional[str] = None


class CountryWithStats(CountryBase):
    """Country with article statistics."""

    article_count_24h: int = 0
    article_count_7d: int = 0
    centroid: Optional[List[float]] = None  # [lon, lat]

    class Config:
        from_attributes = True


class CountryDetail(CountryWithStats):
    """Full country details."""

    subregion: Optional[str] = None
    article_count_30d: int = 0
    avg_impact_score: Optional[float] = None
    dominant_category: Optional[str] = None
    last_article_at: Optional[datetime] = None


class ArticleLocationCreate(BaseModel):
    """Schema for creating article location."""

    article_id: UUID
    country_code: str
    confidence: float = 1.0
    source: str = "entity_extraction"


class ArticleLocationResponse(BaseModel):
    """Response schema for article location."""

    id: UUID
    article_id: UUID
    country_code: str
    confidence: float
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class MapMarker(BaseModel):
    """Marker for map visualization."""

    id: str
    lat: float
    lon: float
    country_code: str
    article_id: UUID
    title: str
    category: Optional[str] = None
    impact_score: Optional[float] = None


class HeatmapPoint(BaseModel):
    """Point for heatmap visualization."""

    iso_code: str
    lat: float
    lon: float
    article_count: int
    intensity: float


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature for country."""

    type: str = "Feature"
    properties: dict
    geometry: dict


class GeoJSONCollection(BaseModel):
    """GeoJSON FeatureCollection."""

    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


class RegionInfo(BaseModel):
    """Region information with countries."""

    id: str
    name: str
    country_count: int
    country_codes: List[str]
