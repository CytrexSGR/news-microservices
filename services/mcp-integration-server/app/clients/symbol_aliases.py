"""
Symbol Alias Resolution for MCP Tools.

Maps human-readable commodity names to FMP futures symbols.
Example: GOLD -> GCUSD, OIL -> CLUSD

This layer is specific to MCP integration and does not affect
the underlying fmp-service, which uses actual FMP symbols.
"""

from typing import Dict

# Commodity aliases: Human-readable name -> FMP symbol
COMMODITY_ALIASES: Dict[str, str] = {
    # Precious Metals
    "GOLD": "GCUSD",
    "SILVER": "SIUSD",
    "PALLADIUM": "PAUSD",
    "PLATINUM": "PLUSD",

    # Base Metals
    "COPPER": "HGUSD",

    # Energy
    "OIL": "CLUSD",
    "CRUDE": "CLUSD",
    "CRUDEOIL": "CLUSD",
    "WTI": "CLUSD",
    "NATGAS": "NGUSD",
    "GAS": "NGUSD",
    "NATURALGAS": "NGUSD",

    # Agricultural (if available in FMP)
    # "CORN": "ZCUSX",  # Uncomment when FMP has these
    # "WHEAT": "ZWUSX",
    # "SOYBEAN": "ZSUSX",
}


def resolve_symbol_alias(symbol: str) -> str:
    """
    Resolve human-readable symbol alias to FMP symbol.

    Args:
        symbol: Input symbol (e.g., "GOLD", "gold", "GCUSD")

    Returns:
        FMP symbol (e.g., "GCUSD") or original if no alias found

    Examples:
        >>> resolve_symbol_alias("GOLD")
        'GCUSD'
        >>> resolve_symbol_alias("AAPL")
        'AAPL'
    """
    # Normalize to uppercase for lookup
    normalized = symbol.upper().strip()

    # Return alias if found, otherwise return original symbol
    return COMMODITY_ALIASES.get(normalized, symbol)
