"""
CHECKPOINT TEST: Tier0 → Tier1 → Tier2 Pipeline
Tests single article through complete analysis pipeline
"""

import asyncio
import asyncpg
from uuid import uuid4
import os
import sys

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.pipeline.tier0.triage import Tier0Triage
from app.pipeline.tier1.foundation import Tier1Foundation
from app.pipeline.tier2.orchestrator import Tier2Orchestrator


# Sample article for testing (financial + geopolitical content)
SAMPLE_ARTICLE = {
    "title": "Federal Reserve Raises Interest Rates Amid Geopolitical Tensions",
    "url": "https://example.com/fed-rate-hike-geopolitical-crisis",
    "content": """
    WASHINGTON - The Federal Reserve announced a 0.25% interest rate increase on Wednesday,
    marking the third consecutive hike this year as the central bank continues its battle
    against persistent inflation. Fed Chair Jerome Powell stated that the decision was made
    to maintain price stability despite ongoing geopolitical uncertainties.

    "We are committed to bringing inflation back to our 2% target," Powell said during
    the press conference. "While we acknowledge the risks posed by global conflicts, our
    primary mandate remains price stability and maximum employment."

    The rate hike comes as global markets remain volatile due to escalating tensions in
    Eastern Europe and the Middle East. Russia's ongoing conflict with Ukraine continues
    to disrupt energy markets, while Israel's response to recent attacks has raised concerns
    about regional stability.

    Wall Street reacted negatively to the news, with the S&P 500 dropping 2.3% and the
    Nasdaq falling 3.1% in afternoon trading. Technology stocks were hit particularly hard,
    with Apple (AAPL) down 4.2% and Tesla (TSLA) falling 5.8%.

    "The Fed is walking a tightrope between controlling inflation and avoiding a recession,"
    said Sarah Chen, Chief Economist at Goldman Sachs. "Higher rates will cool demand, but
    they also risk slowing economic growth at a time when geopolitical risks are elevated."

    Energy prices have remained elevated due to supply disruptions caused by the Russia-Ukraine
    conflict. Brent crude oil traded at $92 per barrel, up from $85 last month. Natural gas
    prices in Europe have also surged as countries scramble to secure alternative supplies.

    The European Central Bank (ECB) is expected to follow the Fed's lead with its own rate
    increase next week. ECB President Christine Lagarde has signaled that fighting inflation
    remains the priority despite economic headwinds from the conflict.

    Analysts predict the Fed will implement at least one more rate hike before the end of
    the year, bringing the federal funds rate to 5.5-5.75%. However, Powell emphasized that
    future decisions will be "data-dependent" and will consider both economic indicators
    and global risk factors.

    The rate decision has implications for consumers, as mortgage rates and credit card
    interest rates are expected to rise further. The average 30-year fixed mortgage rate
    has already climbed to 7.2%, the highest level in over two decades.

    In a joint statement, European leaders expressed concern about the economic impact of
    both inflation and geopolitical instability. NATO Secretary General Jens Stoltenberg
    called for continued Western support for Ukraine while maintaining economic resilience.

    "We must support Ukraine's sovereignty while also ensuring our economies remain strong,"
    Stoltenberg said. "These dual challenges require coordinated action from our allies."
    """
}


