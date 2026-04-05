"""SITREP service constants.

Defines valid categories and report types for SITREP generation.
Categories are aligned with Tier-0 Triage Agent from content-analysis-v3.
"""

from typing import Dict, Set

# Valid SITREP categories - aligned with Tier-0 Agent categories
# Source: services/content-analysis-v3/app/pipeline/tier0/triage.py
SITREP_CATEGORIES: Dict[str, str] = {
    "conflict": "Conflict",
    "finance": "Finance",
    "politics": "Politics",
    "humanitarian": "Humanitarian",
    "security": "Security",
    "technology": "Technology",
    "other": "Other",
    "crypto": "Crypto",  # Special category for crypto news
}

# Valid report types
REPORT_TYPES: Set[str] = {"daily", "weekly", "breaking"}

# Category aliases for mapping incoming cluster/article categories to SITREP categories
# Maps Tier-0 uppercase output to lowercase SITREP keys
CATEGORY_ALIASES: Dict[str, str | None] = {
    # Tier-0 Agent output mappings (uppercase)
    "CONFLICT": "conflict",
    "FINANCE": "finance",
    "POLITICS": "politics",
    "HUMANITARIAN": "humanitarian",
    "SECURITY": "security",
    "TECHNOLOGY": "technology",
    "OTHER": "other",
    # Legacy mappings
    "geopolitics": "politics",
    "breaking_news": "conflict",
    "markets": "finance",
    "conflict_security": "security",  # Legacy category
    "default": None,  # No category filter
}

# Time ranges for report types (in hours)
REPORT_TIME_RANGES: Dict[str, int] = {
    "daily": 24,
    "weekly": 168,  # 7 * 24
    "breaking": 6,  # Only recent breaking news
}
