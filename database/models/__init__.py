"""
Central database models for all microservices.

This module consolidates all database models across the microservices
architecture to ensure consistency and avoid duplication.
"""

from .base import Base, TimestampMixin, get_db, get_db_session
from .auth import User, Role, UserRole, APIKey, AuthAuditLog
from .scheduler import FeedScheduleState, AnalysisJobQueue, JobType, JobStatus
from .analysis import (
    # Main models
    AnalysisResult,
    CategoryClassification,
    SentimentAnalysis,
    FinanceSentiment,
    GeopoliticalSentiment,
    ExtractedEntity,
    EntityRelationship,
    TopicClassification,
    Summary,
    ExtractedFact,
    AnalysisModel,
    AnalysisTemplate,
    AnalysisCache,
    ContentEmbedding,
    AnalysisMetric,
    ModelUsageStat,
    # Enums
    AnalysisType,
    AnalysisStatus,
    SentimentLabel,
    BiasDirection,
    MarketSentiment,
    TimeHorizon,
    ConflictType,
    EntityType,
    RelationshipType,
    SummaryType,
    FactType,
    VerificationStatus,
    ArticleCategory,
    ModelProvider,
)
from .event_analysis import EventAnalysis

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "get_db",
    "get_db_session",
    # Auth models
    "User",
    "Role",
    "UserRole",
    "APIKey",
    "AuthAuditLog",
    # Scheduler models
    "FeedScheduleState",
    "AnalysisJobQueue",
    "JobType",
    "JobStatus",
    # Analysis models
    "AnalysisResult",
    "CategoryClassification",
    "SentimentAnalysis",
    "FinanceSentiment",
    "GeopoliticalSentiment",
    "ExtractedEntity",
    "EntityRelationship",
    "TopicClassification",
    "Summary",
    "ExtractedFact",
    "AnalysisModel",
    "AnalysisTemplate",
    "AnalysisCache",
    "ContentEmbedding",
    "AnalysisMetric",
    "ModelUsageStat",
    "EventAnalysis",
    # Enums
    "AnalysisType",
    "AnalysisStatus",
    "SentimentLabel",
    "BiasDirection",
    "MarketSentiment",
    "TimeHorizon",
    "ConflictType",
    "EntityType",
    "RelationshipType",
    "SummaryType",
    "FactType",
    "VerificationStatus",
    "ArticleCategory",
    "ModelProvider",
]
