"""
Events module for RabbitMQ message handling
"""
from .consumer import get_consumer, close_consumer, NarrativeFrameConsumer

__all__ = ["get_consumer", "close_consumer", "NarrativeFrameConsumer"]
