"""
Neo4j Cypher query templates for Knowledge Graph operations.

Provides ready-to-use parameterized queries for:
- Market operations (CRUD, search, stats)
- Sector operations
- Relationship management
- Graph traversals
"""

from typing import Dict, Any


class MarketQueries:
    """
    Cypher query templates for MARKET node operations.
    """

    MERGE_MARKET = """
    MERGE (m:MARKET {symbol: $symbol})
    ON CREATE SET
        m.name = $name,
        m.asset_type = $asset_type,
        m.currency = $currency,
        m.is_active = $is_active,
        m.created_at = datetime(),
        m.last_updated = datetime()
    ON MATCH SET
        m.name = $name,
        m.asset_type = $asset_type,
        m.currency = $currency,
        m.is_active = $is_active,
        m.last_updated = datetime()
    WITH m
    // Set optional fields if provided
    FOREACH (ignoreMe IN CASE WHEN $exchange IS NOT NULL THEN [1] ELSE [] END |
        SET m.exchange = $exchange
    )
    FOREACH (ignoreMe IN CASE WHEN $sector IS NOT NULL THEN [1] ELSE [] END |
        SET m.sector = $sector
    )
    FOREACH (ignoreMe IN CASE WHEN $isin IS NOT NULL THEN [1] ELSE [] END |
        SET m.isin = $isin
    )
    FOREACH (ignoreMe IN CASE WHEN $description IS NOT NULL THEN [1] ELSE [] END |
        SET m.description = $description
    )
    RETURN m
    """

    MERGE_MARKET_WITH_SECTOR = """
    MERGE (m:MARKET {symbol: $symbol})
    ON CREATE SET
        m.name = $name,
        m.asset_type = $asset_type,
        m.currency = $currency,
        m.is_active = $is_active,
        m.sector = $sector_code,
        m.created_at = datetime(),
        m.last_updated = datetime()
    ON MATCH SET
        m.name = $name,
        m.asset_type = $asset_type,
        m.currency = $currency,
        m.is_active = $is_active,
        m.sector = $sector_code,
        m.last_updated = datetime()
    WITH m
    MERGE (s:SECTOR {code: $sector_code})
    ON CREATE SET
        s.name = $sector_name,
        s.market_classification = COALESCE($market_classification, 'GICS')
    MERGE (m)-[:BELONGS_TO_SECTOR]->(s)
    RETURN m, s
    """

    UPDATE_MARKET_PRICE = """
    MATCH (m:MARKET {symbol: $symbol})
    SET
        m.last_updated = datetime()
    WITH m
    // Update price fields if provided
    FOREACH (ignoreMe IN CASE WHEN $current_price IS NOT NULL THEN [1] ELSE [] END |
        SET m.current_price = $current_price
    )
    FOREACH (ignoreMe IN CASE WHEN $day_change_percent IS NOT NULL THEN [1] ELSE [] END |
        SET m.day_change_percent = $day_change_percent
    )
    FOREACH (ignoreMe IN CASE WHEN $market_cap IS NOT NULL THEN [1] ELSE [] END |
        SET m.market_cap = $market_cap
    )
    FOREACH (ignoreMe IN CASE WHEN $volume IS NOT NULL THEN [1] ELSE [] END |
        SET m.volume = $volume
    )
    FOREACH (ignoreMe IN CASE WHEN $open_price IS NOT NULL THEN [1] ELSE [] END |
        SET m.open_price = $open_price
    )
    FOREACH (ignoreMe IN CASE WHEN $high_price IS NOT NULL THEN [1] ELSE [] END |
        SET m.high_price = $high_price
    )
    FOREACH (ignoreMe IN CASE WHEN $low_price IS NOT NULL THEN [1] ELSE [] END |
        SET m.low_price = $low_price
    )
    FOREACH (ignoreMe IN CASE WHEN $close_price IS NOT NULL THEN [1] ELSE [] END |
        SET m.close_price = $close_price
    )
    RETURN m
    """

    GET_MARKET_BY_SYMBOL = """
    MATCH (m:MARKET {symbol: $symbol})
    RETURN m
    """

    GET_MARKET_WITH_RELATIONSHIPS = """
    MATCH (m:MARKET {symbol: $symbol})
    OPTIONAL MATCH (m)-[:BELONGS_TO_SECTOR]->(s:SECTOR)
    OPTIONAL MATCH (m)<-[:ABOUT_MARKET]-(o:ORGANIZATION)
    RETURN m,
           s,
           COLLECT(DISTINCT o.name) as organizations
    """

    LIST_MARKETS = """
    MATCH (m:MARKET)
    WHERE 1=1
        AND ($asset_types IS NULL OR m.asset_type IN $asset_types)
        AND ($is_active IS NULL OR m.is_active = $is_active)
        AND ($symbol_contains IS NULL OR toLower(m.symbol) CONTAINS toLower($symbol_contains))
        AND ($name_contains IS NULL OR toLower(m.name) CONTAINS toLower($name_contains))
    WITH m
    ORDER BY m.symbol
    SKIP $skip
    LIMIT $limit
    RETURN m
    """

    COUNT_MARKETS = """
    MATCH (m:MARKET)
    WHERE 1=1
        AND ($asset_types IS NULL OR m.asset_type IN $asset_types)
        AND ($is_active IS NULL OR m.is_active = $is_active)
        AND ($symbol_contains IS NULL OR toLower(m.symbol) CONTAINS toLower($symbol_contains))
        AND ($name_contains IS NULL OR toLower(m.name) CONTAINS toLower($name_contains))
    RETURN COUNT(m) as total
    """

    SEARCH_MARKETS_BY_SECTOR = """
    MATCH (m:MARKET)-[:BELONGS_TO_SECTOR]->(s:SECTOR)
    WHERE s.code IN $sector_codes
        AND ($is_active IS NULL OR m.is_active = $is_active)
    RETURN m, s
    ORDER BY m.market_cap DESC
    SKIP $skip
    LIMIT $limit
    """

    GET_MARKETS_BY_MARKET_CAP = """
    MATCH (m:MARKET)
    WHERE m.market_cap IS NOT NULL
        AND ($min_market_cap IS NULL OR m.market_cap >= $min_market_cap)
        AND ($max_market_cap IS NULL OR m.market_cap <= $max_market_cap)
        AND ($asset_types IS NULL OR m.asset_type IN $asset_types)
    RETURN m
    ORDER BY m.market_cap DESC
    SKIP $skip
    LIMIT $limit
    """

    DELETE_MARKET = """
    MATCH (m:MARKET {symbol: $symbol})
    DETACH DELETE m
    RETURN COUNT(m) as deleted_count
    """

    GET_MARKET_STATS = """
    MATCH (m:MARKET)
    RETURN
        COUNT(m) as total_markets,
        SUM(CASE WHEN m.is_active = true THEN 1 ELSE 0 END) as active_markets,
        SUM(COALESCE(m.market_cap, 0)) as total_market_cap,
        AVG(COALESCE(m.day_change_percent, 0)) as avg_day_change
    """

    GET_MARKETS_BY_ASSET_TYPE = """
    MATCH (m:MARKET)
    RETURN m.asset_type as asset_type, COUNT(m) as count
    ORDER BY count DESC
    """

    GET_MARKETS_BY_SECTOR = """
    MATCH (m:MARKET)-[:BELONGS_TO_SECTOR]->(s:SECTOR)
    RETURN s.code as sector_code, s.name as sector_name, COUNT(m) as count
    ORDER BY count DESC
    """


