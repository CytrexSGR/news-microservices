"""Pydantic schemas for geolocation-service."""
from app.schemas.geo import (
    CountryBase,
    CountryWithStats,
    CountryDetail,
    ArticleLocationCreate,
    ArticleLocationResponse,
    MapMarker,
    HeatmapPoint,
    GeoJSONFeature,
    GeoJSONCollection,
    RegionInfo,
)

__all__ = [
    "CountryBase",
    "CountryWithStats",
    "CountryDetail",
    "ArticleLocationCreate",
    "ArticleLocationResponse",
    "MapMarker",
    "HeatmapPoint",
    "GeoJSONFeature",
    "GeoJSONCollection",
    "RegionInfo",
]
