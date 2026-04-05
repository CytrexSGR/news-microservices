"""
Example usage of FMP Service HTTP Client.

This script demonstrates how to use the FMPServiceClient to fetch
market data from the FMP Service with built-in resilience patterns.

Run:
    python examples/fmp_client_usage.py
"""

import asyncio
import logging
from datetime import date, timedelta

from app.clients import (
    FMPServiceClient,
    FMPClientConfig,
    FMPServiceUnavailableError,
    FMPRateLimitError,
    CircuitBreakerOpenError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_fetch_metadata():
    """Example: Fetch asset metadata."""
    logger.info("=== Example: Fetch Asset Metadata ===")

    config = FMPClientConfig(
        fmp_base_url="http://localhost:8113",  # Adjust if needed
        fmp_timeout=30
    )

    async with FMPServiceClient(config) as client:
        try:
            # Fetch metadata for specific symbols
            assets = await client.fetch_asset_metadata(
                symbols=["AAPL", "GOOGL", "BTCUSD"]
            )

            for asset in assets:
                logger.info(
                    f"Asset: {asset.symbol} ({asset.name}) - "
                    f"Type: {asset.asset_type}, Sector: {asset.sector}"
                )

        except FMPServiceUnavailableError:
            logger.error("FMP Service is unavailable")
        except FMPRateLimitError:
            logger.error("FMP API rate limit exceeded")


async def example_fetch_quote():
    """Example: Fetch current market quote."""
    logger.info("\n=== Example: Fetch Market Quote ===")

    config = FMPClientConfig(fmp_base_url="http://localhost:8113")

    async with FMPServiceClient(config) as client:
        try:
            quote = await client.fetch_market_quote("AAPL")

            logger.info(
                f"Quote: {quote.symbol} - "
                f"Price: ${quote.price:.2f}, "
                f"Change: {quote.change:+.2f} ({quote.change_percent:+.2f}%), "
                f"Volume: {quote.volume:,}"
            )

        except FMPServiceUnavailableError:
            logger.error("FMP Service is unavailable")


async def example_fetch_history():
    """Example: Fetch historical market data."""
    logger.info("\n=== Example: Fetch Market History ===")

    config = FMPClientConfig(fmp_base_url="http://localhost:8113")

    async with FMPServiceClient(config) as client:
        try:
            # Last 7 days
            end_date = date.today()
            start_date = end_date - timedelta(days=7)

            history = await client.fetch_market_history(
                symbol="AAPL",
                from_date=start_date,
                to_date=end_date
            )

            logger.info(f"Fetched {len(history)} historical records:")
            for record in history[-5:]:  # Show last 5
                logger.info(
                    f"  {record.date}: "
                    f"Close: ${record.close:.2f}, "
                    f"High: ${record.high:.2f}, "
                    f"Low: ${record.low:.2f}"
                )

        except FMPServiceUnavailableError:
            logger.error("FMP Service is unavailable")


async def example_circuit_breaker():
    """Example: Circuit breaker in action."""
    logger.info("\n=== Example: Circuit Breaker ===")

    config = FMPClientConfig(
        fmp_base_url="http://localhost:8113",
        fmp_circuit_breaker_threshold=3,
        fmp_circuit_breaker_timeout=10
    )

    async with FMPServiceClient(config) as client:
        # Check initial circuit breaker state
        stats = client.get_circuit_breaker_stats()
        logger.info(f"Initial state: {stats['state']}")

        try:
            # Try to fetch data
            await client.fetch_market_quote("AAPL")

        except Exception as e:
            logger.warning(f"Request failed: {e}")

        # Check circuit breaker state after failure
        stats = client.get_circuit_breaker_stats()
        logger.info(
            f"After failure: State={stats['state']}, "
            f"Failures={stats['failure_count']}/{stats['failure_threshold']}"
        )


async def example_health_check():
    """Example: Check FMP Service health."""
    logger.info("\n=== Example: Health Check ===")

    config = FMPClientConfig(fmp_base_url="http://localhost:8113")

    async with FMPServiceClient(config) as client:
        is_healthy = await client.health_check()

        if is_healthy:
            logger.info("✅ FMP Service is healthy")
        else:
            logger.warning("❌ FMP Service is down")


async def example_error_handling():
    """Example: Error handling with different exception types."""
    logger.info("\n=== Example: Error Handling ===")

    config = FMPClientConfig(fmp_base_url="http://localhost:8113")

    async with FMPServiceClient(config) as client:
        # 1. Handle circuit breaker open
        try:
            await client.fetch_market_quote("AAPL")
        except CircuitBreakerOpenError as e:
            logger.warning(f"Circuit breaker is open: {e}")
            logger.info(f"Service will retry after {e.recovery_timeout}s")

        # 2. Handle rate limit
        try:
            await client.fetch_market_quote("AAPL")
        except FMPRateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            logger.info("Daily quota exhausted, try again tomorrow")

        # 3. Handle service unavailable
        try:
            await client.fetch_market_quote("AAPL")
        except FMPServiceUnavailableError as e:
            logger.warning(f"Service unavailable: {e}")
            logger.info("FMP Service is down, using fallback")


async def main():
    """Run all examples."""
    logger.info("FMP Service Client - Usage Examples\n")

    # Run examples
    await example_health_check()
    await example_fetch_metadata()
    await example_fetch_quote()
    await example_fetch_history()
    await example_circuit_breaker()
    await example_error_handling()

    logger.info("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
