"""
FMP Integration Services.

This package contains services for integrating Financial Modeling Prep (FMP)
data with the Knowledge Graph (Neo4j).
"""

from .market_sync_service import MarketSyncService

__all__ = ["MarketSyncService"]
