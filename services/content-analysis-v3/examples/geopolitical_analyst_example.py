"""
Example: Using GEOPOLITICAL_ANALYST Specialist

This example demonstrates how to use the GeopoliticalAnalyst specialist
to analyze articles with geopolitical significance.
"""

import asyncio
from uuid import uuid4

from app.pipeline.tier2.specialists import GeopoliticalAnalyst
from app.models.schemas import (
    Tier1Results,
    Entity,
    Relation,
    Topic
)


async def example_geopolitical_analysis():
    """
    Example: Analyze a geopolitical article about Ukraine-NATO relations.
    """

    # Sample article data
    article_id = uuid4()
    title = "NATO Summit: Alliance Commits to Enhanced Support for Ukraine"
    content = """
    In a landmark decision at the emergency NATO summit in Brussels,
    alliance leaders unanimously agreed to provide comprehensive military
    and humanitarian support to Ukraine. The declaration, signed by all
    32 member states, reinforces NATO's commitment to collective defense
    while stopping short of direct military intervention.

    Secretary General Jens Stoltenberg emphasized that the alliance stands
    united in opposing Russian aggression and will continue to support
    Ukraine's territorial integrity through sustained military aid packages.
    The summit also addressed concerns about regional stability in Eastern
    Europe and the Baltic states.

    The decision comes amid escalating tensions and has already drawn
    strong condemnation from Moscow, raising concerns about further
    deterioration of Russia-NATO relations. European leaders stressed
    the importance of maintaining diplomatic channels while ensuring
    defensive capabilities.
    """

    # Mock Tier1 results (normally provided by Tier1 Foundation)
    tier1_results = Tier1Results(
        entities=[
            Entity(
                name="NATO",
                type="ORGANIZATION",
                confidence=0.95,
                mentions=8,
                role="Military alliance"
            ),
            Entity(
                name="Ukraine",
                type="LOCATION",
                confidence=0.95,
                mentions=6
            ),
            Entity(
                name="Russia",
                type="LOCATION",
                confidence=0.90,
                mentions=4
            ),
            Entity(
                name="Jens Stoltenberg",
                type="PERSON",
                confidence=0.90,
                mentions=2,
                role="NATO Secretary General"
            ),
            Entity(
                name="Brussels",
                type="LOCATION",
                confidence=0.85,
                mentions=2
            ),
        ],
        relations=[
            Relation(
                subject="NATO",
                predicate="SUPPORTS",
                object="Ukraine",
                confidence=0.95
            ),
            Relation(
                subject="Russia",
                predicate="OPPOSES",
                object="NATO",
                confidence=0.90
            ),
            Relation(
                subject="Jens Stoltenberg",
                predicate="LEADS",
                object="NATO",
                confidence=0.95
            ),
        ],
        topics=[
            Topic(
                keyword="CONFLICT",
                confidence=0.95,
                parent_category="Security"
            ),
            Topic(
                keyword="DIPLOMACY",
                confidence=0.90,
                parent_category="International Relations"
            ),
            Topic(
                keyword="SECURITY",
                confidence=0.85,
                parent_category="Defense"
            ),
        ],
        impact_score=9.5,
        credibility_score=9.0,
        urgency_score=8.5,
        tokens_used=1500,
        cost_usd=0.00005,
        model="gemini-2.0-flash-exp"
    )

    # Initialize specialist
    analyst = GeopoliticalAnalyst()

    print(f"=== GEOPOLITICAL ANALYST EXAMPLE ===\n")
    print(f"Article ID: {article_id}")
    print(f"Title: {title}\n")

    # Stage 1: Quick Check
    print("STAGE 1: Quick Relevance Check")
    print("-" * 50)

    quick_result = await analyst.quick_check(
        article_id=article_id,
        title=title,
        content=content,
        tier1_results=tier1_results
    )

    print(f"Is Relevant: {quick_result.is_relevant}")
    print(f"Confidence: {quick_result.confidence:.2f}")
    print(f"Reasoning: {quick_result.reasoning}")
    print(f"Tokens Used: {quick_result.tokens_used}\n")

    if not quick_result.is_relevant:
        print("⚠️  Article not relevant for geopolitical analysis. Stopping.")
        return

    # Stage 2: Deep Dive Analysis
    print("STAGE 2: Deep Geopolitical Analysis")
    print("-" * 50)

    findings = await analyst.deep_dive(
        article_id=article_id,
        title=title,
        content=content,
        tier1_results=tier1_results,
        max_tokens=1500
    )

    print(f"Specialist Type: {findings.specialist_type}")
    print(f"\nGeopolitical Metrics:")

    if findings.geopolitical_metrics:
        metrics = findings.geopolitical_metrics.metrics

        print(f"  • Conflict Severity: {metrics.get('conflict_severity', 0):.1f}/10.0")
        print(f"  • Diplomatic Impact: {metrics.get('diplomatic_impact', 0):.1f}/10.0")
        print(f"  • Regional Stability Risk: {metrics.get('regional_stability_risk', 0):.1f}/10.0")
        print(f"  • International Attention: {metrics.get('international_attention', 0):.1f}/10.0")
        print(f"  • Economic Implications: {metrics.get('economic_implications', 0):.1f}/10.0")

        print(f"\nCountries Involved ({len(findings.geopolitical_metrics.countries_involved)}):")
        for country in findings.geopolitical_metrics.countries_involved:
            print(f"  • {country}")

        print(f"\nGeopolitical Relations ({len(findings.geopolitical_metrics.relations)}):")
        for rel in findings.geopolitical_metrics.relations:
            print(f"  • {rel['subject']} {rel['predicate']} {rel['object']} "
                  f"(confidence: {rel['confidence']:.2f})")

    print(f"\nMetadata:")
    print(f"  • Tokens Used: {findings.tokens_used}")
    print(f"  • Cost: ${findings.cost_usd:.6f}")
    print(f"  • Model: {findings.model}")

    # Total analysis cost
    total_tokens = quick_result.tokens_used + findings.tokens_used
    total_cost = findings.cost_usd

    print(f"\nTotal Analysis:")
    print(f"  • Total Tokens: {total_tokens}")
    print(f"  • Total Cost: ${total_cost:.6f}")

    print("\n✅ Geopolitical analysis complete!")


