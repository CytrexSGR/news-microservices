#!/usr/bin/env python3
"""Seed default escalation anchors for the Intelligence Interpretation Layer.

This script populates the escalation_anchors table with reference anchor points
for each domain (geopolitical, military, economic) and level (1-5).

Run with:
    python scripts/seed_escalation_anchors.py

Or via Docker:
    docker compose exec clustering-service python scripts/seed_escalation_anchors.py

Options:
    --force     Replace existing anchors (deletes and recreates all)
    --dry-run   Show what would be done without making changes
    --verify    Verify existing anchors after seeding
"""

import argparse
import asyncio
import hashlib
import logging
import struct
import sys
from pathlib import Path
from typing import List, Tuple

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type alias for anchor definition
# (domain, level, label, reference_text, keywords)
AnchorDefinition = Tuple[str, int, str, str, List[str]]

# Default anchor data: 15 anchors (3 domains x 5 levels)
DEFAULT_ANCHORS: List[AnchorDefinition] = [
    # =========================================================================
    # GEOPOLITICAL DOMAIN
    # =========================================================================
    ("geopolitical", 1, "routine_diplomatic_activity",
     "Routine diplomatic meetings and bilateral talks continue as scheduled. "
     "Trade negotiations proceed normally with standard protocol. Minor border discussions "
     "resolved through established diplomatic channels. Cultural exchanges and educational "
     "partnerships strengthened between nations. Regular consular operations maintained "
     "without disruption. Diplomatic relations characterized by normalcy and cooperation.",
     ["routine", "diplomatic", "bilateral", "talks", "negotiations", "cooperation",
      "partnership", "normal", "scheduled", "standard"]),

    ("geopolitical", 2, "elevated_diplomatic_tensions",
     "Diplomatic tensions rise as nations exchange sharp rhetoric. Ambassadors recalled "
     "for consultations amid growing concerns. Trade disputes intensify with tariff threats. "
     "Disputed territories see increased surveillance activity. International observers "
     "express concern over deteriorating relations. Diplomatic notes exchanged with "
     "increasingly firm language. Minor diplomatic incidents requiring formal responses.",
     ["tensions", "rhetoric", "recalled", "dispute", "concern", "surveillance",
      "consultations", "deteriorating", "tariff", "escalating"]),

    ("geopolitical", 3, "significant_geopolitical_friction",
     "Significant diplomatic friction emerges as negotiations stall. Sanctions threatened "
     "against perceived violations. Regional alliances strengthen in response to perceived "
     "threats. Border incidents reported but contained. Emergency UN Security Council "
     "session convened to address escalating situation. Diplomatic missions operating under "
     "heightened security. Third-party mediation efforts initiated. Travel advisories issued.",
     ["sanctions", "threats", "alliances", "incidents", "emergency", "escalating",
      "violations", "stalled", "friction", "mediation"]),

    ("geopolitical", 4, "severe_diplomatic_crisis",
     "Severe diplomatic crisis as embassies ordered to reduce staff. Economic sanctions "
     "imposed with immediate effect. Military posturing at disputed borders. Naval vessels "
     "repositioned in contested waters. Emergency evacuation of foreign nationals begins. "
     "International mediation efforts intensify. Airspace restrictions implemented. "
     "State-sponsored cyber operations detected. Diplomatic channels severely strained.",
     ["crisis", "sanctions", "embassies", "military", "evacuation", "posturing",
      "contested", "restrictions", "cyber", "severe"]),

    ("geopolitical", 5, "critical_geopolitical_emergency",
     "Critical geopolitical emergency with complete diplomatic breakdown. Mutual defense "
     "treaties invoked. Full mobilization of allied forces. International community issues "
     "urgent warnings of imminent conflict. Humanitarian corridors established. War declaration "
     "considered imminent by intelligence assessments. All diplomatic personnel withdrawn. "
     "International borders closed. State of emergency declared across multiple nations.",
     ["emergency", "breakdown", "mobilization", "conflict", "war", "imminent",
      "humanitarian", "critical", "withdrawn", "closed"]),

    # =========================================================================
    # MILITARY DOMAIN
    # =========================================================================
    ("military", 1, "routine_military_operations",
     "Standard military exercises conducted as part of annual training schedule. Normal "
     "patrol activities along established routes. Routine equipment maintenance and personnel "
     "rotations completed. Military cooperation continues through established channels. "
     "Joint exercises with allies proceed as planned. Defense readiness at baseline levels. "
     "Regular logistics and supply chain operations maintained.",
     ["routine", "exercises", "training", "patrol", "maintenance", "cooperation",
      "standard", "baseline", "scheduled", "normal"]),

    ("military", 2, "elevated_military_activity",
     "Military activity increases near sensitive areas. Unscheduled exercises announced "
     "with limited notice. Surveillance flights reported in contested airspace. Naval "
     "movements tracked in strategic waters. Intelligence sharing between allies intensified. "
     "Military leave cancellations in key units. Reconnaissance missions expanded. "
     "Defense systems placed on increased monitoring status.",
     ["activity", "exercises", "surveillance", "movements", "tracking", "intelligence",
      "unscheduled", "monitoring", "reconnaissance", "increased"]),

    ("military", 3, "significant_military_buildup",
     "Significant military buildup observed at forward positions. Troop reinforcements "
     "deployed to strategic locations. Air defense systems activated. Naval task forces "
     "assembled in proximity to disputed waters. Cyber operations detected targeting "
     "critical infrastructure. Reserve units called up for active duty. Logistics surge "
     "indicates preparation for extended operations. Military communications frequency increased.",
     ["buildup", "reinforcements", "deployed", "defense", "task force", "cyber",
      "strategic", "activated", "reserves", "preparation"]),

    ("military", 4, "severe_military_confrontation",
     "Severe military confrontation as forces engage in limited skirmishes. Aircraft "
     "intercepts occur with dangerous proximity. Artillery exchanges reported at border. "
     "Special operations forces mobilized. Nuclear deterrent forces placed on heightened "
     "alert status. Casualties reported in initial engagements. Electronic warfare operations "
     "intensify. No-fly zones established. Military assets moved to offensive positions.",
     ["confrontation", "skirmishes", "intercepts", "artillery", "nuclear", "alert",
      "casualties", "warfare", "offensive", "severe"]),

    ("military", 5, "critical_military_conflict",
     "Critical military conflict with sustained combat operations. Large-scale offensive "
     "launched across multiple fronts. Strategic bombing campaigns initiated. Ground forces "
     "advance into contested territory. Mass casualties reported. International laws of "
     "armed conflict invoked. Full wartime footing declared. Total military mobilization. "
     "Strategic weapons systems on highest alert. Theater-wide operations underway.",
     ["conflict", "combat", "offensive", "bombing", "advance", "casualties",
      "wartime", "mobilization", "strategic", "critical"]),

    # =========================================================================
    # ECONOMIC DOMAIN
    # =========================================================================
    ("economic", 1, "routine_economic_conditions",
     "Economic indicators show stable growth within expected ranges. Trade flows maintain "
     "normal patterns. Currency markets exhibit typical volatility. Central banks maintain "
     "standard monetary policy. Employment figures meet forecasts. Consumer confidence steady. "
     "Supply chains operating normally. Financial markets trading within expected parameters. "
     "Regular economic data releases without surprises.",
     ["stable", "growth", "normal", "standard", "steady", "typical",
      "forecasts", "routine", "expected", "regular"]),

    ("economic", 2, "elevated_economic_concerns",
     "Economic concerns rise as market volatility increases. Trade disputes create uncertainty. "
     "Currency fluctuations exceed normal ranges. Supply chain disruptions reported. Investor "
     "sentiment shifts toward caution. Central banks signal potential policy adjustments. "
     "Commodity prices experience unusual movements. Credit spreads begin widening. "
     "Economic forecasts revised with increased uncertainty ranges.",
     ["concerns", "volatility", "uncertainty", "disruptions", "caution", "fluctuations",
      "adjustments", "elevated", "widening", "revised"]),

    ("economic", 3, "significant_economic_stress",
     "Significant economic stress as markets experience sharp corrections. Trade restrictions "
     "impose substantial costs. Energy prices surge affecting multiple sectors. Credit markets "
     "tighten considerably. Major corporations announce layoffs. Emergency economic measures "
     "under consideration. Bond yields spike on sovereign risk concerns. Supply chain "
     "disruptions affect essential goods. Recession indicators emerge.",
     ["stress", "corrections", "restrictions", "surge", "tighten", "layoffs",
      "emergency", "spike", "recession", "significant"]),

    ("economic", 4, "severe_economic_crisis",
     "Severe economic crisis with market crashes across major indices. Financial institutions "
     "face liquidity pressures. Currency collapses trigger capital controls. Trade embargo "
     "implemented with severe impact. Sovereign debt concerns mount. International financial "
     "assistance requested. Bank runs reported in affected regions. Essential commodities "
     "face severe shortages. Circuit breakers triggered repeatedly.",
     ["crisis", "crashes", "collapse", "embargo", "liquidity", "controls",
      "assistance", "severe", "shortages", "triggered"]),

    ("economic", 5, "critical_economic_collapse",
     "Critical economic collapse with systemic financial failure. Banking system requires "
     "emergency intervention. Hyperinflation devastates purchasing power. Essential supply "
     "chains completely disrupted. Mass unemployment triggers social unrest. International "
     "economic isolation complete. Economic warfare measures in full effect. Currency "
     "becomes worthless. Barter economy emerges. Financial system requires complete restructuring.",
     ["collapse", "failure", "hyperinflation", "disrupted", "unrest", "isolation",
      "warfare", "critical", "worthless", "systemic"]),
]


