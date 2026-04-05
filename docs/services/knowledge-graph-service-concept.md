# Knowledge Graph Service - Technical Concept
**Version:** 1.0
**Date:** 2025-10-24
**Status:** 🎯 Ready for Implementation

---

## Executive Summary

The **knowledge-graph-service** is a new microservice that will serve as the **central persistent memory** of our news analysis platform. It ingests relationship triplets `[Subject, Relationship, Object]` extracted by the `content-analysis-service`, stores them in a graph database (Neo4j), and provides a powerful query API for our LLM orchestrator agent.

**Key Benefits:**
- 📊 **Networked Knowledge:** Entities connected through semantic relationships
- 🔍 **Complex Queries:** Multi-hop graph traversal for deep insights
- 🤖 **Agent Integration:** RESTful API as a tool for our LLM orchestrator
- 🚀 **Scalability:** Purpose-built graph database optimized for connected data
- 🔄 **Event-Driven:** Asynchronous ingestion via RabbitMQ

---

## 1. Architectural Integration

### 1.1 System Architecture Diagram

```mermaid
graph TB
    subgraph "Content Analysis Pipeline"
        FeedService[Feed Service<br/>Port 8101]
        ContentAnalysis[Content Analysis Service<br/>Port 8102<br/>PostgreSQL]
    end

    subgraph "Event Bus"
        RabbitMQ[RabbitMQ<br/>Port 5672]
    end

    subgraph "Knowledge Graph Layer (NEW)"
        KGService[Knowledge Graph Service<br/>Port 8109<br/>FastAPI]
        Neo4j[(Neo4j Graph DB<br/>Port 7687)]
    end

    subgraph "AI Orchestration"
        LLMOrchestrator[LLM Orchestrator Agent<br/>Port 8110]
    end

    subgraph "Client Applications"
        Frontend[Analytics Frontend<br/>Port 5173]
    end

    %% Data Flow: Analysis → Event → Graph
    FeedService -->|article.created| RabbitMQ
    RabbitMQ -->|article.created| ContentAnalysis
    ContentAnalysis -->|relationships.extracted<br/>NEW EVENT| RabbitMQ
    RabbitMQ -->|relationships.extracted| KGService
    KGService -->|MERGE Cypher| Neo4j

    %% Query Flow: Agent → Graph → Response
    LLMOrchestrator -->|GET /graph/entity/{name}/connections<br/>POST /graph/query| KGService
    KGService -->|Cypher Query| Neo4j
    Neo4j -->|Graph Data| KGService
    KGService -->|JSON Response| LLMOrchestrator

    %% Frontend Integration
    Frontend -->|Future: Graph Visualization| KGService

    style KGService fill:#00ff00,stroke:#333,stroke-width:4px
    style Neo4j fill:#00ff00,stroke:#333,stroke-width:4px
```

### 1.2 Data Flow Sequences

#### Sequence 1: Relationship Ingestion (Event-Driven)

```mermaid
sequenceDiagram
    participant CA as Content Analysis Service
    participant MQ as RabbitMQ
    participant KG as Knowledge Graph Service
    participant Neo as Neo4j Database

    Note over CA: Article analyzed,<br/>relationships extracted

    CA->>MQ: Publish "relationships.extracted" event<br/>{article_id, triplets[...]}

    MQ->>KG: Deliver event to consumer

    loop For each triplet
        KG->>KG: Validate triplet structure
        KG->>Neo: MERGE entity1 (create if not exists)
        KG->>Neo: MERGE entity2 (create if not exists)
        KG->>Neo: MERGE relationship<br/>(create or update metadata)
    end

    KG->>MQ: ACK message

    Note over Neo: Knowledge graph updated,<br/>ready for queries
```

#### Sequence 2: Agent Query Execution

```mermaid
sequenceDiagram
    participant Agent as LLM Orchestrator Agent
    participant KG as Knowledge Graph Service
    participant Neo as Neo4j Database

    Note over Agent: Agent needs to know:<br/>"Who works for Microsoft?"

    Agent->>KG: GET /api/v1/graph/entity/Microsoft/connections<br/>?relationship_type=WORKS_FOR

    KG->>Neo: MATCH (e:ORGANIZATION {name: "Microsoft"})<br/><-[r:WORKS_FOR]-(p:PERSON)<br/>RETURN p, r

    Neo->>KG: Graph data (nodes + relationships)

    KG->>KG: Transform to JSON

    KG->>Agent: JSON Response:<br/>{entities: [...], relationships: [...]}

    Note over Agent: Use knowledge to<br/>answer user query
```

### 1.3 Event Schema: `relationships.extracted`

```json
{
  "event_type": "relationships.extracted",
  "timestamp": "2025-10-24T10:30:00Z",
  "payload": {
    "article_id": "uuid",
    "source_url": "https://example.com/article",
    "extracted_at": "2025-10-24T10:29:45Z",
    "triplets": [
      {
        "subject": {
          "text": "Sarah Chen",
          "type": "PERSON",
          "normalized_text": "Sarah Chen"
        },
        "relationship": {
          "type": "WORKS_FOR",
          "confidence": 0.95,
          "evidence": "Sarah Chen has been appointed as the new head of its AI division."
        },
        "object": {
          "text": "Microsoft",
          "type": "ORGANIZATION",
          "normalized_text": "Microsoft"
        }
      }
    ],
    "metadata": {
      "analysis_id": "uuid",
      "model_used": "gpt-4",
      "total_triplets": 5
    }
  }
}
```

---

## 2. Technology Stack

### 2.1 Core Technologies

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Language** | Python | 3.11+ | Consistency with existing services |
| **Web Framework** | FastAPI | 0.115+ | High performance, async support, automatic OpenAPI |
| **Graph Database** | Neo4j | 5.x Community | Native graph storage, powerful Cypher queries |
| **Message Queue** | RabbitMQ | 3.x | Already in infrastructure, reliable event delivery |
| **DB Driver** | neo4j-driver | 5.x | Official Python driver for Neo4j |
| **Message Consumer** | aio-pika | 9.x | Async RabbitMQ client (already used) |

