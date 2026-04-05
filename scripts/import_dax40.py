#!/usr/bin/env python3
"""
Import DAX 40 constituents from markdown file into Neo4j.

Parses /home/cytrex/userdocs/knowledge_inputs/run1/dax40.md
and creates Stock nodes with COMPONENT_OF relationships to DAX Index.
"""

import os
import sys
import re
from neo4j import GraphDatabase

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password_2024")

# DAX40 data file (in container: /tmp/dax40.md, on host: /home/cytrex/userdocs/knowledge_inputs/run1/dax40.md)
DAX40_FILE = os.getenv("DAX40_FILE", "/tmp/dax40.md")


def parse_dax40_file(filepath: str):
    """
    Parse DAX40 markdown file and extract company names and ISINs.

    Returns:
        List of dicts with 'name' and 'isin'
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    companies = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for ISIN pattern (starts with country code + 10 digits/letters)
        if re.match(r'^[A-Z]{2}[A-Z0-9]{10}', line):
            # ISIN found, previous line should be company name
            if i > 0:
                name = lines[i-1].strip()
                isin = line.split('\t')[0].strip()  # Extract ISIN before tab

                if name and isin and len(name) > 1:
                    companies.append({
                        'name': name,
                        'isin': isin
                    })

        i += 1

    return companies


def import_dax40_to_neo4j(driver, companies):
    """
    Import DAX40 companies into Neo4j.

    Args:
        driver: Neo4j driver instance
        companies: List of company dicts with 'name' and 'isin'
    """
    with driver.session() as session:
        # Ensure DAX Index exists
        session.run("""
            MERGE (i:Index {symbol: '^GDAXI'})
            SET i.name = 'DAX',
                i.country = 'Germany',
                i.description = 'German stock market index - 40 major companies',
                i.constituent_count = $count,
                i.updated_at = datetime()
        """, count=len(companies))

        # Import companies
        for company in companies:
            session.run("""
                MERGE (s:Stock {isin: $isin})
                SET s.name = $name,
                    s.country = 'Germany',
                    s.exchange = 'XETRA',
                    s.updated_at = datetime()
                WITH s
                MATCH (i:Index {symbol: '^GDAXI'})
                MERGE (s)-[r:COMPONENT_OF]->(i)
                SET r.updated_at = datetime()
            """,
            name=company['name'],
            isin=company['isin']
            )


def main():
    """Main execution function."""
    print("=" * 70)
    print("  DAX 40 Import to Neo4j")
    print("=" * 70)

    # Parse DAX40 file
    print(f"\n📄 Parsing {DAX40_FILE}...")
    if not os.path.exists(DAX40_FILE):
        print(f"❌ ERROR: File not found: {DAX40_FILE}")
        sys.exit(1)

    companies = parse_dax40_file(DAX40_FILE)
    print(f"✓ Found {len(companies)} companies")

    # Show sample
    print("\n📋 Sample companies:")
    for company in companies[:5]:
        print(f"  • {company['name']:30} | {company['isin']}")

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
    print(f"\n📊 Importing {len(companies)} DAX companies to Neo4j...")
    import_dax40_to_neo4j(driver, companies)
    print("✅ Import complete!")

    # Close connection
    driver.close()

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully imported {len(companies)} DAX 40 companies!")
    print("=" * 70)

    print("\n💡 Verify in Neo4j Browser:")
    print("   MATCH (s:Stock)-[:COMPONENT_OF]->(i:Index {symbol: '^GDAXI'})")
    print("   RETURN i.name, count(s)")
    print()


if __name__ == "__main__":
    main()
