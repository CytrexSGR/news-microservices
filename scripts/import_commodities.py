#!/usr/bin/env python3
"""
Import commodities from markdown file into Neo4j.

Parses rohstoffe.md, translates German names to English,
and creates Commodity nodes in the Knowledge Graph.
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

# Commodities file path
COMMODITIES_FILE = "/tmp/rohstoffe.md"

# German to English translation mapping
COMMODITY_TRANSLATIONS = {
    # Precious Metals
    'Goldpreis': ('Gold', 'Precious Metals'),
    'Silberpreis': ('Silver', 'Precious Metals'),
    'Platinpreis': ('Platinum', 'Precious Metals'),
    'Palladiumpreis': ('Palladium', 'Precious Metals'),

    # Energy
    'Erdgaspreis - Natural Gas': ('Natural Gas', 'Energy'),
    'Heizölpreis': ('Heating Oil', 'Energy'),
    'Kohlepreis': ('Coal', 'Energy'),
    'Ölpreis (WTI)': ('Crude Oil (WTI)', 'Energy'),
    'Ölpreis (Brent)': ('Brent Oil', 'Energy'),
    'RBOB Gasoline': ('RBOB Gasoline', 'Energy'),

    # Gasoline
    'Dieselpreis Benzin': ('Diesel', 'Gasoline'),
    'Super Benzin': ('Premium Gasoline', 'Gasoline'),

    # Industrial Metals
    'Aluminiumpreis': ('Aluminum', 'Industrial Metals'),
    'Bleipreis': ('Lead', 'Industrial Metals'),
    'Kupferpreis': ('Copper', 'Industrial Metals'),
    'Nickelpreis': ('Nickel', 'Industrial Metals'),
    'Zinkpreis': ('Zinc', 'Industrial Metals'),
    'Zinnpreis': ('Tin', 'Industrial Metals'),

    # Agricultural
    'Baumwolle': ('Cotton', 'Agricultural'),
    'Haferpreis': ('Oats', 'Agricultural'),
    'Holzpreis': ('Lumber', 'Agricultural'),
    'Kaffeepreis': ('Coffee', 'Agricultural'),
    'Kakaopreis': ('Cocoa', 'Agricultural'),
    'Lebendrindpreis': ('Live Cattle', 'Agricultural'),
    'Mageres Schwein Preis': ('Lean Hogs', 'Agricultural'),
    'Maispreis': ('Corn', 'Agricultural'),
    'Mastrindpreis': ('Feeder Cattle', 'Agricultural'),
    'Milchpreis': ('Milk', 'Agricultural'),
    'Orangensaftpreis': ('Orange Juice', 'Agricultural'),
    'Palmölpreis': ('Palm Oil', 'Agricultural'),
    'Rapspreis': ('Canola', 'Agricultural'),
    'Reispreis': ('Rice', 'Agricultural'),
    'Sojabohnenmehlpreis': ('Soybean Meal', 'Agricultural'),
    'Sojabohnenölpreis': ('Soybean Oil', 'Agricultural'),
    'Sojabohnenpreis': ('Soybeans', 'Agricultural'),
    'Weizenpreis': ('Wheat', 'Agricultural'),
    'Zuckerpreis': ('Sugar', 'Agricultural'),

    # Energy Products
    'EEX Strompreis Phelix DE': ('German Power (Phelix)', 'Energy Products'),
    'Naphthapreis (European)': ('Naphtha (European)', 'Energy Products'),
}


def parse_commodities_file(filepath: str) -> List[Dict]:
    """
    Parse commodities markdown file.

    Format:
        Goldpreis	4.051,34		-0,65	USD je Feinunze	20.11 18:10

    Returns:
        List of dicts with commodity information
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    commodities = []
    lines = content.split('\n')

    for line in lines:
        # Skip headers and empty lines
        if not line.strip() or '\t' not in line:
            continue

        # Extract commodity name (before first tab)
        parts = line.split('\t')
        german_name = parts[0].strip()

        # Check if this is a known commodity
        if german_name in COMMODITY_TRANSLATIONS:
            english_name, category = COMMODITY_TRANSLATIONS[german_name]

            commodities.append({
                'name': english_name,
                'category': category,
                'german_name': german_name
            })

    # Remove duplicates
    seen = set()
    unique_commodities = []
    for commodity in commodities:
        key = commodity['name']
        if key not in seen:
            seen.add(key)
            unique_commodities.append(commodity)

    return unique_commodities


def import_commodities_to_neo4j(driver, commodities: List[Dict]):
    """
    Import commodities into Neo4j.

    Args:
        driver: Neo4j driver instance
        commodities: List of commodity dicts
    """
    with driver.session() as session:
        # Create constraints
        try:
            session.run("""
                CREATE CONSTRAINT commodity_name_unique IF NOT EXISTS
                FOR (c:Commodity) REQUIRE c.name IS UNIQUE
            """)
        except Exception as e:
            print(f"⚠️  Constraint creation warning: {e}")

        # Import commodities
        for commodity in commodities:
            session.run("""
                MERGE (c:Commodity {name: $name})
                SET c.category = $category,
                    c.german_name = $german_name,
                    c.updated_at = datetime()
            """,
            name=commodity['name'],
            category=commodity['category'],
            german_name=commodity['german_name']
            )


def main():
    """Main execution function."""
    print("=" * 70)
    print("  Commodities Import to Neo4j")
    print("=" * 70)

    # Check if file exists
    if not os.path.exists(COMMODITIES_FILE):
        print(f"❌ ERROR: File not found: {COMMODITIES_FILE}")
        sys.exit(1)

    # Parse commodities file
    print(f"\n📄 Parsing {COMMODITIES_FILE}...")
    commodities = parse_commodities_file(COMMODITIES_FILE)
    print(f"✓ Found {len(commodities)} commodities")

    # Count by category
    categories = {}
    for commodity in commodities:
        category = commodity['category']
        categories[category] = categories.get(category, 0) + 1

    print("\n📊 Breakdown by category:")
    for category, count in sorted(categories.items()):
        print(f"  • {category:20} {count:>3} commodities")

    # Show sample
    if commodities:
        print("\n📋 Sample commodities:")
        for commodity in commodities[:10]:
            print(f"  • {commodity['name']:25} | {commodity['category']:20} | {commodity['german_name']}")

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
    print(f"\n🌾 Importing {len(commodities)} commodities to Neo4j...")
    import_commodities_to_neo4j(driver, commodities)
    print("✅ Import complete!")

    # Close connection
    driver.close()

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully imported {len(commodities)} commodities!")
    print("=" * 70)

    print("\n💡 Verify in Neo4j Browser:")
    print("   MATCH (c:Commodity)")
    print("   RETURN c.category, count(c)")
    print("   ORDER BY count(c) DESC")
    print()


if __name__ == "__main__":
    main()