class SectorQueries:
    """
    Cypher query templates for SECTOR node operations.
    """

    MERGE_SECTOR = """
    MERGE (s:SECTOR {code: $code})
    ON CREATE SET
        s.name = $name,
        s.market_classification = COALESCE($market_classification, 'GICS'),
        s.created_at = datetime()
    ON MATCH SET
        s.name = $name,
        s.market_classification = COALESCE($market_classification, 'GICS')
    WITH s
    FOREACH (ignoreMe IN CASE WHEN $description IS NOT NULL THEN [1] ELSE [] END |
        SET s.description = $description
    )
    RETURN s
    """

    GET_SECTOR_BY_CODE = """
    MATCH (s:SECTOR {code: $code})
    RETURN s
    """

    GET_SECTOR_WITH_MARKETS = """
    MATCH (s:SECTOR {code: $code})
    OPTIONAL MATCH (s)<-[:BELONGS_TO_SECTOR]-(m:MARKET)
    RETURN s,
           COUNT(m) as market_count,
           COLLECT(m.symbol)[0..10] as sample_markets
    """

    LIST_SECTORS = """
    MATCH (s:SECTOR)
    OPTIONAL MATCH (s)<-[:BELONGS_TO_SECTOR]-(m:MARKET)
    RETURN s,
           COUNT(m) as market_count
    ORDER BY market_count DESC
    """

    DELETE_SECTOR = """
    MATCH (s:SECTOR {code: $code})
    OPTIONAL MATCH (s)<-[r:BELONGS_TO_SECTOR]-()
    DELETE r
    DELETE s
    RETURN COUNT(s) as deleted_count
    """


