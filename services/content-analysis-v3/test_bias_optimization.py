"""
Test script to validate BiasScorer optimization (Option 1+2).

Compares:
- Token usage (expected: ~65% reduction)
- Bias scores (expected: < 0.05 deviation)
- Processing costs

Usage:
    python test_bias_optimization.py
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://news_user:your_db_password@localhost:5432/news_mcp"

# Test article IDs with known bias scores
TEST_ARTICLES = [
    "f0b6f428-a3e6-4ac5-bd1e-cddac6e3ee67",  # center (0.0)
    "0ab88d72-cc85-4d6b-9f21-92b43f63c497",  # center_left (-0.2)
    "2f8a8160-3763-4761-9803-d3b10508db4f",  # right (0.65)
    "6bfbee24-5085-4785-8cb9-e22fdebed209",  # center (0.0)
]


async def get_article_bias_data(article_ids: list[str]) -> dict:
    """Fetch current bias data for test articles."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        query = text("""
            SELECT
                article_id,
                (tier2_results->'BIAS_SCORER'->>'tokens_used')::int as tokens,
                (tier2_results->'BIAS_SCORER'->>'cost_usd')::float as cost,
                (tier2_results->'BIAS_SCORER'->'political_bias'->>'political_direction')::text as direction,
                (tier2_results->'BIAS_SCORER'->'political_bias'->>'bias_score')::float as bias_score,
                (tier2_results->'BIAS_SCORER'->'political_bias'->>'bias_strength')::text as strength,
                (tier2_results->'BIAS_SCORER'->'political_bias'->>'confidence')::float as confidence
            FROM article_analysis
            WHERE article_id = ANY(:article_ids)
            AND pipeline_version = '3.0'
            AND tier2_results->'BIAS_SCORER' IS NOT NULL
        """)

        result = session.execute(query, {"article_ids": article_ids})

        data = {}
        for row in result:
            data[row.article_id] = {
                "tokens": row.tokens,
                "cost": row.cost,
                "direction": row.direction,
                "bias_score": row.bias_score,
                "strength": row.strength,
                "confidence": row.confidence,
            }

        return data


async def main():
    """Run optimization validation test."""
    print("=" * 80)
    print("BiasScorer Optimization Test (Option 1+2)")
    print("=" * 80)
    print()

    # Get baseline data (before optimization)
    print("📊 Fetching baseline data from database...")
    baseline = await get_article_bias_data(TEST_ARTICLES)

    if not baseline:
        print("❌ No baseline data found! Run analysis on test articles first.")
        return

    print(f"✅ Found {len(baseline)} test articles with bias data\n")

    # Display baseline metrics
    print("📈 BASELINE METRICS (Old Implementation)")
    print("-" * 80)

    total_tokens = 0
    total_cost = 0.0

    for article_id, data in baseline.items():
        print(f"\nArticle: {article_id[:8]}...")
        print(f"  Direction: {data['direction']}")
        print(f"  Bias Score: {data['bias_score']:.2f}")
        print(f"  Strength: {data['strength']}")
        print(f"  Confidence: {data['confidence']:.2f}")
        print(f"  Tokens: {data['tokens']}")
        print(f"  Cost: ${data['cost']:.6f}")

        total_tokens += data['tokens']
        total_cost += data['cost']

    avg_tokens = total_tokens / len(baseline)
    avg_cost = total_cost / len(baseline)

    print("\n" + "=" * 80)
    print(f"BASELINE AVERAGES:")
    print(f"  Average Tokens: {avg_tokens:.0f}")
    print(f"  Average Cost: ${avg_cost:.6f}")
    print("=" * 80)
    print()

    # Expected results after optimization
    expected_tokens = avg_tokens * 0.35  # 65% reduction
    expected_cost = avg_cost * 0.35

    print("🎯 EXPECTED RESULTS (After Optimization)")
    print("-" * 80)
    print(f"  Expected Tokens: ~{expected_tokens:.0f} (65% reduction)")
    print(f"  Expected Cost: ~${expected_cost:.6f} (65% reduction)")
    print(f"  Max Bias Score Deviation: <0.05")
    print()

    print("📋 NEXT STEPS:")
    print("-" * 80)
    print("1. Restart content-analysis-v3 service:")
    print("   docker compose restart content-analysis-v3")
    print()
    print("2. Trigger re-analysis of test articles (use API or n8n workflow)")
    print()
    print("3. Run this script again to compare new results")
    print()
    print("4. Validate:")
    print("   - Token reduction ≥60%")
    print("   - Bias score deviation <0.05")
    print("   - Direction consistency ≥95%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
