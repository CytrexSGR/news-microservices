"""
Database models for the Feed Service
"""

from .feed import (
    Base,
    Feed,
    FeedItem,
    FetchLog,
    FeedHealth,
    FeedCategory,
    FeedSchedule,
    FeedStatus,
    FeedAssessmentHistory,
    SourceType,
)
from .admiralty_code import (
    AdmiraltyCodeThreshold,
    QualityScoreWeight,
)
from .source import (
    Source,
    SourceFeed,
    SourceAssessmentHistory,
    SourceStatus,
    ScrapeStatus,
    PaywallType,
    ProviderType,
    CredibilityTier,
    AssessmentStatus,
)
from .crawl_session import CrawlSession
from .intelligence import (
    ArticleCluster,
    ArticleVersion,
    PublicationReviewQueue,
    SitrepReport,
)

__all__ = [
    # Base
    "Base",
    # Feed models
    "Feed",
    "FeedItem",
    "FetchLog",
    "FeedHealth",
    "FeedCategory",
    "FeedSchedule",
    "FeedStatus",
    "FeedAssessmentHistory",
    "SourceType",
    # Source models (new unified management)
    "Source",
    "SourceFeed",
    "SourceAssessmentHistory",
    # Source enums
    "SourceStatus",
    "ScrapeStatus",
    "PaywallType",
    "ProviderType",
    "CredibilityTier",
    "AssessmentStatus",
    # Admiralty code
    "AdmiraltyCodeThreshold",
    "QualityScoreWeight",
    # Crawl session
    "CrawlSession",
    # Intelligence models (News Intelligence features)
    "ArticleCluster",
    "ArticleVersion",
    "PublicationReviewQueue",
    "SitrepReport",
]