class RelationshipQueries:
    """
    Cypher query templates for managing relationships.
    """

    CREATE_MARKET_SECTOR_RELATIONSHIP = """
    MATCH (m:MARKET {symbol: $market_symbol})
    MATCH (s:SECTOR {code: $sector_code})
    MERGE (m)-[r:BELONGS_TO_SECTOR]->(s)
    RETURN m, r, s
    """

    DELETE_MARKET_SECTOR_RELATIONSHIP = """
    MATCH (m:MARKET {symbol: $market_symbol})-[r:BELONGS_TO_SECTOR]->(s:SECTOR)
    DELETE r
    RETURN COUNT(r) as deleted_count
    """

    GET_MARKET_RELATIONSHIPS = """
    MATCH (m:MARKET {symbol: $symbol})-[r]-(other)
    RETURN type(r) as relationship_type,
           labels(other) as other_labels,
           COUNT(*) as count
    ORDER BY count DESC
    """


class GraphTraversalQueries:
    """
    Advanced graph traversal queries for analysis.
    """

    FIND_RELATED_MARKETS = """
    // Find markets in the same sector
    MATCH (m1:MARKET {symbol: $symbol})-[:BELONGS_TO_SECTOR]->(s:SECTOR)<-[:BELONGS_TO_SECTOR]-(m2:MARKET)
    WHERE m1 <> m2
    RETURN m2.symbol as symbol,
           m2.name as name,
           m2.current_price as price,
           'SAME_SECTOR' as relationship_type
    LIMIT 10

    UNION

    // Find markets mentioned in same articles
    MATCH (m1:MARKET {symbol: $symbol})<-[:ABOUT_MARKET]-(a:ARTICLE)-[:ABOUT_MARKET]->(m2:MARKET)
    WHERE m1 <> m2
    WITH m2, COUNT(a) as article_count
    RETURN m2.symbol as symbol,
           m2.name as name,
           m2.current_price as price,
           'CO_MENTIONED' as relationship_type
    ORDER BY article_count DESC
    LIMIT 10
    """

    GET_SECTOR_PERFORMANCE = """
    MATCH (s:SECTOR {code: $sector_code})<-[:BELONGS_TO_SECTOR]-(m:MARKET)
    WHERE m.day_change_percent IS NOT NULL
    RETURN s.code as sector_code,
           s.name as sector_name,
           COUNT(m) as market_count,
           AVG(m.day_change_percent) as avg_change,
           MIN(m.day_change_percent) as min_change,
           MAX(m.day_change_percent) as max_change,
           SUM(m.market_cap) as total_market_cap
    """

    GET_TOP_MOVERS = """
    MATCH (m:MARKET)
    WHERE m.day_change_percent IS NOT NULL
        AND m.is_active = true
        AND ($asset_types IS NULL OR m.asset_type IN $asset_types)
    RETURN m
    ORDER BY ABS(m.day_change_percent) DESC
    LIMIT $limit
    """


