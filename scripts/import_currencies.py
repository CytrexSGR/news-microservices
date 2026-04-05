#!/usr/bin/env python3
"""
Import currency indices from markdown file into Neo4j.

Parses währungen_groß.md and creates Currency nodes in the Knowledge Graph.
"""

import os
import sys
import re
from neo4j import GraphDatabase
from typing import List, Dict

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password_2024")

# Currencies file path
CURRENCIES_FILE = "/tmp/währungen_groß.md"


def parse_currencies_file(filepath: str) -> List[Dict]:
    """
    Parse currency indices markdown file.

    Format:
        Symbol (e.g., DXY)
        Name (e.g., U.S. Dollar Currency Index)
        Data line (price, change, etc.)

    Returns:
        List of dicts with currency information
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    currencies = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for currency symbols (e.g., DXY, EXY, BXY)
        # Pattern: 1-3 uppercase letters + XY
        if re.match(r'^[A-Z]{1,3}XY$', line):
            symbol = line

            # Next line should be the currency name
            if i + 1 < len(lines):
                name = lines[i + 1].strip()

                # Extract base currency from name and symbol
                base_currency = "Unknown"
                if "Dollar" in name or symbol == "DXY":
                    base_currency = "USD"
                elif "Euro" in name or symbol == "EXY":
                    base_currency = "EUR"
                elif "Pound" in name or symbol == "BXY":
                    base_currency = "GBP"
                elif "Franc" in name or symbol == "SXY":
                    base_currency = "CHF"
                elif "Yen" in name or symbol == "JXY":
                    base_currency = "JPY"
                elif "Canadian" in name or symbol == "CXY":
                    base_currency = "CAD"
                elif "Australian" in name or symbol == "AXY":
                    base_currency = "AUD"
                elif "New Zealand" in name or symbol == "ZXY":
                    base_currency = "NZD"

                if name and len(name) > 5:
                    currencies.append({
                        'symbol': symbol,
                        'name': name,
                        'base_currency': base_currency,
                        'currency_type': 'Currency Index'
                    })

        i += 1

    return currencies


def import_currencies_to_neo4j(driver, currencies: List[Dict]):
    """
    Import currency indices into Neo4j.

    Args:
        driver: Neo4j driver instance
        currencies: List of currency dicts
    """
    with driver.session() as session:
        # Create constraints
        try:
            session.run("""
                CREATE CONSTRAINT currency_symbol_unique IF NOT EXISTS
                FOR (c:Currency) REQUIRE c.symbol IS UNIQUE
            """)
        except Exception as e:
            print(f"⚠️  Constraint creation warning: {e}")

        # Import currencies
        for currency in currencies:
            session.run("""
                MERGE (c:Currency {symbol: $symbol})
                SET c.name = $name,
                    c.base_currency = $base_currency,
                    c.currency_type = $currency_type,
                    c.updated_at = datetime()
            """,
            symbol=currency['symbol'],
            name=currency['name'],
            base_currency=currency['base_currency'],
            currency_type=currency['currency_type']
            )


def main():
    """Main execution function."""
    print("=" * 70)
    print("  Currency Indices Import to Neo4j")
    print("=" * 70)

    # Check if file exists
    if not os.path.exists(CURRENCIES_FILE):
        print(f"❌ ERROR: File not found: {CURRENCIES_FILE}")
        sys.exit(1)

    # Parse currencies file
    print(f"\n📄 Parsing {CURRENCIES_FILE}...")
    currencies = parse_currencies_file(CURRENCIES_FILE)
    print(f"✓ Found {len(currencies)} currency indices")

    # Show sample
    if currencies:
        print("\n📋 Sample currencies:")
        for currency in currencies[:8]:
            print(f"  • {currency['symbol']:5} | {currency['name'][:40]:40} | {currency['base_currency']}")

    # Connect to Neo4j
    print(f"\n🔗 Connecting to Neo4j: {NEO4J_URI}...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✓ Connected")
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to Neo4j: {e}")
        sys.exit(1)

    # Import
    print(f"\n💱 Importing {len(currencies)} currency indices to Neo4j...")
    import_currencies_to_neo4j(driver, currencies)
    print("✅ Import complete!")

    # Close connection
    driver.close()

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully imported {len(currencies)} currency indices!")
    print("=" * 70)

    print("\n💡 Verify in Neo4j Browser:")
    print("   MATCH (c:Currency)")
    print("   RETURN c.base_currency, count(c)")
    print()


if __name__ == "__main__":
    main()