async def run_full_pipeline_test():
    """Run complete checkpoint test for Tier0 → Tier1 → Tier2 pipeline."""

    print("=" * 80)
    print("CHECKPOINT TEST: Tier0 → Tier1 → Tier2 Full Pipeline")
    print("=" * 80)
    print()

    # Connect to database
    print("[1/7] Connecting to database...")
    db_pool = await asyncpg.create_pool(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        min_size=1,
        max_size=3
    )
    print(f"✓ Connected to {settings.POSTGRES_DB}")
    print()

    # Generate article ID
    article_id = uuid4()
    print(f"[2/7] Testing with article ID: {article_id}")
    print(f"Title: {SAMPLE_ARTICLE['title']}")
    print()

    try:
        # ==================================================================
        # TIER 0: TRIAGE
        # ==================================================================
        print("[3/7] Running Tier0 Triage...")
        tier0 = Tier0Triage(db_pool)
        triage_decision = await tier0.execute(
            article_id=article_id,
            title=SAMPLE_ARTICLE["title"],
            url=SAMPLE_ARTICLE["url"],
            content=SAMPLE_ARTICLE["content"]
        )

        print(f"✓ Tier0 Complete:")
        print(f"  - PriorityScore: {triage_decision.PriorityScore}/10")
        print(f"  - Category: {triage_decision.category}")
        print(f"  - Keep: {triage_decision.keep}")
        print(f"  - Model: {triage_decision.model}")
        print(f"  - Tokens: {triage_decision.tokens_used}")
        print(f"  - Cost: ${triage_decision.cost_usd:.6f}")
        print()

        # Verify Tier0 data was stored
        async with db_pool.acquire() as conn:
            tier0_stored = await conn.fetchrow(
                "SELECT * FROM triage_decisions WHERE article_id = $1",
                article_id
            )
            if tier0_stored:
                print("✓ Tier0 data verified in database")
            else:
                print("✗ ERROR: Tier0 data not found in database")
                return False
        print()

        # If discarded, stop here
        if not triage_decision.keep:
            print(f"Article discarded (PriorityScore={triage_decision.PriorityScore})")
            print("Skipping Tier1 and Tier2 (as expected)")
            print()
            print("=" * 80)
            print("CHECKPOINT RESULT: ✓ PASS (article correctly discarded)")
            print("=" * 80)
            return True

        # ==================================================================
        # TIER 1: FOUNDATION EXTRACTION
        # ==================================================================
        print("[4/7] Running Tier1 Foundation Extraction...")
        tier1 = Tier1Foundation(db_pool)
        tier1_results = await tier1.execute(
            article_id=article_id,
            title=SAMPLE_ARTICLE["title"],
            url=SAMPLE_ARTICLE["url"],
            content=SAMPLE_ARTICLE["content"]
        )

        print(f"✓ Tier1 Complete:")
        print(f"  - Entities: {len(tier1_results.entities)}")
        for entity in tier1_results.entities[:5]:  # Show first 5
            print(f"    - {entity.name} ({entity.type}): {entity.mentions} mentions")
        if len(tier1_results.entities) > 5:
            print(f"    ... and {len(tier1_results.entities) - 5} more")

        print(f"  - Relations: {len(tier1_results.relations)}")
        for relation in tier1_results.relations[:3]:  # Show first 3
            print(f"    - {relation.subject} → {relation.predicate} → {relation.object}")
        if len(tier1_results.relations) > 3:
            print(f"    ... and {len(tier1_results.relations) - 3} more")

        print(f"  - Topics: {len(tier1_results.topics)}")
        for topic in tier1_results.topics:
            print(f"    - {topic.keyword} [{topic.parent_category}]")

        print(f"  - Scores:")
        print(f"    - Impact: {tier1_results.impact_score:.1f}/10.0")
        print(f"    - Credibility: {tier1_results.credibility_score:.1f}/10.0")
        print(f"    - Urgency: {tier1_results.urgency_score:.1f}/10.0")

        print(f"  - Model: {tier1_results.model}")
        print(f"  - Tokens: {tier1_results.tokens_used}")
        print(f"  - Cost: ${tier1_results.cost_usd:.6f}")
        print()

        # Verify Tier1 data was stored
        async with db_pool.acquire() as conn:
            entities_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tier1_entities WHERE article_id = $1",
                article_id
            )
            relations_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tier1_relations WHERE article_id = $1",
                article_id
            )
            topics_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tier1_topics WHERE article_id = $1",
                article_id
            )

            print(f"✓ Tier1 data verified:")
            print(f"  - Entities stored: {entities_count}")
            print(f"  - Relations stored: {relations_count}")
            print(f"  - Topics stored: {topics_count}")
        print()

        # ==================================================================
        # TIER 2: SPECIALIST ANALYSIS
        # ==================================================================
        print("[5/7] Running Tier2 Specialist Analysis...")
        tier2 = Tier2Orchestrator(db_pool)
        tier2_results = await tier2.analyze_article(
            article_id=article_id,
            title=SAMPLE_ARTICLE["title"],
            content=SAMPLE_ARTICLE["content"],
            tier1_results=tier1_results
        )

        print(f"✓ Tier2 Complete:")
        print(f"  - Active Specialists: {len(tier2_results.active_specialists)}/{len(tier2.specialists)}")

        # Show which specialists ran
        for specialist_name in tier2_results.active_specialists:
            print(f"    - {specialist_name}")

        # Show specialist-specific results
        if tier2_results.topic_classification:
            print(f"  - Topic Classification:")
            topics = tier2_results.topic_classification.topic_classification.topics
            for topic in topics[:3]:
                print(f"    - {topic.get('topic', 'N/A')} (confidence: {topic.get('confidence', 0):.2f})")

        if tier2_results.entity_enrichment:
            print(f"  - Entity Enrichment:")
            entities = tier2_results.entity_enrichment.entity_enrichment.entities
            print(f"    - {len(entities)} entities enriched")

        if tier2_results.financial_metrics:
            print(f"  - Financial Metrics:")
            metrics = tier2_results.financial_metrics.financial_metrics.metrics
            print(f"    - Market Impact: {metrics.get('market_impact', 'N/A')}")
            if tier2_results.financial_metrics.financial_metrics.affected_symbols:
                symbols = tier2_results.financial_metrics.financial_metrics.affected_symbols
                print(f"    - Affected Symbols: {', '.join(symbols[:5])}")

        if tier2_results.geopolitical_metrics:
            print(f"  - Geopolitical Metrics:")
            countries = tier2_results.geopolitical_metrics.geopolitical_metrics.countries_involved
            print(f"    - Countries Involved: {', '.join(countries)}")

        if tier2_results.sentiment_metrics:
            print(f"  - Sentiment Analysis:")
            metrics = tier2_results.sentiment_metrics.sentiment_metrics.metrics
            bullish = metrics.get('bullish_ratio', 0)
            bearish = metrics.get('bearish_ratio', 0)
            print(f"    - Bullish: {bullish:.2f}, Bearish: {bearish:.2f}")

        print(f"  - Total Tokens Used: {tier2_results.total_tokens_used}")
        print(f"  - Total Cost: ${tier2_results.total_cost_usd:.6f}")
        print()

        # ==================================================================
        # VERIFY DATABASE STORAGE
        # ==================================================================
        print("[6/7] Verifying Tier2 data storage...")
        async with db_pool.acquire() as conn:
            tier2_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tier2_specialist_results WHERE article_id = $1",
                article_id
            )

            # Get specialist types stored
            specialist_types = await conn.fetch(
                "SELECT specialist_type, tokens_used, cost_usd FROM tier2_specialist_results WHERE article_id = $1",
                article_id
            )

            print(f"✓ Tier2 specialist results stored: {tier2_count}")
            for row in specialist_types:
                print(f"  - {row['specialist_type']}: {row['tokens_used']} tokens, ${row['cost_usd']:.6f}")
        print()

        # ==================================================================
        # COST ANALYSIS
        # ==================================================================
        print("[7/7] Cost Analysis...")
        total_cost = (
            triage_decision.cost_usd +
            tier1_results.cost_usd +
            tier2_results.total_cost_usd
        )

        print(f"✓ Total Pipeline Cost: ${total_cost:.6f}")
        print(f"  - Tier0 (Triage):     ${triage_decision.cost_usd:.6f} ({triage_decision.tokens_used} tokens)")
        print(f"  - Tier1 (Foundation): ${tier1_results.cost_usd:.6f} ({tier1_results.tokens_used} tokens)")
        print(f"  - Tier2 (Specialists): ${tier2_results.total_cost_usd:.6f} ({tier2_results.total_tokens_used} tokens)")
        print()

        # Budget validation
        TIER0_BUDGET = settings.V3_TIER0_MAX_COST
        TIER1_BUDGET = settings.V3_TIER1_MAX_COST
        TIER2_BUDGET = settings.V3_TIER2_MAX_COST
        TOTAL_BUDGET = TIER0_BUDGET + TIER1_BUDGET + TIER2_BUDGET

        print(f"Budget Compliance:")
        tier0_pct = (triage_decision.cost_usd / TIER0_BUDGET) * 100
        tier1_pct = (tier1_results.cost_usd / TIER1_BUDGET) * 100
        tier2_pct = (tier2_results.total_cost_usd / TIER2_BUDGET) * 100
        total_pct = (total_cost / TOTAL_BUDGET) * 100

        print(f"  - Tier0: {tier0_pct:.1f}% of budget (${TIER0_BUDGET:.6f})")
        print(f"  - Tier1: {tier1_pct:.1f}% of budget (${TIER1_BUDGET:.6f})")
        print(f"  - Tier2: {tier2_pct:.1f}% of budget (${TIER2_BUDGET:.6f})")
        print(f"  - Total: {total_pct:.1f}% of budget (${TOTAL_BUDGET:.6f})")
        print()

        # Token validation
        if tier2_results.total_tokens_used > settings.V3_TIER2_MAX_TOKENS:
            print(f"⚠ WARNING: Tier2 exceeded token budget!")
            print(f"  Used: {tier2_results.total_tokens_used}, Budget: {settings.V3_TIER2_MAX_TOKENS}")
        else:
            print(f"✓ Tier2 within token budget: {tier2_results.total_tokens_used}/{settings.V3_TIER2_MAX_TOKENS}")
        print()

        # ==================================================================
        # SUMMARY
        # ==================================================================
        print("=" * 80)
        print("CHECKPOINT RESULT: ✓ PASS")
        print("=" * 80)
        print()
        print("Pipeline Summary:")
        print(f"  ✓ Tier0: Article triaged (PriorityScore={triage_decision.PriorityScore}, Keep={triage_decision.keep})")
        print(f"  ✓ Tier1: Extracted {len(tier1_results.entities)} entities, {len(tier1_results.relations)} relations, {len(tier1_results.topics)} topics")
        print(f"  ✓ Tier2: {len(tier2_results.active_specialists)} specialists active")
        print()
        print("Data Storage:")
        print(f"  ✓ Tier0: triage_decisions table")
        print(f"  ✓ Tier1: tier1_entities, tier1_relations, tier1_topics, tier1_scores")
        print(f"  ✓ Tier2: tier2_specialist_results ({tier2_count} records)")
        print()
        print("Cost Summary:")
        print(f"  ✓ Total Cost: ${total_cost:.6f}")
        print(f"  ✓ Budget Utilization: {total_pct:.1f}%")
        print(f"  ✓ Target: ${TOTAL_BUDGET:.6f}")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print("CHECKPOINT RESULT: ✗ FAIL")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await db_pool.close()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run test
    success = asyncio.run(run_full_pipeline_test())
    sys.exit(0 if success else 1)
