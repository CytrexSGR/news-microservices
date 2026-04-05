#!/usr/bin/env python3
"""Live test with real Perplexity API call for structured output."""

import sys
import os
sys.path.insert(0, ".")

import asyncio
from app.services.perplexity import perplexity_client
from app.services.specialized_functions import FeedSourceAssessment, FeedSourceAssessmentOutput
import json


async def test_perplexity_structured_output():
    """Test real Perplexity API call with structured output parsing."""
    print("=" * 70)
    print("Live Perplexity API Test - Feed Source Assessment")
    print("=" * 70)

    # Initialize function
    function = FeedSourceAssessment()

    # Build prompt for a well-known news source
    domain = "reuters.com"
    prompt = function.build_prompt(
        domain=domain,
        include_bias_analysis=True,
        include_publication_patterns=True
    )

    print(f"\n📍 Testing with domain: {domain}")
    print(f"📝 Model: {function.model}")
    print(f"🔍 Depth: {function.depth}")
    print(f"\n⏳ Calling Perplexity AI...")

    try:
        # Call Perplexity with structured output validation
        result = await perplexity_client.research_structured(
            query=prompt,
            output_schema=FeedSourceAssessmentOutput,
            model=function.model,
            depth=function.depth
        )

        print("\n✅ API Call Successful!")
        print(f"   - Tokens used: {result.get('tokens_used', 0)}")
        print(f"   - Cost: ${result.get('cost', 0):.6f}")
        print(f"   - Validation: {result.get('validation_status', 'unknown')}")

        # Check if we got structured data
        if "structured_data" in result and result["validation_status"] == "valid":
            print("\n🎯 Structured Data Extracted and Validated:")
            print(json.dumps(result["structured_data"], indent=2))

            # Extract key metrics
            data = result["structured_data"]
            print(f"\n📊 Key Findings for {domain}:")
            print(f"   - Credibility Tier: {data.get('credibility_tier', 'unknown')}")
            print(f"   - Reputation Score: {data.get('reputation_score', 0)}/100")
            print(f"   - Political Bias: {data.get('political_bias', 'unknown')}")

            if "recommendation" in data:
                rec = data["recommendation"]
                print(f"\n💡 Automated Recommendations:")
                print(f"   - Skip waiting period: {rec.get('skip_waiting_period', False)}")
                print(f"   - Initial quality boost: +{rec.get('initial_quality_boost', 0)}")
                print(f"   - Bot detection: {rec.get('bot_detection_threshold', 'normal')}")

            print("\n📚 Citations:")
            for i, citation in enumerate(result.get("citations", [])[:3], 1):
                print(f"   {i}. {citation}")

            print("\n" + "=" * 70)
            print("✅ STRUCTURED OUTPUT TEST PASSED")
            print("=" * 70)
            print("\nThe system successfully:")
            print("  ✅ Called Perplexity API")
            print("  ✅ Extracted JSON from response")
            print("  ✅ Validated against Pydantic schema")
            print("  ✅ Generated actionable recommendations")
            print("\n🚀 Ready for production use!")

        else:
            print("\n⚠️ Warning: Structured data extraction or validation failed")
            print(f"   Status: {result.get('validation_status', 'unknown')}")
            if "validation_errors" in result:
                print(f"   Errors: {result['validation_errors']}")

            print("\n📄 Raw Content (first 500 chars):")
            print(result.get("content", "")[:500])

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check API key
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key or api_key.startswith("your-"):
        print("❌ PERPLEXITY_API_KEY not configured in .env")
        print("   Please set a valid API key to run this test")
        sys.exit(1)

    print(f"✅ API Key loaded: {api_key[:15]}...")

    # Run test
    asyncio.run(test_perplexity_structured_output())
