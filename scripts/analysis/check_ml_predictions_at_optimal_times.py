#!/usr/bin/env python3
"""
Check ML Gate Predictions at Optimal Entry Times

For each optimal entry point, check what the ML gates signaled.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np

sys.path.insert(0, '/home/cytrex/news-microservices/services/prediction-service')

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp"

# Optimal entry points from the previous analysis
OPTIMAL_ENTRIES = [
    {"time": "2025-11-24 14:50", "side": "long", "pnl": 8.09},
    {"time": "2025-11-13 14:50", "side": "short", "pnl": 8.02},
    {"time": "2025-11-04 21:35", "side": "long", "pnl": 7.87},
    {"time": "2025-11-20 14:30", "side": "short", "pnl": 7.44},
    {"time": "2025-11-05 01:35", "side": "long", "pnl": 7.33},
    {"time": "2025-11-24 15:25", "side": "long", "pnl": 7.11},
    {"time": "2025-11-21 07:05", "side": "short", "pnl": 6.99},
    {"time": "2025-11-21 12:25", "side": "long", "pnl": 6.64},
    {"time": "2025-11-21 07:30", "side": "long", "pnl": 6.51},
    {"time": "2025-11-07 16:10", "side": "long", "pnl": 6.24},
    {"time": "2025-11-21 16:15", "side": "long", "pnl": 5.96},
    {"time": "2025-11-04 19:00", "side": "short", "pnl": 5.78},
    {"time": "2025-11-03 15:00", "side": "short", "pnl": 5.73},
    {"time": "2025-11-04 23:05", "side": "short", "pnl": 5.72},
    {"time": "2025-11-04 20:40", "side": "short", "pnl": 5.66},
]


async def get_ohlcv_at_time(session: AsyncSession, symbol: str, timestamp: datetime, lookback: int = 100) -> pd.DataFrame:
    """Get OHLCV data up to and including the given timestamp."""
    query = text("""
        SELECT
            timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM market_ohlcv
        WHERE symbol = :symbol
          AND interval = 'FIVE_MINUTE'
          AND timestamp <= :timestamp
        ORDER BY timestamp DESC
        LIMIT :lookback
    """)

    result = await session.execute(query, {
        "symbol": symbol,
        "timestamp": timestamp,
        "lookback": lookback
    })
    rows = result.fetchall()

    df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def calculate_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate technical indicators for the most recent bar."""
    if len(df) < 20:
        return {}

    close = df['close']
    high = df['high']
    low = df['low']

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper_bb = sma20 + 2 * std20
    lower_bb = sma20 - 2 * std20

    # ADX
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - close.shift(1)),
        'lc': abs(low - close.shift(1))
    }).max(axis=1)

    plus_dm = ((high - high.shift(1)).where(
        (high - high.shift(1)) > (low.shift(1) - low), 0
    )).where((high - high.shift(1)) > 0, 0)

    minus_dm = ((low.shift(1) - low).where(
        (low.shift(1) - low) > (high - high.shift(1)), 0
    )).where((low.shift(1) - low) > 0, 0)

    atr = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(14).mean()

    current = df.iloc[-1]
    return {
        'close': float(current['close']),
        'rsi': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
        'bb_upper': float(upper_bb.iloc[-1]) if not pd.isna(upper_bb.iloc[-1]) else None,
        'bb_lower': float(lower_bb.iloc[-1]) if not pd.isna(lower_bb.iloc[-1]) else None,
        'bb_position': float((current['close'] - lower_bb.iloc[-1]) / (upper_bb.iloc[-1] - lower_bb.iloc[-1])) if not pd.isna(upper_bb.iloc[-1]) else None,
        'adx': float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None,
        'plus_di': float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else None,
        'minus_di': float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else None,
    }


