"""
Adapters for external data sources

Transforms external API formats into internal Article event format
for unified processing through content-analysis-v2 pipeline.

Available Adapters:
- FMPNewsAdapter: Financial Modeling Prep (FMP) news adapter
"""
from .fmp_adapter import FMPNewsAdapter

__all__ = ["FMPNewsAdapter"]