### 2.2 Why Neo4j?

**Neo4j is the ideal choice for this use case because:**

1. **Native Graph Storage**
   - Stores relationships as first-class citizens (not foreign keys)
   - O(1) relationship traversal complexity
   - Optimized for connected data queries

2. **Cypher Query Language**
   - Declarative, SQL-like syntax for graph patterns
   - Powerful for multi-hop queries: `MATCH (a)-[*1..3]->(b)`
   - Easy to expose to LLM agent as a tool

3. **Production-Ready**
   - ACID transactions
   - Clustering and replication (Enterprise)
   - Proven at scale (LinkedIn, eBay, NASA)

4. **Developer Experience**
   - Official Python driver with excellent documentation
   - Browser-based graph visualization (Neo4j Browser)
   - Rich ecosystem of tools

5. **Community Edition**
   - Free for production use
   - Full feature set for our requirements
   - Easy Docker deployment

**Alternatives Considered:**
- ❌ PostgreSQL + pg_graph: Not native graph, poor traversal performance
- ❌ Amazon Neptune: Vendor lock-in, complex setup
- ⚠️ ArangoDB: Multi-model flexible, but less mature graph features
- ✅ **Neo4j**: Best-in-class for property graphs

### 2.3 New Python Dependencies

```toml
# pyproject.toml additions for knowledge-graph-service

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.30.0"}

# Graph Database
neo4j = "^5.25.0"  # Official Neo4j Python driver

# Message Queue
aio-pika = "^9.4.0"  # Async RabbitMQ client

# Data Validation
pydantic = "^2.8.0"
pydantic-settings = "^2.4.0"

# HTTP Client (for health checks, external APIs)
httpx = "^0.27.0"

# Authentication (JWT validation)
python-jose = {extras = ["cryptography"], version = "^3.3.0"}

# Monitoring
prometheus-client = "^0.20.0"
structlog = "^24.4.0"

# Utilities
tenacity = "^9.0.0"  # Retry logic for Neo4j connections
python-dateutil = "^2.8.2"
```

---

## 3. Data Ingestion (Event-Driven Synchronization)

### 3.1 RabbitMQ Consumer Architecture

```python
# Conceptual structure (not full implementation)

class RelationshipsConsumer:
    """
    Consumes 'relationships.extracted' events from RabbitMQ
    and syncs triplets to Neo4j.
    """

    def __init__(self, neo4j_driver, rabbitmq_connection):
        self.neo4j = neo4j_driver
        self.rabbitmq = rabbitmq_connection
        self.logger = structlog.get_logger()

    async def start(self):
        """Start consuming events from the queue."""
        channel = await self.rabbitmq.channel()

        # Declare exchange and queue
        exchange = await channel.declare_exchange(
            'news.events',
            type='topic',
            durable=True
        )

        queue = await channel.declare_queue(
            'knowledge-graph.relationships',
            durable=True
        )

        # Bind queue to routing key
        await queue.bind(
            exchange,
            routing_key='relationships.extracted'
        )

        # Start consuming
        await queue.consume(self.handle_message)

    async def handle_message(self, message):
        """Process a single relationships.extracted event."""
        try:
            # 1. Parse event payload
            event = RelationshipsExtractedEvent.model_validate_json(
                message.body
            )

            # 2. Validate triplets
            valid_triplets = self._validate_triplets(event.payload.triplets)

            # 3. Ingest to Neo4j (transactionally)
            ingested_count = await self._ingest_to_neo4j(
                valid_triplets,
                event.payload.article_id,
                event.payload.source_url
            )

            # 4. Log success
            self.logger.info(
                "relationships_ingested",
                article_id=event.payload.article_id,
                triplets=ingested_count
            )

            # 5. ACK message
            await message.ack()

        except ValidationError as e:
            self.logger.error("invalid_event_schema", error=str(e))
            await message.reject(requeue=False)  # Send to DLQ

        except Exception as e:
            self.logger.error("ingestion_failed", error=str(e))
            await message.reject(requeue=True)  # Retry
```

### 3.2 Idempotent Neo4j Ingestion Logic

**Key Principle:** Use `MERGE` to ensure idempotency. Running the same triplet multiple times should not create duplicates.

```cypher
// Idempotent Cypher Query for Triplet Ingestion
// Example: ["Sarah Chen", "WORKS_FOR", "Microsoft"]

// Step 1: MERGE subject entity (create if not exists)
MERGE (subject:PERSON {name: $subject_name})
ON CREATE SET
    subject.created_at = datetime(),
    subject.type = $subject_type,
    subject.normalized_name = $subject_normalized
ON MATCH SET
    subject.last_seen = datetime()

// Step 2: MERGE object entity (create if not exists)
MERGE (object:ORGANIZATION {name: $object_name})
ON CREATE SET
    object.created_at = datetime(),
    object.type = $object_type,
    object.normalized_name = $object_normalized
ON MATCH SET
    object.last_seen = datetime()

// Step 3: MERGE relationship (create or update metadata)
MERGE (subject)-[rel:WORKS_FOR]->(object)
ON CREATE SET
    rel.created_at = datetime(),
    rel.confidence = $confidence,
    rel.evidence = $evidence,
    rel.source_article_id = $article_id,
    rel.source_url = $source_url,
    rel.first_seen = datetime(),
    rel.mention_count = 1
ON MATCH SET
    rel.last_seen = datetime(),
    rel.mention_count = rel.mention_count + 1,
    // Update confidence if new value is higher
    rel.confidence = CASE
        WHEN $confidence > rel.confidence
        THEN $confidence
        ELSE rel.confidence
    END,
    // Append new evidence (keep list of sources)
    rel.evidence_list = CASE
        WHEN rel.evidence_list IS NULL
        THEN [$evidence]
        WHEN NOT $evidence IN rel.evidence_list
        THEN rel.evidence_list + [$evidence]
        ELSE rel.evidence_list
    END

RETURN subject, rel, object
```

