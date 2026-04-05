"""Services module."""

from app.services.clustering import ClusteringService
from app.services.cluster_repository import ClusterRepository
from app.services.batch_cluster_repository import BatchClusterRepository
from app.services.event_publisher import (
    ClusterEventPublisher,
    close_event_publisher,
    get_event_publisher,
)
from app.services.escalation_calculator import (
    EscalationCalculator,
    EscalationSignal,
    DomainEscalation,
    EscalationResult,
)
from app.services.fmp_correlation_service import (
    FMPCorrelationService,
    RegimeState,
    CorrelationAlert,
)

__all__ = [
    # Clustering services
    "ClusteringService",
    "ClusterRepository",
    "BatchClusterRepository",
    # Event publishing
    "ClusterEventPublisher",
    "get_event_publisher",
    "close_event_publisher",
    # Escalation calculation (Intelligence Interpretation Layer)
    "EscalationCalculator",
    "EscalationSignal",
    "DomainEscalation",
    "EscalationResult",
    # FMP Correlation (Intelligence Interpretation Layer)
    "FMPCorrelationService",
    "RegimeState",
    "CorrelationAlert",
]
