"""Database models."""

from app.models.cluster import ArticleCluster, Base, ClusterMembership
from app.models.burst_alert import BurstAlert
from app.models.batch_cluster import (
    ClusterBatch,
    BatchCluster,
    BatchArticleCluster,
    ClusterFeedback,
)
from app.models.escalation import (
    EscalationAnchor,
    EscalationDomain,
    FMPNewsCorrelation,
    CorrelationType,
    FMPRegime,
)

__all__ = [
    # Existing models (Single-Pass Clustering)
    "ArticleCluster",
    "Base",
    "ClusterMembership",
    "BurstAlert",
    # Batch clustering models (UMAP+HDBSCAN)
    "ClusterBatch",
    "BatchCluster",
    "BatchArticleCluster",
    "ClusterFeedback",
    # Escalation models (Intelligence Interpretation Layer)
    "EscalationAnchor",
    "EscalationDomain",
    "FMPNewsCorrelation",
    "CorrelationType",
    "FMPRegime",
]
