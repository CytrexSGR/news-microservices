"""
Pydantic schemas for Admiralty Code configuration API
"""
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ========== Admiralty Code Thresholds ==========

class AdmiraltyCodeData(BaseModel):
    """
    Admiralty Code rating data (returned with feed responses).

    Lightweight representation without full threshold details.
    """
    code: Literal["A", "B", "C", "D", "E", "F"] = Field(..., description="Admiralty code letter")
    label: str = Field(..., description="Human-readable label")
    color: str = Field(..., description="UI color for badge display")

    model_config = ConfigDict(from_attributes=True)


class AdmiraltyThresholdBase(BaseModel):
    """Base schema for admiralty thresholds."""
    code: Literal["A", "B", "C", "D", "E", "F"] = Field(..., description="Admiralty code letter (A-F)")
    label: str = Field(..., min_length=1, max_length=50, description="Human-readable label")
    min_score: int = Field(..., ge=0, le=100, description="Minimum quality score for this rating")
    description: Optional[str] = Field(None, description="Detailed description of this rating")
    color: Optional[str] = Field(None, max_length=20, description="UI color (e.g., 'green', 'blue')")


class AdmiraltyThresholdCreate(AdmiraltyThresholdBase):
    """Schema for creating a new threshold (not typically used - defaults are pre-populated)."""
    pass


class AdmiraltyThresholdUpdate(BaseModel):
    """Schema for updating an existing threshold."""
    min_score: Optional[int] = Field(None, ge=0, le=100, description="New minimum score")
    label: Optional[str] = Field(None, min_length=1, max_length=50, description="New label")
    description: Optional[str] = Field(None, description="New description")
    color: Optional[str] = Field(None, max_length=20, description="New color")

    @field_validator('min_score')
    @classmethod
    def validate_min_score(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('min_score must be between 0 and 100')
        return v


class AdmiraltyThresholdResponse(AdmiraltyThresholdBase):
    """Schema for threshold responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Quality Score Weights ==========

class QualityWeightBase(BaseModel):
    """Base schema for quality score weights."""
    category: Literal["credibility", "editorial", "trust", "health"] = Field(
        ...,
        description="Weight category"
    )
    weight: Decimal = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weight value (0.00 - 1.00, must sum to 1.00 across all categories)"
    )
    description: Optional[str] = Field(None, description="Description of what this weight represents")


class QualityWeightUpdate(BaseModel):
    """Schema for updating a weight."""
    weight: Decimal = Field(..., ge=0.0, le=1.0, description="New weight value")
    description: Optional[str] = Field(None, description="New description")

    @field_validator('weight')
    @classmethod
    def validate_weight(cls, v):
        if not 0.0 <= float(v) <= 1.0:
            raise ValueError('weight must be between 0.0 and 1.0')
        return v


class QualityWeightResponse(QualityWeightBase):
    """Schema for weight responses."""
    id: UUID
    min_value: Decimal = Field(..., description="Minimum allowed value")
    max_value: Decimal = Field(..., description="Maximum allowed value")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Bulk Operations ==========

class BulkThresholdUpdate(BaseModel):
    """Schema for bulk threshold updates."""
    thresholds: dict[Literal["A", "B", "C", "D", "E", "F"], int] = Field(
        ...,
        description="Map of code -> min_score"
    )

    @field_validator('thresholds')
    @classmethod
    def validate_thresholds(cls, v):
        """Ensure all codes are present and scores are valid."""
        required_codes = {"A", "B", "C", "D", "E", "F"}
        if set(v.keys()) != required_codes:
            raise ValueError(f"Must provide thresholds for all codes: {required_codes}")

        for code, score in v.items():
            if not 0 <= score <= 100:
                raise ValueError(f"Score for {code} must be between 0 and 100")

        # Ensure descending order (A >= B >= C >= D >= E >= F)
        scores = [v[code] for code in ["A", "B", "C", "D", "E", "F"]]
        if scores != sorted(scores, reverse=True):
            raise ValueError("Scores must be in descending order (A >= B >= C >= D >= E >= F)")

        return v


class BulkWeightUpdate(BaseModel):
    """Schema for bulk weight updates."""
    weights: dict[Literal["credibility", "editorial", "trust", "health"], Decimal] = Field(
        ...,
        description="Map of category -> weight"
    )

    @field_validator('weights')
    @classmethod
    def validate_weights(cls, v):
        """Ensure all categories are present and weights sum to 1.00."""
        required_categories = {"credibility", "editorial", "trust", "health"}
        if set(v.keys()) != required_categories:
            raise ValueError(f"Must provide weights for all categories: {required_categories}")

        for category, weight in v.items():
            if not 0.0 <= float(weight) <= 1.0:
                raise ValueError(f"Weight for {category} must be between 0.0 and 1.0")

        # Ensure sum is 1.00 (allow small floating point tolerance)
        total = sum(float(w) for w in v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.00, got {total:.2f}")

        return v


# ========== Status Responses ==========

class WeightValidationResponse(BaseModel):
    """Response for weight validation."""
    is_valid: bool = Field(..., description="True if weights sum to 1.00")
    total: Decimal = Field(..., description="Current sum of all weights")
    message: str = Field(..., description="Validation message")


class ConfigurationStatusResponse(BaseModel):
    """Overall configuration status."""
    thresholds_count: int = Field(..., description="Number of configured thresholds")
    weights_count: int = Field(..., description="Number of configured weights")
    weights_valid: bool = Field(..., description="True if weights sum to 1.00")
    using_defaults: bool = Field(..., description="True if using hardcoded defaults (not from DB)")
