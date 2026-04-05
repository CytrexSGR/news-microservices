"""
Verification tools for DIA Verifier.

This module contains all external verification tools that can be executed
to gather evidence for hypothesis validation.

Related: ADR-018 (DIA-Planner & Verifier)
"""

from .perplexity_tool import perplexity_deep_search
from .financial_data_tool import financial_data_lookup

__all__ = [
    "perplexity_deep_search",
    "financial_data_lookup",
]
