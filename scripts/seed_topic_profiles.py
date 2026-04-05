#!/usr/bin/env python3
"""
Seed Initial Topic Profiles for Semantic Category Matching.

Creates the initial set of topic profiles (Finance, Conflict, Technology, etc.)
with descriptive text for embedding-based cluster matching.

Run from project root:
    docker exec news-clustering-service python /app/scripts/seed_topic_profiles.py

Or from host with Docker network access:
    python scripts/seed_topic_profiles.py
"""

import asyncio
import os
import sys

# Add service path for imports when running in container
sys.path.insert(0, "/home/cytrex/news-microservices/services/clustering-service")
sys.path.insert(0, "/app")

from dotenv import load_dotenv

load_dotenv("/home/cytrex/news-microservices/.env")
load_dotenv("/app/.env")


# Profile definitions with English descriptions (better embedding match for English news)
PROFILES = [
    {
        "name": "finance",
        "display_name": "Financial Markets",
        "priority": 10,
        "min_similarity": 0.40,
        "description_text": """
Financial markets stocks bonds ETFs mutual funds hedge funds investment banking
Federal Reserve interest rates monetary policy quantitative easing inflation
Wall Street NASDAQ NYSE S&P 500 Dow Jones stock market trading
Earnings reports quarterly results revenue profit margins market capitalization
IPO mergers acquisitions corporate finance private equity venture capital
Currency exchange forex foreign exchange dollar euro yen pound
Cryptocurrency Bitcoin Ethereum blockchain digital assets tokenization
Banking credit lending mortgages loans debt securities treasury bonds
Commodities gold silver oil natural gas futures derivatives options
Economic indicators GDP unemployment consumer spending retail sales
Financial regulation SEC CFTC banking supervision compliance
Insurance underwriting risk management actuarial analysis
Real estate investment trusts REITs property markets commercial residential
Central banks ECB Bank of Japan monetary policy decisions
Credit ratings Moody's S&P Fitch bond ratings sovereign debt
""",
    },
    {
        "name": "conflict",
        "display_name": "Conflict & Geopolitics",
        "priority": 9,
        "min_similarity": 0.40,
        "description_text": """
Military conflict war armed forces combat operations battlefield
Ukraine Russia invasion offensive counteroffensive front lines casualties
Gaza Israel Hamas conflict ceasefire hostilities humanitarian crisis
NATO alliance defense treaty military cooperation security
Geopolitical tensions diplomatic relations international disputes sanctions
Nuclear weapons proliferation arms control treaties deterrence
Terrorism counterterrorism extremism radicalization security threats
Civil war insurgency rebellion armed groups militia
Peacekeeping UN missions international intervention blue helmets
Arms trade weapons exports military equipment defense industry
Espionage intelligence agencies covert operations surveillance
Border disputes territorial claims sovereignty maritime conflicts
Refugees displacement humanitarian corridors asylum migration crisis
War crimes atrocities international courts prosecution
Cyberwarfare hacking state-sponsored attacks digital warfare
Military technology drones precision weapons defense systems
Strategic alliances security partnerships regional stability
""",
    },
    {
        "name": "technology",
        "display_name": "Technology & Innovation",
        "priority": 8,
        "min_similarity": 0.40,
        "description_text": """
Artificial intelligence machine learning deep learning neural networks
Large language models GPT Claude AI assistants chatbots automation
Semiconductor chips processors GPU AMD Intel NVIDIA TSMC manufacturing
Cloud computing AWS Azure Google Cloud data centers infrastructure
Software development programming coding DevOps agile methodology
Cybersecurity data breaches hacking ransomware malware protection
5G networks telecommunications wireless technology mobile infrastructure
Electric vehicles EV Tesla autonomous driving self-driving cars
Robotics automation industrial robots manufacturing AI
Quantum computing research quantum supremacy computational advances
Virtual reality augmented reality metaverse immersive technology
Blockchain distributed ledger smart contracts Web3 decentralization
Biotechnology genetic engineering CRISPR gene therapy
Space technology satellites SpaceX rocket launches exploration
Internet of Things IoT connected devices smart home sensors
Streaming platforms digital content entertainment technology
Social media platforms algorithms content moderation digital advertising
Tech regulation antitrust data privacy GDPR compliance
""",
    },
    {
        "name": "politics",
        "display_name": "Politics & Government",
        "priority": 7,
        "min_similarity": 0.38,
        "description_text": """
Elections voting campaigns candidates polls primary general election
Congress Senate House of Representatives legislation bills laws
Executive orders presidential actions White House administration policy
Supreme Court judicial decisions constitutional interpretation rulings
Political parties Democrats Republicans independents coalitions
Government spending budget appropriations fiscal policy deficit
Tax policy reform corporate taxes income taxes deductions credits
Healthcare policy Medicare Medicaid insurance reform
Immigration policy border security asylum refugees citizenship
Climate policy environmental regulations emissions carbon
Foreign policy diplomacy international relations treaties
State governors local government municipal county politics
Lobbying interest groups political action committees donations
Political scandals investigations ethics violations corruption
Cabinet appointments confirmations executive branch officials
Parliamentary democracy prime minister coalition government
European Union Brexit EU policies member states integration
United Nations General Assembly Security Council resolutions
""",
    },
    {
        "name": "climate",
        "display_name": "Climate & Environment",
        "priority": 6,
        "min_similarity": 0.38,
        "description_text": """
Climate change global warming greenhouse gases carbon dioxide emissions
Renewable energy solar wind hydroelectric geothermal clean energy
Paris Agreement climate accords COP conference emissions targets
Extreme weather hurricanes floods droughts wildfires heat waves
Sea level rise ice sheet melting glaciers Arctic Antarctic
Biodiversity species extinction habitat loss conservation
Deforestation rainforest Amazon Congo forest preservation
Air pollution smog particulate matter air quality health
Ocean acidification marine ecosystems coral reef bleaching
Electric grid energy transition power generation infrastructure
Carbon capture storage sequestration negative emissions technology
Sustainable development ESG investing green finance
Climate adaptation resilience infrastructure planning
Water scarcity drought management freshwater resources
Waste management recycling circular economy plastic pollution
Agriculture farming sustainable practices food security
Climate migration environmental refugees displacement
Environmental justice equity frontline communities
""",
    },
    {
        "name": "health",
        "display_name": "Health & Medicine",
        "priority": 5,
        "min_similarity": 0.38,
        "description_text": """
Public health epidemiology disease prevention health policy
Vaccines vaccination immunization COVID-19 flu shots
Pharmaceutical drugs medication FDA approval clinical trials
Hospital healthcare system medical treatment patient care
Mental health depression anxiety therapy psychiatric treatment
Cancer research oncology treatment chemotherapy immunotherapy
Infectious diseases outbreak pandemic epidemic virus bacteria
Medical research clinical studies scientific discoveries
Health insurance coverage costs premiums deductibles
Chronic diseases diabetes heart disease obesity management
Drug prices pharmaceutical industry generic medications
Medical devices technology innovation diagnostics
Telemedicine virtual healthcare digital health services
Nutrition diet wellness preventive care lifestyle
Aging population elderly care geriatric medicine
Maternal health childbirth reproductive healthcare
Global health WHO initiatives developing countries
Substance abuse addiction opioid crisis treatment
""",
    },
]


