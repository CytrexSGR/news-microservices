#!/usr/bin/env python3
"""
Debug script to test CCXT Bybit symbol formats.

Tests which symbol format works with Bybit V5 API for fetching OHLCV data.
"""

import asyncio
import ccxt.async_support as ccxt
from datetime import datetime, timedelta


async def test_symbol_format(exchange, symbol: str, timeframe: str = "1h") -> dict:
    """
    Test fetching OHLCV data for a specific symbol format.

    Args:
        exchange: CCXT exchange instance
        symbol: Symbol to test (e.g., "BTC/USDT", "BTCUSDT", "BTC/USDT:USDT")
        timeframe: Timeframe for candles (default: 1h)

    Returns:
        dict with keys: symbol, success, candles_count, error
    """
    try:
        # Fetch recent data (last 24 hours)
        since = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)

        ohlcv = await exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=24
        )

        if ohlcv and len(ohlcv) > 0:
            return {
                "symbol": symbol,
                "success": True,
                "candles_count": len(ohlcv),
                "error": None,
                "sample_candle": {
                    "timestamp": datetime.fromtimestamp(ohlcv[0][0] / 1000).isoformat(),
                    "open": ohlcv[0][1],
                    "high": ohlcv[0][2],
                    "low": ohlcv[0][3],
                    "close": ohlcv[0][4],
                    "volume": ohlcv[0][5],
                }
            }
        else:
            return {
                "symbol": symbol,
                "success": False,
                "candles_count": 0,
                "error": "Empty response"
            }

    except Exception as e:
        return {
            "symbol": symbol,
            "success": False,
            "candles_count": 0,
            "error": str(e)
        }


async def main():
    """
    Test multiple symbol formats with Bybit V5 API.
    """
    print("=" * 80)
    print("🔍 Debugging CCXT Bybit Symbol Formats")
    print("=" * 80)
    print()

    # Initialize Bybit exchange
    exchange = ccxt.bybit({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',  # Use perpetual futures (inverse or linear)
        }
    })

    try:
        # Load markets to see available symbols
        print("📋 Loading markets...")
        await exchange.load_markets()
        print(f"✅ Loaded {len(exchange.markets)} markets")
        print()

        # Test different symbol formats
        symbol_formats = [
            "BTC/USDT",      # Standard format
            "BTCUSDT",       # No slash
            "BTC/USDT:USDT", # Futures format (linear perpetual)
            "BTC/USD:BTC",   # Inverse perpetual format
        ]

        print("🧪 Testing Symbol Formats:")
        print("-" * 80)

        results = []
        for symbol in symbol_formats:
            print(f"\n📊 Testing: {symbol}")
            result = await test_symbol_format(exchange, symbol)
            results.append(result)

            if result["success"]:
                print(f"   ✅ SUCCESS - {result['candles_count']} candles")
                print(f"   📈 Sample: {result['sample_candle']}")
            else:
                print(f"   ❌ FAILED - {result['error']}")

        print()
        print("=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if successful:
            print(f"\n✅ Working formats ({len(successful)}):")
            for r in successful:
                print(f"   • {r['symbol']} → {r['candles_count']} candles")

            # Recommendation
            print(f"\n💡 RECOMMENDATION:")
            print(f"   Use format: {successful[0]['symbol']}")
            print(f"   Implement normalization logic to convert user input to this format.")

        if failed:
            print(f"\n❌ Failed formats ({len(failed)}):")
            for r in failed:
                print(f"   • {r['symbol']} → {r['error']}")

        # Check if BTC/USDT:USDT is in markets
        print(f"\n🔍 Market Lookup:")
        for symbol in symbol_formats:
            if symbol in exchange.markets:
                market = exchange.markets[symbol]
                print(f"   • {symbol}: {market['type']} ({market['quote']}/{market['base']})")
            else:
                print(f"   • {symbol}: NOT FOUND in markets")

    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