**Parameters:**
```python
{
    "subject_name": "Sarah Chen",
    "subject_type": "PERSON",
    "subject_normalized": "sarah_chen",
    "object_name": "Microsoft",
    "object_type": "ORGANIZATION",
    "object_normalized": "microsoft",
    "confidence": 0.95,
    "evidence": "Sarah Chen has been appointed as the new head of its AI division.",
    "article_id": "uuid",
    "source_url": "https://example.com/article"
}
```

### 3.3 Ingestion Service Implementation

```python
class Neo4jIngestionService:
    """Service for ingesting triplets into Neo4j."""

    def __init__(self, driver):
        self.driver = driver

    async def ingest_triplets(
        self,
        triplets: List[Triplet],
        article_id: str,
        source_url: str
    ) -> int:
        """
        Ingest multiple triplets in a single transaction.

        Returns:
            Number of triplets successfully ingested
        """

        async with self.driver.session() as session:
            return await session.execute_write(
                self._ingest_transaction,
                triplets,
                article_id,
                source_url
            )

    @staticmethod
    async def _ingest_transaction(tx, triplets, article_id, source_url):
        """Transaction function for batch ingestion."""

        count = 0

        for triplet in triplets:
            # Execute the idempotent MERGE query
            result = tx.run(
                TRIPLET_MERGE_QUERY,  # Cypher query from above
                {
                    "subject_name": triplet.subject.text,
                    "subject_type": triplet.subject.type,
                    "subject_normalized": triplet.subject.normalized_text,
                    "object_name": triplet.object.text,
                    "object_type": triplet.object.type,
                    "object_normalized": triplet.object.normalized_text,
                    "confidence": triplet.relationship.confidence,
                    "evidence": triplet.relationship.evidence,
                    "article_id": article_id,
                    "source_url": source_url
                }
            )

            # Verify ingestion
            if result.single():
                count += 1

        return count
```

---

## 4. Graph Data Model

### 4.1 Node (Entity) Schema

**Principle:** Each entity type gets its own label for type safety and query optimization.

#### Node Labels (From EntityType Enum)

```cypher
// Core Entity Types
(:PERSON {name, type, normalized_name, created_at, last_seen})
(:ORGANIZATION {name, type, normalized_name, created_at, last_seen})
(:LOCATION {name, type, normalized_name, created_at, last_seen})
(:EVENT {name, type, normalized_name, created_at, last_seen})
(:PRODUCT {name, type, normalized_name, created_at, last_seen})

// Extended Entity Types (Phase 2)
(:LEGISLATION {name, type, normalized_name, created_at, last_seen})
(:LEGAL_CASE {name, type, normalized_name, created_at, last_seen})
(:MOVIE {name, type, normalized_name, created_at, last_seen})
(:PLATFORM {name, type, normalized_name, created_at, last_seen})
(:NATIONALITY {name, type, normalized_name, created_at, last_seen})

// Measurable Entities
(:MONEY {name, type, amount, currency, normalized_name, created_at, last_seen})
(:PERCENT {name, type, value, normalized_name, created_at, last_seen})
(:QUANTITY {name, type, value, unit, normalized_name, created_at, last_seen})
(:DATE {name, type, date_value, normalized_name, created_at, last_seen})
```

#### Node Properties (Common)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | String | ✅ | Entity name (e.g., "Sarah Chen") |
| `type` | String | ✅ | Original EntityType enum value |
| `normalized_name` | String | ✅ | Lowercase, normalized for deduplication |
| `created_at` | DateTime | ✅ | First appearance in graph |
| `last_seen` | DateTime | ✅ | Most recent mention |
| `aliases` | List[String] | ❌ | Alternative names (future) |
| `metadata` | Map | ❌ | Additional properties (flexible) |

**Indexes for Performance:**
```cypher
// Create indexes on entity names (compound with label for uniqueness)
CREATE CONSTRAINT person_name_unique IF NOT EXISTS
FOR (p:PERSON) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT org_name_unique IF NOT EXISTS
FOR (o:ORGANIZATION) REQUIRE o.name IS UNIQUE;

// Create indexes for normalized names (fuzzy matching)
CREATE INDEX normalized_names IF NOT EXISTS
FOR (n) ON (n.normalized_name);

// Create index for temporal queries
CREATE INDEX entity_last_seen IF NOT EXISTS
FOR (n) ON (n.last_seen);
```

### 4.2 Relationship Schema

**Principle:** Relationship types map directly to `RelationshipType` enum values.

#### Relationship Types (From RelationshipType Enum)

```cypher
// Core Relationships
-[:WORKS_FOR]->
-[:LOCATED_IN]->
-[:OWNS]->
-[:MEMBER_OF]->
-[:PARTNER_OF]->
-[:RELATED_TO]->

// Legal/Judicial
-[:RULED_AGAINST]->
-[:ABUSED_MONOPOLY_IN]->
-[:REGULATES]->

// Business Relationships
-[:REPORTS_TO]->
-[:PRODUCES]->
-[:FOUNDED_BY]->
-[:FOUNDED_IN]->
-[:OWNED_BY]->
-[:ACQUIRED]->
-[:INVESTED_IN]->
-[:COMPETES_WITH]->

// Professional Relationships
-[:ADVISED]->
-[:WORKED_WITH]->
-[:COLLABORATED_WITH]->
-[:CREATED]->
-[:STUDIED_AT]->

// Political/Social
-[:SUPPORTS]->
-[:OPPOSES]->

// Organizational Roles
-[:RAN]->
-[:OVERSAW]->
-[:BRAND_AMBASSADOR_FOR]->
-[:SPOKESPERSON_FOR]->

// Transactional
-[:INITIALLY_AGREED_TO_ACQUIRE]->

// Generic Fallback
-[:NOT_APPLICABLE]->
```

