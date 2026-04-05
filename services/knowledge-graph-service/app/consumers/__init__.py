"""
Event consumers for Knowledge-Graph Service.

Consumers:
- MarketDataConsumer: Consumes finance.market.data.updated events
"""

from .market_consumer import MarketDataConsumer

__all__ = ["MarketDataConsumer"]