async def seed_profiles():
    """Create or update topic profiles with embeddings."""
    print("=" * 60)
    print("Seeding Topic Profiles")
    print("=" * 60)

    # Import after path setup
    from openai import AsyncOpenAI
    import asyncpg

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return

    db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    if not db_url:
        db_url = "postgresql://news_user:your_db_password@localhost:5432/news_mcp"

    client = AsyncOpenAI(api_key=api_key)
    conn = await asyncpg.connect(db_url)

    try:
        for profile in PROFILES:
            print(f"\n[{profile['name']}] {profile['display_name']}")

            # Check if exists
            existing = await conn.fetchrow(
                "SELECT id, name FROM topic_profiles WHERE name = $1",
                profile["name"],
            )

            if existing:
                print(f"   Already exists (id={existing['id']}), updating...")
                # Update existing profile
                await conn.execute(
                    """
                    UPDATE topic_profiles
                    SET display_name = $1, description_text = $2,
                        min_similarity = $3, priority = $4, updated_at = NOW()
                    WHERE name = $5
                    """,
                    profile["display_name"],
                    profile["description_text"].strip(),
                    profile["min_similarity"],
                    profile["priority"],
                    profile["name"],
                )
                profile_id = existing["id"]
            else:
                # Insert new profile
                profile_id = await conn.fetchval(
                    """
                    INSERT INTO topic_profiles (name, display_name, description_text, min_similarity, priority)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    profile["name"],
                    profile["display_name"],
                    profile["description_text"].strip(),
                    profile["min_similarity"],
                    profile["priority"],
                )
                print(f"   Created (id={profile_id})")

            # Generate embedding
            print(f"   Generating embedding...")
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=profile["description_text"].strip(),
                encoding_format="float",
            )
            embedding = response.data[0].embedding
            embedding_str = "[" + ",".join(str(f) for f in embedding) + "]"

            # Store embedding
            await conn.execute(
                """
                UPDATE topic_profiles
                SET embedding_vec = $1::vector
                WHERE id = $2
                """,
                embedding_str,
                profile_id,
            )
            print(f"   Embedding stored (dim={len(embedding)})")

        # Summary
        count = await conn.fetchval("SELECT COUNT(*) FROM topic_profiles")
        embedded = await conn.fetchval(
            "SELECT COUNT(*) FROM topic_profiles WHERE embedding_vec IS NOT NULL"
        )
        print(f"\n{'=' * 60}")
        print(f"DONE: {count} profiles total, {embedded} with embeddings")
        print("=" * 60)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_profiles())
