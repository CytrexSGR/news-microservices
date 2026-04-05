"""
Test suite for feed assessment edge cases and validation.

Tests the ResearchTaskValidationMixin to ensure robust handling of:
- None values from research service
- Invalid data types
- Missing required fields
- Invalid status values
- Malformed structured_data
- Missing result.content for fallback parsing
"""

import pytest
from app.schemas.research_response import ResearchTaskValidationMixin, ResearchTaskResponse


class TestValidateTaskResult:
    """Test validate_task_result() method."""

    def test_valid_task_result(self):
        """Should accept valid task result with all required fields."""
        task_result = {
            "id": 123,
            "status": "completed",
            "query": "Test query",
            "structured_data": {"tier": "tier_1"},
            "result": {"content": "Test content"}
        }

        validated = ResearchTaskValidationMixin.validate_task_result(task_result)
        assert validated == task_result

    def test_none_task_result(self):
        """Should raise ValueError when task_result is None."""
        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_task_result(None)

        assert "task_result is None" in str(exc_info.value)
        assert "research service may have returned empty response" in str(exc_info.value)

    def test_invalid_type_task_result(self):
        """Should raise ValueError when task_result is not a dict."""
        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_task_result("invalid string")

        assert "task_result is not a dict" in str(exc_info.value)
        assert "got str" in str(exc_info.value)

    def test_missing_required_field_id(self):
        """Should raise ValueError when 'id' field is missing."""
        task_result = {
            "status": "completed",
            "query": "Test query"
        }

        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_task_result(task_result)

        assert "missing required fields" in str(exc_info.value)
        assert "id" in str(exc_info.value)

    def test_missing_required_field_status(self):
        """Should raise ValueError when 'status' field is missing."""
        task_result = {
            "id": 123,
            "query": "Test query"
        }

        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_task_result(task_result)

        assert "missing required fields" in str(exc_info.value)
        assert "status" in str(exc_info.value)

    def test_missing_required_field_query(self):
        """Should raise ValueError when 'query' field is missing."""
        task_result = {
            "id": 123,
            "status": "completed"
        }

        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_task_result(task_result)

        assert "missing required fields" in str(exc_info.value)
        assert "query" in str(exc_info.value)

    def test_invalid_status_value(self):
        """Should raise ValueError when status is not a valid value."""
        task_result = {
            "id": 123,
            "status": "invalid_status",
            "query": "Test query"
        }

        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_task_result(task_result)

        assert "invalid status" in str(exc_info.value)
        assert "invalid_status" in str(exc_info.value)
        assert "pending" in str(exc_info.value)
        assert "completed" in str(exc_info.value)

    def test_valid_pending_status(self):
        """Should accept 'pending' as valid status."""
        task_result = {
            "id": 123,
            "status": "pending",
            "query": "Test query"
        }

        validated = ResearchTaskValidationMixin.validate_task_result(task_result)
        assert validated["status"] == "pending"

    def test_valid_processing_status(self):
        """Should accept 'processing' as valid status."""
        task_result = {
            "id": 123,
            "status": "processing",
            "query": "Test query"
        }

        validated = ResearchTaskValidationMixin.validate_task_result(task_result)
        assert validated["status"] == "processing"

    def test_valid_failed_status(self):
        """Should accept 'failed' as valid status."""
        task_result = {
            "id": 123,
            "status": "failed",
            "query": "Test query"
        }

        validated = ResearchTaskValidationMixin.validate_task_result(task_result)
        assert validated["status"] == "failed"


class TestValidateStructuredData:
    """Test validate_structured_data() method."""

    def test_valid_structured_data(self):
        """Should accept valid dict structured_data."""
        structured_data = {
            "credibility_tier": "tier_1",
            "reputation_score": 85,
            "category": "Tech & Science"
        }

        validated = ResearchTaskValidationMixin.validate_structured_data(structured_data)
        assert validated == structured_data

    def test_none_structured_data_allowed(self):
        """Should return None when structured_data is None and allow_none=True."""
        validated = ResearchTaskValidationMixin.validate_structured_data(None, allow_none=True)
        assert validated is None

    def test_none_structured_data_not_allowed(self):
        """Should raise ValueError when structured_data is None and allow_none=False."""
        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_structured_data(None, allow_none=False)

        assert "structured_data is None but required" in str(exc_info.value)

    def test_invalid_type_structured_data(self):
        """Should raise ValueError when structured_data is not a dict."""
        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_structured_data("invalid string")

        assert "structured_data is not a dict" in str(exc_info.value)
        assert "got str" in str(exc_info.value)

    def test_empty_dict_structured_data(self):
        """Should accept empty dict as valid structured_data."""
        validated = ResearchTaskValidationMixin.validate_structured_data({})
        assert validated == {}


class TestValidateResultContent:
    """Test validate_result_content() method."""

    def test_valid_result_content(self):
        """Should extract content string from valid result."""
        task_result = {
            "result": {
                "content": "Test content from Perplexity"
            }
        }

        content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert content == "Test content from Perplexity"

    def test_missing_result_field(self):
        """Should return None when result field is missing."""
        task_result = {}

        content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert content is None

    def test_none_result_field(self):
        """Should return None when result field is None."""
        task_result = {"result": None}

        content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert content is None

    def test_invalid_result_type(self):
        """Should return None when result is not a dict."""
        task_result = {"result": "invalid string"}

        content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert content is None

    def test_missing_content_field(self):
        """Should return None when content field is missing."""
        task_result = {"result": {}}

        content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert content is None

    def test_none_content_field(self):
        """Should return None when content field is None."""
        task_result = {"result": {"content": None}}

        content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert content is None

    def test_non_string_content_converted(self):
        """Should convert non-string content to string."""
        task_result = {"result": {"content": 12345}}

        content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert content == "12345"


