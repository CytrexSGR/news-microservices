"""
Enumerations for Knowledge Graph Service.

Defines all enum types used across the service for consistent
type safety and validation.
"""

from enum import Enum


class AssetType(str, Enum):
    """
    Asset classification types.

    Determines how market data is processed and which
    providers are used for price feeds.
    """
    STOCK = "STOCK"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"
    CRYPTO = "CRYPTO"


class MarketSector(str, Enum):
    """
    Market sectors based on Global Industry Classification Standard (GICS).

    11 sectors as defined by MSCI and S&P Dow Jones Indices.
    Used for sector-based analysis and correlation studies.
    """
    COMMUNICATION_SERVICES = "Communication Services"
    CONSUMER_DISCRETIONARY = "Consumer Discretionary"
    CONSUMER_STAPLES = "Consumer Staples"
    ENERGY = "Energy"
    FINANCIALS = "Financials"
    HEALTH_CARE = "Health Care"
    INDUSTRIALS = "Industrials"
    INFORMATION_TECHNOLOGY = "Information Technology"
    MATERIALS = "Materials"
    REAL_ESTATE = "Real Estate"
    UTILITIES = "Utilities"


class ExchangeType(str, Enum):
    """
    Major stock exchanges.

    Used for determining trading hours and regulatory context.
    """
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    LSE = "LSE"  # London Stock Exchange
    TSE = "TSE"  # Tokyo Stock Exchange
    HKEX = "HKEX"  # Hong Kong Exchange
    SSE = "SSE"  # Shanghai Stock Exchange
    EURONEXT = "EURONEXT"
    TSX = "TSX"  # Toronto Stock Exchange
    ASX = "ASX"  # Australian Securities Exchange
    OTHER = "OTHER"


class RelationshipType(str, Enum):
    """
    Neo4j relationship types for knowledge graph.

    Defines all possible relationships between nodes.
    """
    # Market relationships
    BELONGS_TO_SECTOR = "BELONGS_TO_SECTOR"
    TRADED_ON = "TRADED_ON"

    # Organization relationships
    MENTIONED_IN = "MENTIONED_IN"
    HEADQUARTERED_IN = "HEADQUARTERED_IN"
    OPERATES_IN = "OPERATES_IN"
    SUBSIDIARY_OF = "SUBSIDIARY_OF"
    PARTNER_WITH = "PARTNER_WITH"

    # Article relationships
    PUBLISHED_BY = "PUBLISHED_BY"
    ABOUT_MARKET = "ABOUT_MARKET"
    ABOUT_ORGANIZATION = "ABOUT_ORGANIZATION"
    ABOUT_LOCATION = "ABOUT_LOCATION"
    ABOUT_PERSON = "ABOUT_PERSON"
    HAS_RESEARCH = "HAS_RESEARCH"  # Links original article to Perplexity research

    # Event relationships
    CAUSED_BY = "CAUSED_BY"
    IMPACTS = "IMPACTS"
    RELATED_TO = "RELATED_TO"


class SentimentLabel(str, Enum):
    """
    Sentiment classification for articles and analysis.
    """
    VERY_NEGATIVE = "VERY_NEGATIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    POSITIVE = "POSITIVE"
    VERY_POSITIVE = "VERY_POSITIVE"


class MarketClassification(str, Enum):
    """
    Market classification systems.
    """
    GICS = "GICS"  # Global Industry Classification Standard
    ICB = "ICB"    # Industry Classification Benchmark
    NAICS = "NAICS"  # North American Industry Classification System
    SIC = "SIC"    # Standard Industrial Classification
