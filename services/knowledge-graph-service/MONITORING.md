# Knowledge Graph Service - Monitoring

**Implementiert:** 2025-10-24
**Version:** 1.0.0

## Überblick

Der Knowledge Graph Service verfügt über umfassendes Monitoring mit Prometheus Metrics und Enhanced Health Checks für Production-Ready Deployment.

---

## 📊 Prometheus Metrics

**Endpoint:** `http://localhost:8111/metrics/`

### Consumer Metrics

Überwachung des RabbitMQ Event-Consumers:

```prometheus
# Events verarbeitet (success/failed)
kg_events_consumed_total{status="success"}

# Event-Verarbeitungszeit (End-to-End)
kg_consumer_processing_duration_seconds_bucket{le="0.1"}

# Aktuelle Queue-Größe
kg_consumer_queue_size

# Triplets pro Event
kg_consumer_triplets_per_event_bucket{le="1.0"}
```

**Typische Werte:**
- Verarbeitungszeit: 0.09s pro Event
- Triplets pro Event: 1-20 (Median: 5)
- Queue-Größe: 0 (alle Events sofort verarbeitet)

### Ingestion Metrics

Überwachung der Neo4j Ingestion-Performance:

```prometheus
# Triplets eingefügt (success/failed)
kg_ingestion_triplets_total{status="success"}

# Ingestion-Dauer pro Triplet
kg_ingestion_duration_seconds_bucket{le="0.1"}

# Batch-Größe
kg_ingestion_batch_size_bucket{le="10.0"}

# Erstellte Nodes pro Entity-Typ
kg_nodes_created_total{entity_type="PERSON"}

# Erstellte Relationships pro Typ
kg_relationships_created_total{relationship_type="WORKS_FOR"}
```

**Typische Werte:**
- Ingestion-Dauer: 0.05-0.10s pro Triplet
- Batch-Größe: 1-20 Triplets
- Success Rate: >99%

### Graph Statistics

Live-Statistiken des Knowledge Graphs:

```prometheus
# Gesamtanzahl Nodes
kg_graph_nodes_total 3560

# Gesamtanzahl Relationships
kg_graph_relationships_total 4074

# Nodes pro Entity-Typ
kg_graph_entity_types_total{entity_type="PERSON"} 1061
kg_graph_entity_types_total{entity_type="ORGANIZATION"} 1003
kg_graph_entity_types_total{entity_type="LOCATION"} 609
```

**Wird aktualisiert durch:** `/api/v1/graph/stats` Endpoint-Aufruf

### Query Performance

Überwachung der Graph Query Performance:

```prometheus
# Queries ausgeführt (connections/stats, success/error)
kg_queries_total{endpoint="connections",status="success"}

# Query-Antwortzeit
kg_query_duration_seconds_bucket{endpoint="connections",le="0.1"}

# Ergebnis-Größe
kg_query_results_size_bucket{endpoint="connections",le="50.0"}
```

**Typische Werte:**
- Query Duration: 10-100ms
- Ergebnisse: 10-100 Nodes/Edges
- Success Rate: >99%

### Neo4j Operations

Neo4j Operation-Metriken:

```prometheus
# Operationen (query/write/read, success/error)
kg_neo4j_operations_total{operation="write",status="success"}

# Operation-Dauer
kg_neo4j_operation_duration_seconds{operation="write"}

# Connection Pool Größe
kg_neo4j_connection_pool_size

# Fehler
kg_neo4j_errors_total{error_type="connection"}
```

### System Health

Komponenten-Gesundheit:

```prometheus
# 1=healthy, 0=unhealthy
kg_health_status{component="neo4j"} 1
kg_health_status{component="rabbitmq"} 1
kg_health_status{component="consumer"} 1
kg_health_status{component="overall"} 1

# Uptime in Sekunden
kg_uptime_seconds 3600
```

---

## 🏥 Health Check Endpoints

### Basic Health Check

**Endpoint:** `GET /health`

Einfacher Health Check für Load Balancer:

```bash
curl http://localhost:8111/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "knowledge-graph-service",
  "version": "1.0.0",
  "timestamp": "2025-10-24T16:00:00.000000"
}
```

### Liveness Probe

**Endpoint:** `GET /health/live`

Kubernetes Liveness Probe (Container-Neustart bei Fehler):

```bash
curl http://localhost:8111/health/live
```

**Response (200 OK):**
```json
{
  "status": "alive",
  "service": "knowledge-graph-service"
}
```

**Zweck:** Prüft ob der Prozess läuft

### Readiness Probe

**Endpoint:** `GET /health/ready`

Kubernetes Readiness Probe (Traffic Routing):

```bash
curl http://localhost:8111/health/ready
```

**Response (200 OK):**
```json
{
  "status": "ready",
  "checks": {
    "neo4j": "healthy",
    "rabbitmq_consumer": "healthy"
  },
  "service": "knowledge-graph-service"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "not_ready",
  "checks": {
    "neo4j": "unhealthy",
    "rabbitmq_consumer": "not_connected"
  },
  "message": "Service dependencies are not healthy"
}
```

**Zweck:** Prüft ob Service bereit ist Traffic zu empfangen

### Neo4j Health

**Endpoint:** `GET /health/neo4j`

Detaillierter Neo4j Status:

```bash
curl http://localhost:8111/health/neo4j
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "connected": true,
  "version": "5.25.1",
  "edition": "community",
  "host": "bolt://neo4j:7687"
}
```

### RabbitMQ Health

**Endpoint:** `GET /health/rabbitmq`

Detaillierter RabbitMQ Consumer Status:

```bash
curl http://localhost:8111/health/rabbitmq
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "connection": "open",
  "channel": "open",
  "exchange": "news.events",
  "queue": {
    "name": "knowledge_graph_relationships",
    "message_count": 0,
    "consumer_count": 1
  },
  "routing_key": "analysis.relationships.extracted"
}
```

---

## 📈 Monitoring Best Practices

### Alerting Rules

Empfohlene Prometheus Alerts:

```yaml
groups:
  - name: knowledge_graph_alerts
    rules:
      # Consumer stopped
      - alert: KGConsumerStopped
        expr: increase(kg_events_consumed_total[5m]) == 0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Knowledge Graph consumer has stopped processing events"

      # High error rate
      - alert: KGHighErrorRate
        expr: rate(kg_events_consumed_total{status="failed"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Knowledge Graph has high event processing error rate"

      # Slow ingestion
      - alert: KGSlowIngestion
        expr: rate(kg_ingestion_duration_seconds_sum[5m]) / rate(kg_ingestion_duration_seconds_count[5m]) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Knowledge Graph ingestion is slow (>500ms per triplet)"

      # Neo4j disconnected
      - alert: KGNeo4jDown
        expr: kg_health_status{component="neo4j"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Knowledge Graph cannot connect to Neo4j"

      # RabbitMQ disconnected
      - alert: KGRabbitMQDown
        expr: kg_health_status{component="rabbitmq"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Knowledge Graph cannot connect to RabbitMQ"

      # Large queue backlog
      - alert: KGQueueBacklog
        expr: kg_consumer_queue_size > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Knowledge Graph queue has large backlog (>100 messages)"
```

### Dashboard Queries

Empfohlene Grafana/Prometheus Queries:

**Event Processing Rate:**
```promql
rate(kg_events_consumed_total{status="success"}[5m])
```

**Average Processing Time:**
```promql
rate(kg_consumer_processing_duration_seconds_sum[5m]) / rate(kg_consumer_processing_duration_seconds_count[5m])
```

**Error Rate:**
```promql
rate(kg_events_consumed_total{status="failed"}[5m]) / rate(kg_events_consumed_total[5m]) * 100
```

**Graph Growth Rate:**
```promql
rate(kg_graph_nodes_total[1h])
```

**Query Latency (p95):**
```promql
histogram_quantile(0.95, rate(kg_query_duration_seconds_bucket[5m]))
```

### Monitoring Checklist