#### Relationship Properties (Metadata)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `confidence` | Float | ✅ | Extraction confidence (0.0-1.0) |
| `evidence` | String | ✅ | Source text supporting relationship |
| `source_article_id` | UUID | ✅ | Article where first mentioned |
| `source_url` | String | ✅ | URL of source article |
| `created_at` | DateTime | ✅ | First extraction timestamp |
| `last_seen` | DateTime | ✅ | Most recent mention |
| `first_seen` | DateTime | ✅ | Same as created_at (redundant) |
| `mention_count` | Integer | ✅ | How many times extracted |
| `evidence_list` | List[String] | ✅ | All evidence texts (multi-source) |

**Why Store Metadata on Relationships?**
1. **Provenance Tracking:** Know where each fact came from
2. **Confidence Scoring:** Filter low-confidence relationships
3. **Temporal Analysis:** Track when relationships were first/last seen
4. **Multi-Source Validation:** Higher mention_count = higher trust

---

## 5. Query API Design

### 5.1 RESTful API Endpoints

#### Base URL
```
http://localhost:8109/api/v1
```

#### Endpoint 1: Entity Connections (Simple)

**Purpose:** Get all direct neighbors of an entity (1-hop traversal)

```
GET /api/v1/graph/entity/{entity_name}/connections
```

**Query Parameters:**
- `relationship_type` (optional): Filter by relationship type (e.g., `WORKS_FOR`)
- `direction` (optional): `outgoing`, `incoming`, `both` (default: `both`)
- `limit` (optional): Max results (default: 100, max: 1000)
- `min_confidence` (optional): Minimum confidence score (default: 0.0)

**Example Request:**
```http
GET /api/v1/graph/entity/Microsoft/connections?relationship_type=WORKS_FOR&direction=incoming&limit=50
Authorization: Bearer <jwt_token>
```

**Cypher Query (Generated):**
```cypher
MATCH (e {name: $entity_name})<-[r:WORKS_FOR]-(connected)
WHERE r.confidence >= $min_confidence
RETURN connected, r, e
ORDER BY r.confidence DESC
LIMIT $limit
```

**Response Schema (Pydantic):**
```python
class EntityConnectionsResponse(BaseModel):
    """Response for entity connections query."""

    entity: EntityNode  # The queried entity
    connections: List[Connection]
    total_count: int
    query_time_ms: int

class EntityNode(BaseModel):
    """A node in the graph."""

    name: str
    type: str  # EntityType value
    normalized_name: str
    created_at: datetime
    last_seen: datetime
    metadata: Optional[Dict[str, Any]] = None

class Connection(BaseModel):
    """A connection between two entities."""

    entity: EntityNode  # The connected entity
    relationship: Relationship

class Relationship(BaseModel):
    """A relationship between two entities."""

    type: str  # RelationshipType value
    confidence: float
    evidence: str
    source_article_id: str
    source_url: str
    mention_count: int
    created_at: datetime
    last_seen: datetime
```

**Example Response:**
```json
{
  "entity": {
    "name": "Microsoft",
    "type": "ORGANIZATION",
    "normalized_name": "microsoft",
    "created_at": "2025-01-15T10:30:00Z",
    "last_seen": "2025-10-24T05:35:00Z"
  },
  "connections": [
    {
      "entity": {
        "name": "Sarah Chen",
        "type": "PERSON",
        "normalized_name": "sarah_chen",
        "created_at": "2025-10-23T14:20:00Z",
        "last_seen": "2025-10-24T05:35:00Z"
      },
      "relationship": {
        "type": "WORKS_FOR",
        "confidence": 0.95,
        "evidence": "Sarah Chen has been appointed as the new head of its AI division.",
        "source_article_id": "uuid",
        "source_url": "https://example.com/article",
        "mention_count": 1,
        "created_at": "2025-10-24T05:35:00Z",
        "last_seen": "2025-10-24T05:35:00Z"
      }
    },
    {
      "entity": {
        "name": "Satya Nadella",
        "type": "PERSON",
        "normalized_name": "satya_nadella",
        "created_at": "2025-01-15T10:30:00Z",
        "last_seen": "2025-10-20T12:00:00Z"
      },
      "relationship": {
        "type": "WORKS_FOR",
        "confidence": 0.98,
        "evidence": "Microsoft CEO Satya Nadella...",
        "source_article_id": "uuid",
        "source_url": "https://example.com/article2",
        "mention_count": 15,
        "created_at": "2025-01-15T10:30:00Z",
        "last_seen": "2025-10-20T12:00:00Z"
      }
    }
  ],
  "total_count": 2,
  "query_time_ms": 23
}
```

---

#### Endpoint 2: Custom Cypher Query (Advanced)

**Purpose:** Execute arbitrary Cypher queries for maximum flexibility (agent use)

```
POST /api/v1/graph/query
```

**Request Schema (Pydantic):**
```python
class CypherQueryRequest(BaseModel):
    """Request for custom Cypher query execution."""

    query: str = Field(
        ...,
        description="Cypher query to execute",
        min_length=1,
        max_length=10000
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Query parameters (prevents injection)"
    )
    timeout_seconds: Optional[int] = Field(
        default=30,
        ge=1,
        le=300,
        description="Query timeout (max 5 minutes)"
    )

    @field_validator('query')
    def validate_query(cls, v):
        """Validate query for safety."""

        # Block dangerous operations
        dangerous_keywords = [
            'DELETE', 'DETACH DELETE', 'REMOVE', 'DROP',
            'CREATE CONSTRAINT', 'CREATE INDEX'
        ]

        query_upper = v.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(
                    f"Query contains forbidden operation: {keyword}"
                )

        return v
```

