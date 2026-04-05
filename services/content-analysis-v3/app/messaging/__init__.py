"""
RabbitMQ Messaging for Content-Analysis-V3

Provides both consumer and publisher for event-driven analysis:
- Consumer: Receives analysis requests from other services
- Publisher: Publishes completion/failure events
"""
from app.messaging.event_publisher import get_event_publisher, close_event_publisher
from app.messaging.request_consumer import AnalysisRequestConsumer

__all__ = [
    "get_event_publisher",
    "close_event_publisher",
    "AnalysisRequestConsumer",
]
