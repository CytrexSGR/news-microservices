#!/usr/bin/env python3
"""
Phase 4.4 Hybrid Data Architecture - Production Monitoring Script

Tracks Bybit worker performance, data quality, and system health over 7-day
observation period. Generates daily reports and alerts on anomalies.

Usage:
    python scripts/monitor_hybrid_data_phase44.py
    python scripts/monitor_hybrid_data_phase44.py --report daily
    python scripts/monitor_hybrid_data_phase44.py --alert

Author: Phase 4.4 Implementation Team
Date: 2025-12-01
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import aiohttp
import asyncpg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
FMP_SERVICE_URL = "http://localhost:8113"
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/predictions"
MONITORING_DATA_DIR = Path("/home/cytrex/news-microservices/monitoring/phase44")
MONITORING_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Expected symbols (16 Bybit-managed)
EXPECTED_SYMBOLS = [
    "BTC/USDT:USDT", "ETH/USDT:USDT", "XRP/USDT:USDT", "BNB/USDT:USDT",
    "SOL/USDT:USDT", "TRX/USDT:USDT", "DOGE/USDT:USDT", "ADA/USDT:USDT",
    "AVAX/USDT:USDT", "LINK/USDT:USDT", "DOT/USDT:USDT", "XLM/USDT:USDT",
    "LTC/USDT:USDT", "TON/USDT:USDT", "HBAR/USDT:USDT", "UNI/USDT:USDT"
]

# Alert thresholds
THRESHOLDS = {
    "max_error_rate": 0.05,          # 5% max error rate
    "min_sync_frequency": 50,         # At least 50 syncs/hour
    "max_stale_seconds": 300,         # Max 5 minutes stale data
    "min_symbols_per_sync": 14,       # At least 14/16 symbols per sync
    "max_missing_oi_rate": 0.10,      # Max 10% missing OI data
    "max_missing_funding_rate": 0.10  # Max 10% missing funding data
}


@dataclass
class MonitoringSnapshot:
    """Single monitoring data point."""
    timestamp: str
    bybit_status: Dict[str, Any]
    database_stats: Dict[str, Any]
    data_quality: Dict[str, Any]
    alerts: List[str]


class HybridDataMonitor:
    """
    Monitor Bybit worker performance and data quality.
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.db_pool: Optional[asyncpg.Pool] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.db_pool = await asyncpg.create_pool(DATABASE_URL)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()

    async def get_bybit_status(self) -> Dict[str, Any]:
        """Fetch Bybit worker status from FMP service."""
        try:
            async with self.session.get(f"{FMP_SERVICE_URL}/api/v1/admin/bybit/status") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Failed to get Bybit status: {resp.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching Bybit status: {e}")
            return {}

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics for analysis_logs."""
        async with self.db_pool.acquire() as conn:
            # Total analyses by source (last 24h)
            last_24h = datetime.utcnow() - timedelta(hours=24)

            source_counts = await conn.fetch("""
                SELECT
                    source,
                    COUNT(*) as count,
                    MIN(timestamp) as first_entry,
                    MAX(timestamp) as last_entry
                FROM analysis_logs
                WHERE timestamp >= $1
                GROUP BY source
                ORDER BY count DESC
            """, last_24h)

            # Symbol coverage (last 24h)
            symbol_coverage = await conn.fetch("""
                SELECT
                    symbol,
                    COUNT(*) as analyses,
                    COUNT(DISTINCT strategy) as strategies
                FROM analysis_logs
                WHERE timestamp >= $1 AND source = 'bybit'
                GROUP BY symbol
                ORDER BY analyses DESC
            """, last_24h)

            # Data quality (last 24h Bybit data)
            data_quality = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN market_data->>'open_interest' IS NOT NULL THEN 1 END) as with_oi,
                    COUNT(CASE WHEN market_data->>'funding_rate' IS NOT NULL THEN 1 END) as with_funding
                FROM analysis_logs
                WHERE timestamp >= $1 AND source = 'bybit'
            """, last_24h)

            return {
                "source_distribution": [
                    {
                        "source": row['source'],
                        "count": row['count'],
                        "first_entry": row['first_entry'].isoformat(),
                        "last_entry": row['last_entry'].isoformat()
                    }
                    for row in source_counts
                ],
                "symbol_coverage": [
                    {
                        "symbol": row['symbol'],
                        "analyses": row['analyses'],
                        "strategies": row['strategies']
                    }
                    for row in symbol_coverage
                ],
                "data_quality_24h": {
                    "total_bybit_analyses": data_quality['total'],
                    "with_open_interest": data_quality['with_oi'],
                    "with_funding_rate": data_quality['with_funding'],
                    "oi_completeness_pct": round((data_quality['with_oi'] / data_quality['total'] * 100), 2) if data_quality['total'] > 0 else 0,
                    "funding_completeness_pct": round((data_quality['with_funding'] / data_quality['total'] * 100), 2) if data_quality['total'] > 0 else 0
                }
            }

    def check_alerts(self, bybit_status: Dict[str, Any], db_stats: Dict[str, Any]) -> List[str]:
        """Check for alert conditions."""
        alerts = []

        # Check if worker is running
        if not bybit_status.get("worker_running"):
            alerts.append("🚨 CRITICAL: Bybit worker is not running!")

        # Check error rate
        if bybit_status.get("syncs_completed", 0) > 0:
            error_rate = bybit_status.get("errors", 0) / bybit_status.get("syncs_completed", 1)
            if error_rate > THRESHOLDS["max_error_rate"]:
                alerts.append(f"⚠️ WARNING: Error rate {error_rate:.2%} exceeds threshold {THRESHOLDS['max_error_rate']:.2%}")

        # Check last sync staleness
        if bybit_status.get("last_sync"):
            last_sync = datetime.fromisoformat(bybit_status["last_sync"].replace("Z", "+00:00"))
            stale_seconds = (datetime.utcnow().replace(tzinfo=last_sync.tzinfo) - last_sync).total_seconds()
            if stale_seconds > THRESHOLDS["max_stale_seconds"]:
                alerts.append(f"⚠️ WARNING: Last sync {stale_seconds:.0f}s ago (threshold: {THRESHOLDS['max_stale_seconds']}s)")

        # Check symbol coverage
        symbol_coverage = db_stats.get("symbol_coverage", [])
        symbols_syncing = len(symbol_coverage)
        if symbols_syncing < len(EXPECTED_SYMBOLS):
            missing = set(EXPECTED_SYMBOLS) - {s["symbol"] for s in symbol_coverage}
            alerts.append(f"⚠️ WARNING: Only {symbols_syncing}/{len(EXPECTED_SYMBOLS)} symbols syncing. Missing: {missing}")

        # Check data quality
        dq = db_stats.get("data_quality_24h", {})
        if dq.get("oi_completeness_pct", 100) < (100 - THRESHOLDS["max_missing_oi_rate"] * 100):
            alerts.append(f"⚠️ WARNING: OI data completeness {dq['oi_completeness_pct']:.1f}% below threshold")
        if dq.get("funding_completeness_pct", 100) < (100 - THRESHOLDS["max_missing_funding_rate"] * 100):
            alerts.append(f"⚠️ WARNING: Funding rate completeness {dq['funding_completeness_pct']:.1f}% below threshold")

        return alerts

    async def take_snapshot(self) -> MonitoringSnapshot:
        """Take a single monitoring snapshot."""
        logger.info("Taking monitoring snapshot...")

        bybit_status = await self.get_bybit_status()
        db_stats = await self.get_database_stats()
        alerts = self.check_alerts(bybit_status, db_stats)

        snapshot = MonitoringSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            bybit_status=bybit_status,
            database_stats=db_stats,
            data_quality=db_stats.get("data_quality_24h", {}),
            alerts=alerts
        )

        # Save snapshot to file
        snapshot_file = MONITORING_DATA_DIR / f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(asdict(snapshot), f, indent=2)

        logger.info(f"Snapshot saved: {snapshot_file}")

        # Log alerts
        if alerts:
            logger.warning(f"Found {len(alerts)} alerts:")
            for alert in alerts:
                logger.warning(f"  {alert}")
        else:
            logger.info("✅ No alerts - system healthy")

        return snapshot

    async def generate_daily_report(self) -> str:
        """Generate daily monitoring report."""
        logger.info("Generating daily report...")

        # Load all snapshots from today
        today = datetime.utcnow().strftime('%Y%m%d')
        today_snapshots = sorted(MONITORING_DATA_DIR.glob(f"snapshot_{today}_*.json"))

        if not today_snapshots:
            return "No snapshots available for today."

        # Load snapshots
        snapshots = []
        for snapshot_file in today_snapshots:
            with open(snapshot_file, 'r') as f:
                snapshots.append(json.load(f))

        # Aggregate statistics
        total_syncs = max([s["bybit_status"].get("syncs_completed", 0) for s in snapshots])
        total_errors = max([s["bybit_status"].get("errors", 0) for s in snapshots])
        avg_error_rate = (total_errors / total_syncs * 100) if total_syncs > 0 else 0

        all_alerts = []
        for s in snapshots:
            all_alerts.extend(s.get("alerts", []))

        unique_alerts = list(set(all_alerts))

        # Generate report
        report = f"""
# Phase 4.4 Hybrid Data Architecture - Daily Monitoring Report
**Date:** {datetime.utcnow().strftime('%Y-%m-%d')}
**Snapshots:** {len(snapshots)}

## Bybit Worker Performance
- **Total Syncs:** {total_syncs}
- **Total Errors:** {total_errors}
- **Error Rate:** {avg_error_rate:.2f}%
- **Uptime:** {snapshots[-1]["bybit_status"].get("uptime_hours", 0):.2f} hours

## Data Quality (Last 24h)
- **Total Bybit Analyses:** {snapshots[-1]["data_quality"].get("total_bybit_analyses", 0):,}
- **OI Completeness:** {snapshots[-1]["data_quality"].get("oi_completeness_pct", 0):.1f}%
- **Funding Completeness:** {snapshots[-1]["data_quality"].get("funding_completeness_pct", 0):.1f}%

## Symbol Coverage
{chr(10).join([f"- **{s['symbol']}:** {s['analyses']} analyses, {s['strategies']} strategies" for s in snapshots[-1]["database_stats"]["symbol_coverage"][:5]])}
... (showing top 5 symbols)

## Alerts ({len(unique_alerts)})
"""
        if unique_alerts:
            for alert in unique_alerts:
                report += f"- {alert}\n"
        else:
            report += "✅ No alerts - system healthy\n"

        report += "\n---\n"
        report += f"*Report generated: {datetime.utcnow().isoformat()}*\n"

        # Save report
        report_file = MONITORING_DATA_DIR / f"daily_report_{today}.md"
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Daily report saved: {report_file}")

        return report


async def main():
    """Main monitoring entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 4.4 Hybrid Data Architecture Monitoring")
    parser.add_argument("--report", choices=["daily"], help="Generate report")
    parser.add_argument("--alert", action="store_true", help="Check alerts only")
    parser.add_argument("--continuous", action="store_true", help="Continuous monitoring (every 5 minutes)")
    args = parser.parse_args()

    async with HybridDataMonitor() as monitor:
        if args.report == "daily":
            report = await monitor.generate_daily_report()
            print(report)
        elif args.alert:
            snapshot = await monitor.take_snapshot()
            if snapshot.alerts:
                print(f"⚠️ Found {len(snapshot.alerts)} alerts:")
                for alert in snapshot.alerts:
                    print(f"  {alert}")
                sys.exit(1)  # Exit with error code if alerts found
            else:
                print("✅ No alerts - system healthy")
                sys.exit(0)
        elif args.continuous:
            logger.info("Starting continuous monitoring (5-minute intervals)")
            while True:
                await monitor.take_snapshot()
                await asyncio.sleep(300)  # 5 minutes
        else:
            # Single snapshot
            await monitor.take_snapshot()


if __name__ == "__main__":
    asyncio.run(main())
