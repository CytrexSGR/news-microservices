#!/usr/bin/env python3
"""
Import countries from markdown file into Neo4j.

Parses liste_länder.md and creates Country nodes in the Knowledge Graph.
Extracts country names (German/English), capitals, ISO codes, and basic stats.
"""

import os
import sys
import re
from neo4j import GraphDatabase
from typing import List, Dict, Optional

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password_2024")

# Countries file path
COUNTRIES_FILE = "/tmp/liste_länder.md"


def parse_population(pop_str: str) -> Optional[int]:
    """Parse population string to integer."""
    if not pop_str or pop_str.strip() == '':
        return None
    try:
        # Remove dots and convert to int
        clean_str = pop_str.replace('.', '').replace(',', '').strip()
        return int(clean_str)
    except:
        return None


def parse_area(area_str: str) -> Optional[int]:
    """Parse area string to integer."""
    if not area_str or area_str.strip() == '':
        return None
    try:
        # Remove dots and convert to int
        clean_str = area_str.replace('.', '').replace(',', '').strip()
        return int(clean_str)
    except:
        return None


def parse_countries_file(filepath: str) -> List[Dict]:
    """
    Parse countries markdown file.

    Multi-line format per country:
        Line 1: Name	Langform	Hauptstadt	Einwohner	Fläche
        Line 2: (empty or density data)
        Line 3: Density
        Line 4: 	ISO-3	ISO-2	TLD	English Name	Local Name

    Returns:
        List of dicts with country information
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    countries = []

    # Split by lines (handle Windows line endings)
    lines = content.replace('\r\n', '\n').split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip header, empty lines, and Earth entry
        if not line or line.startswith('Liste') or line.startswith('Staat oder') or line.startswith('Erde'):
            i += 1
            continue

        # Look for lines with ISO-3 codes (format: \t\tAFG\tAF\t.af\t...)
        if '\t' in line:
            parts = line.split('\t')

            # Find ISO-3 code (3 uppercase letters)
            iso3 = None
            iso2 = None
            tld = None
            name_en = None

            for j, part in enumerate(parts):
                part = part.strip()

                # ISO-3 code (3 uppercase letters)
                if re.match(r'^[A-Z]{3}$', part):
                    iso3 = part

                    # ISO-2 should be next
                    if j + 1 < len(parts):
                        iso2_candidate = parts[j + 1].strip()
                        if re.match(r'^[A-Z]{2}$', iso2_candidate):
                            iso2 = iso2_candidate

                    # TLD should be after ISO-2
                    if j + 2 < len(parts):
                        tld_candidate = parts[j + 2].strip()
                        if re.match(r'^\.[a-z]{2,}$', tld_candidate):
                            tld = tld_candidate

                    # English name should be after TLD
                    if j + 3 < len(parts):
                        name_en = parts[j + 3].strip()
                        if name_en.startswith('???'):
                            name_en = None

                    break

            # If we found ISO-3 code, look back for country data (3-4 lines up)
            if iso3:
                # Look back for the main country line
                for lookback in range(1, min(5, i + 1)):
                    prev_line = lines[i - lookback]

                    if prev_line.strip() and '\t' in prev_line:
                        prev_parts = prev_line.split('\t')

                        # First part should be country name (German)
                        if len(prev_parts) >= 4:
                            name_de = prev_parts[0].strip()

                            # Skip if name is empty or too short
                            if name_de and len(name_de) >= 3:
                                # Skip non-country entries
                                if not name_de.startswith('Europäische Union'):
                                    capital = prev_parts[2].strip() if len(prev_parts) > 2 else None
                                    population_str = prev_parts[3].strip() if len(prev_parts) > 3 else None
                                    area_str = prev_parts[4].strip() if len(prev_parts) > 4 else None

                                    population = parse_population(population_str)
                                    area_km2 = parse_area(area_str)

                                    # Use German name as fallback for English
                                    if not name_en or len(name_en) < 2:
                                        name_en = name_de

                                    countries.append({
                                        'name_de': name_de,
                                        'name_en': name_en,
                                        'capital': capital,
                                        'iso2': iso2,
                                        'iso3': iso3,
                                        'tld': tld,
                                        'population': population,
                                        'area_km2': area_km2
                                    })

                                    break

        i += 1

    return countries


def import_countries_to_neo4j(driver, countries: List[Dict]):
    """
    Import countries into Neo4j.

    Args:
        driver: Neo4j driver instance
        countries: List of country dicts
    """
    with driver.session() as session:
        # Create constraints
        try:
            session.run("""
                CREATE CONSTRAINT country_iso3_unique IF NOT EXISTS
                FOR (c:Country) REQUIRE c.iso3 IS UNIQUE
            """)
        except Exception as e:
            print(f"⚠️  Constraint creation warning: {e}")

        # Import countries
        for country in countries:
            # Skip if no ISO-3 code (invalid entry)
            if not country['iso3']:
                continue

            session.run("""
                MERGE (c:Country {iso3: $iso3})
                SET c.name_de = $name_de,
                    c.name_en = $name_en,
                    c.capital = $capital,
                    c.iso2 = $iso2,
                    c.tld = $tld,
                    c.population = $population,
                    c.area_km2 = $area_km2,
                    c.updated_at = datetime()
            """,
            iso3=country['iso3'],
            name_de=country['name_de'],
            name_en=country['name_en'],
            capital=country['capital'],
            iso2=country['iso2'],
            tld=country['tld'],
            population=country['population'],
            area_km2=country['area_km2']
            )


def main():
    """Main execution function."""
    print("=" * 70)
    print("  Countries Import to Neo4j")
    print("=" * 70)

    # Check if file exists
    if not os.path.exists(COUNTRIES_FILE):
        print(f"❌ ERROR: File not found: {COUNTRIES_FILE}")
        sys.exit(1)

    # Parse countries file
    print(f"\n📄 Parsing {COUNTRIES_FILE}...")
    countries = parse_countries_file(COUNTRIES_FILE)

    # Filter valid countries (with ISO-3 code)
    valid_countries = [c for c in countries if c['iso3']]
    print(f"✓ Found {len(valid_countries)} valid countries")

    # Show sample
    if valid_countries:
        print("\n📋 Sample countries:")
        for country in valid_countries[:10]:
            pop_str = f"{country['population']:,}" if country['population'] else "N/A"
            print(f"  • {country['iso3']:3} | {country['name_en']:30} | {country['capital']:20} | Pop: {pop_str}")

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
    print(f"\n🌍 Importing {len(valid_countries)} countries to Neo4j...")
    import_countries_to_neo4j(driver, valid_countries)
    print("✅ Import complete!")

    # Close connection
    driver.close()

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully imported {len(valid_countries)} countries!")
    print("=" * 70)

    print("\n💡 Verify in Neo4j Browser:")
    print("   MATCH (c:Country)")
    print("   WHERE c.population IS NOT NULL")
    print("   RETURN c.name_en, c.capital, c.population")
    print("   ORDER BY c.population DESC LIMIT 10")
    print()


if __name__ == "__main__":
    main()
