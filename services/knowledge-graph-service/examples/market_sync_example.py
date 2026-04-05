"""
Market Sync Service Usage Example

Demonstrates how to use the Market Sync Service to synchronize
market data from FMP Service to Neo4j Knowledge Graph.
"""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_initial_sync():
    """Example 1: Initial sync of all markets."""
    from app.services.fmp_integration import MarketSyncService

    service = MarketSyncService()

    logger.info("=== Example 1: Initial Sync ===")

    # Step 1: Initialize sectors
    logger.info("Step 1: Initializing sectors...")
    sector_result = await service.sync_sectors()

    logger.info(f"Sectors initialized:")
    logger.info(f"  Total: {sector_result.total_sectors}")
    logger.info(f"  Created: {sector_result.sectors_created}")
    logger.info(f"  Verified: {sector_result.sectors_verified}")
    logger.info(f"  Codes: {', '.join(sector_result.sector_codes)}")

    # Step 2: Sync all 40 default markets
    logger.info("\nStep 2: Syncing all markets...")
    sync_result = await service.sync_all_markets()

    logger.info(f"\nSync complete:")
    logger.info(f"  Sync ID: {sync_result.sync_id}")
    logger.info(f"  Status: {sync_result.status}")
    logger.info(f"  Assets synced: {sync_result.synced}/{sync_result.total_assets}")
    logger.info(f"  Nodes created: {sync_result.nodes_created}")
    logger.info(f"  Nodes updated: {sync_result.nodes_updated}")
    logger.info(f"  Relationships: {sync_result.relationships_created}")
    logger.info(f"  Duration: {sync_result.duration_seconds:.2f}s")
    logger.info(f"  FMP API calls: {sync_result.fmp_api_calls_used}")

    if sync_result.errors:
        logger.warning(f"\nErrors encountered: {len(sync_result.errors)}")
        for error in sync_result.errors:
            logger.warning(f"  - {error.symbol}: {error.error}")

    return sync_result


async def example_2_sync_specific_assets():
    """Example 2: Sync specific symbols."""
    from app.services.fmp_integration import MarketSyncService

    service = MarketSyncService()

    logger.info("\n=== Example 2: Sync Specific Assets ===")

    # Sync only tech stocks
    symbols = ["AAPL", "GOOGL", "MSFT", "META", "NVDA"]

    logger.info(f"Syncing {len(symbols)} tech stocks...")
    result = await service.sync_all_markets(symbols=symbols, force_refresh=True)

    logger.info(f"\nSync complete:")
    logger.info(f"  Synced: {result.synced}/{result.total_assets}")
    logger.info(f"  Status: {result.status}")

    return result


async def example_3_update_quotes():
    """Example 3: Update market quotes (prices)."""
    from app.services.fmp_integration import MarketSyncService

    service = MarketSyncService()

    logger.info("\n=== Example 3: Update Market Quotes ===")

    # Update prices for major indices and stocks
    symbols = [
        "AAPL", "GOOGL", "MSFT",
        "BTCUSD", "ETHUSD",
        "EURUSD", "GBPUSD"
    ]

    logger.info(f"Updating quotes for {len(symbols)} symbols...")
    result = await service.sync_market_quotes(symbols)

    logger.info(f"\nQuote update complete:")
    logger.info(f"  Updated: {result.symbols_updated}")
    logger.info(f"  Failed: {result.symbols_failed}")
    logger.info(f"  Duration: {result.duration_seconds:.2f}s")

    if result.errors:
        logger.warning(f"\nErrors: {len(result.errors)}")
        for error in result.errors:
            logger.warning(f"  - {error.symbol}: {error.error}")

    return result


async def example_4_sync_by_asset_type():
    """Example 4: Sync specific asset types."""
    from app.services.fmp_integration import MarketSyncService

    service = MarketSyncService()

    logger.info("\n=== Example 4: Sync by Asset Type ===")

    # Sync only crypto
    logger.info("Syncing cryptocurrency assets...")
    result = await service.sync_all_markets(asset_types=["CRYPTO"])

    logger.info(f"\nCrypto sync complete:")
    logger.info(f"  Synced: {result.synced} crypto assets")
    logger.info(f"  Duration: {result.duration_seconds:.2f}s")

    return result


async def example_5_error_handling():
    """Example 5: Handle errors gracefully."""
    from app.services.fmp_integration import MarketSyncService
    from app.clients.fmp_service_client import FMPServiceUnavailableError

    service = MarketSyncService()

    logger.info("\n=== Example 5: Error Handling ===")

    # Attempt sync with invalid symbols (to demonstrate error handling)
    symbols = ["AAPL", "INVALID_SYMBOL_XYZ", "GOOGL"]

    try:
        result = await service.sync_all_markets(symbols=symbols)

        logger.info(f"\nSync result:")
        logger.info(f"  Status: {result.status}")
        logger.info(f"  Successful: {result.synced}")
        logger.info(f"  Failed: {result.failed}")

        if result.status == "partial":
            logger.warning("Partial sync - some assets failed")
            for error in result.errors:
                logger.error(f"  - {error.symbol}: {error.error}")

        elif result.status == "failed":
            logger.error("Complete sync failure")

    except FMPServiceUnavailableError as e:
        logger.error(f"FMP Service unavailable: {e}")
        logger.info("Consider implementing retry logic or fallback mechanism")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")


async def example_6_scheduled_updates():
    """Example 6: Scheduled quote updates (simulated)."""
    from app.services.fmp_integration import MarketSyncService

    service = MarketSyncService()

    logger.info("\n=== Example 6: Scheduled Updates ===")
    logger.info("Simulating scheduled price updates (every 15 minutes)")

    # In production: Use APScheduler or Celery Beat
    # This is just a simulation

    update_count = 0
    max_updates = 3

    while update_count < max_updates:
        logger.info(f"\nUpdate #{update_count + 1}")

        # Update prices for top 10 stocks
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
                   "META", "NVDA", "JPM", "V", "WMT"]

        result = await service.sync_market_quotes(symbols)

        logger.info(f"  Updated: {result.symbols_updated} symbols")
        logger.info(f"  Duration: {result.duration_seconds:.2f}s")

        update_count += 1

        # In production: Wait 15 minutes
        # await asyncio.sleep(900)

        # For demo: Wait 2 seconds
        if update_count < max_updates:
            await asyncio.sleep(2)

    logger.info("\nScheduled updates complete")


async def main():
    """Run all examples."""
    logger.info("=" * 60)
    logger.info("Market Sync Service Examples")
    logger.info("=" * 60)

    # Run examples sequentially
    await example_1_initial_sync()
    await example_2_sync_specific_assets()
    await example_3_update_quotes()
    await example_4_sync_by_asset_type()
    await example_5_error_handling()
    await example_6_scheduled_updates()

    logger.info("\n" + "=" * 60)
    logger.info("All examples complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