class QUERIES:
    """
    Aggregated query collection for easy access.

    Usage:
        from app.models.neo4j_queries import QUERIES

        result = session.run(
            QUERIES.merge_market,
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="STOCK"
        )
    """
    # Market queries
    merge_market = MarketQueries.MERGE_MARKET
    merge_market_with_sector = MarketQueries.MERGE_MARKET_WITH_SECTOR
    update_market_price = MarketQueries.UPDATE_MARKET_PRICE
    get_market_by_symbol = MarketQueries.GET_MARKET_BY_SYMBOL
    get_market_with_relationships = MarketQueries.GET_MARKET_WITH_RELATIONSHIPS
    list_markets = MarketQueries.LIST_MARKETS
    count_markets = MarketQueries.COUNT_MARKETS
    search_markets_by_sector = MarketQueries.SEARCH_MARKETS_BY_SECTOR
    get_markets_by_market_cap = MarketQueries.GET_MARKETS_BY_MARKET_CAP
    delete_market = MarketQueries.DELETE_MARKET
    get_market_stats = MarketQueries.GET_MARKET_STATS
    get_markets_by_asset_type = MarketQueries.GET_MARKETS_BY_ASSET_TYPE
    get_markets_by_sector = MarketQueries.GET_MARKETS_BY_SECTOR

    # Sector queries
    merge_sector = SectorQueries.MERGE_SECTOR
    get_sector_by_code = SectorQueries.GET_SECTOR_BY_CODE
    get_sector_with_markets = SectorQueries.GET_SECTOR_WITH_MARKETS
    list_sectors = SectorQueries.LIST_SECTORS
    delete_sector = SectorQueries.DELETE_SECTOR

    # Relationship queries
    create_market_sector_relationship = RelationshipQueries.CREATE_MARKET_SECTOR_RELATIONSHIP
    delete_market_sector_relationship = RelationshipQueries.DELETE_MARKET_SECTOR_RELATIONSHIP
    get_market_relationships = RelationshipQueries.GET_MARKET_RELATIONSHIPS

    # Graph traversal queries
    find_related_markets = GraphTraversalQueries.FIND_RELATED_MARKETS
    get_sector_performance = GraphTraversalQueries.GET_SECTOR_PERFORMANCE
    get_top_movers = GraphTraversalQueries.GET_TOP_MOVERS


# Query parameter builders for common operations
class QueryParamBuilder:
    """
    Helper functions to build query parameters with proper types.
    """

    @staticmethod
    def market_create_params(market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build parameters for market creation query.

        Args:
            market_data: MarketCreate schema dict

        Returns:
            Dict ready for Neo4j query
        """
        return {
            "symbol": market_data["symbol"],
            "name": market_data["name"],
            "asset_type": market_data["asset_type"],
            "currency": market_data.get("currency", "USD"),
            "is_active": market_data.get("is_active", True),
            "exchange": market_data.get("exchange"),
            "sector": market_data.get("sector"),
            "isin": market_data.get("isin"),
            "description": market_data.get("description"),
        }

    @staticmethod
    def market_update_params(symbol: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build parameters for market price update query.

        Args:
            symbol: Market symbol
            update_data: MarketUpdate schema dict

        Returns:
            Dict ready for Neo4j query
        """
        return {
            "symbol": symbol,
            "current_price": update_data.get("current_price"),
            "day_change_percent": update_data.get("day_change_percent"),
            "market_cap": update_data.get("market_cap"),
            "volume": update_data.get("volume"),
            "open_price": update_data.get("open_price"),
            "high_price": update_data.get("high_price"),
            "low_price": update_data.get("low_price"),
            "close_price": update_data.get("close_price"),
        }

    @staticmethod
    def search_params(search_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build parameters for market search query.

        Args:
            search_query: MarketSearchQuery schema dict

        Returns:
            Dict ready for Neo4j query
        """
        page = search_query.get("page", 0)
        page_size = search_query.get("page_size", 20)

        return {
            "symbol_contains": search_query.get("symbol_contains"),
            "name_contains": search_query.get("name_contains"),
            "asset_types": search_query.get("asset_types"),
            "is_active": search_query.get("is_active"),
            "skip": page * page_size,
            "limit": page_size,
        }