async def generate_embedding(text: str) -> List[float]:
    """Generate deterministic placeholder embedding for anchor text.

    In production, this would call an embedding service (OpenAI, etc.).
    For seeding, we generate a deterministic 1536-dimensional placeholder
    based on the text hash. This ensures:
    - Consistent embeddings across runs
    - Different texts produce different embeddings
    - Embeddings are normalized to [-1, 1] range

    Args:
        text: The reference text to embed

    Returns:
        1536-dimensional embedding vector
    """
    # Create a SHA-256 hash of the text
    text_hash = hashlib.sha256(text.encode('utf-8')).digest()

    # Generate 1536 floats from the hash
    embedding = []
    for i in range(1536):
        # Use rolling bytes from hash combined with index for variation
        byte_idx = i % 32
        # Combine multiple sources for better distribution
        seed = text_hash[byte_idx] ^ text_hash[(byte_idx + 1) % 32]
        seed = (seed * 257 + i * 12345) % 65536
        # Normalize to [-1, 1] range
        value = (seed / 32768.0) - 1.0
        embedding.append(value)

    return embedding


async def seed_anchors(
    session: AsyncSession,
    force: bool = False,
    dry_run: bool = False
) -> int:
    """Seed default escalation anchors into the database.

    Args:
        session: Async database session
        force: If True, delete existing anchors before seeding
        dry_run: If True, show what would be done without making changes

    Returns:
        Number of anchors created (0 if skipped or dry run)
    """
    if dry_run:
        logger.info("[DRY-RUN] Checking current anchor count...")
        result = await session.execute(
            text("SELECT COUNT(*) FROM escalation_anchors")
        )
        count = result.scalar() or 0
        logger.info(f"[DRY-RUN] Found {count} existing anchors")

        if force:
            logger.info(f"[DRY-RUN] Would delete {count} existing anchors")
        elif count > 0:
            logger.info("[DRY-RUN] Would skip seeding (anchors exist)")
            return 0

        logger.info(f"[DRY-RUN] Would create {len(DEFAULT_ANCHORS)} anchors:")
        for domain, level, label, _, _ in DEFAULT_ANCHORS:
            logger.info(f"[DRY-RUN]   - {domain}/L{level}/{label}")

        return 0

    # Check existing anchors
    result = await session.execute(
        text("SELECT COUNT(*) FROM escalation_anchors")
    )
    existing_count = result.scalar() or 0

    if force:
        # Delete all existing anchors
        await session.execute(text("DELETE FROM escalation_anchors"))
        logger.info(f"Deleted {existing_count} existing anchors")
    elif existing_count > 0:
        logger.info(
            f"Found {existing_count} existing anchors, skipping seed "
            "(use --force to replace)"
        )
        return 0

    # Seed new anchors
    created = 0
    for domain, level, label, reference_text, keywords in DEFAULT_ANCHORS:
        embedding = await generate_embedding(reference_text)

        # Format embedding as pgvector string
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

        # Insert anchor using raw SQL for pgvector compatibility
        await session.execute(
            text("""
                INSERT INTO escalation_anchors
                (domain, level, label, reference_text, embedding, keywords, weight, is_active)
                VALUES (
                    :domain,
                    :level,
                    :label,
                    :reference_text,
                    :embedding::vector,
                    :keywords,
                    1.0,
                    true
                )
            """),
            {
                "domain": domain,
                "level": level,
                "label": label,
                "reference_text": reference_text,
                "embedding": embedding_str,
                "keywords": keywords,
            }
        )
        created += 1
        logger.info(f"Created anchor: {domain}/L{level}/{label}")

    await session.commit()
    return created


