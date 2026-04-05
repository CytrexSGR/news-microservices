"""
V3 Graph Client for Neo4j Knowledge Graph Integration

Publishes Content-Analysis-V3 results to Neo4j for knowledge graph construction.

Architecture:
- Tier0 (Triage) → Article node with priority/category
- Tier1 (Foundation) → Entity, Topic nodes + relationships
- Tier2 (Specialists) → Market, Region, Sector nodes + relationships

Compared to V2:
- V2: 7 finding categories (EVENT_TYPE, IHL_CONCERN, REGIONAL_IMPACT, etc.)
- V3: Structured entity/relation extraction + specialist findings
- Cost: 96.7% reduction ($0.0085 → $0.00028 per article)

Missing V2 Features:
- ❌ Event type tracking (MISSILE_STRIKE, AIR_STRIKE, etc.)
- ❌ IHL violation analysis
- ❌ Humanitarian crisis tracking
→ Can be added as optional Tier2 specialists if needed
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from neo4j import AsyncGraphDatabase, AsyncDriver
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class V3GraphClient:
    """
    Neo4j Knowledge Graph client for V3 analysis results.

    **Initialization:**
    ```python
    client = V3GraphClient(uri="bolt://localhost:7687", user="neo4j", password="secret")
    await client.connect()
    ```

    **Usage:**
    ```python
    # After Tier0 analysis
    await client.create_article_node(
        article_id="uuid-123",
        tier0_data={"PriorityScore": 8, "category": "CONFLICT", "keep": True}
    )

    # After Tier1 analysis
    await client.publish_tier1(
        article_id="uuid-123",
        tier1_data={
            "entities": [{"name": "Russia", "type": "ORGANIZATION", "relevance": 0.95}],
            "relations": [{"source": "Russia", "target": "Ukraine", "type": "ATTACKS"}],
            "topics": ["Geopolitical Conflict"]
        }
    )

    # After Tier2 analysis
    await client.publish_tier2(
        article_id="uuid-123",
        tier2_data={
            "FINANCIAL_ANALYST": {"affected_sectors": {"energy": "negative"}},
            "GEOPOLITICAL_ANALYST": {"affected_regions": ["Eastern Europe"]}
        }
    )
    ```
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        max_pool_size: int = 50,
        connection_timeout: int = 30
    ):
        """
        Initialize V3 Graph Client.

        Args:
            uri: Neo4j bolt URI (e.g., "bolt://localhost:7687")
            user: Neo4j username
            password: Neo4j password
            max_pool_size: Maximum connection pool size
            connection_timeout: Connection timeout in seconds
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.max_pool_size = max_pool_size
        self.connection_timeout = connection_timeout
        self.driver: Optional[AsyncDriver] = None

    async def connect(self):
        """
        Establish connection to Neo4j database.

        Should be called during application startup.

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info(f"Connecting to Neo4j at {self.uri}...")

            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=self.max_pool_size,
                connection_timeout=self.connection_timeout
            )

            # Verify connectivity
            await self.driver.verify_connectivity()

            logger.info("✓ V3 Graph Client: Neo4j connection established")

            # Create indexes for performance
            await self._create_indexes()

        except Exception as e:
            logger.error(f"✗ V3 Graph Client: Failed to connect to Neo4j: {e}")
            raise

    async def disconnect(self):
        """
        Close Neo4j driver connection.

        Should be called during application shutdown.
        """
        if self.driver:
            await self.driver.close()
            logger.info("V3 Graph Client: Neo4j connection closed")

    # ========================================================================
    # TIER 0: ARTICLE NODE CREATION
    # ========================================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def create_article_node(
        self,
        article_id: str,
        tier0_data: Dict[str, Any],
        article_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Article node with Tier0 triage data.

        Args:
            article_id: Article UUID
            tier0_data: Tier0 triage decision
                - PriorityScore: int (0-10)
                - category: str (CONFLICT, FINANCE, POLITICS, etc.)
                - keep: bool (whether to keep article)
            article_metadata: Optional metadata (title, published_at, etc.)

        Returns:
            Dict with node creation summary

        Example:
            ```python
            result = await client.create_article_node(
                article_id="abc-123",
                tier0_data={
                    "PriorityScore": 8,
                    "category": "CONFLICT",
                    "keep": True,
                    "tokens_used": 500,
                    "cost_usd": 0.00005
                },
                article_metadata={
                    "title": "Russia strikes Kyiv",
                    "published_at": "2025-11-19T10:00:00Z"
                }
            )
            # Returns: {"nodes_created": 1, "properties_set": 8}
            ```
        """
        if not self.driver:
            raise RuntimeError("Graph client not connected. Call connect() first.")

        metadata = article_metadata or {}

        query = """
        MERGE (a:Article {article_id: $article_id})
        SET a.priority_score = $priority_score,
            a.category = $category,
            a.keep = $keep,
            a.analyzed_at = datetime($analyzed_at),
            a.tier0_tokens = $tier0_tokens,
            a.tier0_cost_usd = $tier0_cost_usd
        """

        # Add optional metadata
        if "title" in metadata:
            query += ", a.title = $title"
        if "published_at" in metadata:
            query += ", a.published_at = datetime($published_at)"

        query += "\nRETURN a"

        parameters = {
            "article_id": article_id,
            "priority_score": tier0_data.get("PriorityScore", 0),
            "category": tier0_data.get("category", "OTHER"),
            "keep": tier0_data.get("keep", False),
            "analyzed_at": datetime.utcnow().isoformat(),
            "tier0_tokens": tier0_data.get("tokens_used", 0),
            "tier0_cost_usd": tier0_data.get("cost_usd", 0.0),
            **metadata
        }

        async with self.driver.session() as session:
            result = await session.run(query, parameters)
            summary = await result.consume()

            return {
                "success": True,
                "article_id": article_id,
                "nodes_created": summary.counters.nodes_created,
                "properties_set": summary.counters.properties_set
            }

    # ========================================================================
    # TIER 1: ENTITY/RELATION/TOPIC EXTRACTION
    # ========================================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def publish_tier1(
        self,
        article_id: str,
        tier1_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publish Tier1 foundation extraction to graph.

        Creates:
        - Entity nodes (from tier1_data["entities"])
        - Topic nodes (from tier1_data["topics"])
        - Relations between entities (from tier1_data["relations"])
        - HAS_ENTITY relationships (Article → Entity)
        - DISCUSSES relationships (Article → Topic)

        Args:
            article_id: Article UUID
            tier1_data: Tier1 extraction results
                - entities: List[{name, type, relevance}]
                - relations: List[{source, target, type, confidence}]
                - topics: List[str]

        Returns:
            Dict with creation summary

        Example:
            ```python
            result = await client.publish_tier1(
                article_id="abc-123",
                tier1_data={
                    "entities": [
                        {"name": "Russia", "type": "ORGANIZATION", "relevance": 0.95},
                        {"name": "Ukraine", "type": "LOCATION", "relevance": 0.92}
                    ],
                    "relations": [
                        {
                            "source": "Russia",
                            "target": "Ukraine",
                            "type": "ATTACKS",
                            "confidence": 0.9
                        }
                    ],
                    "topics": ["Geopolitical Conflict", "Military Operations"]
                }
            )
            # Returns: {
            #   "entities_created": 2,
            #   "topics_created": 2,
            #   "relations_created": 1
            # }
            ```
        """
        if not self.driver:
            raise RuntimeError("Graph client not connected. Call connect() first.")

        entities = tier1_data.get("entities", [])
        relations = tier1_data.get("relations", [])
        topics = tier1_data.get("topics", [])

        entity_count = 0
        topic_count = 0
        relation_count = 0

        async with self.driver.session() as session:
            # 1. Create Entity nodes and link to Article
            for entity in entities:
                query = """
                MATCH (a:Article {article_id: $article_id})
                MERGE (e:Entity {name: $name})
                ON CREATE SET
                    e.entity_id = substring(toString(randomUUID()), 0, 16),
                    e.type = $type,
                    e.last_updated = datetime()
                ON MATCH SET
                    e.type = $type,
                    e.last_updated = datetime()
                MERGE (a)-[r:HAS_ENTITY]->(e)
                SET r.relevance = $relevance
                RETURN e
                """

                result = await session.run(query, {
                    "article_id": article_id,
                    "name": entity.get("name"),
                    "type": entity.get("type"),
                    "relevance": entity.get("relevance", 0.0)
                })
                summary = await result.consume()
                entity_count += summary.counters.nodes_created
                relation_count += summary.counters.relationships_created

            # 2. Create Entity-Entity relations
            for relation in relations:
                query = """
                MATCH (source:Entity {name: $source_name})
                MATCH (target:Entity {name: $target_name})
                MERGE (source)-[r:RELATES_TO {type: $relation_type}]->(target)
                SET r.confidence = $confidence
                RETURN r
                """

                result = await session.run(query, {
                    "source_name": relation.get("source"),
                    "target_name": relation.get("target"),
                    "relation_type": relation.get("type"),
                    "confidence": relation.get("confidence", 0.0)
                })
                summary = await result.consume()
                relation_count += summary.counters.relationships_created

            # 3. Create Topic nodes and link to Article
            for topic_name in topics:
                query = """
                MATCH (a:Article {article_id: $article_id})
                MERGE (t:Topic {name: $name})
                MERGE (a)-[:DISCUSSES]->(t)
                RETURN t
                """

                result = await session.run(query, {
                    "article_id": article_id,
                    "name": topic_name
                })
                summary = await result.consume()
                topic_count += summary.counters.nodes_created

        return {
            "success": True,
            "article_id": article_id,
            "entities_created": entity_count,
            "topics_created": topic_count,
            "relations_created": relation_count
        }

    # ========================================================================
    # TIER 2: SPECIALIST ANALYSIS
    # ========================================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def publish_tier2(
        self,
        article_id: str,
        tier2_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publish Tier2 specialist analysis to graph.

        Supported specialists:
        - FINANCIAL_ANALYST → Market, Sector nodes
        - GEOPOLITICAL_ANALYST → Region nodes
        - TOPIC_CLASSIFIER → Category relationships

        Args:
            article_id: Article UUID
            tier2_data: Tier2 specialist results
                - FINANCIAL_ANALYST: {affected_sectors, market_volatility}
                - GEOPOLITICAL_ANALYST: {affected_regions, stability_impact}
                - TOPIC_CLASSIFIER: {primary_category, subcategories}

        Returns:
            Dict with creation summary

        Example:
            ```python
            result = await client.publish_tier2(
                article_id="abc-123",
                tier2_data={
                    "FINANCIAL_ANALYST": {
                        "affected_sectors": {"energy": "negative", "defense": "positive"},
                        "market_volatility": "HIGH"
                    },
                    "GEOPOLITICAL_ANALYST": {
                        "affected_regions": ["Eastern Europe"],
                        "stability_impact": "DEGRADING",
                        "spillover_risk": 0.78
                    }
                }
            )
            # Returns: {
            #   "sectors_created": 2,
            #   "regions_created": 1,
            #   "relationships_created": 3
            # }
            ```
        """
        if not self.driver:
            raise RuntimeError("Graph client not connected. Call connect() first.")

        sectors_created = 0
        regions_created = 0
        markets_created = 0
        relationships_created = 0

        async with self.driver.session() as session:
            # 1. Financial Analyst → Sector nodes
            if "FINANCIAL_ANALYST" in tier2_data:
                financial = tier2_data["FINANCIAL_ANALYST"]
                affected_sectors = financial.get("affected_sectors", {})

                for sector_name, direction in affected_sectors.items():
                    query = """
                    MATCH (a:Article {article_id: $article_id})
                    MERGE (s:Sector {name: $sector_name})
                    MERGE (a)-[r:AFFECTS_SECTOR]->(s)
                    SET r.direction = $direction,
                        r.volatility = $volatility
                    RETURN s
                    """

                    result = await session.run(query, {
                        "article_id": article_id,
                        "sector_name": sector_name,
                        "direction": direction,
                        "volatility": financial.get("market_volatility", "UNKNOWN")
                    })
                    summary = await result.consume()
                    sectors_created += summary.counters.nodes_created
                    relationships_created += summary.counters.relationships_created

            # 2. Geopolitical Analyst → Region nodes
            if "GEOPOLITICAL_ANALYST" in tier2_data:
                geopolitical = tier2_data["GEOPOLITICAL_ANALYST"]
                affected_regions = geopolitical.get("affected_regions", [])

                for region_name in affected_regions:
                    query = """
                    MATCH (a:Article {article_id: $article_id})
                    MERGE (r:Region {name: $region_name})
                    SET r.stability = $stability
                    MERGE (a)-[rel:IMPACTS_REGION]->(r)
                    SET rel.spillover_risk = $spillover_risk
                    RETURN r
                    """

                    result = await session.run(query, {
                        "article_id": article_id,
                        "region_name": region_name,
                        "stability": geopolitical.get("stability_impact", "UNKNOWN"),
                        "spillover_risk": geopolitical.get("spillover_risk", 0.0)
                    })
                    summary = await result.consume()
                    regions_created += summary.counters.nodes_created
                    relationships_created += summary.counters.relationships_created

        return {
            "success": True,
            "article_id": article_id,
            "sectors_created": sectors_created,
            "regions_created": regions_created,
            "markets_created": markets_created,
            "relationships_created": relationships_created
        }

    # ========================================================================
    # UTILITIES
    # ========================================================================

    async def _create_indexes(self):
        """
        Create indexes for fast lookups.

        Indexes:
        - Article.article_id (unique constraint)
        - Entity.name (index)
        - Topic.name (index)
        - Region.name (index)
        - Sector.name (index)
        """
        try:
            logger.info("Creating V3 Graph indexes...")

            async with self.driver.session() as session:
                # Unique constraint on Article.article_id
                await session.run("""
                    CREATE CONSTRAINT article_id_unique IF NOT EXISTS
                    FOR (a:Article)
                    REQUIRE a.article_id IS UNIQUE
                """)

                # Index on Entity.name
                await session.run("""
                    CREATE INDEX entity_name_index IF NOT EXISTS
                    FOR (e:Entity)
                    ON (e.name)
                """)

                # Index on Topic.name
                await session.run("""
                    CREATE INDEX topic_name_index IF NOT EXISTS
                    FOR (t:Topic)
                    ON (t.name)
                """)

                # Index on Region.name
                await session.run("""
                    CREATE INDEX region_name_index IF NOT EXISTS
                    FOR (r:Region)
                    ON (r.name)
                """)

                # Index on Sector.name
                await session.run("""
                    CREATE INDEX sector_name_index IF NOT EXISTS
                    FOR (s:Sector)
                    ON (s.name)
                """)

            logger.info("✓ V3 Graph indexes created")

        except Exception as e:
            logger.error(f"✗ Failed to create V3 Graph indexes: {e}")
            raise

    async def get_article_graph(self, article_id: str) -> Dict[str, Any]:
        """
        Retrieve complete knowledge graph for an article.

        Returns all nodes and relationships connected to the article.

        Args:
            article_id: Article UUID

        Returns:
            Dict with nodes and relationships

        Example:
            ```python
            graph = await client.get_article_graph("abc-123")
            # Returns: {
            #   "article": {...},
            #   "entities": [...],
            #   "topics": [...],
            #   "regions": [...],
            #   "sectors": [...],
            #   "relationships": [...]
            # }
            ```
        """
        if not self.driver:
            raise RuntimeError("Graph client not connected. Call connect() first.")

        query = """
        MATCH (a:Article {article_id: $article_id})
        OPTIONAL MATCH (a)-[r1:HAS_ENTITY]->(e:Entity)
        OPTIONAL MATCH (a)-[r2:DISCUSSES]->(t:Topic)
        OPTIONAL MATCH (a)-[r3:IMPACTS_REGION]->(r:Region)
        OPTIONAL MATCH (a)-[r4:AFFECTS_SECTOR]->(s:Sector)
        RETURN a, collect(DISTINCT e) as entities, collect(DISTINCT t) as topics,
               collect(DISTINCT r) as regions, collect(DISTINCT s) as sectors
        """

        async with self.driver.session() as session:
            result = await session.run(query, {"article_id": article_id})
            record = await result.single()

            if not record:
                return {"error": "Article not found in graph"}

            return {
                "article": dict(record["a"]),
                "entities": [dict(e) for e in record["entities"] if e],
                "topics": [dict(t) for t in record["topics"] if t],
                "regions": [dict(r) for r in record["regions"] if r],
                "sectors": [dict(s) for s in record["sectors"] if s]
            }
