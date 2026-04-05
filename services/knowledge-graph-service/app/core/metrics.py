"""
Prometheus Metrics for Knowledge Graph Service

Defines all custom metrics for monitoring graph operations,
consumer performance, and query patterns.
"""

from prometheus_client import Counter, Histogram, Gauge

# =============================================================================
# Consumer Metrics - RabbitMQ Event Processing
# =============================================================================

kg_events_consumed_total = Counter(
    'kg_events_consumed_total',
    'Total events consumed from RabbitMQ',
    ['status']  # success, failed
)

kg_consumer_processing_duration = Histogram(
    'kg_consumer_processing_duration_seconds',
    'Time to process a single event (end-to-end)',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

kg_consumer_queue_size = Gauge(
    'kg_consumer_queue_size',
    'Current number of messages in RabbitMQ queue'
)

kg_consumer_triplets_per_event = Histogram(
    'kg_consumer_triplets_per_event',
    'Number of triplets per consumed event',
    buckets=[1, 5, 10, 20, 50, 100]
)

# =============================================================================
# Ingestion Metrics - Neo4j Write Operations
# =============================================================================

kg_ingestion_triplets_total = Counter(
    'kg_ingestion_triplets_total',
    'Total triplets ingested into Neo4j',
    ['status']  # success, failed
)

kg_ingestion_duration_seconds = Histogram(
    'kg_ingestion_duration_seconds',
    'Time to ingest a single triplet',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

kg_ingestion_batch_size = Histogram(
    'kg_ingestion_batch_size',
    'Number of triplets per batch ingestion',
    buckets=[1, 5, 10, 20, 50, 100, 200]
)

kg_nodes_created_total = Counter(
    'kg_nodes_created_total',
    'Total nodes created in Neo4j',
    ['entity_type']  # PERSON, ORGANIZATION, etc.
)

kg_relationships_created_total = Counter(
    'kg_relationships_created_total',
    'Total relationships created in Neo4j',
    ['relationship_type']  # WORKS_FOR, LOCATED_IN, etc.
)

# =============================================================================
# Neo4j Operations Metrics
# =============================================================================

kg_neo4j_operations_total = Counter(
    'kg_neo4j_operations_total',
    'Total Neo4j operations by type',
    ['operation', 'status']  # operation: query/write/read, status: success/error
)

kg_neo4j_operation_duration = Histogram(
    'kg_neo4j_operation_duration_seconds',
    'Neo4j operation duration',
    ['operation'],  # query, write, read
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

kg_neo4j_connection_pool_size = Gauge(
    'kg_neo4j_connection_pool_size',
    'Current Neo4j connection pool size'
)

kg_neo4j_errors_total = Counter(
    'kg_neo4j_errors_total',
    'Total Neo4j errors by type',
    ['error_type']  # connection, query, timeout, etc.
)

# =============================================================================
# Graph Statistics Metrics
# =============================================================================

kg_graph_nodes_total = Gauge(
    'kg_graph_nodes_total',
    'Total number of nodes in graph'
)

kg_graph_relationships_total = Gauge(
    'kg_graph_relationships_total',
    'Total number of relationships in graph'
)

kg_graph_entity_types_total = Gauge(
    'kg_graph_entity_types_total',
    'Number of nodes by entity type',
    ['entity_type']  # PERSON, ORGANIZATION, etc.
)

# =============================================================================
# Query Performance Metrics
# =============================================================================

kg_queries_total = Counter(
    'kg_queries_total',
    'Total graph queries by endpoint',
    ['endpoint', 'status']  # endpoint: connections/stats, status: success/error
)

kg_query_duration_seconds = Histogram(
    'kg_query_duration_seconds',
    'Graph query response time',
    ['endpoint'],  # connections, stats
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

kg_query_results_size = Histogram(
    'kg_query_results_size',
    'Number of results returned per query',
    ['endpoint'],
    buckets=[1, 10, 50, 100, 500, 1000]
)

# =============================================================================
# System Health Metrics
# =============================================================================

kg_health_status = Gauge(
    'kg_health_status',
    'Service health status (1=healthy, 0=unhealthy)',
    ['component']  # overall, neo4j, rabbitmq, consumer
)

kg_uptime_seconds = Gauge(
    'kg_uptime_seconds',
    'Service uptime in seconds'
)
