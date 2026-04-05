"""
Pydantic schemas for the Feed Service
"""

from .feed import (
    FeedCreate,
    FeedUpdate,
    FeedResponse,
    FeedItemResponse,
    FeedItemWithFeedResponse,
    FeedItemUpdate,
    FetchLogResponse,
    FeedHealthResponse,
    FeedQualityResponse,
    FeedQualityV2Response,
    ComponentScoreDetails,
    QualityTrends,
    QualityDataStats,
    BulkFetchRequest,
    BulkFetchResponse,
    ResearchArticleCreate,
    AnalysisTriggerResponse,
    # Epic 0.4: Article Update schemas
    ArticleUpdateRequest,
    ArticleVersionResponse,
)
from .review import (
    # Review queue schemas (HITL workflow)
    ReviewStatus,
    ReviewDecision,
    RiskLevel,
    ReviewItemCreate,
    ReviewItemResponse,
    ReviewDecisionRequest,
    ReviewQueueListResponse,
    ReviewStatsResponse,
)
from .source import (
    # Source schemas
    SourceCreate,
    SourceUpdate,
    SourceResponse,
    SourceListResponse,
    SourceAssessmentData,
    ScrapeConfigData,
    ScrapeMetricsData,
    SourceFilters,
    # SourceFeed schemas
    SourceFeedCreate,
    SourceFeedUpdate,
    SourceFeedResponse,
    SourceFeedWithSourceResponse,
    SourceFeedListResponse,
    SourceFeedSummary,
    SourceFeedFilters,
    # Assessment schemas
    SourceAssessmentTrigger,
    SourceAssessmentTriggerResponse,
    SourceAssessmentHistoryResponse,
    # Bulk operations
    BulkSourceCreate,
    BulkSourceCreateResponse,
    MediaStackSourceImport,
    MediaStackSourceImportResponse,
    # Helper functions
    extract_domain,
)

__all__ = [
    # Feed schemas
    "FeedCreate",
    "FeedUpdate",
    "FeedResponse",
    "FeedItemResponse",
    "FeedItemWithFeedResponse",
    "FeedItemUpdate",
    "FetchLogResponse",
    "FeedHealthResponse",
    "FeedQualityResponse",
    "FeedQualityV2Response",
    "ComponentScoreDetails",
    "QualityTrends",
    "QualityDataStats",
    "BulkFetchRequest",
    "BulkFetchResponse",
    "ResearchArticleCreate",
    "AnalysisTriggerResponse",
    # Epic 0.4: Article Update schemas
    "ArticleUpdateRequest",
    "ArticleVersionResponse",
    # Source schemas
    "SourceCreate",
    "SourceUpdate",
    "SourceResponse",
    "SourceListResponse",
    "SourceAssessmentData",
    "ScrapeConfigData",
    "ScrapeMetricsData",
    "SourceFilters",
    # SourceFeed schemas
    "SourceFeedCreate",
    "SourceFeedUpdate",
    "SourceFeedResponse",
    "SourceFeedWithSourceResponse",
    "SourceFeedListResponse",
    "SourceFeedSummary",
    "SourceFeedFilters",
    # Assessment schemas
    "SourceAssessmentTrigger",
    "SourceAssessmentTriggerResponse",
    "SourceAssessmentHistoryResponse",
    # Bulk operations
    "BulkSourceCreate",
    "BulkSourceCreateResponse",
    "MediaStackSourceImport",
    "MediaStackSourceImportResponse",
    # Helper functions
    "extract_domain",
    # Review queue schemas (HITL workflow)
    "ReviewStatus",
    "ReviewDecision",
    "RiskLevel",
    "ReviewItemCreate",
    "ReviewItemResponse",
    "ReviewDecisionRequest",
    "ReviewQueueListResponse",
    "ReviewStatsResponse",
]