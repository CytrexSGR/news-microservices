"""
Admiralty Code Configuration API Routes

Endpoints for managing Admiralty Code thresholds and quality score weights.
"""
import logging
from typing import List, Dict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.services.admiralty_code import AdmiraltyCodeService
from app.schemas.admiralty_code import (
    AdmiraltyThresholdResponse,
    AdmiraltyThresholdUpdate,
    QualityWeightResponse,
    QualityWeightUpdate,
    BulkThresholdUpdate,
    BulkWeightUpdate,
    WeightValidationResponse,
    ConfigurationStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admiralty-codes", tags=["admiralty-codes"])


def get_admiralty_service(db: AsyncSession = Depends(get_async_db)) -> AdmiraltyCodeService:
    """Dependency to get AdmiraltyCodeService instance."""
    return AdmiraltyCodeService(db)


# ========== Admiralty Code Thresholds ==========

@router.get("/thresholds", response_model=List[AdmiraltyThresholdResponse])
async def get_all_thresholds(
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Get all Admiralty Code thresholds.

    Returns thresholds from database, falls back to defaults if empty.
    Thresholds define the minimum quality score for each rating (A-F).
    """
    try:
        thresholds = await service.get_all_thresholds()
        return thresholds
    except Exception as e:
        logger.error(f"Error fetching thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch admiralty code thresholds"
        )


@router.get("/thresholds/{code}", response_model=AdmiraltyThresholdResponse)
async def get_threshold_by_code(
    code: str,
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Get a specific threshold by code (A-F).

    Args:
        code: Admiralty code letter (A, B, C, D, E, or F)

    Returns:
        Threshold configuration

    Raises:
        404: If threshold not found
    """
    # Validate code
    if code.upper() not in ["A", "B", "C", "D", "E", "F"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code '{code}'. Must be A, B, C, D, E, or F."
        )

    threshold = await service.get_threshold_by_code(code.upper())
    if not threshold:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threshold with code '{code}' not found"
        )

    return threshold


@router.put("/thresholds/{code}", response_model=AdmiraltyThresholdResponse)
async def update_threshold(
    code: str,
    update_data: AdmiraltyThresholdUpdate,
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Update a threshold's configuration.

    Args:
        code: Admiralty code letter (A-F)
        update_data: Fields to update (min_score, label, description, color)

    Returns:
        Updated threshold

    Raises:
        400: If validation fails
        404: If threshold not found
    """
    # Validate code
    if code.upper() not in ["A", "B", "C", "D", "E", "F"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code '{code}'. Must be A, B, C, D, E, or F."
        )

    try:
        updated_threshold = await service.update_threshold(
            code=code.upper(),
            min_score=update_data.min_score,
            label=update_data.label,
            description=update_data.description,
            color=update_data.color
        )
        return updated_threshold
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating threshold {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update threshold"
        )


@router.post("/thresholds/reset", response_model=List[AdmiraltyThresholdResponse])
async def reset_thresholds_to_defaults(
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Reset all thresholds to hardcoded defaults.

    Deletes all custom thresholds and recreates defaults:
    - A: 90 (Completely Reliable)
    - B: 75 (Usually Reliable)
    - C: 60 (Fairly Reliable)
    - D: 40 (Not Usually Reliable)
    - E: 20 (Unreliable)
    - F: 0 (Cannot Be Judged)

    Returns:
        List of reset thresholds
    """
    try:
        thresholds = await service.reset_thresholds_to_defaults()
        return thresholds
    except Exception as e:
        logger.error(f"Error resetting thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset thresholds"
        )


# ========== Quality Score Weights ==========

@router.get("/weights", response_model=List[QualityWeightResponse])
async def get_all_weights(
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Get all category weights for quality score calculation.

    Returns weights from database, falls back to defaults if empty.

    Default weights:
    - credibility: 40% (tier_1/tier_2/tier_3 assessment)
    - editorial: 25% (fact-checking, corrections, attribution)
    - trust: 20% (NewsGuard, AllSides, MBFC ratings)
    - health: 15% (uptime, response time, reliability)
    """
    try:
        weights_dict = await service.get_all_weights()

        # Convert dict to list of QualityWeightResponse
        weights_list = []
        for category, weight_value in weights_dict.items():
            weight_obj = await service.get_weight_by_category(category)
            if weight_obj:
                weights_list.append(weight_obj)

        return weights_list
    except Exception as e:
        logger.error(f"Error fetching weights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quality score weights"
        )


@router.get("/weights/validate", response_model=WeightValidationResponse)
async def validate_weights_sum(
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Validate that all weights sum to 1.00 (100%).

    Returns:
        Validation result with total and message
    """
    try:
        weights = await service.get_all_weights()
        total = sum(weights.values())
        is_valid = await service.validate_weights_sum()

        return WeightValidationResponse(
            is_valid=is_valid,
            total=total,
            message="Weights are valid (sum to 1.00)" if is_valid
            else f"Weights are invalid (sum to {float(total):.2f}, should be 1.00)"
        )
    except Exception as e:
        logger.error(f"Error validating weights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate weights"
        )


@router.get("/weights/{category}", response_model=QualityWeightResponse)
async def get_weight_by_category(
    category: str,
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Get a specific weight by category.

    Args:
        category: Category name (credibility, editorial, trust, health)

    Returns:
        Weight configuration

    Raises:
        404: If weight not found
    """
    # Validate category
    valid_categories = ["credibility", "editorial", "trust", "health"]
    if category.lower() not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
        )

    weight = await service.get_weight_by_category(category.lower())
    if not weight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weight for category '{category}' not found"
        )

    return weight


@router.put("/weights/{category}", response_model=QualityWeightResponse)
async def update_weight(
    category: str,
    update_data: QualityWeightUpdate,
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Update a category weight.

    Args:
        category: Category name (credibility, editorial, trust, health)
        update_data: New weight value and optional description

    Returns:
        Updated weight

    Raises:
        400: If validation fails or weights don't sum to 1.00
        404: If weight not found

    Note:
        After updating, all weights must sum to 1.00 (100%).
        If they don't, the update will fail with validation error.
    """
    # Validate category
    valid_categories = ["credibility", "editorial", "trust", "health"]
    if category.lower() not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
        )

    try:
        updated_weight = await service.update_weight(
            category=category.lower(),
            weight=float(update_data.weight),
            description=update_data.description
        )

        # Validate that weights still sum to 1.00
        weights_valid = await service.validate_weights_sum()
        if not weights_valid:
            # Rollback is automatic due to exception
            raise ValueError(
                "Weights must sum to 1.00 (100%). "
                "Please adjust other weights accordingly."
            )

        return updated_weight
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating weight {category}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update weight"
        )


@router.post("/weights/reset", response_model=List[QualityWeightResponse])
async def reset_weights_to_defaults(
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Reset all weights to hardcoded defaults.

    Deletes all custom weights and recreates defaults:
    - credibility: 0.40 (40%)
    - editorial: 0.25 (25%)
    - trust: 0.20 (20%)
    - health: 0.15 (15%)

    Returns:
        List of reset weights
    """
    try:
        weights_dict = await service.reset_weights_to_defaults()
        return list(weights_dict.values())
    except Exception as e:
        logger.error(f"Error resetting weights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset weights"
        )


# ========== Validation & Status ==========

@router.get("/status", response_model=ConfigurationStatusResponse)
async def get_configuration_status(
    service: AdmiraltyCodeService = Depends(get_admiralty_service)
):
    """
    Get overall configuration status.

    Returns:
        Status information about thresholds and weights configuration
    """
    try:
        thresholds = await service.get_all_thresholds()
        weights = await service.get_all_weights()
        weights_valid = await service.validate_weights_sum()

        # Check if using defaults (no DB records)
        using_defaults = len(thresholds) == 0 or len(weights) == 0

        return ConfigurationStatusResponse(
            thresholds_count=len(thresholds),
            weights_count=len(weights),
            weights_valid=weights_valid,
            using_defaults=using_defaults
        )
    except Exception as e:
        logger.error(f"Error fetching configuration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch configuration status"
        )