async def verify_anchors(session: AsyncSession) -> dict:
    """Verify the seeded anchors.

    Args:
        session: Async database session

    Returns:
        Dict with verification results
    """
    # Count by domain
    result = await session.execute(text("""
        SELECT
            domain,
            COUNT(*) as count,
            array_agg(level ORDER BY level) as levels
        FROM escalation_anchors
        WHERE is_active = true
        GROUP BY domain
        ORDER BY domain
    """))
    rows = result.fetchall()

    domains = {}
    for row in rows:
        domains[row[0]] = {
            "count": row[1],
            "levels": list(row[2]) if row[2] else []
        }

    # Get total count
    total_result = await session.execute(
        text("SELECT COUNT(*) FROM escalation_anchors WHERE is_active = true")
    )
    total = total_result.scalar() or 0

    # Check for duplicates
    dup_result = await session.execute(text("""
        SELECT domain, level, label, COUNT(*)
        FROM escalation_anchors
        GROUP BY domain, level, label
        HAVING COUNT(*) > 1
    """))
    duplicates = dup_result.fetchall()

    return {
        "total": total,
        "domains": domains,
        "duplicates": len(duplicates),
        "expected_total": len(DEFAULT_ANCHORS),
        "is_complete": total == len(DEFAULT_ANCHORS) and len(duplicates) == 0
    }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed escalation anchors for Intelligence Interpretation Layer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing anchors and reseed (replaces all)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify anchors after seeding"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create async engine and session
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=args.verbose
    )
    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    try:
        async with async_session_maker() as session:
            # Seed anchors
            count = await seed_anchors(
                session,
                force=args.force,
                dry_run=args.dry_run
            )

            if args.dry_run:
                logger.info("[DRY-RUN] Complete - no changes made")
            else:
                logger.info(f"Seeding complete: {count} anchors created")

            # Verify if requested
            if args.verify and not args.dry_run:
                logger.info("Verifying anchors...")
                verification = await verify_anchors(session)

                logger.info("=" * 50)
                logger.info("Verification Results:")
                logger.info(f"  Total anchors:    {verification['total']}")
                logger.info(f"  Expected:         {verification['expected_total']}")
                logger.info(f"  Duplicates:       {verification['duplicates']}")

                for domain, info in verification['domains'].items():
                    logger.info(f"  {domain}: {info['count']} anchors, levels {info['levels']}")

                if verification['is_complete']:
                    logger.info("Verification PASSED - all anchors present")
                else:
                    logger.warning("Verification FAILED - missing or duplicate anchors")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
