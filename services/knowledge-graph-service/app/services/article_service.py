"""
Article Service

Business logic for querying article-related graph data.
"""

import logging
from typing import Optional, List, Dict, Any

from app.services.neo4j_service import neo4j_service
from app.models.articles import ArticleEntity, ArticleNode

logger = logging.getLogger(__name__)


class ArticleService:
    """Service for article-related graph operations."""

    async def get_article_entities(
        self,
        article_id: str,
        entity_type: Optional[str] = None,
        limit: int = 50
    ) -> tuple[List[ArticleEntity], Optional[ArticleNode]]:
        """
        Fetch all entities extracted from a specific article.

        Args:
            article_id: Article identifier
            entity_type: Optional filter by entity type (PERSON, ORGANIZATION, etc.)
            limit: Maximum number of entities to return

        Returns:
            Tuple of (list of entities, article node info or None)

        Note:
            Gracefully handles cases where Article node doesn't exist in Neo4j yet.
            In such cases, returns entities with article_node=None.
        """
        # Build Cypher query
        if entity_type:
            cypher = """
            // Try to find Article node (may not exist yet)
            OPTIONAL MATCH (a:Article {id: $article_id})

            // Find entities with EXTRACTED_FROM relationship
            MATCH (e:Entity)-[r:EXTRACTED_FROM]->(article)
            WHERE article.id = $article_id OR article = a
              AND ($entity_type IS NULL OR e.type = $entity_type)

            // Return article info and entities
            RETURN
                e.name AS name,
                e.type AS type,
                e.wikidata_id AS wikidata_id,
                r.confidence AS confidence,
                r.mention_count AS mention_count,
                r.first_mention_index AS first_mention_index,
                a.id AS article_id,
                a.title AS article_title,
                a.url AS article_url,
                a.published_date AS published_date
            ORDER BY r.confidence DESC, r.mention_count DESC
            LIMIT $limit
            """
        else:
            cypher = """
            // Try to find Article node (may not exist yet)
            OPTIONAL MATCH (a:Article {id: $article_id})

            // Find entities with EXTRACTED_FROM relationship
            MATCH (e:Entity)-[r:EXTRACTED_FROM]->(article)
            WHERE article.id = $article_id OR article = a

            // Return article info and entities
            RETURN
                e.name AS name,
                e.type AS type,
                e.wikidata_id AS wikidata_id,
                r.confidence AS confidence,
                r.mention_count AS mention_count,
                r.first_mention_index AS first_mention_index,
                a.id AS article_id,
                a.title AS article_title,
                a.url AS article_url,
                a.published_date AS published_date
            ORDER BY r.confidence DESC, r.mention_count DESC
            LIMIT $limit
            """

        try:
            results = await neo4j_service.execute_query(
                cypher,
                parameters={
                    "article_id": article_id,
                    "entity_type": entity_type,
                    "limit": limit
                }
            )

            # Extract article info from first result (if exists)
            article_node = None
            if results and results[0].get("article_id"):
                first = results[0]
                article_node = ArticleNode(
                    article_id=first["article_id"],
                    title=first.get("article_title"),
                    url=first.get("article_url"),
                    published_date=first.get("published_date"),
                    entity_count=len(results)
                )

            # Transform results to ArticleEntity models
            entities = [
                ArticleEntity(
                    name=record["name"],
                    type=record["type"],
                    wikidata_id=record.get("wikidata_id"),
                    confidence=record["confidence"],
                    mention_count=record.get("mention_count", 1),
                    first_mention_index=record.get("first_mention_index")
                )
                for record in results
            ]

            logger.info(
                f"Fetched {len(entities)} entities for article_id={article_id}"
                + (f" (filtered by type={entity_type})" if entity_type else "")
            )

            return entities, article_node

        except Exception as e:
            logger.error(f"Failed to fetch article entities: {e}", exc_info=True)
            raise

    async def get_article_info(self, article_id: str) -> Optional[ArticleNode]:
        """
        Get article node information from graph.

        Args:
            article_id: Article identifier

        Returns:
            ArticleNode if found, None otherwise
        """
        cypher = """
        MATCH (a:Article {id: $article_id})
        OPTIONAL MATCH (e:Entity)-[:EXTRACTED_FROM]->(a)
        RETURN
            a.id AS article_id,
            a.title AS title,
            a.url AS url,
            a.published_date AS published_date,
            count(e) AS entity_count
        """

        try:
            results = await neo4j_service.execute_query(
                cypher,
                parameters={"article_id": article_id}
            )

            if not results:
                return None

            record = results[0]
            return ArticleNode(
                article_id=record["article_id"],
                title=record.get("title"),
                url=record.get("url"),
                published_date=record.get("published_date"),
                entity_count=record.get("entity_count", 0)
            )

        except Exception as e:
            logger.error(f"Failed to fetch article info: {e}", exc_info=True)
            raise

    async def count_article_entities(
        self,
        article_id: str,
        entity_type: Optional[str] = None
    ) -> int:
        """
        Count entities for an article (respecting filters).

        Args:
            article_id: Article identifier
            entity_type: Optional filter by entity type

        Returns:
            Total count of entities
        """
        if entity_type:
            cypher = """
            MATCH (e:Entity)-[:EXTRACTED_FROM]->(article)
            WHERE article.id = $article_id AND e.type = $entity_type
            RETURN count(e) AS total
            """
        else:
            cypher = """
            MATCH (e:Entity)-[:EXTRACTED_FROM]->(article)
            WHERE article.id = $article_id
            RETURN count(e) AS total
            """

        try:
            results = await neo4j_service.execute_query(
                cypher,
                parameters={"article_id": article_id, "entity_type": entity_type}
            )

            return results[0]["total"] if results else 0

        except Exception as e:
            logger.error(f"Failed to count article entities: {e}", exc_info=True)
            raise


# Global service instance
article_service = ArticleService()
