"""
Central Constants for OSS Service

Issue #10: Extracts magic numbers and strings to named constants
for better maintainability and readability.
"""

# =============================================================================
# Request/Response Limits
# =============================================================================

# Maximum request body size in bytes (1 MB)
MAX_REQUEST_SIZE_BYTES = 1_000_000

# Maximum records per query result
MAX_QUERY_RESULTS = 50

# Maximum proposals to process in one cycle
MAX_PROPOSALS_PER_CYCLE = 100


# =============================================================================
# Neo4j Query Limits
# =============================================================================

# Default query timeout in seconds
DEFAULT_QUERY_TIMEOUT_SECONDS = 30

# Maximum sample IDs to collect per query
MAX_SAMPLE_IDS = 5

# Maximum duplicate pairs to report
MAX_DUPLICATE_PAIRS = 20

# Maximum entity pattern results
MAX_ENTITY_PATTERNS = 20

# Maximum relationship pattern results
MAX_RELATIONSHIP_PATTERNS = 10


# =============================================================================
# Neo4j Connection Pool
# =============================================================================

# Maximum connection lifetime in seconds (1 hour)
MAX_CONNECTION_LIFETIME = 3600

# Maximum connections in pool
MAX_CONNECTION_POOL_SIZE = 50

# Connection acquisition timeout in seconds
CONNECTION_ACQUISITION_TIMEOUT = 60


# =============================================================================
# Deduplication Cache
# =============================================================================

# How long to remember submitted proposals (hours)
DEDUPLICATION_CACHE_TTL_HOURS = 24

# Maximum entries in deduplication cache
DEDUPLICATION_CACHE_MAX_SIZE = 10000

# Fingerprint hash length (characters)
FINGERPRINT_LENGTH = 32


# =============================================================================
# Retry Queue
# =============================================================================

# Maximum proposals in retry queue
MAX_QUEUE_SIZE = 1000

# Maximum retry attempts per proposal
MAX_RETRIES = 5

# Base retry delay in seconds (doubles each attempt)
BASE_RETRY_DELAY_SECONDS = 60

# Maximum retry delay in seconds (1 hour)
MAX_RETRY_DELAY_SECONDS = 3600


# =============================================================================
# Confidence Calculation
# =============================================================================

# Base confidence for pattern detection
BASE_CONFIDENCE = 0.5

# Maximum confidence score
MAX_CONFIDENCE = 0.95

# Frequency divisor for confidence boost
FREQUENCY_CONFIDENCE_DIVISOR = 100


# =============================================================================
# Data Quality Thresholds
# =============================================================================

# Total entities in graph (for percentage calculations)
# Update this periodically based on graph stats
ESTIMATED_TOTAL_ENTITIES = 46205

# ISO country code expected length
ISO_COUNTRY_CODE_LENGTH = 2

# UUID length for detecting article entities
UUID_LENGTH = 36

# Maximum entity name length
MAX_ENTITY_NAME_LENGTH = 200

# Minimum entity name length
MIN_ENTITY_NAME_LENGTH = 3


# =============================================================================
# API Response Messages
# =============================================================================

class ErrorMessages:
    """
    Issue #9: Standardized, user-friendly error messages.
    """

    # Analysis errors
    ANALYSIS_IN_PROGRESS = (
        "An analysis cycle is already running. "
        "Please wait for it to complete before starting a new one."
    )

    ANALYSIS_FAILED = (
        "The analysis cycle failed unexpectedly. "
        "Check the service logs for details."
    )

    # Rate limiting
    RATE_LIMIT_EXCEEDED = (
        "Rate limit exceeded. Please wait before making more requests. "
        "See the Retry-After header for when you can retry."
    )

    # Request validation
    REQUEST_TOO_LARGE = (
        "Request payload too large. "
        f"Maximum allowed size is {MAX_REQUEST_SIZE_BYTES / 1_000_000:.1f} MB."
    )

    INVALID_CONTENT_TYPE = (
        "Invalid Content-Type header. "
        "This endpoint expects 'application/json'."
    )

    INVALID_JSON = (
        "Invalid JSON in request body. "
        "Please check the JSON syntax and try again."
    )

    # Database errors
    NEO4J_CONNECTION_FAILED = (
        "Unable to connect to the knowledge graph database. "
        "The service may be temporarily unavailable."
    )

    NEO4J_QUERY_TIMEOUT = (
        "Database query timed out. "
        "Try again later or contact support if the issue persists."
    )

    # Proposals API errors
    PROPOSALS_API_UNAVAILABLE = (
        "The Ontology Proposals service is currently unavailable. "
        "Proposals have been queued for automatic retry."
    )

    PROPOSALS_API_REJECTED = (
        "The Ontology Proposals service rejected the submission. "
        "Check the proposal format and try again."
    )

    # Queue errors
    QUEUE_FULL = (
        "The retry queue is full. "
        "Some proposals may be lost. Please investigate and clear the queue."
    )

    # General errors
    INTERNAL_ERROR = (
        "An internal error occurred. "
        "Please try again or contact support if the issue persists."
    )

    SERVICE_UNAVAILABLE = (
        "The service is temporarily unavailable. "
        "Please try again in a few moments."
    )


class SuccessMessages:
    """
    Standardized success messages.
    """

    ANALYSIS_COMPLETED = "Analysis cycle completed successfully."

    CACHE_CLEARED = "Cache cleared successfully."

    QUEUE_CLEARED = "Retry queue cleared successfully."

    PROPOSAL_SUBMITTED = "Proposal submitted successfully."

    RETRY_COMPLETED = "Retry completed successfully."