**Example Request:**
```http
POST /api/v1/graph/query
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "query": "MATCH (p:PERSON)-[r:WORKS_FOR]->(o:ORGANIZATION {name: $org_name}) WHERE r.confidence > $min_conf RETURN p.name, r.confidence ORDER BY r.confidence DESC LIMIT $limit",
  "parameters": {
    "org_name": "Microsoft",
    "min_conf": 0.8,
    "limit": 10
  },
  "timeout_seconds": 30
}
```

**Response Schema (Pydantic):**
```python
class CypherQueryResponse(BaseModel):
    """Response for Cypher query execution."""

    columns: List[str]  # Column names
    records: List[Dict[str, Any]]  # Query results
    total_records: int
    query_time_ms: int
    summary: Optional[QuerySummary] = None

class QuerySummary(BaseModel):
    """Neo4j query execution summary."""

    nodes_created: int = 0
    relationships_created: int = 0
    properties_set: int = 0
    server_info: Optional[str] = None
```

**Example Response:**
```json
{
  "columns": ["p.name", "r.confidence"],
  "records": [
    {"p.name": "Sarah Chen", "r.confidence": 0.95},
    {"p.name": "Satya Nadella", "r.confidence": 0.98},
    {"p.name": "Brad Smith", "r.confidence": 0.92}
  ],
  "total_records": 3,
  "query_time_ms": 15,
  "summary": {
    "nodes_created": 0,
    "relationships_created": 0,
    "properties_set": 0,
    "server_info": "Neo4j/5.25.0"
  }
}
```

---

#### Additional Endpoints (Future)

```
GET /api/v1/graph/entity/{entity_name}
  → Get entity details only

GET /api/v1/graph/path/{source_name}/to/{target_name}
  → Find shortest path between two entities

POST /api/v1/graph/subgraph
  → Extract a subgraph matching criteria

GET /api/v1/graph/stats
  → Graph statistics (total nodes, relationships, etc.)

POST /api/v1/graph/search
  → Full-text search across entity names
```

### 5.2 Authentication & Authorization

**JWT Token Validation** (same as other services):
```python
from app.api.dependencies import get_current_user_id

@router.get("/graph/entity/{entity_name}/connections")
async def get_entity_connections(
    entity_name: str,
    user_id: str = Depends(get_current_user_id),  # JWT validation
    neo4j: Neo4jService = Depends(get_neo4j_service)
):
    # Only authenticated users can query the graph
    pass
```

**Future:** Role-based access control (RBAC) for sensitive relationships.

---

## 6. End-to-End Example

### Scenario: Apple Antitrust Case

**Input Triplet (from content-analysis-service):**
```
Subject: "Competition Appeal Tribunal"
Relationship: "ruled_against"
Object: "Apple"
```

---

### Step 1: Event Published to RabbitMQ

```json
{
  "event_type": "relationships.extracted",
  "timestamp": "2025-10-24T10:30:00Z",
  "payload": {
    "article_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "source_url": "https://techcrunch.com/apple-antitrust-ruling",
    "extracted_at": "2025-10-24T10:29:45Z",
    "triplets": [
      {
        "subject": {
          "text": "Competition Appeal Tribunal",
          "type": "LEGAL_CASE",
          "normalized_text": "competition_appeal_tribunal"
        },
        "relationship": {
          "type": "ruled_against",
          "confidence": 0.92,
          "evidence": "The Competition Appeal Tribunal ruled against Apple's app store practices."
        },
        "object": {
          "text": "Apple",
          "type": "ORGANIZATION",
          "normalized_text": "apple"
        }
      }
    ],
    "metadata": {
      "analysis_id": "9876-5432-1098-abcd",
      "model_used": "gpt-4",
      "total_triplets": 1
    }
  }
}
```

**RabbitMQ Routing:**
```
Exchange: news.events (topic)
Routing Key: relationships.extracted
Queue: knowledge-graph.relationships (bound to routing key)
```

---

### Step 2: Knowledge Graph Service Consumes Event

**Consumer Logic:**
1. Receive message from RabbitMQ
2. Parse JSON into `RelationshipsExtractedEvent` Pydantic model
3. Validate triplet structure
4. Execute Neo4j MERGE query

**Neo4j MERGE Query Executed:**

```cypher
// MERGE subject entity (LEGAL_CASE)
MERGE (subject:LEGAL_CASE {name: "Competition Appeal Tribunal"})
ON CREATE SET
    subject.created_at = datetime(),
    subject.type = "LEGAL_CASE",
    subject.normalized_name = "competition_appeal_tribunal"
ON MATCH SET
    subject.last_seen = datetime()

// MERGE object entity (ORGANIZATION)
MERGE (object:ORGANIZATION {name: "Apple"})
ON CREATE SET
    object.created_at = datetime(),
    object.type = "ORGANIZATION",
    object.normalized_name = "apple"
ON MATCH SET
    object.last_seen = datetime()

// MERGE relationship
MERGE (subject)-[rel:RULED_AGAINST]->(object)
ON CREATE SET
    rel.created_at = datetime(),
    rel.confidence = 0.92,
    rel.evidence = "The Competition Appeal Tribunal ruled against Apple's app store practices.",
    rel.source_article_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    rel.source_url = "https://techcrunch.com/apple-antitrust-ruling",
    rel.first_seen = datetime(),
    rel.mention_count = 1
ON MATCH SET
    rel.last_seen = datetime(),
    rel.mention_count = rel.mention_count + 1,
    rel.confidence = CASE
        WHEN 0.92 > rel.confidence THEN 0.92
        ELSE rel.confidence
    END,
    rel.evidence_list = CASE
        WHEN rel.evidence_list IS NULL
        THEN ["The Competition Appeal Tribunal ruled against Apple's app store practices."]
        WHEN NOT "The Competition Appeal Tribunal ruled against Apple's app store practices." IN rel.evidence_list
        THEN rel.evidence_list + ["The Competition Appeal Tribunal ruled against Apple's app store practices."]
        ELSE rel.evidence_list
    END

RETURN subject, rel, object
```

