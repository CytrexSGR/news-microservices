"""
Entity Knowledge Graph Processor

Processes unprocessed entities from content analysis and sends them to Knowledge Graph
via Entity-Canonicalization service with Wikidata enrichment.

Design:
- Runs every 30 seconds
- Processes batches of 10-15 articles
- Sub-batches of 3 for Entity-Canonicalization (Wikidata latency handling)
- Parallel processing with asyncio
- Robust error handling (single failures don't block batch)
- Transactional database updates

Data Source: public.article_analysis (unified table)
- Entities from: tier1_results->'entities'
- Relations from: tier1_results->'relations'
- Tracking: processed_by_kg column

Updated: 2025-12-27 - Migrated from deprecated content_analysis_v2 schema
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
import httpx
import aio_pika

from app.core.database import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 15  # Total entities to fetch per run
SUB_BATCH_SIZE = 3  # Entities per Entity-Canonicalization job
CANONICALIZATION_TIMEOUT = 300  # 5 minutes
CANONICALIZATION_MAX_ATTEMPTS = 20  # 20 * 3s = 60s max wait
# RABBITMQ_URL removed - use settings.RABBITMQ_URL directly for runtime lookup
ENTITY_CANON_URL = "http://news-entity-canonicalization:8112"


class EntityKGProcessor:
    """Processes entities and sends them to Knowledge Graph"""

    def __init__(self):
        self.rabbitmq_connection: Optional[aio_pika.Connection] = None
        self.rabbitmq_channel: Optional[aio_pika.Channel] = None

    async def _ensure_rabbitmq_connection(self):
        """Ensure RabbitMQ connection is established"""
        if not self.rabbitmq_connection or self.rabbitmq_connection.is_closed:
            try:
                # Use runtime config lookup instead of cached module constant
                self.rabbitmq_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                self.rabbitmq_channel = await self.rabbitmq_connection.channel()
                logger.info(f"RabbitMQ connection established to {settings.RABBITMQ_URL}")
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ ({settings.RABBITMQ_URL}): {e}")
                raise

    async def _send_to_rabbitmq(self, message: Dict[str, Any]):
        """Send message to RabbitMQ exchange"""
        await self._ensure_rabbitmq_connection()

        exchange = await self.rabbitmq_channel.declare_exchange(
            "news.events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key="analysis.relationships.extracted"
        )

    async def _process_entity_batch(
        self,
        db: Session,
        entities_data: List[Dict[str, Any]]
    ) -> int:
        """
        Process a batch of entities through Entity-Canonicalization

        Args:
            db: Database session
            entities_data: List of dicts with keys: agent_result_id, article_id, entities, relationships

        Returns:
            Number of successfully processed entities
        """
        processed_count = 0

        # Split into sub-batches of 3
        sub_batches = [
            entities_data[i:i + SUB_BATCH_SIZE]
            for i in range(0, len(entities_data), SUB_BATCH_SIZE)
        ]

        logger.info(f"Processing {len(entities_data)} entities in {len(sub_batches)} sub-batches")

        # Process sub-batches in parallel
        tasks = [
            self._process_sub_batch(db, sub_batch)
            for sub_batch in sub_batches
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Sub-batch {i} failed: {result}")
            else:
                processed_count += result

        return processed_count

    async def _process_sub_batch(
        self,
        db: Session,
        sub_batch: List[Dict[str, Any]]
    ) -> int:
        """Process a sub-batch of 3 entities"""
        if not sub_batch:
            return 0

        try:
            # Extract entity list for canonicalization
            entity_list = []
            for item in sub_batch:
                for e in item['entities']:
                    entity_list.append({
                        "entity_name": e.get('text') or e.get('name'),
                        "entity_type": e.get('type') or e.get('entity_type', 'MISC'),
                        "language": "de"
                    })

            if not entity_list:
                logger.warning("Sub-batch has no entities to process")
                return 0

            # Call Entity-Canonicalization async API
            async with httpx.AsyncClient(timeout=CANONICALIZATION_TIMEOUT) as client:
                # Start async job
                resp = await client.post(
                    f"{ENTITY_CANON_URL}/api/v1/canonicalization/canonicalize/batch/async",
                    json={"entities": entity_list}
                )
                resp.raise_for_status()
                job_id = resp.json()['job_id']

                logger.info(f"Started canonicalization job {job_id} with {len(entity_list)} entities")

                # Poll for completion
                for attempt in range(CANONICALIZATION_MAX_ATTEMPTS):
                    await asyncio.sleep(3)

                    status_resp = await client.get(
                        f"{ENTITY_CANON_URL}/api/v1/canonicalization/jobs/{job_id}/status"
                    )
                    status_data = status_resp.json()

                    if status_data['status'] == 'completed':
                        # Get results
                        result_resp = await client.get(
                            f"{ENTITY_CANON_URL}/api/v1/canonicalization/jobs/{job_id}/result"
                        )
                        canonicalized = result_resp.json()

                        # Process each item in sub-batch
                        processed = 0
                        for item in sub_batch:
                            try:
                                await self._send_to_knowledge_graph(
                                    item['analysis_id'],
                                    item['article_id'],
                                    canonicalized['results'],
                                    item['relationships'],
                                    item['entities']  # Pass original entities for type preservation
                                )

                                # Mark as processed in unified table
                                db.execute(
                                    text("""
                                        UPDATE public.article_analysis
                                        SET processed_by_kg = true
                                        WHERE id = :id
                                    """),
                                    {"id": item['analysis_id']}
                                )
                                processed += 1

                            except Exception as e:
                                logger.error(f"Failed to process article {item['article_id']}: {e}")
                                continue

                        db.commit()
                        logger.info(f"Sub-batch completed: {processed}/{len(sub_batch)} entities processed")
                        return processed

                    elif status_data['status'] == 'failed':
                        raise Exception(f"Canonicalization job failed: {status_data.get('error_message')}")

                raise Exception(f"Job {job_id} timeout after {CANONICALIZATION_MAX_ATTEMPTS * 3}s")

        except Exception as e:
            logger.error(f"Sub-batch processing failed: {e}")
            db.rollback()
            return 0

    async def _send_to_knowledge_graph(
        self,
        analysis_id: str,
        article_id: str,
        canonicalized_results: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        original_entities: List[Dict[str, Any]]
    ):
        """Transform canonicalized results and send to Knowledge Graph via RabbitMQ"""

        # Build entity type map from ORIGINAL entities (preserve types from PostgreSQL)
        # CRITICAL: Don't rely on canonicalized_results for types - they may be missing/wrong
        original_entity_type_map = {
            (e.get('text') or e.get('name')): e.get('type', 'MISC')
            for e in original_entities
        }

        # Build entity map
        entity_map = {
            entity['canonical_name']: entity
            for entity in canonicalized_results
        }

        # Build relationship triplets
        triplets = []
        for rel in relationships:
            # FIXED: Use ORIGINAL entity types from PostgreSQL as fallback
            # Previously: Defaulted to 'UNKNOWN' if entity not in canonicalized results
            # Problem: Entity-Canonicalization doesn't always return all entities
            # Solution: Use original_entity_type_map to preserve types from PostgreSQL
            entity1_name = rel.get('entity1')
            entity2_name = rel.get('entity2')

            subject = entity_map.get(entity1_name, {
                'canonical_name': entity1_name,
                'entity_type': (
                    original_entity_type_map.get(entity1_name) or
                    rel.get('entity1_type', 'MISC')
                ),
                'canonical_id': None
            })

            obj = entity_map.get(entity2_name, {
                'canonical_name': entity2_name,
                'entity_type': (
                    original_entity_type_map.get(entity2_name) or
                    rel.get('entity2_type', 'MISC')
                ),
                'canonical_id': None
            })

            triplets.append({
                "subject": {
                    "text": subject['canonical_name'],
                    "type": subject.get('entity_type', 'UNKNOWN'),
                    "wikidata_id": subject.get('canonical_id')
                },
                "relationship": {
                    "type": rel.get('relationship_type', 'RELATED_TO'),
                    "confidence": rel.get('confidence', 0.5),
                    "evidence": rel.get('evidence', f"Extracted from article {article_id}")
                },
                "object": {
                    "text": obj['canonical_name'],
                    "type": obj.get('entity_type', 'UNKNOWN'),
                    "wikidata_id": obj.get('canonical_id')
                }
            })

        # Add entity-article relationships
        for entity in canonicalized_results:
            entity_name = entity['canonical_name']
            triplets.append({
                "subject": {
                    "text": entity_name,
                    # FIXED: Use original entity type from PostgreSQL, not from canonicalized results
                    "type": (
                        original_entity_type_map.get(entity_name) or
                        entity.get('entity_type', 'MISC')
                    ),
                    "wikidata_id": entity.get('canonical_id')
                },
                "relationship": {
                    "type": "MENTIONED_IN",
                    "confidence": entity.get('confidence', 0.8),
                    "evidence": f"Mentioned in article {article_id}"
                },
                "object": {
                    "text": f"Article {article_id}",
                    "type": "ARTICLE",
                    "wikidata_id": None
                }
            })

        # Send to RabbitMQ
        message = {
            "event_type": "relationships.extracted",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "article_id": str(article_id),  # Convert UUID to string
                "source_url": None,
                "triplets": triplets,
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "total_relationships": len(triplets)
            },
            "analysis_id": str(analysis_id)  # Reference to article_analysis.id
        }

        await self._send_to_rabbitmq(message)
        logger.debug(f"Sent {len(triplets)} triplets to Knowledge Graph for article {article_id}")

    async def process_entities(self):
        """
        Main processing function - fetches and processes unprocessed entities

        Called every 30 seconds by APScheduler

        Data source: public.article_analysis (unified table)
        - Reads tier1_results JSONB for entities and relations
        - Updates processed_by_kg column after processing
        """
        db = SessionLocal()

        try:
            # Fetch unprocessed articles with tier1 entities
            # Uses public.article_analysis (unified table, migrated 2025-12-27)
            result = db.execute(
                text("""
                    SELECT
                        id,
                        article_id,
                        tier1_results->'entities' as entities,
                        tier1_results->'relations' as relations
                    FROM public.article_analysis
                    WHERE processed_by_kg = false
                      AND tier1_results IS NOT NULL
                      AND jsonb_array_length(tier1_results->'entities') > 0
                    ORDER BY created_at ASC
                    LIMIT :batch_size
                """),
                {"batch_size": BATCH_SIZE}
            )

            rows = result.fetchall()

            if not rows:
                logger.debug("No unprocessed entities found")
                return {"status": "no_data", "processed": 0}

            logger.info(f"Found {len(rows)} unprocessed articles with entities")

            # Extract entities data
            entities_data = []
            for row in rows:
                analysis_id, article_id, entities_json, relations_json = row

                # Parse JSONB (already dict from psycopg2)
                entities = entities_json if isinstance(entities_json, list) else []
                relations = relations_json if isinstance(relations_json, list) else []

                if not entities:
                    logger.warning(f"Article {article_id} has no entities - skipping")
                    continue

                # Transform tier1 entity format to match expected format
                # Two formats exist in the database:
                # - Old format: {"text": "India", "type": "LOCATION", ...}
                # - New format: {"name": "PAS", "type": "ORGANIZATION", ...}
                # We need to handle both
                transformed_entities = []
                for e in entities:
                    # Get entity name from either 'name' or 'text' field
                    entity_name = e.get("name") or e.get("text")
                    if not entity_name:
                        continue

                    transformed_entities.append({
                        "text": entity_name,
                        "name": entity_name,
                        "type": e.get("type", "MISC"),
                        "confidence": e.get("confidence", 0.8)
                    })

                # Transform tier1 relations format
                # tier1: {"subject": "X", "predicate": "Y", "object": "Z", "confidence": 0.8}
                # expected: {"entity1": "X", "relationship_type": "Y", "entity2": "Z"}
                transformed_relations = [
                    {
                        "entity1": r.get("subject"),
                        "entity2": r.get("object"),
                        "relationship_type": r.get("predicate", "RELATED_TO").upper().replace(" ", "_"),
                        "confidence": r.get("confidence", 0.5),
                        "evidence": f"Extracted from article {article_id}"
                    }
                    for r in relations
                    if r.get("subject") and r.get("object")
                ]

                entities_data.append({
                    "analysis_id": analysis_id,  # Changed from agent_result_id
                    "article_id": article_id,
                    "entities": transformed_entities,
                    "relationships": transformed_relations
                })

            if not entities_data:
                logger.warning("No valid entities to process")
                return {"status": "no_valid_data", "processed": 0}

            # Process batch
            processed_count = await self._process_entity_batch(db, entities_data)

            logger.info(f"Batch processing complete: {processed_count}/{len(entities_data)} articles processed")

            return {
                "status": "success",
                "processed": processed_count,
                "total": len(entities_data)
            }

        except Exception as e:
            logger.error(f"Entity processing failed: {e}", exc_info=True)
            db.rollback()
            return {"status": "error", "error": str(e)}

        finally:
            db.close()


# Global instance
entity_kg_processor = EntityKGProcessor()


async def process_entities_job():
    """Job function for APScheduler"""
    await entity_kg_processor.process_entities()
