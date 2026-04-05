# tests/test_symbol_aliases.py
"""Tests for symbol alias resolution."""
import pytest
from app.clients.symbol_aliases import resolve_symbol_alias, COMMODITY_ALIASES


class TestSymbolAliases:
    """Test symbol alias resolution."""

    def test_gold_resolves_to_gcusd(self):
        """GOLD should resolve to GCUSD."""
        assert resolve_symbol_alias("GOLD") == "GCUSD"

    def test_gold_lowercase_resolves(self):
        """gold (lowercase) should also resolve to GCUSD."""
        assert resolve_symbol_alias("gold") == "GCUSD"

    def test_silver_resolves_to_siusd(self):
        """SILVER should resolve to SIUSD."""
        assert resolve_symbol_alias("SILVER") == "SIUSD"

    def test_oil_resolves_to_clusd(self):
        """OIL should resolve to CLUSD."""
        assert resolve_symbol_alias("OIL") == "CLUSD"

    def test_crude_resolves_to_clusd(self):
        """CRUDE should also resolve to CLUSD."""
        assert resolve_symbol_alias("CRUDE") == "CLUSD"

    def test_natgas_resolves_to_ngusd(self):
        """NATGAS should resolve to NGUSD."""
        assert resolve_symbol_alias("NATGAS") == "NGUSD"

    def test_gas_resolves_to_ngusd(self):
        """GAS should also resolve to NGUSD."""
        assert resolve_symbol_alias("GAS") == "NGUSD"

    def test_unknown_symbol_returns_original(self):
        """Unknown symbols should be returned unchanged."""
        assert resolve_symbol_alias("AAPL") == "AAPL"
        assert resolve_symbol_alias("BTCUSD") == "BTCUSD"

    def test_gcusd_returns_gcusd(self):
        """Already-correct FMP symbols should be unchanged."""
        assert resolve_symbol_alias("GCUSD") == "GCUSD"

    def test_commodity_aliases_dict_exists(self):
        """COMMODITY_ALIASES dict should have all commodities."""
        assert "GOLD" in COMMODITY_ALIASES
        assert "SILVER" in COMMODITY_ALIASES
        assert "COPPER" in COMMODITY_ALIASES
        assert "OIL" in COMMODITY_ALIASES
        assert "CRUDE" in COMMODITY_ALIASES
        assert "NATGAS" in COMMODITY_ALIASES
        assert "GAS" in COMMODITY_ALIASES
        assert "PALLADIUM" in COMMODITY_ALIASES
        assert "PLATINUM" in COMMODITY_ALIASES