**Result:** Graph updated, message ACKed.

---

### Step 3: Agent Queries the Graph

**Agent Task:** "Find all legal cases involving Apple"

**API Call (from LLM Orchestrator):**
```http
GET /api/v1/graph/entity/Apple/connections?relationship_type=RULED_AGAINST&direction=incoming
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Cypher Query (Generated by Service):**
```cypher
MATCH (e:ORGANIZATION {name: "Apple"})<-[r:RULED_AGAINST]-(legal_case)
WHERE r.confidence >= 0.0
RETURN legal_case, r, e
ORDER BY r.confidence DESC
LIMIT 100
```

---

### Step 4: API Response

```json
{
  "entity": {
    "name": "Apple",
    "type": "ORGANIZATION",
    "normalized_name": "apple",
    "created_at": "2024-05-10T08:00:00Z",
    "last_seen": "2025-10-24T10:30:00Z"
  },
  "connections": [
    {
      "entity": {
        "name": "Competition Appeal Tribunal",
        "type": "LEGAL_CASE",
        "normalized_name": "competition_appeal_tribunal",
        "created_at": "2025-10-24T10:30:00Z",
        "last_seen": "2025-10-24T10:30:00Z"
      },
      "relationship": {
        "type": "RULED_AGAINST",
        "confidence": 0.92,
        "evidence": "The Competition Appeal Tribunal ruled against Apple's app store practices.",
        "source_article_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "source_url": "https://techcrunch.com/apple-antitrust-ruling",
        "mention_count": 1,
        "created_at": "2025-10-24T10:30:00Z",
        "last_seen": "2025-10-24T10:30:00Z"
      }
    },
    {
      "entity": {
        "name": "EU Commission",
        "type": "ORGANIZATION",
        "normalized_name": "eu_commission",
        "created_at": "2024-08-15T12:00:00Z",
        "last_seen": "2025-09-01T14:00:00Z"
      },
      "relationship": {
        "type": "RULED_AGAINST",
        "confidence": 0.95,
        "evidence": "The European Commission ruled against Apple in a €13 billion tax case.",
        "source_article_id": "xyz-123-456",
        "source_url": "https://reuters.com/eu-apple-tax",
        "mention_count": 5,
        "created_at": "2024-08-15T12:00:00Z",
        "last_seen": "2025-09-01T14:00:00Z"
      }
    }
  ],
  "total_count": 2,
  "query_time_ms": 18
}
```

---

### Step 5: Agent Uses Knowledge

**LLM Orchestrator Agent:**
```
User Query: "What legal trouble has Apple faced?"

Agent calls: GET /graph/entity/Apple/connections?relationship_type=RULED_AGAINST

Agent receives: 2 legal cases

Agent synthesizes response:
"Apple has faced multiple legal challenges:
1. Competition Appeal Tribunal ruled against Apple's app store practices (confidence: 92%)
2. EU Commission ruled against Apple in a €13 billion tax case (confidence: 95%)

Both cases are well-documented with high confidence scores."
```

---

## 7. Service Structure & File Organization

```
knowledge-graph-service/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Environment configuration
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py          # JWT validation, Neo4j session
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── graph.py             # Graph query endpoints
│   │       └── health.py            # Health check endpoints
│   │
│   ├── consumers/
│   │   ├── __init__.py
│   │   ├── relationships_consumer.py  # RabbitMQ consumer
│   │   └── event_schemas.py           # Pydantic event models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── neo4j_service.py         # Neo4j connection & queries
│   │   ├── ingestion_service.py     # Triplet ingestion logic
│   │   └── query_service.py         # Graph query logic
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── graph.py                 # Graph node/relationship models
│   │   ├── requests.py              # API request models
│   │   └── responses.py             # API response models
│   │
│   └── core/
│       ├── __init__.py
│       ├── exceptions.py            # Custom exceptions
│       └── logging.py               # Structured logging setup
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_ingestion.py
│   ├── test_queries.py
│   └── test_api.py
│
├── alembic/                         # Database migrations (if needed)
├── docker/
│   ├── Dockerfile
│   └── docker-compose.neo4j.yml     # Neo4j standalone setup
│
├── pyproject.toml                   # Poetry dependencies
├── README.md                        # Service documentation
└── .env.example                     # Environment variables template
```

---

## 8. Configuration & Environment Variables

```bash
# .env.example for knowledge-graph-service

# Service Configuration
SERVICE_NAME=knowledge-graph-service
SERVICE_PORT=8109
LOG_LEVEL=INFO

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_secret_password
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30

# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=rabbitmq_user
RABBITMQ_PASSWORD=rabbitmq_password
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=news.events
RABBITMQ_ROUTING_KEY=relationships.extracted
RABBITMQ_QUEUE=knowledge-graph.relationships

