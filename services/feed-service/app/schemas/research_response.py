"""
Research service response validation schemas.

Provides type-safe validation for responses from the research service,
preventing NoneType errors and ensuring data integrity.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator


class ResearchTaskValidationMixin(BaseModel):
    """
    Validates research service responses with detailed error messages.

    Used to ensure task_result from research service is valid before processing.
    Prevents AttributeError when task_result is None or invalid.
    """

    @classmethod
    def validate_task_result(cls, task_result: Any) -> Dict[str, Any]:
        """
        Validates task_result from research service.

        Args:
            task_result: Response from research service API

        Returns:
            Validated task_result dict

        Raises:
            ValueError: If task_result is None, not a dict, or missing required fields

        Example:
            >>> result = ResearchTaskValidationMixin.validate_task_result(response.json())
            >>> structured_data = result.get("structured_data")
        """
        if task_result is None:
            raise ValueError(
                "task_result is None - research service may have returned empty response"
            )

        if not isinstance(task_result, dict):
            raise ValueError(
                f"task_result is not a dict, got {type(task_result).__name__}. "
                f"Research service returned invalid data type."
            )

        # Check for required fields
        required_fields = ["id", "status", "query"]
        missing = [f for f in required_fields if f not in task_result]
        if missing:
            raise ValueError(
                f"task_result missing required fields: {missing}. "
                f"Available fields: {list(task_result.keys())}"
            )

        # Validate status is a known value
        valid_statuses = ["pending", "processing", "completed", "failed"]
        status = task_result.get("status")
        if status not in valid_statuses:
            raise ValueError(
                f"task_result has invalid status '{status}'. "
                f"Expected one of: {valid_statuses}"
            )

        return task_result

    @classmethod
    def validate_structured_data(
        cls, structured_data: Any, allow_none: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Validates structured_data from research task result.

        Args:
            structured_data: The structured_data field from task_result
            allow_none: Whether None is allowed (default: True)

        Returns:
            Validated structured_data dict or None

        Raises:
            ValueError: If structured_data is invalid type

        Example:
            >>> data = ResearchTaskValidationMixin.validate_structured_data(
            ...     task_result.get("structured_data")
            ... )
            >>> if data:
            ...     category = data.get("category")
        """
        if structured_data is None:
            if not allow_none:
                raise ValueError("structured_data is None but required")
            return None

        if not isinstance(structured_data, dict):
            raise ValueError(
                f"structured_data is not a dict, got {type(structured_data).__name__}"
            )

        return structured_data

    @classmethod
    def validate_result_content(
        cls, task_result: Dict[str, Any]
    ) -> Optional[str]:
        """
        Safely extracts result.content from task_result for fallback parsing.

        Args:
            task_result: Validated task_result dict

        Returns:
            Content string or None if not available

        Example:
            >>> content = ResearchTaskValidationMixin.validate_result_content(task_result)
            >>> if content:
            ...     # Parse with regex
            ...     tier_match = re.search(r'tier_\d+', content)
        """
        result = task_result.get("result")

        if not result or not isinstance(result, dict):
            return None

        content = result.get("content")

        if content and not isinstance(content, str):
            # Log warning but don't raise - allow fallback
            return str(content)

        return content


class ResearchTaskResponse(BaseModel):
    """
    Typed response model for research service task.

    Provides automatic validation and type safety.
    """
    id: int
    status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    query: str
    structured_data: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None

    class Config:
        # Allow extra fields from API
        extra = "allow"

    @validator("structured_data", pre=True)
    def validate_structured_data_type(cls, v):
        """Ensure structured_data is dict or None."""
        if v is not None and not isinstance(v, dict):
            raise ValueError(f"structured_data must be dict or None, got {type(v)}")
        return v

    @validator("result", pre=True)
    def validate_result_type(cls, v):
        """Ensure result is dict or None."""
        if v is not None and not isinstance(v, dict):
            raise ValueError(f"result must be dict or None, got {type(v)}")
        return v