class TestResearchTaskResponseModel:
    """Test ResearchTaskResponse Pydantic model."""

    def test_valid_model_creation(self):
        """Should create model with valid data."""
        data = {
            "id": 123,
            "status": "completed",
            "query": "Test query",
            "structured_data": {"tier": "tier_1"},
            "result": {"content": "Test"},
            "tokens_used": 500,
            "cost": 0.001
        }

        model = ResearchTaskResponse(**data)
        assert model.id == 123
        assert model.status == "completed"
        assert model.query == "Test query"

    def test_invalid_status_pattern(self):
        """Should reject invalid status values."""
        data = {
            "id": 123,
            "status": "invalid",
            "query": "Test query"
        }

        with pytest.raises(ValueError) as exc_info:
            ResearchTaskResponse(**data)

        assert "status" in str(exc_info.value)

    def test_optional_fields_none(self):
        """Should accept None for optional fields."""
        data = {
            "id": 123,
            "status": "pending",
            "query": "Test query"
        }

        model = ResearchTaskResponse(**data)
        assert model.structured_data is None
        assert model.result is None
        assert model.tokens_used is None

    def test_invalid_structured_data_type(self):
        """Should reject non-dict structured_data."""
        data = {
            "id": 123,
            "status": "completed",
            "query": "Test query",
            "structured_data": "invalid"
        }

        with pytest.raises(ValueError) as exc_info:
            ResearchTaskResponse(**data)

        assert "structured_data must be dict or None" in str(exc_info.value)

    def test_invalid_result_type(self):
        """Should reject non-dict result."""
        data = {
            "id": 123,
            "status": "completed",
            "query": "Test query",
            "result": "invalid"
        }

        with pytest.raises(ValueError) as exc_info:
            ResearchTaskResponse(**data)

        assert "result must be dict or None" in str(exc_info.value)


class TestRealWorldScenarios:
    """Test real-world scenarios based on production issues."""

    def test_perplexity_structured_output_success(self):
        """Simulates successful Perplexity response with structured_data."""
        task_result = {
            "id": 123,
            "status": "completed",
            "query": "Assess Democracy Now",
            "structured_data": {
                "credibility_tier": "tier_2",
                "reputation_score": 75,
                "founded_year": 1996,
                "organization_type": "independent_media",
                "political_bias": "left_leaning",
                "category": "General News",
                "summary": "Independent progressive news",
                "recommendation": {
                    "skip_waiting_period": False,
                    "initial_quality_boost": 5
                }
            },
            "result": {
                "content": "Democracy Now is...",
                "search_results": []
            },
            "tokens_used": 1200,
            "cost": 0.024
        }

        # Validate entire structure
        validated = ResearchTaskValidationMixin.validate_task_result(task_result)
        assert validated["status"] == "completed"

        # Validate structured_data
        structured_data = ResearchTaskValidationMixin.validate_structured_data(
            task_result.get("structured_data")
        )
        assert structured_data is not None
        assert structured_data["credibility_tier"] == "tier_2"

    def test_perplexity_no_structured_data_fallback(self):
        """Simulates Perplexity response without structured_data (requires regex parsing)."""
        task_result = {
            "id": 124,
            "status": "completed",
            "query": "Assess Channel NewsAsia",
            "structured_data": None,
            "result": {
                "content": """
                **Credibility tier:** *tier_1*
                **Reputation score (0-100):** *80-90*
                **Founded year:** *1999*
                **Organization type:** *state_owned*
                **Political bias:** *moderate*
                """
            },
            "tokens_used": 800,
            "cost": 0.016
        }

        # Validate task_result
        validated = ResearchTaskValidationMixin.validate_task_result(task_result)
        assert validated["status"] == "completed"

        # structured_data is None (allowed)
        structured_data = ResearchTaskValidationMixin.validate_structured_data(
            task_result.get("structured_data")
        )
        assert structured_data is None

        # Use fallback: extract result.content
        result_content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert result_content is not None
        assert "tier_1" in result_content

    def test_research_service_still_processing(self):
        """Simulates fetching task while Perplexity is still processing (race condition)."""
        task_result = {
            "id": 125,
            "status": "processing",
            "query": "Assess Aljazeera",
            "structured_data": None,
            "result": None
        }

        # Should validate successfully with status="processing"
        validated = ResearchTaskValidationMixin.validate_task_result(task_result)
        assert validated["status"] == "processing"

        # structured_data is None when processing
        structured_data = ResearchTaskValidationMixin.validate_structured_data(
            task_result.get("structured_data")
        )
        assert structured_data is None

        # result.content is None when processing
        result_content = ResearchTaskValidationMixin.validate_result_content(task_result)
        assert result_content is None

    def test_research_service_none_response(self):
        """Simulates the original bug: research service returns None."""
        task_result = None

        # Should raise clear error message
        with pytest.raises(ValueError) as exc_info:
            ResearchTaskValidationMixin.validate_task_result(task_result)

        assert "task_result is None" in str(exc_info.value)
        assert "research service may have returned empty response" in str(exc_info.value)