# Authentication (JWT)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Monitoring
PROMETHEUS_PORT=9090
```

---

## 9. Deployment & Docker Integration

### 9.1 Add to docker-compose.yml

```yaml
services:
  # ... existing services ...

  # Neo4j Graph Database
  neo4j:
    image: neo4j:5.25-community
    container_name: neo4j
    ports:
      - "7474:7474"  # HTTP (Neo4j Browser)
      - "7687:7687"  # Bolt protocol
    environment:
      NEO4J_AUTH: neo4j/neo4j_secret_password
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_dbms_memory_heap_initial__size: 512m
      NEO4J_dbms_memory_heap_max__size: 2G
      NEO4J_dbms_memory_pagecache_size: 1G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_plugins:/plugins
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - news-network

  # Knowledge Graph Service
  knowledge-graph-service:
    build:
      context: .
      dockerfile: services/knowledge-graph-service/Dockerfile.dev
    container_name: news-knowledge-graph-service
    ports:
      - "8109:8109"
    environment:
      SERVICE_PORT: 8109
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: neo4j_secret_password
      RABBITMQ_HOST: rabbitmq
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    volumes:
      - ./services/knowledge-graph-service/app:/app/app:ro
    depends_on:
      neo4j:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8109/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - news-network

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_plugins:
```

### 9.2 Neo4j Browser Access

After deployment:
- **URL:** http://localhost:7474
- **Username:** neo4j
- **Password:** neo4j_secret_password

**Initial Cypher Query to Verify:**
```cypher
MATCH (n) RETURN count(n) AS total_nodes;
MATCH ()-[r]->() RETURN count(r) AS total_relationships;
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

```python
# tests/test_ingestion.py

@pytest.mark.asyncio
async def test_triplet_ingestion_idempotent(neo4j_driver):
    """Test that ingesting the same triplet twice is idempotent."""

    ingestion_service = Neo4jIngestionService(neo4j_driver)

    triplet = Triplet(
        subject=Entity(text="Sarah Chen", type="PERSON"),
        relationship=Relation(type="WORKS_FOR", confidence=0.95),
        object=Entity(text="Microsoft", type="ORGANIZATION")
    )

    # Ingest once
    count1 = await ingestion_service.ingest_triplets(
        [triplet],
        article_id="test-123",
        source_url="https://test.com"
    )
    assert count1 == 1

    # Ingest again (should update, not duplicate)
    count2 = await ingestion_service.ingest_triplets(
        [triplet],
        article_id="test-123",
        source_url="https://test.com"
    )
    assert count2 == 1  # Still reports success

    # Verify only one relationship exists
    async with neo4j_driver.session() as session:
        result = await session.run(
            "MATCH (:PERSON {name: 'Sarah Chen'})"
            "-[r:WORKS_FOR]->"
            "(:ORGANIZATION {name: 'Microsoft'}) "
            "RETURN count(r) AS count"
        )
        record = await result.single()
        assert record["count"] == 1
```

### 10.2 Integration Tests

```python
# tests/test_api.py

@pytest.mark.asyncio
async def test_entity_connections_endpoint(client, populated_graph):
    """Test the entity connections API endpoint."""

    response = await client.get(
        "/api/v1/graph/entity/Microsoft/connections",
        params={"relationship_type": "WORKS_FOR"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["entity"]["name"] == "Microsoft"
    assert len(data["connections"]) > 0
    assert data["connections"][0]["relationship"]["type"] == "WORKS_FOR"
```

### 10.3 E2E Tests

```python
# tests/test_e2e.py

@pytest.mark.asyncio
async def test_full_pipeline_event_to_query(
    rabbitmq_publisher,
    neo4j_driver,
    api_client
):
    """Test the full pipeline: Event → Ingestion → Query."""

    # Step 1: Publish relationships.extracted event
    event = RelationshipsExtractedEvent(
        event_type="relationships.extracted",
        payload={
            "article_id": "e2e-test",
            "triplets": [
                {
                    "subject": {"text": "Alice", "type": "PERSON"},
                    "relationship": {"type": "WORKS_FOR", "confidence": 0.9},
                    "object": {"text": "TechCorp", "type": "ORGANIZATION"}
                }
            ]
        }
    )

    await rabbitmq_publisher.publish(event)

    # Step 2: Wait for ingestion (with timeout)
    await asyncio.sleep(2)

    # Step 3: Query via API
    response = await api_client.get(
        "/api/v1/graph/entity/TechCorp/connections"
    )

    assert response.status_code == 200
    data = response.json()

    # Verify Alice is connected to TechCorp
    assert any(
        conn["entity"]["name"] == "Alice"
        for conn in data["connections"]
    )
```

---

## 11. Monitoring & Observability

### 11.1 Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Ingestion Metrics
triplets_ingested_total = Counter(
    'triplets_ingested_total',
    'Total number of triplets ingested',
    ['status']  # success, failed
)

