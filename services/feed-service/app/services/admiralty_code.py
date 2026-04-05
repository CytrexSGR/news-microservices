"""
Admiralty Code Service

Manages Admiralty Code ratings (A-F) based on quality scores.
Provides configurable thresholds with database storage and fallback to defaults.
"""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admiralty_code import AdmiraltyCodeThreshold, QualityScoreWeight

logger = logging.getLogger(__name__)


# Hardcoded default thresholds (fallback if database is empty)
DEFAULT_THRESHOLDS = [
    {"code": "A", "label": "Completely Reliable", "min_score": 90, "color": "green"},
    {"code": "B", "label": "Usually Reliable", "min_score": 75, "color": "blue"},
    {"code": "C", "label": "Fairly Reliable", "min_score": 60, "color": "yellow"},
    {"code": "D", "label": "Not Usually Reliable", "min_score": 40, "color": "orange"},
    {"code": "E", "label": "Unreliable", "min_score": 20, "color": "red"},
    {"code": "F", "label": "Cannot Be Judged", "min_score": 0, "color": "gray"},
]

# Hardcoded default weights (fallback if database is empty)
DEFAULT_WEIGHTS = {
    "credibility": 0.40,
    "editorial": 0.25,
    "trust": 0.20,
    "health": 0.15,
}


