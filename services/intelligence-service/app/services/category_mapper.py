"""
Category Mapping Service
Maps V3 Analysis categories to Intelligence Dashboard categories
"""
import logging
from typing import Optional, List
from collections import Counter

logger = logging.getLogger(__name__)


class CategoryMapper:
    """
    Maps Content Analysis V3 categories to Intelligence Dashboard categories

    V3 Categories (14):
    - GEOPOLITICS_SECURITY
    - POLITICS_SOCIETY
    - ECONOMY_MARKETS
    - TECHNOLOGY_SCIENCE
    - CLIMATE_ENVIRONMENT_HEALTH
    - FINANCE
    - HUMANITARIAN
    - SECURITY
    - CONFLICT
    - POLITICS
    - TECHNOLOGY
    - HEALTH
    - PANORAMA
    - OTHER

    Dashboard Categories (4):
    - geo (geopolitics, conflicts, security)
    - finance (economy, markets, business)
    - tech (technology, science)
    - security (humanitarian, health, climate)
    """

    # Mapping from V3 categories to dashboard categories
    CATEGORY_MAP = {
        # Geo/Political
        "GEOPOLITICS_SECURITY": "geo",
        "POLITICS_SOCIETY": "geo",
        "POLITICS": "geo",
        "CONFLICT": "geo",
        "SECURITY": "security",

        # Finance/Economy
        "ECONOMY_MARKETS": "finance",
        "FINANCE": "finance",

        # Technology
        "TECHNOLOGY_SCIENCE": "tech",
        "TECHNOLOGY": "tech",

        # Security/Humanitarian
        "HUMANITARIAN": "security",
        "CLIMATE_ENVIRONMENT_HEALTH": "security",
        "HEALTH": "security",

        # Others
        "PANORAMA": "other",
        "OTHER": "other",
    }

    def map_category(self, v3_category: Optional[str]) -> Optional[str]:
        """
        Map single V3 category to dashboard category

        Args:
            v3_category: Category from v3_analysis.tier0.category

        Returns:
            Dashboard category: 'geo', 'finance', 'tech', 'security', or None
        """
        if not v3_category:
            return None

        mapped = self.CATEGORY_MAP.get(v3_category)

        if not mapped:
            logger.warning(f"Unknown V3 category: {v3_category}, mapping to 'other'")
            return "other"

        return mapped

    def map_categories_bulk(self, v3_categories: List[str]) -> str:
        """
        Map multiple V3 categories to single dashboard category
        Uses majority voting

        Args:
            v3_categories: List of V3 categories from multiple events

        Returns:
            Most common dashboard category
        """
        if not v3_categories:
            return "other"

        # Map all categories
        mapped_categories = [
            self.map_category(cat)
            for cat in v3_categories
            if cat
        ]

        # Filter None and 'other'
        valid_categories = [
            cat for cat in mapped_categories
            if cat and cat != "other"
        ]

        if not valid_categories:
            return "other"

        # Count occurrences
        counter = Counter(valid_categories)
        most_common = counter.most_common(1)[0][0]

        logger.debug(f"Bulk mapping: {counter} -> {most_common}")
        return most_common

    def get_category_display_name(self, dashboard_category: str) -> str:
        """Get human-readable name for dashboard category"""
        names = {
            "geo": "Geopolitics",
            "finance": "Finance",
            "tech": "Technology",
            "security": "Security & Humanitarian",
            "other": "Other"
        }
        return names.get(dashboard_category, dashboard_category.title())


# Global mapper instance
category_mapper = CategoryMapper()
