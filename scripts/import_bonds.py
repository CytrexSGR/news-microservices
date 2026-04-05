#!/usr/bin/env python3
"""
Import government bonds from markdown file into Neo4j.

Parses AnleihenGroß.md and creates Bond nodes in the Knowledge Graph.
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

# Bonds file path
BONDS_FILE = "/tmp/AnleihenGroß.md"


def parse_bonds_file(filepath: str) -> List[Dict]:
    """
    Parse government bonds markdown file.

    Format:
        Symbol (e.g., US10Y)
        Name (e.g., United States 10 Year Government Bonds Yield)
        Data line (coupon, yield, maturity, price, etc.)

    Returns:
        List of dicts with bond information
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    bonds = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for bond symbols (e.g., US10Y, DE10Y, JP10Y)
        if re.match(r'^[A-Z]{2,3}\d{1,2}Y$', line):
            symbol = line

            # Next line should be the bond name
            if i + 1 < len(lines):
                name = lines[i + 1].strip()

                # Extract country from name
                country = "Unknown"
                if "United States" in name or "U.S." in name:
                    country = "USA"
                elif "Germany" in name:
                    country = "Germany"
                elif "United Kingdom" in name or "UK" in name:
                    country = "UK"
                elif "France" in name:
                    country = "France"
                elif "Italy" in name:
                    country = "Italy"
                elif "Japan" in name:
                    country = "Japan"
                elif "China" in name:
                    country = "China"
                elif "Canada" in name:
                    country = "Canada"
                elif "India" in name:
                    country = "India"
                elif "Indonesia" in name:
                    country = "Indonesia"
                elif "Australia" in name:
                    country = "Australia"
                elif "Brazil" in name:
                    country = "Brazil"
                elif "Euro" in name:
                    country = "EU"
                elif "South Africa" in name:
                    country = "South Africa"
                elif "South Korea" in name:
                    country = "South Korea"
                elif "Turkey" in name:
                    country = "Turkey"

                # Extract maturity years from symbol (e.g., 10 from US10Y)
                maturity_match = re.search(r'(\d{1,2})Y$', symbol)
                maturity_years = int(maturity_match.group(1)) if maturity_match else None

                if name and len(name) > 5:
                    bonds.append({
                        'symbol': symbol,
                        'name': name,
                        'country': country,
                        'bond_type': 'Government Bond',
                        'maturity_years': maturity_years
                    })

        i += 1

    return bonds


def import_bonds_to_neo4j(driver, bonds: List[Dict]):
    """
    Import government bonds into Neo4j.

    Args:
        driver: Neo4j driver instance
        bonds: List of bond dicts
    """
    with driver.session() as session:
        # Create constraints
        try:
            session.run("""
                CREATE CONSTRAINT bond_symbol_unique IF NOT EXISTS
                FOR (b:Bond) REQUIRE b.symbol IS UNIQUE
            """)
        except Exception as e:
            print(f"⚠️  Constraint creation warning: {e}")

        # Import bonds
        for bond in bonds:
            session.run("""
                MERGE (b:Bond {symbol: $symbol})
                SET b.name = $name,
                    b.country = $country,
                    b.bond_type = $bond_type,
                    b.maturity_years = $maturity_years,
                    b.updated_at = datetime()
            """,
            symbol=bond['symbol'],
            name=bond['name'],
            country=bond['country'],
            bond_type=bond['bond_type'],
            maturity_years=bond['maturity_years']
            )


def main():
    """Main execution function."""
    print("=" * 70)
    print("  Government Bonds Import to Neo4j")
    print("=" * 70)

    # Check if file exists
    if not os.path.exists(BONDS_FILE):
        print(f"❌ ERROR: File not found: {BONDS_FILE}")
        sys.exit(1)

    # Parse bonds file
    print(f"\n📄 Parsing {BONDS_FILE}...")
    bonds = parse_bonds_file(BONDS_FILE)
    print(f"✓ Found {len(bonds)} government bonds")

    # Show sample
    if bonds:
        print("\n📋 Sample bonds:")
        for bond in bonds[:5]:
            print(f"  • {bond['symbol']:8} | {bond['name'][:50]:50} | {bond['country']}")

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
    print(f"\n📊 Importing {len(bonds)} government bonds to Neo4j...")
    import_bonds_to_neo4j(driver, bonds)
    print("✅ Import complete!")

    # Close connection
    driver.close()

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully imported {len(bonds)} government bonds!")
    print("=" * 70)

    print("\n💡 Verify in Neo4j Browser:")
    print("   MATCH (b:Bond)")
    print("   RETURN b.country, count(b)")
    print("   ORDER BY count(b) DESC")
    print()


if __name__ == "__main__":
    main()