class AdmiraltyCodeService:
    """Service for managing Admiralty Code configuration and calculations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._threshold_cache: Optional[List[AdmiraltyCodeThreshold]] = None
        self._weight_cache: Optional[Dict[str, Decimal]] = None

    async def get_admiralty_code(self, quality_score: Optional[int]) -> Dict[str, str]:
        """
        Calculate Admiralty Code for a given quality score.

        Args:
            quality_score: Quality score (0-100), or None for unassessed

        Returns:
            Dict with code, label, and color
            Example: {"code": "B", "label": "Usually Reliable", "color": "blue"}
        """
        # Handle None or invalid scores
        if quality_score is None or quality_score < 0:
            return {
                "code": "F",
                "label": "Cannot Be Judged",
                "color": "gray"
            }

        # Get thresholds (cached)
        thresholds = await self.get_all_thresholds()

        # Sort by min_score descending (A first, F last)
        sorted_thresholds = sorted(thresholds, key=lambda t: t.min_score, reverse=True)

        # Find matching threshold
        for threshold in sorted_thresholds:
            if quality_score >= threshold.min_score:
                return {
                    "code": threshold.code,
                    "label": threshold.label,
                    "color": threshold.color or "gray"
                }

        # Fallback to F (should never happen if min_score=0 exists)
        return {
            "code": "F",
            "label": "Cannot Be Judged",
            "color": "gray"
        }

    async def get_all_thresholds(self) -> List[AdmiraltyCodeThreshold]:
        """
        Get all Admiralty Code thresholds.

        Returns thresholds from database, falls back to hardcoded defaults if empty.
        Results are cached for performance.
        """
        # Return cached thresholds if available
        if self._threshold_cache is not None:
            return self._threshold_cache

        # Query database
        result = await self.session.execute(
            select(AdmiraltyCodeThreshold).order_by(AdmiraltyCodeThreshold.min_score.desc())
        )
        db_thresholds = result.scalars().all()

        # If database has thresholds, cache and return
        if db_thresholds:
            self._threshold_cache = list(db_thresholds)
            return self._threshold_cache

        # Fallback to hardcoded defaults
        logger.warning("No thresholds in database, using hardcoded defaults")
        default_thresholds = [
            AdmiraltyCodeThreshold(
                code=t["code"],
                label=t["label"],
                min_score=t["min_score"],
                color=t["color"]
            )
            for t in DEFAULT_THRESHOLDS
        ]
        self._threshold_cache = default_thresholds
        return default_thresholds

    async def get_threshold_by_code(self, code: str) -> Optional[AdmiraltyCodeThreshold]:
        """Get a specific threshold by code (A-F)."""
        result = await self.session.execute(
            select(AdmiraltyCodeThreshold).where(AdmiraltyCodeThreshold.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def update_threshold(
        self,
        code: str,
        min_score: int,
        label: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None
    ) -> AdmiraltyCodeThreshold:
        """
        Update an existing threshold.

        Args:
            code: Admiralty code (A-F)
            min_score: New minimum score (0-100)
            label: Optional new label
            description: Optional new description
            color: Optional new color

        Returns:
            Updated threshold

        Raises:
            ValueError: If threshold not found or validation fails
        """
        # Validate min_score
        if not 0 <= min_score <= 100:
            raise ValueError("min_score must be between 0 and 100")

        # Get existing threshold
        threshold = await self.get_threshold_by_code(code)
        if not threshold:
            raise ValueError(f"Threshold with code '{code}' not found")

        # Update fields
        threshold.min_score = min_score
        if label is not None:
            threshold.label = label
        if description is not None:
            threshold.description = description
        if color is not None:
            threshold.color = color

        # Commit changes
        await self.session.commit()
        await self.session.refresh(threshold)

        # Invalidate cache
        self._threshold_cache = None

        logger.info(f"Updated threshold {code}: min_score={min_score}")
        return threshold

    async def reset_thresholds_to_defaults(self) -> List[AdmiraltyCodeThreshold]:
        """
        Reset all thresholds to hardcoded defaults.

        Deletes all existing thresholds and recreates from defaults.
        """
        # Delete all existing thresholds
        await self.session.execute(
            select(AdmiraltyCodeThreshold).where(AdmiraltyCodeThreshold.id != None)
        )
        existing_thresholds = (await self.session.execute(select(AdmiraltyCodeThreshold))).scalars().all()
        for threshold in existing_thresholds:
            await self.session.delete(threshold)

        # Create default thresholds
        new_thresholds = []
        for default in DEFAULT_THRESHOLDS:
            threshold = AdmiraltyCodeThreshold(
                code=default["code"],
                label=default["label"],
                min_score=default["min_score"],
                color=default["color"]
            )
            self.session.add(threshold)
            new_thresholds.append(threshold)

        # Commit
        await self.session.commit()

        # Refresh all
        for threshold in new_thresholds:
            await self.session.refresh(threshold)

        # Invalidate cache
        self._threshold_cache = None

        logger.info("Reset all thresholds to defaults")
        return new_thresholds

    # ========== Quality Score Weights ==========

    async def get_all_weights(self) -> Dict[str, Decimal]:
        """
        Get all category weights.

        Returns dict of category -> weight, falls back to defaults if empty.
        Results are cached for performance.
        """
        # Return cached weights if available
        if self._weight_cache is not None:
            return self._weight_cache

        # Query database
        result = await self.session.execute(select(QualityScoreWeight))
        db_weights = result.scalars().all()

        # If database has weights, cache and return
        if db_weights:
            weight_dict = {w.category: w.weight for w in db_weights}
            self._weight_cache = weight_dict
            return weight_dict

        # Fallback to hardcoded defaults
        logger.warning("No weights in database, using hardcoded defaults")
        self._weight_cache = {k: Decimal(str(v)) for k, v in DEFAULT_WEIGHTS.items()}
        return self._weight_cache

    async def get_weight_by_category(self, category: str) -> Optional[QualityScoreWeight]:
        """Get a specific weight by category name."""
        result = await self.session.execute(
            select(QualityScoreWeight).where(QualityScoreWeight.category == category.lower())
        )
        return result.scalar_one_or_none()

    async def update_weight(
        self,
        category: str,
        weight: float,
        description: Optional[str] = None
    ) -> QualityScoreWeight:
        """
        Update a category weight.

        Args:
            category: Category name (credibility, editorial, trust, health)
            weight: New weight value (0.00 - 1.00)
            description: Optional description

        Returns:
            Updated weight

        Raises:
            ValueError: If weight not found or validation fails
        """
        # Validate weight
        if not 0.0 <= weight <= 1.0:
            raise ValueError("weight must be between 0.0 and 1.0")

        # Get existing weight
        weight_obj = await self.get_weight_by_category(category)
        if not weight_obj:
            raise ValueError(f"Weight for category '{category}' not found")

        # Update fields
        weight_obj.weight = Decimal(str(weight))
        if description is not None:
            weight_obj.description = description

        # Commit changes
        await self.session.commit()
        await self.session.refresh(weight_obj)

        # Invalidate cache
        self._weight_cache = None

        logger.info(f"Updated weight {category}: weight={weight}")
        return weight_obj

    async def validate_weights_sum(self) -> bool:
        """
        Validate that all weights sum to 1.00 (100%).

        Returns:
            True if sum is 1.00, False otherwise
        """
        weights = await self.get_all_weights()
        total = sum(weights.values())
        return abs(float(total) - 1.0) < 0.01  # Allow small floating point errors

    async def reset_weights_to_defaults(self) -> Dict[str, QualityScoreWeight]:
        """
        Reset all weights to hardcoded defaults.

        Deletes all existing weights and recreates from defaults.
        """
        # Delete all existing weights
        existing_weights = (await self.session.execute(select(QualityScoreWeight))).scalars().all()
        for weight in existing_weights:
            await self.session.delete(weight)

        # Create default weights
        new_weights = {}
        for category, value in DEFAULT_WEIGHTS.items():
            weight = QualityScoreWeight(
                category=category,
                weight=Decimal(str(value))
            )
            self.session.add(weight)
            new_weights[category] = weight

        # Commit
        await self.session.commit()

        # Refresh all
        for weight in new_weights.values():
            await self.session.refresh(weight)

        # Invalidate cache
        self._weight_cache = None

        logger.info("Reset all weights to defaults")
        return new_weights

    def clear_cache(self):
        """Clear all cached data."""
        self._threshold_cache = None
        self._weight_cache = None
