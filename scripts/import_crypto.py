#!/usr/bin/env python3
"""
Import cryptocurrencies from markdown file into Neo4j.

Parses crypto.md and creates Crypto nodes in the Knowledge Graph.
Extracts unique crypto assets from trading pairs.
"""

import os
import sys
import re
from neo4j import GraphDatabase
from typing import List, Dict, Set

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password_2024")

# Crypto file path
CRYPTO_FILE = "/tmp/crypto.md"

# Known stablecoins
STABLECOINS = {
    'USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'USDD',
    'USDP', 'GUSD', 'FRAX', 'LUSD', 'SUSD'
}

# Known fiat currencies (to skip)
FIAT_CURRENCIES = {
    'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'TRY',
    'AUD', 'CAD', 'CHF', 'NZD', 'KRW'
}

# Major cryptocurrencies with full names
CRYPTO_NAMES = {
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum',
    'BNB': 'Binance Coin',
    'SOL': 'Solana',
    'XRP': 'Ripple',
    'ADA': 'Cardano',
    'AVAX': 'Avalanche',
    'DOT': 'Polkadot',
    'DOGE': 'Dogecoin',
    'MATIC': 'Polygon',
    'LINK': 'Chainlink',
    'UNI': 'Uniswap',
    'ATOM': 'Cosmos',
    'LTC': 'Litecoin',
    'BCH': 'Bitcoin Cash',
    'ETC': 'Ethereum Classic',
    'FIL': 'Filecoin',
    'AAVE': 'Aave',
    'ALGO': 'Algorand',
    'APT': 'Aptos',
    'ARB': 'Arbitrum',
    'CAKE': 'PancakeSwap',
    'CRV': 'Curve DAO',
    'DYDX': 'dYdX',
    'FET': 'Fetch.ai',
    'GALA': 'Gala',
    'ICP': 'Internet Computer',
    'IMX': 'Immutable X',
    'INJ': 'Injective',
    'LDO': 'Lido DAO',
    'MNT': 'Mantle',
    'NEAR': 'NEAR Protocol',
    'OP': 'Optimism',
    'PEPE': 'Pepe',
    'RUNE': 'THORChain',
    'SAND': 'The Sandbox',
    'SHIB': 'Shiba Inu',
    'STX': 'Stacks',
    'SUI': 'Sui',
    'TIA': 'Celestia',
    'WLD': 'Worldcoin',
    'XLM': 'Stellar',
    'XAUT': 'Tether Gold',
    # Stablecoins
    'USDT': 'Tether',
    'USDC': 'USD Coin',
    'DAI': 'Dai',
}


def parse_crypto_file(filepath: str) -> List[Dict]:
    """
    Parse crypto trading pairs markdown file.

    Format:
        BTC/USDT
        10X
        86,978.7
        ...

    Returns:
        List of dicts with crypto information
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extract all trading pairs
    trading_pairs = re.findall(r'^([A-Z0-9]+)/([A-Z]+)$', content, re.MULTILINE)

    # Extract unique crypto symbols
    crypto_symbols: Set[str] = set()
    for base, quote in trading_pairs:
        # Skip fiat currencies
        if base not in FIAT_CURRENCIES:
            crypto_symbols.add(base)
        if quote not in FIAT_CURRENCIES:
            crypto_symbols.add(quote)

    # Create crypto dict list
    cryptos = []
    for symbol in sorted(crypto_symbols):
        # Determine type
        if symbol in STABLECOINS:
            crypto_type = 'Stablecoin'
        else:
            crypto_type = 'Cryptocurrency'

        # Get full name
        name = CRYPTO_NAMES.get(symbol, symbol)

        cryptos.append({
            'symbol': symbol,
            'name': name,
            'crypto_type': crypto_type
        })

    return cryptos


def import_crypto_to_neo4j(driver, cryptos: List[Dict]):
    """
    Import cryptocurrencies into Neo4j.

    Args:
        driver: Neo4j driver instance
        cryptos: List of crypto dicts
    """
    with driver.session() as session:
        # Create constraints
        try:
            session.run("""
                CREATE CONSTRAINT crypto_symbol_unique IF NOT EXISTS
                FOR (c:Crypto) REQUIRE c.symbol IS UNIQUE
            """)
        except Exception as e:
            print(f"⚠️  Constraint creation warning: {e}")

        # Import cryptos
        for crypto in cryptos:
            session.run("""
                MERGE (c:Crypto {symbol: $symbol})
                SET c.name = $name,
                    c.crypto_type = $crypto_type,
                    c.updated_at = datetime()
            """,
            symbol=crypto['symbol'],
            name=crypto['name'],
            crypto_type=crypto['crypto_type']
            )


def main():
    """Main execution function."""
    print("=" * 70)
    print("  Cryptocurrency Import to Neo4j")
    print("=" * 70)

    # Check if file exists
    if not os.path.exists(CRYPTO_FILE):
        print(f"❌ ERROR: File not found: {CRYPTO_FILE}")
        sys.exit(1)

    # Parse crypto file
    print(f"\n📄 Parsing {CRYPTO_FILE}...")
    cryptos = parse_crypto_file(CRYPTO_FILE)
    print(f"✓ Found {len(cryptos)} unique cryptocurrencies")

    # Count by type
    crypto_count = sum(1 for c in cryptos if c['crypto_type'] == 'Cryptocurrency')
    stablecoin_count = sum(1 for c in cryptos if c['crypto_type'] == 'Stablecoin')
    print(f"  • Cryptocurrencies: {crypto_count}")
    print(f"  • Stablecoins: {stablecoin_count}")

    # Show sample
    if cryptos:
        print("\n📋 Sample cryptocurrencies:")
        for crypto in cryptos[:10]:
            print(f"  • {crypto['symbol']:8} | {crypto['name'][:35]:35} | {crypto['crypto_type']}")

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
    print(f"\n🪙 Importing {len(cryptos)} cryptocurrencies to Neo4j...")
    import_crypto_to_neo4j(driver, cryptos)
    print("✅ Import complete!")

    # Close connection
    driver.close()

    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully imported {len(cryptos)} cryptocurrencies!")
    print(f"   • {crypto_count} cryptocurrencies")
    print(f"   • {stablecoin_count} stablecoins")
    print("=" * 70)

    print("\n💡 Verify in Neo4j Browser:")
    print("   MATCH (c:Crypto)")
    print("   RETURN c.crypto_type, count(c)")
    print()


if __name__ == "__main__":
    main()
