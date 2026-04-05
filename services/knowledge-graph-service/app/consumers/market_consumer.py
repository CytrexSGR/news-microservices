"""
Market Data Event Consumer for Knowledge-Graph Service.

Listens for finance.market.data.updated events from FMP Service
and automatically syncs market data to Neo4j.
"""

import logging
from typing import Dict, Any
import aio_pika
from aio_pika import ExchangeType, Message
from aio_pika.abc import AbstractIncomingMessage
import json

from app.config import settings
from app.services.fmp_integration.market_sync_service import MarketSyncService

logger = logging.getLogger(__name__)


class MarketDataConsumer:
    """
    RabbitMQ consumer for market data update events.

    Routing: finance.market.data.updated
    Queue: knowledge_graph_market_updates
    Exchange: finance (Topic)
    """

    def __init__(self, market_sync_service: MarketSyncService):
        """
        Initialize consumer.

        Args:
            market_sync_service: Market sync service instance
        """
        self.market_sync_service = market_sync_service
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            # Create robust connection (auto-reconnects)
            self.connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                timeout=30
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange (must match FMP Service exchange)
            self.exchange = await self.channel.declare_exchange(
                'finance',  # Same as FMP Service
                ExchangeType.TOPIC,
                durable=True
            )

            # Declare queue
            self.queue = await self.channel.declare_queue(
                'knowledge_graph_market_updates',
                durable=True,
                arguments={
                    'x-dead-letter-exchange': 'finance.dlx',
                    'x-message-ttl': 86400000,  # 24 hours
                }
            )

            # Bind queue to exchange with routing key
            await self.queue.bind(
                self.exchange,
                routing_key='finance.market.data.updated'
            )

            logger.info("MarketDataConsumer connected to RabbitMQ")
            logger.info("Listening on queue 'knowledge_graph_market_updates'")
            logger.info("Routing key: 'finance.market.data.updated'")

        except Exception as e:
            logger.error(f"Failed to connect MarketDataConsumer: {e}")
            raise

    async def start_consuming(self):
        """Start consuming messages."""
        if not self.queue:
            raise RuntimeError("Consumer not connected. Call connect() first.")

        await self.queue.consume(self._handle_message)
        logger.info("MarketDataConsumer started consuming")

    async def _handle_message(self, message: AbstractIncomingMessage):
        """Handle incoming market data update event."""
        try:
            # Parse message body
            body = json.loads(message.body.decode())
            event_type = body.get("event_type", "unknown")

            logger.info(f"Received {event_type} event for symbol: {body.get('symbol')}")
            logger.debug(f"Message body: {body}")

            # Process market data update
            success = await self.process_market_update(body)

            if success:
                logger.info(f"Successfully synced market data for {body.get('symbol')}")
                await message.ack()
            else:
                logger.error(f"Failed to sync market data for {body.get('symbol')}")
                # Reject and send to DLX (don't requeue to avoid loops)
                await message.reject(requeue=False)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            await message.reject(requeue=False)

        except Exception as e:
            logger.error(f"Error processing market data event: {e}", exc_info=True)

            # Check retry count
            retry_count = message.headers.get("x-retry-count", 0) if message.headers else 0

            if retry_count < 3:
                # Retry with backoff
                await self._retry_message(message, retry_count + 1)
                await message.ack()  # Acknowledge original message before retry
            else:
                logger.error("Max retries exceeded, sending to DLX")
                await message.reject(requeue=False)

    async def _retry_message(self, message: AbstractIncomingMessage, retry_count: int):
        """Republish message with retry count and delay."""
        try:
            # Exponential backoff: 2, 4, 8 seconds
            delay = 2 ** retry_count

            logger.info(f"Retrying message in {delay}s (attempt {retry_count}/3)")

            # Republish with delay
            new_headers = message.headers or {}
            new_headers["x-retry-count"] = retry_count

            new_message = Message(
                body=message.body,
                headers=new_headers,
                expiration=int(delay * 1000)  # Delay in milliseconds
            )

            await self.exchange.publish(
                new_message,
                routing_key='finance.market.data.updated'
            )

        except Exception as e:
            logger.error(f"Failed to retry message: {e}")

    async def process_market_update(self, body: Dict[str, Any]) -> bool:
        """
        Process market data update event.

        Syncs market data to Neo4j using MarketSyncService.

        Args:
            body: Event payload

        Returns:
            True if sync successful, False otherwise
        """
        try:
            symbol = body.get('symbol')
            if not symbol:
                logger.error("Event missing 'symbol' field")
                return False

            # Extract market data from event
            market_data = {
                'symbol': symbol,
                'name': body.get('name'),
                'asset_type': body.get('asset_type'),
                'exchange': body.get('exchange'),
                'currency': body.get('currency'),
                'is_active': body.get('is_active', True)
            }

            # Sync to Neo4j
            result = await self.market_sync_service.sync_single_market(market_data)

            if result:
                logger.info(f"Market {symbol} synced to Neo4j via event")
                return True
            else:
                logger.error(f"Failed to sync market {symbol} to Neo4j")
                return False

        except Exception as e:
            logger.error(f"Error syncing market data: {e}", exc_info=True)
            return False

    async def close(self):
        """Close RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("MarketDataConsumer connection closed")


# Global consumer instance
_consumer: MarketDataConsumer = None


async def get_market_consumer(market_sync_service: MarketSyncService) -> MarketDataConsumer:
    """
    Get global market consumer instance.

    Args:
        market_sync_service: Market sync service instance

    Returns:
        MarketDataConsumer: Shared consumer instance
    """
    global _consumer
    if _consumer is None:
        _consumer = MarketDataConsumer(market_sync_service)
        await _consumer.connect()
    return _consumer


async def close_market_consumer():
    """Close global market consumer instance."""
    global _consumer
    if _consumer:
        await _consumer.close()
        _consumer = None
