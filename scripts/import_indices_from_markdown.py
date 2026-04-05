#!/usr/bin/env python3
"""
Import German indices (DAX, TecDAX, MDAX, SDAX) from markdown files into Neo4j.

Parses markdown files with company names and ISINs, creates Stock nodes
with COMPONENT_OF relationships to respective Index nodes.
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

# Index definitions
INDICES = {
    "dax40.md": {
        "symbol": "^GDAXI",
        "name": "DAX",
        "country": "Germany",
        "description": "German stock market index - 40 major companies",
        "exchange": "XETRA"
    },
    "TecDAX.md": {
        "symbol": "^TECDAX",
        "name": "TecDAX",
        "country": "Germany",
        "description": "German technology stock index - 30 companies",
        "exchange": "XETRA"
    },
    "MDAX.md": {
        "symbol": "^MDAXI",
        "name": "MDAX",
        "country": "Germany",
        "description": "Mid-cap German stock index - 50 companies",
        "exchange": "XETRA"
    },
    "DowJones.md": {
        "symbol": "^DJI",
        "name": "Dow Jones",
        "country": "USA",
        "description": "Dow Jones Industrial Average - 30 major US companies",
        "exchange": "NYSE"
    },
    "S&P500.md": {
        "symbol": "^GSPC",
        "name": "S&P 500",
        "country": "USA",
        "description": "Standard & Poor's 500 Index - 500 largest US companies",
        "exchange": "NYSE"
    },
    "NASDAQ100.md": {
        "symbol": "^NDX",
        "name": "NASDAQ 100",
        "country": "USA",
        "description": "100 largest non-financial companies on NASDAQ",
        "exchange": "NASDAQ"
    },
    "Nikkei225.md": {
        "symbol": "^N225",
        "name": "Nikkei 225",
        "country": "Japan",
        "description": "Japanese stock market index - 225 companies",
        "exchange": "Tokyo Stock Exchange"
    }
}


def parse_markdown_file(filepath: str) -> List[Dict]:
    """
    Parse markdown file and extract company names and ISINs.

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


def import_index_to_neo4j(driver, index_info: Dict, companies: List[Dict]):
    """
    Import an index and its constituent stocks into Neo4j.

    Args:
        driver: Neo4j driver instance
        index_info: Index metadata dict
        companies: List of company dicts with 'name' and 'isin'
    """
    with driver.session() as session:
        # Create or update Index node
        session.run("""
            MERGE (i:Index {symbol: $symbol})
            SET i.name = $name,
                i.country = $country,
                i.description = $description,
                i.constituent_count = $count,
                i.updated_at = datetime()
        """,
        symbol=index_info['symbol'],
        name=index_info['name'],
        country=index_info['country'],
        description=index_info['description'],
        count=len(companies)
        )

        # Import companies
        for company in companies:
            session.run("""
                MERGE (s:Stock {isin: $isin})
                SET s.name = $name,
                    s.country = $country,
                    s.exchange = $exchange,
                    s.updated_at = datetime()
                WITH s
                MATCH (i:Index {symbol: $index_symbol})
                MERGE (s)-[r:COMPONENT_OF]->(i)
                SET r.updated_at = datetime()
            """,
            name=company['name'],
            isin=company['isin'],
            country=index_info.get('country', 'Unknown'),
            exchange=index_info.get('exchange', 'Unknown'),
            index_symbol=index_info['symbol']
            )


def main():
    """Main execution function."""
    print("=" * 70)
    print("  International Stock Indices Import to Neo4j")
    print("=" * 70)

    # Connect to Neo4j
    print(f"\n🔗 Connecting to Neo4j: {NEO4J_URI}...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✓ Connected")
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to Neo4j: {e}")
        sys.exit(1)

    total_companies = 0
    imported_indices = 0

    # Process each index file
    for filename, index_info in INDICES.items():
        filepath = f"/tmp/{filename}"

        print(f"\n{'='*70}")
        print(f"📊 {index_info['name']} ({index_info['symbol']})")
        print(f"{'='*70}")

        # Check if file exists
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath} - Skipping")
            continue

        # Parse file
        print(f"📄 Parsing {filename}...")
        try:
            companies = parse_markdown_file(filepath)
            print(f"✓ Found {len(companies)} companies")

            # Show sample
            if companies:
                print("\n📋 Sample companies:")
                for company in companies[:5]:
                    print(f"  • {company['name']:30} | {company['isin']}")

                # Import to Neo4j
                print(f"\n→ Importing to Neo4j...")
                import_index_to_neo4j(driver, index_info, companies)
                print(f"✅ Imported {len(companies)} stocks")

                total_companies += len(companies)
                imported_indices += 1
            else:
                print("⚠️  No companies found in file")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    # Close connection
    driver.close()

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Import Complete!")
    print(f"   • {imported_indices} indices imported")
    print(f"   • {total_companies} stocks imported")
    print("=" * 70)

    print("\n💡 Verify in Neo4j Browser:")
    print("   MATCH (s:Stock)-[:COMPONENT_OF]->(i:Index)")
    print("   WHERE i.country = 'Germany'")
    print("   RETURN i.name, count(s)")
    print()


if __name__ == "__main__":
    main()
