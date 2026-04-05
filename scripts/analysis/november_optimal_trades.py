#!/usr/bin/env python3
"""
November 2025 Optimal Trades Analysis

Reverse analysis: What would have been the optimal trades?
Then compare with ML gate predictions at those times.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Add service path
sys.path.insert(0, '/home/cytrex/news-microservices/services/prediction-service')

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp"


async def get_ohlcv_data(session: AsyncSession, symbol: str, start_date: str, end_date: str, interval: str = 'FIVE_MINUTE') -> pd.DataFrame:
    """Fetch OHLCV data from database."""
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
          AND interval = :interval
          AND timestamp >= :start_date
          AND timestamp <= :end_date
        ORDER BY timestamp
    """)

    result = await session.execute(query, {
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date
    })
    rows = result.fetchall()

    df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def find_swing_points(df: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """
    Find swing highs and lows.
    A swing high is a high that is higher than `lookback` bars on each side.
    """
    df = df.copy()
    df['swing_high'] = False
    df['swing_low'] = False

    for i in range(lookback, len(df) - lookback):
        # Check swing high
        high = df['high'].iloc[i]
        is_swing_high = all(high >= df['high'].iloc[i-j] for j in range(1, lookback+1)) and \
                       all(high >= df['high'].iloc[i+j] for j in range(1, lookback+1))

        # Check swing low
        low = df['low'].iloc[i]
        is_swing_low = all(low <= df['low'].iloc[i-j] for j in range(1, lookback+1)) and \
                      all(low <= df['low'].iloc[i+j] for j in range(1, lookback+1))

        df.iloc[i, df.columns.get_loc('swing_high')] = is_swing_high
        df.iloc[i, df.columns.get_loc('swing_low')] = is_swing_low

    return df


def identify_optimal_trades(df: pd.DataFrame, min_move_pct: float = 1.0) -> List[Dict[str, Any]]:
    """
    Identify optimal trades based on swing points.

    Logic:
    - Buy at swing low, sell at next swing high (LONG)
    - Sell at swing high, cover at next swing low (SHORT)
    - Filter for minimum percentage move
    """
    df = find_swing_points(df, lookback=5)

    # Get swing points
    swing_highs = df[df['swing_high']].copy()
    swing_lows = df[df['swing_low']].copy()

    # Combine and sort
    swing_highs['type'] = 'high'
    swing_highs['price'] = swing_highs['high']
    swing_lows['type'] = 'low'
    swing_lows['price'] = swing_lows['low']

    all_swings = pd.concat([
        swing_highs[['type', 'price']],
        swing_lows[['type', 'price']]
    ]).sort_index()

    trades = []

    # Find trades from swing low to swing high (LONG)
    for i, (ts, row) in enumerate(all_swings.iterrows()):
        if row['type'] == 'low':
            # Look for next swing high
            future_swings = all_swings.loc[ts:].iloc[1:]
            for fut_ts, fut_row in future_swings.iterrows():
                if fut_row['type'] == 'high':
                    pnl_pct = ((fut_row['price'] - row['price']) / row['price']) * 100
                    if pnl_pct >= min_move_pct:
                        trades.append({
                            'entry_time': ts,
                            'exit_time': fut_ts,
                            'side': 'long',
                            'entry_price': row['price'],
                            'exit_price': fut_row['price'],
                            'pnl_pct': pnl_pct,
                            'duration_hours': (fut_ts - ts).total_seconds() / 3600
                        })
                    break

        elif row['type'] == 'high':
            # Look for next swing low (SHORT)
            future_swings = all_swings.loc[ts:].iloc[1:]
            for fut_ts, fut_row in future_swings.iterrows():
                if fut_row['type'] == 'low':
                    pnl_pct = ((row['price'] - fut_row['price']) / row['price']) * 100
                    if pnl_pct >= min_move_pct:
                        trades.append({
                            'entry_time': ts,
                            'exit_time': fut_ts,
                            'side': 'short',
                            'entry_price': row['price'],
                            'exit_price': fut_row['price'],
                            'pnl_pct': pnl_pct,
                            'duration_hours': (fut_ts - ts).total_seconds() / 3600
                        })
                    break

    # Sort by P&L
    trades.sort(key=lambda x: x['pnl_pct'], reverse=True)

    return trades


def find_major_moves(df: pd.DataFrame, window_hours: int = 24, min_move_pct: float = 3.0) -> List[Dict[str, Any]]:
    """
    Find major price moves by looking at rolling windows.
    """
    window_bars = window_hours * 12  # 5min bars

    moves = []

    for i in range(len(df) - window_bars):
        window = df.iloc[i:i+window_bars]

        # Find high and low in window
        high_idx = window['high'].idxmax()
        low_idx = window['low'].idxmin()
        high_price = window.loc[high_idx, 'high']
        low_price = window.loc[low_idx, 'low']

        # Calculate move
        if high_idx > low_idx:
            # Upward move
            move_pct = ((high_price - low_price) / low_price) * 100
            if move_pct >= min_move_pct:
                moves.append({
                    'start_time': low_idx,
                    'end_time': high_idx,
                    'direction': 'up',
                    'start_price': low_price,
                    'end_price': high_price,
                    'move_pct': move_pct,
                    'duration_hours': (high_idx - low_idx).total_seconds() / 3600
                })
        else:
            # Downward move
            move_pct = ((high_price - low_price) / high_price) * 100
            if move_pct >= min_move_pct:
                moves.append({
                    'start_time': high_idx,
                    'end_time': low_idx,
                    'direction': 'down',
                    'start_price': high_price,
                    'end_price': low_price,
                    'move_pct': move_pct,
                    'duration_hours': (low_idx - high_idx).total_seconds() / 3600
                })

    # Deduplicate overlapping moves
    moves.sort(key=lambda x: x['move_pct'], reverse=True)
    filtered = []
    for move in moves:
        overlaps = False
        for existing in filtered:
            # Check if start times are within 12 hours of each other
            if abs((move['start_time'] - existing['start_time']).total_seconds()) < 12 * 3600:
                overlaps = True
                break
        if not overlaps:
            filtered.append(move)

    return filtered[:20]  # Top 20 moves


async def get_price_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate basic price statistics for the period."""
    return {
        'start_price': float(df['close'].iloc[0]),
        'end_price': float(df['close'].iloc[-1]),
        'high': float(df['high'].max()),
        'low': float(df['low'].min()),
        'range_pct': float((df['high'].max() - df['low'].min()) / df['low'].min() * 100),
        'total_return_pct': float((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100),
        'volatility': float(df['close'].pct_change().std() * np.sqrt(288) * 100),  # Daily volatility
        'avg_daily_range': float((df['high'] - df['low']).mean() / df['close'].mean() * 100)
    }


async def main():
    """Main analysis function."""
    print("=" * 80)
    print("NOVEMBER 2025 OPTIMAL TRADES ANALYSIS")
    print("=" * 80)
    print()

    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Fetch November data
        print("Loading XRPUSDT 5min data for November 2025...")
        df = await get_ohlcv_data(
            session,
            "XRPUSDT",
            datetime(2025, 11, 1, 0, 0, 0),
            datetime(2025, 11, 30, 23, 59, 59)
        )
        print(f"Loaded {len(df)} candles ({len(df)/288:.1f} days)")
        print()

        # Price statistics
        stats = await get_price_stats(df)
        print("=" * 60)
        print("PRICE STATISTICS - November 2025")
        print("=" * 60)
        print(f"Start Price:     ${stats['start_price']:.4f}")
        print(f"End Price:       ${stats['end_price']:.4f}")
        print(f"High:            ${stats['high']:.4f}")
        print(f"Low:             ${stats['low']:.4f}")
        print(f"Range:           {stats['range_pct']:.2f}%")
        print(f"Buy & Hold:      {stats['total_return_pct']:+.2f}%")
        print(f"Daily Volatility: {stats['volatility']:.2f}%")
        print(f"Avg Daily Range: {stats['avg_daily_range']:.2f}%")
        print()

        # Find major moves
        print("=" * 60)
        print("TOP 10 MAJOR PRICE MOVES (>3% within 24h)")
        print("=" * 60)
        major_moves = find_major_moves(df, window_hours=24, min_move_pct=3.0)

        for i, move in enumerate(major_moves[:10], 1):
            direction_emoji = "📈" if move['direction'] == 'up' else "📉"
            print(f"\n{i}. {direction_emoji} {move['direction'].upper()} Move: {move['move_pct']:+.2f}%")
            print(f"   From: {move['start_time']} @ ${move['start_price']:.4f}")
            print(f"   To:   {move['end_time']} @ ${move['end_price']:.4f}")
            print(f"   Duration: {move['duration_hours']:.1f} hours")

        # Find optimal swing trades
        print("\n")
        print("=" * 60)
        print("TOP 15 OPTIMAL SWING TRADES (>1% move)")
        print("=" * 60)
        optimal_trades = identify_optimal_trades(df, min_move_pct=1.0)

        total_potential_pnl = 0
        for i, trade in enumerate(optimal_trades[:15], 1):
            side_emoji = "🟢" if trade['side'] == 'long' else "🔴"
            print(f"\n{i}. {side_emoji} {trade['side'].upper()}: {trade['pnl_pct']:+.2f}%")
            print(f"   Entry: {trade['entry_time']} @ ${trade['entry_price']:.4f}")
            print(f"   Exit:  {trade['exit_time']} @ ${trade['exit_price']:.4f}")
            print(f"   Duration: {trade['duration_hours']:.1f} hours")
            total_potential_pnl += trade['pnl_pct']

        print("\n" + "=" * 60)
        print(f"TOTAL POTENTIAL (Top 15): {total_potential_pnl:.2f}%")
        print("=" * 60)

        # Summary for ML comparison
        print("\n")
        print("=" * 60)
        print("ENTRY POINTS FOR ML GATE ANALYSIS")
        print("=" * 60)
        print("\nThese are the timestamps where optimal entries occurred:")
        print("(Use these to check what the ML gates signaled)")
        print()

        for i, trade in enumerate(optimal_trades[:10], 1):
            print(f"{i}. {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} -> {trade['side'].upper()} entry")

        # Export data for further analysis
        export_data = {
            'stats': stats,
            'major_moves': major_moves[:10],
            'optimal_trades': optimal_trades[:15]
        }

        return export_data


if __name__ == "__main__":
    result = asyncio.run(main())
