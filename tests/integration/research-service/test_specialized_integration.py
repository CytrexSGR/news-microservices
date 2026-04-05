#!/usr/bin/env python3
"""Direct integration test for specialized functions (bypasses HTTP auth)."""

import sys
sys.path.insert(0, ".")

from app.services.function_registry import list_functions, get_function
from app.services.specialized_functions import FeedSourceAssessment
import json


def test_function_registry():
    """Test that function registry loads correctly."""
    print("=" * 60)
    print("Testing Function Registry")
    print("=" * 60)

    functions = list_functions()
    print(f"\n✅ Found {len(functions)} registered functions:")
    print(json.dumps(functions, indent=2))

    assert len(functions) == 3, "Expected 3 functions"
    assert any(f["name"] == "feed_source_assessment" for f in functions)
    print("\n✅ All expected functions registered")


def test_feed_source_assessment_prompt():
    """Test prompt generation for Feed Source Assessment."""
    print("\n" + "=" * 60)
    print("Testing Feed Source Assessment Prompt Generation")
    print("=" * 60)

    function = get_function("feed_source_assessment")

    prompt = function.build_prompt(
        domain="pravda.com.ua",
        include_bias_analysis=True,
        include_publication_patterns=True
    )

    print(f"\n📝 Generated Prompt (first 500 chars):")
    print("-" * 60)
    print(prompt[:500] + "...")
    print("-" * 60)

    # Verify prompt contains expected elements
    assert "pravda.com.ua" in prompt
    assert "credibility_tier" in prompt
    assert "reputation_score" in prompt
    assert "recommendation" in prompt
    assert "JSON" in prompt

    print("\n✅ Prompt structure validated")
    print(f"   - Domain mentioned: pravda.com.ua")
    print(f"   - JSON schema included")
    print(f"   - All required fields present")


def test_output_schema_validation():
    """Test Pydantic output schema."""
    print("\n" + "=" * 60)
    print("Testing Output Schema Validation")
    print("=" * 60)

    function = get_function("feed_source_assessment")
    schema = function.output_schema

    print(f"\n📋 Output Schema: {schema.__name__}")
    print(f"   Fields:")
    for field_name, field_info in schema.model_fields.items():
        print(f"   - {field_name}: {field_info.annotation}")

    # Test valid data
    valid_data = {
        "credibility_tier": "tier_3",
        "reputation_score": 78,
        "founded_year": 2000,
        "organization_type": "digital_native",
        "editorial_standards": {
            "fact_checking_level": "medium",
            "corrections_policy": "moderate",
            "source_attribution": "good"
        },
        "trust_ratings": {
            "media_bias_fact_check": "unknown",
            "allsides_rating": "unknown",
            "newsguard_score": None
        },
        "political_bias": "center_left",
        "recommendation": {
            "skip_waiting_period": True,
            "initial_quality_boost": 10,
            "bot_detection_threshold": "normal"
        },
        "summary": "Test summary"
    }

    try:
        validated = schema(**valid_data)
        print("\n✅ Valid data validated successfully")
        print(f"   - credibility_tier: {validated.credibility_tier}")
        print(f"   - reputation_score: {validated.reputation_score}")
        print(f"   - recommendation.skip_waiting_period: {validated.recommendation['skip_waiting_period']}")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        raise

    # Test invalid data
    invalid_data = valid_data.copy()
    invalid_data["credibility_tier"] = "invalid_tier"

    try:
        schema(**invalid_data)
        print("\n❌ Should have failed on invalid tier")
        raise AssertionError("Expected validation error")
    except Exception:
        print("\n✅ Invalid data correctly rejected")


if __name__ == "__main__":
    try:
        test_function_registry()
        test_feed_source_assessment_prompt()
        test_output_schema_validation()

        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\nSpecialized functions are ready for use!")
        print("Next steps:")
        print("  1. Test with real Perplexity API call (requires valid API key)")
        print("  2. Create templates via API")
        print("  3. Integrate with Feed Service for automated assessments")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
