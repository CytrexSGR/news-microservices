#!/usr/bin/env python3
"""
Backfill Bybit OHLCV Data for Trading Strategies

Fetches historical OHLCV data from Bybit and inserts into market_ohlcv table.
Uses the existing BybitFetcher from fmp-service.

Usage:
    docker exec news-fmp-service python /app/scripts/backfill_bybit_ohlcv.py

Or run directly (if dependencies are installed):
    python scripts/backfill_bybit_ohlcv.py --symbols BTCUSDT,ETHUSDT --days 60 --interval 1h
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Optional

# Add parent directory to path for imports when running from scripts folder
sys.path.insert(0, '/home/cytrex/news-microservices/services/fmp-service')

try:
    import ccxt.async_support as ccxt
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run this script inside the fmp-service container:")
    print("  docker exec -it news-fmp-service python /app/scripts/backfill_bybit_ohlcv.py")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration - use environment variables or defaults
import os
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://news_user:+t1koDEJO+ruZ3QnYlkVeU2u6Z+zCJtL6wFW+wfN5Yk=@postgres:5432/news_mcp"
)

# Interval mapping: input -> (db_interval, ccxt_timeframe)
INTERVAL_MAP = {
    "1m": ("ONE_MINUTE", "1m"),
    "5m": ("FIVE_MINUTE", "5m"),
    "15m": ("FIFTEEN_MINUTE", "15m"),
    "30m": ("THIRTY_MINUTE", "30m"),
    "1h": ("ONE_HOUR", "1h"),
    "4h": ("FOUR_HOUR", "4h"),
    "1d": ("ONE_DAY", "1d"),
}


async def fetch_bybit_ohlcv(
    symbol: str,
    timeframe: str,
    start_date: datetime,
    end_date: datetime
) -> List[dict]:
    """Fetch OHLCV data from Bybit using CCXT."""

    # Convert symbol to Bybit format
    base = symbol.replace("USDT", "").replace("USD", "")
    bybit_symbol = f"{base}/USDT:USDT"

    logger.info(f"Fetching {bybit_symbol} {timeframe} from {start_date} to {end_date}")

    exchange = ccxt.bybit({
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })

    candles = []
    current_start = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)

    # Timeframe to milliseconds
    tf_ms = {
        "1m": 60000, "5m": 300000, "15m": 900000,
        "30m": 1800000, "1h": 3600000, "4h": 14400000, "1d": 86400000
    }

    try:
        while current_start < end_ms:
            try:
                raw = await exchange.fetch_ohlcv(
                    symbol=bybit_symbol,
                    timeframe=timeframe,
                    since=current_start,
                    limit=1000
                )

                if not raw:
                    break

                for c in raw:
                    ts = datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc)
                    if ts > end_date.replace(tzinfo=timezone.utc):
                        break
                    candles.append({
                        "timestamp": ts,
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": int(c[5])
                    })

                current_start = raw[-1][0] + tf_ms[timeframe]
                logger.info(f"  Fetched {len(candles)} candles so far...")
                await asyncio.sleep(0.2)  # Rate limiting

            except ccxt.RateLimitExceeded:
                logger.warning("Rate limit hit, waiting 5 seconds...")
                await asyncio.sleep(5)
                continue

    finally:
        await exchange.close()

    # Remove duplicates
    seen = set()
    unique = []
    for c in candles:
        if c["timestamp"] not in seen:
            seen.add(c["timestamp"])
            unique.append(c)

    logger.info(f"Fetched {len(unique)} unique candles for {symbol}")
    return unique


async def insert_candles(
    session: AsyncSession,
    symbol: str,
    interval: str,
    candles: List[dict]
) -> int:
    """Insert candles into market_ohlcv table."""

    if not candles:
        return 0

    inserted = 0
    batch_size = 100

    for i in range(0, len(candles), batch_size):
        batch = candles[i:i + batch_size]

        for c in batch:
            # Use ON CONFLICT to handle duplicates
            query = text("""
                INSERT INTO market_ohlcv (
                    id, symbol, asset_type, interval, timestamp,
                    open, high, low, close, volume, source
                ) VALUES (
                    gen_random_uuid(), :symbol, 'crypto', :interval, :timestamp,
                    :open, :high, :low, :close, :volume, 'bybit'
                )
                ON CONFLICT (symbol, interval, timestamp) DO NOTHING
            """)

            try:
                result = await session.execute(query, {
                    "symbol": symbol,
                    "interval": interval,
                    "timestamp": c["timestamp"],
                    "open": c["open"],
                    "high": c["high"],
                    "low": c["low"],
                    "close": c["close"],
                    "volume": c["volume"]
                })
                if result.rowcount > 0:
                    inserted += 1
            except Exception as e:
                logger.error(f"Error inserting candle: {e}")
                continue

        await session.commit()
        logger.info(f"  Inserted batch {i // batch_size + 1}, total inserted: {inserted}")

    return inserted


async def backfill_symbol(
    symbol: str,
    interval: str,
    days_back: int
) -> dict:
    """Backfill a single symbol with historical data."""

    if interval not in INTERVAL_MAP:
        raise ValueError(f"Invalid interval: {interval}. Supported: {list(INTERVAL_MAP.keys())}")

    db_interval, ccxt_tf = INTERVAL_MAP[interval]

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)

    logger.info(f"=== Backfilling {symbol} {interval} for {days_back} days ===")

    # Fetch from Bybit
    candles = await fetch_bybit_ohlcv(symbol, ccxt_tf, start_date, end_date)

    if not candles:
        logger.warning(f"No candles fetched for {symbol}")
        return {"symbol": symbol, "fetched": 0, "inserted": 0}

    # Insert into database
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        inserted = await insert_candles(session, symbol, db_interval, candles)

    await engine.dispose()

    logger.info(f"=== {symbol}: Fetched {len(candles)}, Inserted {inserted} new candles ===")
    return {"symbol": symbol, "fetched": len(candles), "inserted": inserted}


async def main():
    parser = argparse.ArgumentParser(description="Backfill Bybit OHLCV data")
    parser.add_argument(
        "--symbols",
        type=str,
        default="BTCUSDT,ETHUSDT,XRPUSDT",
        help="Comma-separated list of symbols (default: BTCUSDT,ETHUSDT,XRPUSDT)"
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1h",
        help="Candle interval (1m, 5m, 15m, 30m, 1h, 4h, 1d) (default: 1h)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=60,
        help="Days of history to fetch (default: 60)"
    )

    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",")]

    logger.info(f"Starting backfill: {symbols}, interval={args.interval}, days={args.days}")

    results = []
    for symbol in symbols:
        try:
            result = await backfill_symbol(symbol, args.interval, args.days)
            results.append(result)
        except Exception as e:
            logger.error(f"Error backfilling {symbol}: {e}")
            results.append({"symbol": symbol, "fetched": 0, "inserted": 0, "error": str(e)})

    # Summary
    logger.info("\n=== BACKFILL SUMMARY ===")
    total_fetched = 0
    total_inserted = 0
    for r in results:
        status = "ERROR" if "error" in r else "OK"
        logger.info(f"  {r['symbol']}: {r['fetched']} fetched, {r['inserted']} inserted [{status}]")
        total_fetched += r.get("fetched", 0)
        total_inserted += r.get("inserted", 0)
    logger.info(f"TOTAL: {total_fetched} fetched, {total_inserted} inserted")


if __name__ == "__main__":
    asyncio.run(main())
