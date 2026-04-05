#!/usr/bin/env python3
"""
Test: Topic Profile Search via Embedding Similarity

Tests the concept of finding clusters by profile embedding similarity.
Uses the finanzmarkt.md text as a test profile.
"""

import asyncio
import os
import sys

# Add service path for imports
sys.path.insert(0, "/home/cytrex/news-microservices/services/clustering-service")

from openai import AsyncOpenAI

# Load environment
from dotenv import load_dotenv
load_dotenv("/home/cytrex/news-microservices/.env")


PROFILE_TEXT = """
Finanzmarkt Finanzinstrument Kapitalmarkt Geldmarkt Kreditmarkt Devisenmarkt
Wertpapiere Aktien Anleihen Schuldverschreibungen Genussscheine Investmentzertifikate
Derivate Futures Optionen Swaps Forward Rate Agreements
Zinsen Geldmarktzins Kapitalmarktzins Kreditzins Zinsänderungsrisiko
Börse Börsenkurse Handelsvolumen Kursrisiko Marktrisiko Wechselkursrisiko
Kreditinstitute Banken Finanzdienstleistungsinstitute Bundesanstalt für Finanzdienstleistungsaufsicht
Eigenhandel Emissionsgeschäft Finanzkommissionsgeschäft Anlageberatung
Investmentfonds ETF Kapitalanlage Vermögensanlagen Portfolio
Inflation Realwirtschaft Finanzwirtschaft Finanzkrise Risikoprämie
Federal Reserve EZB Zentralbank Refinanzierung Geldpolitik
"""


async def main():
    print("=" * 60)
    print("TEST: Topic Profile Search via Embedding Similarity")
    print("=" * 60)

    # 1. Create embedding for profile text
    print("\n1. Creating embedding for Finance profile...")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return

    client = AsyncOpenAI(api_key=api_key)

    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=PROFILE_TEXT,
        encoding_format="float"
    )

    profile_embedding = response.data[0].embedding
    print(f"   Embedding created: {len(profile_embedding)} dimensions")

    # 2. Search clusters by similarity
    print("\n2. Searching clusters by similarity to Finance profile...")

    import asyncpg

    db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return

    conn = await asyncpg.connect(db_url)

    try:
        # Format embedding for pgvector
        emb_str = "[" + ",".join(str(f) for f in profile_embedding) + "]"

        # Get latest batch
        batch_row = await conn.fetchrow("""
            SELECT batch_id FROM cluster_batches
            WHERE status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 1
        """)

        if not batch_row:
            print("ERROR: No completed batch found")
            return

        batch_id = batch_row["batch_id"]
        print(f"   Using batch: {batch_id}")

        # Search by cosine similarity
        results = await conn.fetch(f"""
            SELECT
                id,
                label,
                article_count,
                keywords,
                1 - (centroid_vec <=> '{emb_str}'::vector) as similarity
            FROM batch_clusters
            WHERE batch_id = $1
              AND centroid_vec IS NOT NULL
            ORDER BY centroid_vec <=> '{emb_str}'::vector
            LIMIT 25
        """, batch_id)

        print(f"\n3. TOP 25 Clusters by Finance-Similarity:\n")
        print("-" * 80)
        print(f"{'Sim':>6} | {'Articles':>8} | Label")
        print("-" * 80)

        for row in results:
            sim = row["similarity"] * 100
            label = (row["label"] or "")[:60]
            keywords = row["keywords"]
            kw_str = ", ".join(keywords.get("terms", [])[:3]) if keywords else ""

            # Color coding
            if sim >= 50:
                indicator = "🔥"
            elif sim >= 40:
                indicator = "✅"
            elif sim >= 30:
                indicator = "⚠️"
            else:
                indicator = "  "

            print(f"{sim:5.1f}% {indicator} | {row['article_count']:>8} | {label}")
            if kw_str:
                print(f"       |          | Keywords: {kw_str}")

        print("-" * 80)

        # Statistics
        high_match = sum(1 for r in results if r["similarity"] >= 0.4)
        print(f"\nStatistics:")
        print(f"  - Clusters with >= 40% similarity: {high_match}")
        print(f"  - Highest similarity: {results[0]['similarity']*100:.1f}%")
        print(f"  - Lowest in top 25: {results[-1]['similarity']*100:.1f}%")

    finally:
        await conn.close()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