- [ ] Prometheus scraping configured
- [ ] Alerts configured in Alertmanager
- [ ] Grafana dashboards created
- [ ] Log aggregation configured
- [ ] Health checks configured in Kubernetes
- [ ] Uptime monitoring configured
- [ ] Performance baseline established

---

## 🔍 Debugging mit Metrics

### Consumer Probleme

```bash
# Prüfe Consumer Status
curl http://localhost:8111/health/rabbitmq | jq .

# Prüfe Event Processing Rate
curl http://localhost:8111/metrics/ | grep kg_events_consumed_total

# Prüfe Queue Backlog
curl http://localhost:8111/metrics/ | grep kg_consumer_queue_size
```

### Performance Probleme

```bash
# Prüfe Ingestion Performance
curl http://localhost:8111/metrics/ | grep kg_ingestion_duration

# Prüfe Query Performance
curl http://localhost:8111/metrics/ | grep kg_query_duration

# Prüfe Neo4j Operations
curl http://localhost:8111/metrics/ | grep kg_neo4j_operation_duration
```

### Graph Statistiken

```bash
# Aktualisiere Graph Stats
curl http://localhost:8111/api/v1/graph/stats

# Prüfe Graph Größe
curl http://localhost:8111/metrics/ | grep "kg_graph_nodes_total\|kg_graph_relationships_total"

# Prüfe Entity-Verteilung
curl http://localhost:8111/metrics/ | grep kg_graph_entity_types_total
```

---

## 📊 Performance Benchmarks

### Baseline Performance

**Getestet:** 2025-10-24
**System:** Development Environment

- **Consumer Throughput:** 22.8 articles/second (Backfill)
- **Event Processing:** ~90ms pro Event (1-5 Triplets)
- **Triplet Ingestion:** ~50-100ms pro Triplet
- **Query Latency:** 10-100ms (10-100 Ergebnisse)
- **Memory Usage:** ~94MB resident

### Scaling Characteristics

- **Linear Scaling:** Ja (bis 100 concurrent consumers)
- **Bottleneck:** Neo4j Write Operations
- **Optimization Potential:** Batch-MERGE Queries
- **Max Throughput:** ~50 events/second (single consumer)

---

## 🚨 Troubleshooting

### Metrics nicht sichtbar

**Problem:** `/metrics` Endpoint gibt nichts zurück

**Lösung:**
```bash
# Verwende trailing slash
curl http://localhost:8111/metrics/
```

### Health Checks fehlerhaft

**Problem:** `/health/ready` gibt 503

**Schritte:**
1. Prüfe Neo4j: `curl http://localhost:8111/health/neo4j`
2. Prüfe RabbitMQ: `curl http://localhost:8111/health/rabbitmq`
3. Prüfe Service Logs: `docker logs news-knowledge-graph-service`

### Slow Queries

**Problem:** Hohe Query Latenz

**Schritte:**
1. Prüfe Neo4j Indexes: Siehe `neo4j_service.py:_create_indexes()`
2. Prüfe Query Complexity: Limitiere Results (`?limit=100`)
3. Prüfe Graph Größe: `curl http://localhost:8111/api/v1/graph/stats`

---

## 📝 Maintenance

### Metrics Retention

- **Prometheus:** 15 Tage (Standard)
- **Empfohlen:** 30-90 Tage für Trend-Analyse

### Monitoring Updates

Bei Code-Änderungen:
1. Aktualisiere Metrics in `app/core/metrics.py`
2. Integriere Metrics in relevante Services
3. Aktualisiere Dokumentation
4. Teste Metrics Endpoint
5. Update Dashboards

---

## 🔗 Weitere Ressourcen

- **Prometheus Best Practices:** https://prometheus.io/docs/practices/
- **Neo4j Monitoring:** https://neo4j.com/docs/operations-manual/current/monitoring/
- **FastAPI Monitoring:** https://fastapi.tiangolo.com/advanced/monitoring/
- **Grafana Dashboards:** https://grafana.com/grafana/dashboards/