async def get_ml_predictions(symbol: str, timestamp: datetime) -> Dict[str, Any]:
    """
    Get ML gate predictions for a specific timestamp.
    This calls the prediction service API.
    """
    import aiohttp

    url = f"http://localhost:8116/api/v1/ml/predict"
    payload = {
        "symbol": symbol,
        "timestamp": timestamp.isoformat(),
        "timeframe": "5min"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
    except Exception as e:
        return {"error": str(e)}


async def main():
    """Main analysis function."""
    print("=" * 100)
    print("ML GATE PREDICTIONS AT OPTIMAL ENTRY TIMES")
    print("=" * 100)
    print()
    print("Checking what the ML gates signaled at the 15 best entry points...")
    print()

    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    results = []

    async with async_session() as session:
        for i, entry in enumerate(OPTIMAL_ENTRIES, 1):
            timestamp = datetime.strptime(entry['time'], "%Y-%m-%d %H:%M")
            optimal_side = entry['side']
            potential_pnl = entry['pnl']

            print(f"\n{'='*80}")
            print(f"#{i} OPTIMAL ENTRY: {entry['time']} -> {optimal_side.upper()} ({potential_pnl:+.2f}%)")
            print(f"{'='*80}")

            # Get OHLCV data
            df = await get_ohlcv_at_time(session, "XRPUSDT", timestamp)
            if len(df) < 20:
                print(f"  ⚠️  Insufficient data at this timestamp")
                continue

            # Calculate indicators
            indicators = calculate_indicators(df)
            print(f"\n  📊 TECHNICAL INDICATORS at {entry['time']}:")
            print(f"     Close:    ${indicators.get('close', 0):.4f}")
            print(f"     RSI:      {indicators.get('rsi', 0):.1f}")
            print(f"     ADX:      {indicators.get('adx', 0):.1f}")
            print(f"     +DI:      {indicators.get('plus_di', 0):.1f}")
            print(f"     -DI:      {indicators.get('minus_di', 0):.1f}")
            print(f"     BB Pos:   {indicators.get('bb_position', 0):.2f} (0=lower, 1=upper)")

            # Technical signal interpretation
            rsi = indicators.get('rsi', 50)
            plus_di = indicators.get('plus_di', 0)
            minus_di = indicators.get('minus_di', 0)
            bb_pos = indicators.get('bb_position', 0.5)

            tech_signal = "neutral"
            if rsi < 30 and plus_di > minus_di:
                tech_signal = "bullish (oversold + positive trend)"
            elif rsi > 70 and minus_di > plus_di:
                tech_signal = "bearish (overbought + negative trend)"
            elif plus_di > minus_di and rsi < 50:
                tech_signal = "bullish (trend up, room to grow)"
            elif minus_di > plus_di and rsi > 50:
                tech_signal = "bearish (trend down, room to fall)"

            print(f"     Tech Signal: {tech_signal}")

            # ML Predictions (via API call)
            print(f"\n  🤖 ML GATE PREDICTIONS:")
            ml_result = await get_ml_predictions("XRPUSDT", timestamp)

            if "error" in ml_result:
                print(f"     Error: {ml_result['error']}")
                print(f"     (ML predictions may not be available for historical timestamps)")
            else:
                for gate, pred in ml_result.items():
                    if isinstance(pred, dict):
                        signal = pred.get('prediction', pred.get('signal', 'N/A'))
                        conf = pred.get('confidence', 0)
                        print(f"     {gate.upper():12s}: {signal:15s} ({conf:.1%})")

            # Compare optimal vs signal
            print(f"\n  📈 COMPARISON:")
            print(f"     Optimal:  {optimal_side.upper()}")
            print(f"     Tech:     {tech_signal}")

            # Would the ML have taken this trade?
            would_take = "UNKNOWN"
            if rsi and plus_di and minus_di:
                if optimal_side == "long":
                    if plus_di > minus_di or rsi < 40:
                        would_take = "MAYBE (tech supports)"
                    else:
                        would_take = "NO (tech against)"
                else:  # short
                    if minus_di > plus_di or rsi > 60:
                        would_take = "MAYBE (tech supports)"
                    else:
                        would_take = "NO (tech against)"

            print(f"     Would Tech agree?: {would_take}")

            results.append({
                'time': entry['time'],
                'optimal_side': optimal_side,
                'potential_pnl': potential_pnl,
                'rsi': rsi,
                'plus_di': plus_di,
                'minus_di': minus_di,
                'bb_pos': bb_pos,
                'tech_signal': tech_signal,
                'would_take': would_take
            })

    # Summary
    print("\n\n")
    print("=" * 100)
    print("SUMMARY: TECHNICAL INDICATORS AT OPTIMAL ENTRY POINTS")
    print("=" * 100)

    df_results = pd.DataFrame(results)

    print("\n📊 Tech Signal Distribution at Optimal Entries:")
    if 'tech_signal' in df_results.columns:
        for signal, count in df_results['tech_signal'].value_counts().items():
            print(f"   {signal}: {count}")

    print("\n📊 Would Tech Have Agreed?:")
    if 'would_take' in df_results.columns:
        for answer, count in df_results['would_take'].value_counts().items():
            print(f"   {answer}: {count}")

    # RSI analysis at optimal longs vs shorts
    longs = df_results[df_results['optimal_side'] == 'long']
    shorts = df_results[df_results['optimal_side'] == 'short']

    print(f"\n📊 RSI at Optimal LONG entries:   avg={longs['rsi'].mean():.1f}, range={longs['rsi'].min():.1f}-{longs['rsi'].max():.1f}")
    print(f"📊 RSI at Optimal SHORT entries:  avg={shorts['rsi'].mean():.1f}, range={shorts['rsi'].min():.1f}-{shorts['rsi'].max():.1f}")

    print(f"\n📊 +DI/-DI at Optimal LONG entries:   +DI avg={longs['plus_di'].mean():.1f}, -DI avg={longs['minus_di'].mean():.1f}")
    print(f"📊 +DI/-DI at Optimal SHORT entries:  +DI avg={shorts['plus_di'].mean():.1f}, -DI avg={shorts['minus_di'].mean():.1f}")

    print(f"\n📊 BB Position at Optimal LONG entries:   avg={longs['bb_pos'].mean():.2f}")
    print(f"📊 BB Position at Optimal SHORT entries:  avg={shorts['bb_pos'].mean():.2f}")


if __name__ == "__main__":
    asyncio.run(main())
