"""
Infrastructure module for external integrations.

Contains clients for:
- Neo4j Knowledge Graph (V3GraphClient)
"""

from .graph_client import V3GraphClient

__all__ = ["V3GraphClient"]
