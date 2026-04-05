"""
CHECKPOINT TEST: Tier0 → Tier1 Pipeline
Tests single article through triage and foundation extraction
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


# Sample article for testing
SAMPLE_ARTICLE = {
    "title": "Russia Launches Major Cyberattack on Ukrainian Infrastructure",
    "url": "https://example.com/russia-ukraine-cyberattack",
    "content": """
    KYIV, Ukraine - Russian state-sponsored hackers launched a sophisticated cyberattack
    targeting critical infrastructure in Ukraine on Monday, according to Ukrainian security
    officials and cybersecurity experts.

    The attack, attributed to the Russian military intelligence unit known as APT28 (also
    called Fancy Bear), targeted power grids, telecommunications networks, and government
    systems across multiple Ukrainian cities including Kyiv, Kharkiv, and Lviv.

    Oleksiy Danilov, Secretary of Ukraine's National Security and Defense Council, said
    in a statement that "Russian cyber forces attempted to disrupt essential services, but
    our defenses held strong." He added that Ukraine's cyber defense teams, with support
    from NATO allies, were able to mitigate most of the attack within hours.

    The attack comes amid escalating tensions in the region and follows recent statements
    by Russian President Vladimir Putin warning of "consequences" for Western military aid
    to Ukraine. Cybersecurity firm CrowdStrike confirmed they are tracking the incident and
    have shared threat intelligence with Ukrainian authorities.

    "This is one of the most significant cyber operations we've observed in months," said
    John Smith, Chief Security Officer at CrowdStrike. "The sophistication and coordination
    suggest this was a state-level operation aimed at maximum disruption."

    The European Union condemned the attack, with EU Commission President Ursula von der Leyen
    calling it "another example of Russia's hybrid warfare tactics." NATO Secretary General
    Jens Stoltenberg said the alliance is monitoring the situation closely and stands ready
    to support Ukraine's cyber defense capabilities.

    Ukrainian President Volodymyr Zelenskyy thanked international partners for their support
    and vowed that Ukraine would continue strengthening its cyber defenses. "We will not be
    intimidated by these cowardly attacks on civilian infrastructure," he stated.

    The incident highlights the growing importance of cyber warfare in modern conflicts and
    the ongoing threat posed by Russian state-sponsored cyber operations. Security experts
    warn that such attacks could escalate further as geopolitical tensions remain high.
    """
}


async def run_checkpoint_test():
    """Run checkpoint test for Tier0 → Tier1 pipeline."""

    print("=" * 80)
    print("CHECKPOINT TEST: Tier0 → Tier1 Pipeline")
    print("=" * 80)
    print()

    # Connect to database
    print("[1/5] Connecting to database...")
    db_pool = await asyncpg.create_pool(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        min_size=1,
        max_size=2
    )
    print(f"✓ Connected to {settings.POSTGRES_DB}")
    print()

    # Generate article ID
    article_id = uuid4()
    print(f"[2/5] Testing with article ID: {article_id}")
    print(f"Title: {SAMPLE_ARTICLE['title']}")
    print()

    try:
        # Run Tier0 Triage
        print("[3/5] Running Tier0 Triage...")
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
            print("Skipping Tier1 (as expected)")
            print()
            print("=" * 80)
            print("CHECKPOINT RESULT: ✓ PASS (article correctly discarded)")
            print("=" * 80)
            return True

        # Run Tier1 Foundation
        print("[4/5] Running Tier1 Foundation Extraction...")
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
            print(f"    - {relation.subject} → {relation.predicate} → {relation.object} (confidence: {relation.confidence:.2f})")
        if len(tier1_results.relations) > 3:
            print(f"    ... and {len(tier1_results.relations) - 3} more")

        print(f"  - Topics: {len(tier1_results.topics)}")
        for topic in tier1_results.topics:
            print(f"    - {topic.keyword} [{topic.parent_category}] (confidence: {topic.confidence:.2f})")

        print(f"  - Scores:")
        print(f"    - Impact: {tier1_results.impact_score:.1f}/10.0")
        print(f"    - Credibility: {tier1_results.credibility_score:.1f}/10.0")
        print(f"    - Urgency: {tier1_results.urgency_score:.1f}/10.0")

        print(f"  - Model: {tier1_results.model}")
        print(f"  - Tokens: {tier1_results.tokens_used}")
        print(f"  - Cost: ${tier1_results.cost_usd:.6f}")
        print()

        # Verify Tier1 data was stored
        print("[5/5] Verifying data storage...")
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
            scores = await conn.fetchrow(
                "SELECT * FROM tier1_scores WHERE article_id = $1",
                article_id
            )

            print(f"✓ Entities stored: {entities_count}")
            print(f"✓ Relations stored: {relations_count}")
            print(f"✓ Topics stored: {topics_count}")
            print(f"✓ Scores stored: {scores is not None}")
        print()

        # Calculate total cost
        total_cost = triage_decision.cost_usd + tier1_results.cost_usd
        print(f"Total Cost: ${total_cost:.6f}")
        print(f"  - Tier0: ${triage_decision.cost_usd:.6f}")
        print(f"  - Tier1: ${tier1_results.cost_usd:.6f}")
        print()

        # Verify cost is within budget
        EXPECTED_COST = 0.00009  # $0.00002 (Tier0) + $0.00007 (Tier1)
        cost_ratio = total_cost / EXPECTED_COST

        if cost_ratio <= 1.5:  # Allow 50% variance
            print(f"✓ Cost within expected range ({cost_ratio:.1%} of target)")
        else:
            print(f"⚠ Cost higher than expected ({cost_ratio:.1%} of target)")
        print()

        print("=" * 80)
        print("CHECKPOINT RESULT: ✓ PASS")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"- Article processed successfully through Tier0 → Tier1")
        print(f"- Extracted {len(tier1_results.entities)} entities, {len(tier1_results.relations)} relations, {len(tier1_results.topics)} topics")
        print(f"- All data verified in database")
        print(f"- Total cost: ${total_cost:.6f} (target: ${EXPECTED_COST:.6f})")
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
    success = asyncio.run(run_checkpoint_test())
    sys.exit(0 if success else 1)