ingestion_duration_seconds = Histogram(
    'ingestion_duration_seconds',
    'Time spent ingesting triplets',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Query Metrics
graph_queries_total = Counter(
    'graph_queries_total',
    'Total number of graph queries',
    ['endpoint', 'status']
)

query_duration_seconds = Histogram(
    'query_duration_seconds',
    'Time spent executing graph queries',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Graph Statistics
graph_nodes_total = Gauge(
    'graph_nodes_total',
    'Total number of nodes in the graph',
    ['type']  # PERSON, ORGANIZATION, etc.
)

graph_relationships_total = Gauge(
    'graph_relationships_total',
    'Total number of relationships in the graph',
    ['type']  # WORKS_FOR, OWNS, etc.
)
```

### 11.2 Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Ingestion Logging
logger.info(
    "triplet_ingested",
    article_id=article_id,
    subject=triplet.subject.text,
    relationship=triplet.relationship.type,
    object=triplet.object.text,
    confidence=triplet.relationship.confidence
)

# Query Logging
logger.info(
    "graph_query_executed",
    endpoint="/graph/entity/connections",
    entity_name=entity_name,
    results_count=len(connections),
    query_time_ms=query_time
)
```

### 11.3 Health Check Endpoint

```python
@router.get("/health")
async def health_check(neo4j: Neo4jService = Depends(get_neo4j_service)):
    """Comprehensive health check."""

    health_status = {
        "service": "knowledge-graph-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Check Neo4j connection
    try:
        async with neo4j.driver.session() as session:
            result = await session.run("RETURN 1")
            await result.single()
        health_status["checks"]["neo4j"] = "healthy"
    except Exception as e:
        health_status["checks"]["neo4j"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check RabbitMQ connection
    # ... similar check ...

    return health_status
```

---

## 12. Security Considerations

### 12.1 Cypher Injection Prevention

**Always use parameterized queries:**
```python
# ❌ BAD: String interpolation (vulnerable to injection)
query = f"MATCH (n {{name: '{user_input}'}}) RETURN n"

# ✅ GOOD: Parameterized query
query = "MATCH (n {name: $name}) RETURN n"
parameters = {"name": user_input}
```

### 12.2 Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/graph/query")
@limiter.limit("10/minute")  # Max 10 custom queries per minute
async def execute_cypher_query(...):
    pass
```

### 12.3 Query Complexity Limits

```python
def validate_query_complexity(query: str):
    """Prevent expensive queries."""

    # Limit query length
    if len(query) > 10000:
        raise ValueError("Query too long")

    # Block unbounded path queries
    if re.search(r'\[\*\.\.\]', query):  # [*..] = infinite depth
        raise ValueError("Unbounded path queries not allowed")

    # Require LIMIT clause for MATCH queries
    if 'MATCH' in query.upper() and 'LIMIT' not in query.upper():
        raise ValueError("MATCH queries must include LIMIT clause")
```

---

## 13. Future Enhancements

### 13.1 Graph Algorithms (Neo4j GDS)

**Use Neo4j Graph Data Science library for:**
- **Community Detection:** Find clusters of related entities
- **PageRank:** Identify most important entities
- **Shortest Path:** Find connections between entities
- **Similarity:** Recommend similar entities

**Example:**
```cypher
// Find most influential people (PageRank)
CALL gds.pageRank.stream('myGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS person, score
ORDER BY score DESC
LIMIT 10
```

### 13.2 Temporal Queries

**Track relationship evolution over time:**
```cypher
// Find relationships that appeared in the last 7 days
MATCH (a)-[r]->(b)
WHERE r.created_at > datetime() - duration('P7D')
RETURN a, r, b
```

### 13.3 Entity Resolution & Deduplication

**Merge duplicate entities using fuzzy matching:**
- "Microsoft Corp" vs "Microsoft Corporation"
- "Sarah Chen" vs "S. Chen"

**Tools:**
- String similarity (Levenshtein distance)
- Embeddings-based matching
- Manual curation UI

### 13.4 Graph Visualization

**Integrate with visualization tools:**
- **Neo4j Bloom:** No-code graph exploration
- **D3.js:** Custom web visualizations
- **Gephi:** Desktop graph analysis

---

## 14. Implementation Roadmap

### Phase 1: MVP (Week 1-2)
- [x] Design complete (this document)
- [ ] Setup Neo4j container in docker-compose
- [ ] Implement Neo4j connection service
- [ ] Implement RabbitMQ consumer for relationships.extracted
- [ ] Implement idempotent MERGE logic
- [ ] Implement GET /entity/{name}/connections endpoint
- [ ] Basic health check and monitoring

**Deliverable:** Service can ingest triplets and answer simple queries

### Phase 2: Advanced Queries (Week 3)
- [ ] Implement POST /graph/query endpoint (Cypher execution)
- [ ] Add query validation and security checks
- [ ] Add rate limiting
- [ ] Add comprehensive error handling
- [ ] Write unit and integration tests

**Deliverable:** Agent can use custom Cypher queries

### Phase 3: Production Hardening (Week 4)
- [ ] Add Prometheus metrics
- [ ] Add structured logging
- [ ] Performance benchmarks (1000+ QPS target)
- [ ] E2E testing with content-analysis-service
- [ ] Documentation and API docs
- [ ] Deploy to staging environment

**Deliverable:** Production-ready service

### Phase 4: Enhancements (Future)
- [ ] Graph algorithms (PageRank, community detection)
- [ ] Entity resolution and deduplication
- [ ] Temporal queries and versioning
- [ ] Graph visualization frontend
- [ ] Multi-tenancy support

---

## 15. Success Criteria

### Performance Targets
- [ ] **Ingestion Rate:** > 100 triplets/second
- [ ] **Query Latency (p95):** < 100ms for simple queries
- [ ] **Query Latency (p95):** < 500ms for complex queries
- [ ] **Uptime:** > 99.9%

### Quality Targets
- [ ] **Test Coverage:** > 90%
- [ ] **Zero Data Loss:** All events ACKed only after successful ingestion
- [ ] **Idempotency:** Re-ingesting same triplet doesn't create duplicates
- [ ] **Type Safety:** All API requests/responses validated with Pydantic

### Integration Targets
- [ ] **Event Consumer:** Successfully consumes relationships.extracted events
- [ ] **Agent Integration:** LLM orchestrator can query graph via API
- [ ] **Monitoring:** Prometheus metrics exposed and scraped
- [ ] **Documentation:** Complete API docs with examples

---

## 16. Conclusion

The **knowledge-graph-service** represents a paradigm shift in how our platform stores and leverages extracted knowledge. By materializing relationship triplets in a purpose-built graph database, we unlock:

1. **Network Effects:** Entities gain value through their connections
2. **Complex Reasoning:** Multi-hop queries answer sophisticated questions
3. **Agent Empowerment:** LLM orchestrator gains a powerful reasoning tool
4. **Scalable Memory:** Graph grows organically with each analyzed article

**This service transforms our platform from a collection of isolated analyses into a living, networked knowledge base.**

---

**Next Steps:**
1. ✅ Review and approve this concept document
2. Setup development environment (Neo4j, update docker-compose)
3. Implement Phase 1 (MVP) following this blueprint
4. Iterate and refine based on real-world usage

**Ready to build our platform's memory? Let's start with Phase 1!** 🚀
