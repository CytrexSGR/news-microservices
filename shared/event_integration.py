"""
Event Integration Helpers
Provides ready-to-use integration for all microservices
"""

import os
from typing import Dict, Any, Optional
from .event_publisher import EventPublisher, get_event_publisher
from .event_consumer import MultiEventConsumer, create_consumer


# Event type constants
class EventTypes:
    """Event type constants"""
    ARTICLE_CREATED = "article.created"
    ARTICLE_UPDATED = "article.updated"
    ANALYSIS_COMPLETED = "analysis.completed"
    RESEARCH_COMPLETED = "research.completed"
    ALERT_TRIGGERED = "alert.triggered"
    NOTIFICATION_SENT = "notification.sent"
    USER_REGISTERED = "user.registered"
    SEARCH_EXECUTED = "search.executed"


# Queue names
class QueueNames:
    """Queue name constants"""
    CONTENT_ANALYSIS_ARTICLES = "content-analysis.articles"
    SEARCH_ARTICLES = "search.articles"
    RESEARCH_ANALYSIS = "research.analysis"
    OSINT_INTELLIGENCE = "osint.intelligence"
    NOTIFICATION_ALERTS = "notification.alerts"
    ANALYTICS_ALL = "analytics.all"


# Service-specific integrations

class FeedServiceEvents:
    """Event integration for Feed Service"""

    @staticmethod
    def get_publisher(rabbitmq_url: Optional[str] = None) -> EventPublisher:
        """Get publisher for Feed Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return get_event_publisher(url, service_name="feed-service")

    @staticmethod
    async def publish_article_created(
        publisher: EventPublisher,
        article_id: str,
        feed_id: str,
        title: str,
        url: str,
        content: str,
        author: Optional[str] = None,
        published_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish article.created event"""
        data = {
            "article_id": article_id,
            "feed_id": feed_id,
            "title": title,
            "url": url,
            "content": content,
            "author": author,
            "published_at": published_at,
            "metadata": metadata,
        }
        return await publisher.publish(
            EventTypes.ARTICLE_CREATED,
            data,
            correlation_id=correlation_id,
        )

    @staticmethod
    async def publish_article_updated(
        publisher: EventPublisher,
        article_id: str,
        feed_id: str,
        changes: Dict[str, Any],
        updated_at: str,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish article.updated event"""
        data = {
            "article_id": article_id,
            "feed_id": feed_id,
            "changes": changes,
            "updated_at": updated_at,
        }
        return await publisher.publish(
            EventTypes.ARTICLE_UPDATED,
            data,
            correlation_id=correlation_id,
        )


class ContentAnalysisServiceEvents:
    """Event integration for Content Analysis Service"""

    @staticmethod
    def get_publisher(rabbitmq_url: Optional[str] = None) -> EventPublisher:
        """Get publisher for Content Analysis Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return get_event_publisher(url, service_name="content-analysis-service")

    @staticmethod
    async def create_consumer(
        rabbitmq_url: Optional[str] = None,
        handlers: Optional[Dict[str, Any]] = None,
    ) -> MultiEventConsumer:
        """Create consumer for Content Analysis Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return await create_consumer(
            rabbitmq_url=url,
            queue_name=QueueNames.CONTENT_ANALYSIS_ARTICLES,
            routing_keys=["article.created"],
            handlers=handlers or {},
            service_name="content-analysis-service",
        )

    @staticmethod
    async def publish_analysis_completed(
        publisher: EventPublisher,
        article_id: str,
        analysis_id: str,
        sentiment: Dict[str, Any],
        entities: list,
        topics: list,
        keywords: list,
        summary: str,
        language: str,
        processing_time_ms: int,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish analysis.completed event"""
        data = {
            "article_id": article_id,
            "analysis_id": analysis_id,
            "sentiment": sentiment,
            "entities": entities,
            "topics": topics,
            "keywords": keywords,
            "summary": summary,
            "language": language,
            "processing_time_ms": processing_time_ms,
        }
        return await publisher.publish(
            EventTypes.ANALYSIS_COMPLETED,
            data,
            correlation_id=correlation_id,
        )


class ResearchServiceEvents:
    """Event integration for Research Service"""

    @staticmethod
    def get_publisher(rabbitmq_url: Optional[str] = None) -> EventPublisher:
        """Get publisher for Research Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return get_event_publisher(url, service_name="research-service")

    @staticmethod
    async def create_consumer(
        rabbitmq_url: Optional[str] = None,
        handlers: Optional[Dict[str, Any]] = None,
    ) -> MultiEventConsumer:
        """Create consumer for Research Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return await create_consumer(
            rabbitmq_url=url,
            queue_name=QueueNames.RESEARCH_ANALYSIS,
            routing_keys=["analysis.completed"],
            handlers=handlers or {},
            service_name="research-service",
        )

    @staticmethod
    async def publish_research_completed(
        publisher: EventPublisher,
        research_id: str,
        article_id: Optional[str],
        query: str,
        results: list,
        sources_count: int,
        confidence_score: float,
        processing_time_ms: int,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish research.completed event"""
        data = {
            "research_id": research_id,
            "article_id": article_id,
            "query": query,
            "results": results,
            "sources_count": sources_count,
            "confidence_score": confidence_score,
            "processing_time_ms": processing_time_ms,
        }
        return await publisher.publish(
            EventTypes.RESEARCH_COMPLETED,
            data,
            correlation_id=correlation_id,
        )


class OSINTServiceEvents:
    """Event integration for OSINT Service"""

    @staticmethod
    def get_publisher(rabbitmq_url: Optional[str] = None) -> EventPublisher:
        """Get publisher for OSINT Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return get_event_publisher(url, service_name="osint-service")

    @staticmethod
    async def create_consumer(
        rabbitmq_url: Optional[str] = None,
        handlers: Optional[Dict[str, Any]] = None,
    ) -> MultiEventConsumer:
        """Create consumer for OSINT Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return await create_consumer(
            rabbitmq_url=url,
            queue_name=QueueNames.OSINT_INTELLIGENCE,
            routing_keys=["analysis.completed", "research.completed"],
            handlers=handlers or {},
            service_name="osint-service",
        )

    @staticmethod
    async def publish_alert_triggered(
        publisher: EventPublisher,
        alert_id: str,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        indicators: list,
        confidence_score: float,
        recommended_actions: list,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish alert.triggered event"""
        data = {
            "alert_id": alert_id,
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "description": description,
            "indicators": indicators,
            "confidence_score": confidence_score,
            "recommended_actions": recommended_actions,
        }
        return await publisher.publish(
            EventTypes.ALERT_TRIGGERED,
            data,
            correlation_id=correlation_id,
        )


class NotificationServiceEvents:
    """Event integration for Notification Service"""

    @staticmethod
    def get_publisher(rabbitmq_url: Optional[str] = None) -> EventPublisher:
        """Get publisher for Notification Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return get_event_publisher(url, service_name="notification-service")

    @staticmethod
    async def create_consumer(
        rabbitmq_url: Optional[str] = None,
        handlers: Optional[Dict[str, Any]] = None,
    ) -> MultiEventConsumer:
        """Create consumer for Notification Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return await create_consumer(
            rabbitmq_url=url,
            queue_name=QueueNames.NOTIFICATION_ALERTS,
            routing_keys=["alert.triggered"],
            handlers=handlers or {},
            service_name="notification-service",
        )

    @staticmethod
    async def publish_notification_sent(
        publisher: EventPublisher,
        notification_id: str,
        user_id: str,
        channel: str,
        alert_id: Optional[str],
        status: str,
        sent_at: str,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish notification.sent event"""
        data = {
            "notification_id": notification_id,
            "user_id": user_id,
            "channel": channel,
            "alert_id": alert_id,
            "status": status,
            "sent_at": sent_at,
        }
        return await publisher.publish(
            EventTypes.NOTIFICATION_SENT,
            data,
            correlation_id=correlation_id,
        )


class SearchServiceEvents:
    """Event integration for Search Service"""

    @staticmethod
    def get_publisher(rabbitmq_url: Optional[str] = None) -> EventPublisher:
        """Get publisher for Search Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return get_event_publisher(url, service_name="search-service")

    @staticmethod
    async def create_consumer(
        rabbitmq_url: Optional[str] = None,
        handlers: Optional[Dict[str, Any]] = None,
    ) -> MultiEventConsumer:
        """Create consumer for Search Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return await create_consumer(
            rabbitmq_url=url,
            queue_name=QueueNames.SEARCH_ARTICLES,
            routing_keys=["article.created", "article.updated"],
            handlers=handlers or {},
            service_name="search-service",
        )

    @staticmethod
    async def publish_search_executed(
        publisher: EventPublisher,
        search_id: str,
        user_id: Optional[str],
        query: str,
        filters: Dict[str, Any],
        results_count: int,
        execution_time_ms: int,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish search.executed event"""
        data = {
            "search_id": search_id,
            "user_id": user_id,
            "query": query,
            "filters": filters,
            "results_count": results_count,
            "execution_time_ms": execution_time_ms,
        }
        return await publisher.publish(
            EventTypes.SEARCH_EXECUTED,
            data,
            correlation_id=correlation_id,
        )


class AnalyticsServiceEvents:
    """Event integration for Analytics Service"""

    @staticmethod
    async def create_consumer(
        rabbitmq_url: Optional[str] = None,
        handlers: Optional[Dict[str, Any]] = None,
    ) -> MultiEventConsumer:
        """Create consumer for Analytics Service (subscribes to all events)"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return await create_consumer(
            rabbitmq_url=url,
            queue_name=QueueNames.ANALYTICS_ALL,
            routing_keys=["#"],  # Subscribe to all events
            handlers=handlers or {},
            service_name="analytics-service",
        )


class AuthServiceEvents:
    """Event integration for Auth Service"""

    @staticmethod
    def get_publisher(rabbitmq_url: Optional[str] = None) -> EventPublisher:
        """Get publisher for Auth Service"""
        url = rabbitmq_url or os.getenv("RABBITMQ_URL")
        return get_event_publisher(url, service_name="auth-service")

    @staticmethod
    async def publish_user_registered(
        publisher: EventPublisher,
        user_id: str,
        email: str,
        username: str,
        role: str,
        registered_at: str,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """Publish user.registered event"""
        data = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "role": role,
            "registered_at": registered_at,
        }
        return await publisher.publish(
            EventTypes.USER_REGISTERED,
            data,
            correlation_id=correlation_id,
        )
