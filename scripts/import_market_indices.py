#!/usr/bin/env python3
"""
Import Market Indices and their Constituents into Neo4j Knowledge Graph.

Fetches data from FMP API for 5 major international indices:
- S&P 500 (^GSPC) - 500 US stocks
- NASDAQ 100 (^NDX) - 100 US tech stocks
- DAX (^GDAXI) - 40 German stocks
- FTSE 100 (^FTSE) - 100 UK stocks
- CAC 40 (^FCHI) - 40 French stocks

Creates Neo4j graph structure:
- (Index) nodes for each index
- (Stock) nodes for each constituent stock
- (Stock)-[:COMPONENT_OF]->(Index) relationships
"""

import os
import sys
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict
import time

# Load environment variables
load_dotenv()

# FMP API Configuration
FMP_API_KEY = os.getenv("FMP_API_KEY")
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")  # Use 'neo4j' hostname for Docker, 'localhost' for local
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password_2024")

# Index Definitions
INDICES = {
    "^GSPC": {
        "name": "S&P 500",
        "endpoint": "sp500_constituent",
        "country": "USA",
        "description": "Standard & Poor's 500 Index - 500 largest US companies"
    },
    "^NDX": {
        "name": "NASDAQ 100",
        "endpoint": "nasdaq_constituent",
        "country": "USA",
        "description": "100 largest non-financial companies on NASDAQ"
    },
    "^GDAXI": {
        "name": "DAX",
        "endpoint": "dax_constituent",
        "country": "Germany",
        "description": "German stock market index - 40 major companies"
    },
    "^FTSE": {
        "name": "FTSE 100",
        "endpoint": "ftse_constituent",
        "country": "UK",
        "description": "Financial Times Stock Exchange - 100 largest UK companies"
    },
    "^FCHI": {
        "name": "CAC 40",
        "endpoint": "cac40_constituent",
        "country": "France",
        "description": "Cotation Assistée en Continu - 40 largest French companies"
    }
}


def fetch_constituents(endpoint: str) -> List[Dict]:
    """
    Fetch index constituents from FMP API.

    Args:
        endpoint: FMP constituent endpoint name (e.g., 'sp500_constituent')

    Returns:
        List of constituent dictionaries with symbol and name
    """
    url = f"{FMP_BASE_URL}/{endpoint}"
    params = {"apikey": FMP_API_KEY}

    print(f"  → Calling FMP API: {endpoint}...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    print(f"  ✓ Received {len(data)} constituents")

    return data


def create_neo4j_schema(driver):
    """
    Create Neo4j schema: indexes and constraints.

    Args:
        driver: Neo4j driver instance
    """
    print("\n📐 Creating Neo4j schema...")

    with driver.session() as session:
        # Constraints (unique symbol for Index and Stock)
        try:
            session.run("CREATE CONSTRAINT index_symbol_unique IF NOT EXISTS FOR (i:Index) REQUIRE i.symbol IS UNIQUE")
            print("  ✓ Index symbol constraint created")
        except Exception as e:
            print(f"  ⚠ Index constraint already exists: {e}")

        try:
            session.run("CREATE CONSTRAINT stock_symbol_unique IF NOT EXISTS FOR (s:Stock) REQUIRE s.symbol IS UNIQUE")
            print("  ✓ Stock symbol constraint created")
        except Exception as e:
            print(f"  ⚠ Stock constraint already exists: {e}")

        # Indexes for performance
        try:
            session.run("CREATE INDEX index_name IF NOT EXISTS FOR (i:Index) ON (i.name)")
            print("  ✓ Index name index created")
        except Exception as e:
            print(f"  ⚠ Index name index already exists: {e}")

        try:
            session.run("CREATE INDEX stock_name IF NOT EXISTS FOR (s:Stock) ON (s.name)")
            print("  ✓ Stock name index created")
        except Exception as e:
            print(f"  ⚠ Stock name index already exists: {e}")


def import_index_and_constituents(driver, index_symbol: str, info: Dict, constituents: List[Dict]):
    """
    Import an index and its constituent stocks into Neo4j.

    Args:
        driver: Neo4j driver instance
        index_symbol: Index symbol (e.g., '^GSPC')
        info: Index metadata dict
        constituents: List of constituent stock dicts
    """
    with driver.session() as session:
        # Create Index node
        session.run("""
            MERGE (i:Index {symbol: $symbol})
            SET i.name = $name,
                i.country = $country,
                i.description = $description,
                i.constituent_count = $count,
                i.updated_at = datetime()
        """,
        symbol=index_symbol,
        name=info["name"],
        country=info["country"],
        description=info["description"],
        count=len(constituents)
        )

        # Create Stock nodes and relationships (batch for performance)
        for constituent in constituents:
            symbol = constituent.get("symbol")
            name = constituent.get("name", constituent.get("companyName", ""))

            if not symbol:
                continue

            session.run("""
                MERGE (s:Stock {symbol: $symbol})
                SET s.name = $name,
                    s.updated_at = datetime()
                WITH s
                MATCH (i:Index {symbol: $index_symbol})
                MERGE (s)-[r:COMPONENT_OF]->(i)
                SET r.updated_at = datetime()
            """,
            symbol=symbol,
            name=name,
            index_symbol=index_symbol
            )


def main():
    """Main execution function."""
    print("=" * 70)
    print("  FMP → Neo4j Market Indices Import")
    print("=" * 70)

    # Validate API Key
    if not FMP_API_KEY:
        print("❌ ERROR: FMP_API_KEY not found in .env")
        sys.exit(1)

    print(f"\n✓ FMP API Key loaded: {FMP_API_KEY[:10]}...")
    print(f"✓ Neo4j URI: {NEO4J_URI}")

    # Connect to Neo4j
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✓ Connected to Neo4j")
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to Neo4j: {e}")
        sys.exit(1)

    # Create schema
    create_neo4j_schema(driver)

    # Import indices
    print(f"\n📊 Importing {len(INDICES)} indices...\n")

    total_stocks = 0
    for index_symbol, info in INDICES.items():
        print(f"🔹 {info['name']} ({index_symbol})")

        try:
            # Fetch from FMP
            constituents = fetch_constituents(info["endpoint"])
            total_stocks += len(constituents)

            # Import to Neo4j
            print(f"  → Importing to Neo4j...")
            import_index_and_constituents(driver, index_symbol, info, constituents)
            print(f"  ✅ Imported {len(constituents)} stocks\n")

            # Rate limiting (FMP: 300 calls/minute)
            time.sleep(0.5)

        except requests.exceptions.HTTPError as e:
            print(f"  ❌ HTTP Error: {e}")
            if e.response.status_code == 403:
                print(f"  💡 Check FMP API Key or rate limits")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Close connection
    driver.close()

    # Summary
    print("=" * 70)
    print(f"✅ Import Complete!")
    print(f"   • {len(INDICES)} indices imported")
    print(f"   • ~{total_stocks} stocks imported")
    print(f"   • ~{total_stocks} COMPONENT_OF relationships created")
    print("=" * 70)

    print("\n💡 Next steps:")
    print("   1. Verify in Neo4j Browser: http://localhost:7474")
    print("   2. Run query: MATCH (s:Stock)-[:COMPONENT_OF]->(i:Index) RETURN i.name, count(s)")
    print()


if __name__ == "__main__":
    main()