async def example_non_geopolitical_article():
    """
    Example: Test with non-geopolitical article (should be skipped).
    """

    article_id = uuid4()
    title = "Apple Unveils New iPhone 15 Pro with Revolutionary Camera System"
    content = """
    Apple today announced the iPhone 15 Pro, featuring a groundbreaking
    camera system with advanced computational photography capabilities.
    The new device includes a 48MP main sensor, improved low-light
    performance, and AI-enhanced image processing.
    """

    # Mock Tier1 results for tech article
    tier1_results = Tier1Results(
        entities=[
            Entity(name="Apple", type="ORGANIZATION", confidence=0.95, mentions=3),
            Entity(name="iPhone 15 Pro", type="EVENT", confidence=0.90, mentions=2),
        ],
        relations=[
            Relation(
                subject="Apple",
                predicate="LAUNCHES",
                object="iPhone 15 Pro",
                confidence=0.95
            ),
        ],
        topics=[
            Topic(keyword="TECHNOLOGY", confidence=0.95, parent_category="Technology"),
        ],
        impact_score=6.0,
        credibility_score=8.0,
        urgency_score=5.0,
        tokens_used=1000,
        cost_usd=0.00003,
        model="gemini-2.0-flash-exp"
    )

    analyst = GeopoliticalAnalyst()

    print(f"\n=== NON-GEOPOLITICAL ARTICLE TEST ===\n")
    print(f"Article ID: {article_id}")
    print(f"Title: {title}\n")

    quick_result = await analyst.quick_check(
        article_id=article_id,
        title=title,
        content=content,
        tier1_results=tier1_results
    )

    print(f"Is Relevant: {quick_result.is_relevant}")
    print(f"Confidence: {quick_result.confidence:.2f}")
    print(f"Reasoning: {quick_result.reasoning}")

    if not quick_result.is_relevant:
        print("\n✅ Correctly identified as non-geopolitical. Analysis skipped.")


async def main():
    """Run all examples."""
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "GEOPOLITICAL ANALYST EXAMPLES" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝\n")

    # Example 1: Geopolitical article (full analysis)
    await example_geopolitical_analysis()

    print("\n" + "=" * 80 + "\n")

    # Example 2: Non-geopolitical article (should skip)
    await example_non_geopolitical_article()


if __name__ == "__main__":
    # Note: This example requires a working LLM provider configured
    # In production, ProviderFactory will handle provider initialization
    print("Note: This example requires LLM provider configuration.")
    print("Run from within content-analysis-v3 service with proper env vars.\n")

    asyncio.run(main())
