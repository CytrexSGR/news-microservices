# OSS (Ontology Suggestion System) - Comprehensive Technical Documentation

**Service Name:** oss-service
**Port:** 8110
**Version:** 1.0.0
**Framework:** FastAPI 0.109.2
**Status:** Production Ready
**Last Updated:** 2025-11-24

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Quick Start](#quick-start)
3. [Overview](#overview)
4. [Architecture & Design](#architecture--design)
5. [Core Components](#core-components)
6. [Pattern Detection System](#pattern-detection-system)
7. [Inconsistency Detection System](#inconsistency-detection-system)
8. [Proposal Generation & Submission](#proposal-generation--submission)
9. [Scheduled Analysis](#scheduled-analysis)
10. [API Reference](#api-reference)
11. [Data Models](#data-models)
12. [Neo4j Integration](#neo4j-integration)
13. [Configuration](#configuration)
14. [Deployment](#deployment)
15. [Monitoring & Observability](#monitoring--observability)
16. [Performance Characteristics](#performance-characteristics)
17. [Troubleshooting](#troubleshooting)
18. [Code Examples](#code-examples)
19. [Future Enhancements](#future-enhancements)

---

## Executive Summary

The **OSS (Ontology Suggestion System)** is a specialized microservice that learns from the Neo4j knowledge graph and automatically detects patterns, inconsistencies, and opportunities for ontology improvement. It generates structured change proposals that are submitted to the Ontology Proposals Service for human review and potential implementation.

### Key Responsibilities

- **Pattern Detection:** Identifies recurring entity types and relationship patterns suggesting new ontology types
- **Inconsistency Detection:** Finds data quality issues including ISO code violations, duplicates, and missing properties
- **Proposal Generation:** Creates detailed, evidence-based ontology change proposals
- **API Submission:** Automatically submits proposals to the Ontology Proposals Service for review
- **Scheduled Analysis:** Runs analysis cycles at configurable intervals using APScheduler
- **Self-Learning:** Improves confidence calculations based on approval patterns and outcomes

### Business Value

- **Automated Discovery:** Eliminates manual review of knowledge graph patterns
- **Data Quality Improvement:** Proactively identifies and flags data inconsistencies
- **Ontology Evolution:** Suggests targeted improvements based on actual data usage patterns
- **Operational Efficiency:** Reduces manual curation burden through automation
- **Knowledge Preservation:** Creates audit trail of all suggestions and their rationale

### Current Capabilities

- Pattern detection: Entity types and relationship types (>10 occurrences)
- Inconsistency detection: ISO codes, duplicates, missing properties, unknown types, article entities
- Confidence scoring: Multi-factor confidence calculation (0.0-1.0)
- Impact analysis: Affected entities, breaking changes, migration complexity, effort estimates
- Scheduled execution: Configurable intervals via APScheduler (default: 1 hour)
- RESTful API: Manual trigger, status checks, health monitoring
- Neo4j integration: Direct graph database access with connection pooling

---

## Quick Start

### Using Docker Compose

```bash
# Navigate to project root
cd /home/cytrex/news-microservices

# Start entire stack (includes oss-service)
docker compose up -d

# Verify service is running
docker ps | grep oss-service
curl http://localhost:8110/health

# Access API documentation
open http://localhost:8110/docs

# View logs
docker logs oss-service -f

# Trigger manual analysis
curl -X POST http://localhost:8110/api/v1/analysis/run

# Check service status
curl http://localhost:8110/api/v1/analysis/status

# Stop when done
docker compose down
```

### Manual Setup (Development)

```bash
# Clone repository
cd /home/cytrex/news-microservices/services/oss-service

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=news_graph_2024
export PROPOSALS_API_URL=http://localhost:8109
export ANALYSIS_INTERVAL_SECONDS=3600

# Run service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8110 --reload
```

### Verify Installation

```bash
# Health check
curl http://localhost:8110/health
# Expected: { "status": "healthy", "service": "OSS Service", ... }

# Service status
curl http://localhost:8110/api/v1/analysis/status
# Expected: service operational, Neo4j connected, configuration details

# API documentation
http://localhost:8110/docs  # Swagger UI
http://localhost:8110/redoc # ReDoc
```

---

## Overview

### Purpose

The OSS Service analyzes the News MCP knowledge graph stored in Neo4j to discover actionable patterns and data quality issues. Rather than requiring human experts to manually review the entire graph, OSS continuously learns from the data and generates structured proposals for ontology improvements.

### Problem Statement

Knowledge graphs evolve over time as new data is ingested. Manual ontology curation is:
- **Time-consuming:** Requires experts to review thousands of entities and relationships
- **Error-prone:** Inconsistencies and duplicates are easy to miss
- **Reactive:** Problems are discovered after they impact queries and analytics
- **Expensive:** Skilled labor is required for continuous graph maintenance

### Solution

The OSS Service solves this through:

1. **Automated Pattern Detection:** Discovers frequently occurring entity and relationship types
2. **Proactive Quality Checks:** Identifies data inconsistencies before they cause problems
3. **Evidence-Based Proposals:** Every suggestion includes concrete evidence from the graph
4. **Confidence Scoring:** Proposals are ranked by confidence to prioritize human review
5. **Continuous Learning:** Operates 24/7 via scheduled analysis cycles

### Design Philosophy

- **Non-invasive:** Read-only access to Neo4j; never modifies graph directly
- **Human-in-the-loop:** All changes require human approval via Ontology Proposals Service
- **Transparent:** Every proposal explains its reasoning and provides evidence
- **Configurable:** Analysis parameters (thresholds, intervals) are user-configurable
- **Fault-tolerant:** Graceful handling of errors; analysis failures don't crash the service

---

## Architecture & Design

### System Architecture

```
┌─────────────────────┐
│   Neo4j Database    │ (Knowledge Graph)
│   (Read-only)       │
└──────────┬──────────┘
           │
           │ Cypher Queries
           │ (Pattern Analysis)
           ▼
┌─────────────────────┐
│   OSS Service       │ (Port 8110)
│  ┌─────────────────┤
│  │ Pattern         │
│  │ Detector        │
│  ├─────────────────┤
│  │ Inconsistency   │
│  │ Detector        │
│  ├─────────────────┤
│  │ Proposal        │
│  │ Generator       │
│  └─────────────────┤
│                    │
│ ┌──────────────────┤
│ │ APScheduler      │ (Scheduled Analysis)
│ └──────────────────┘
└──────────┬──────────┘
           │
           │ REST API
           │ (POST proposals)
           ▼
┌─────────────────────┐
│ Ontology Proposals  │ (Port 8109)
│ Service             │
└─────────────────────┘
           │
           ▼
    ┌────────────────┐
    │  PostgreSQL    │ (Proposals Storage)
    └────────────────┘
```

### Component Hierarchy

```
FastAPI Application
├── Lifespan Manager
│   ├── Startup: Check Neo4j, start scheduler
│   ├── Shutdown: Stop scheduler, close connections
│   └── Background Scheduler (APScheduler)
│       └── Scheduled Job: run_analysis_cycle()
│
├── Health Check Endpoints
│   ├── GET /health
│   ├── GET /
│   └── Exception Handlers
│
├── API Routes (/api/v1/analysis)
│   ├── POST /run → trigger_analysis()
│   └── GET /status → get_status()
│
├── Analyzers
│   ├── PatternDetector
│   │   ├── detect_entity_patterns()
│   │   ├── detect_relationship_patterns()
│   │   └── Proposal Builders
│   │
│   └── InconsistencyDetector
│       ├── detect_iso_code_violations()
│       ├── detect_duplicate_entities()
│       ├── detect_missing_required_properties()
│       ├── detect_unknown_entity_types()
│       ├── detect_article_entities()
│       └── Proposal Builders
│
└── Database Layer
    ├── Neo4jConnection (Connection Manager)
    │   ├── connect()
    │   ├── execute_read()
    │   └── check_connection()
    │
    └── Models (Pydantic)
        ├── OntologyChangeProposal
        ├── AnalysisResult
        ├── Evidence
        └── ImpactAnalysis
```

### Data Flow: Analysis Cycle

```
START: Scheduled or Manual Trigger
  │
  ├─→ Initialize Analyzers
  │     └─ PatternDetector(neo4j_connection)
  │     └─ InconsistencyDetector(neo4j_connection)
  │
  ├─→ Pattern Detection Phase
  │     ├─ Entity Type Patterns
  │     │   └─ Query: Frequent entity_type values
  │     │   └─ Proposal: NEW_ENTITY_TYPE for each pattern
  │     │
  │     └─ Relationship Patterns
  │         └─ Query: Frequent RELATED_TO patterns
  │         └─ Proposal: NEW_RELATIONSHIP_TYPE for each pattern
  │
  ├─→ Inconsistency Detection Phase
  │     ├─ ISO Code Violations
  │     │   └─ Proposal: FLAG_INCONSISTENCY (CRITICAL)
  │     ├─ Duplicate Entities
  │     │   └─ Proposal: FLAG_INCONSISTENCY (HIGH)
  │     ├─ Missing Properties
  │     │   └─ Proposal: FLAG_INCONSISTENCY (HIGH)
  │     ├─ Unknown Entity Types
  │     │   └─ Proposal: FLAG_INCONSISTENCY (CRITICAL)
  │     └─ Article Entities
  │         └─ Proposal: FLAG_INCONSISTENCY (HIGH)
  │
  ├─→ Confidence Filtering
  │     └─ Filter: confidence >= CONFIDENCE_THRESHOLD (default: 0.7)
  │
  ├─→ Proposal Submission
  │     └─ For each filtered proposal:
  │         ├─ POST to /api/v1/ontology/proposals
  │         ├─ Log result (success/failure)
  │         └─ Track in AnalysisResult
  │
  └─→ END: Return AnalysisResult with metrics
```

---

## Core Components

### 1. FastAPI Application (main.py)

The FastAPI application manages the service lifecycle, scheduling, and HTTP endpoints.

**Key Features:**
- Lifespan management with startup/shutdown hooks
- Graceful Neo4j connection checks
- APScheduler integration for background jobs
- CORS configuration for service-to-service communication
- Global exception handling
- Health check endpoint for monitoring

**Lifespan Flow:**
```python
async def lifespan(app: FastAPI):
    # STARTUP
    yield  # Application runs
    # SHUTDOWN
```

### 2. Configuration (config.py)

Pydantic-based settings management with sensible defaults and environment variable overrides.

**Key Settings:**

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| APP_NAME | str | "OSS Service" | Service identifier |
| PORT | int | 8110 | HTTP server port |
| NEO4J_URI | str | bolt://neo4j:7687 | Graph database connection |
| NEO4J_USER | str | neo4j | Database username |
| NEO4J_PASSWORD | str | news_graph_2024 | Database password |
| PROPOSALS_API_URL | str | http://ontology-proposals-service:8109 | Target service URL |
| ANALYSIS_INTERVAL_SECONDS | int | 3600 | Scheduled job interval (1 hour) |
| MIN_PATTERN_OCCURRENCES | int | 10 | Minimum occurrences for pattern detection |
| CONFIDENCE_THRESHOLD | float | 0.7 | Minimum confidence to generate proposal |
| LOG_LEVEL | str | INFO | Logging level |
| LOG_FORMAT | str | text | text or json |

### 3. Neo4j Database Connection (database.py)

Thread-safe connection management with health checking and query execution.

**Key Methods:**

```python
class Neo4jConnection:
    def connect() -> Driver          # Establish/get driver instance
    def close()                      # Close connection gracefully
    def execute_read(query, params)  # Execute Cypher read query
    def check_connection() -> bool   # Health check
```

**Design Patterns:**
- Lazy initialization: Connection established on first use
- Singleton: Single driver instance across application
- Connection pooling: Neo4j driver manages connection pool

### 4. Data Models (models/proposal.py)

Pydantic models representing ontology change proposals with validation.

**Core Models:**

```python
class ChangeType(Enum):
    NEW_ENTITY_TYPE
    NEW_RELATIONSHIP_TYPE
    MODIFY_ENTITY_PROPERTIES
    MODIFY_RELATIONSHIP_PROPERTIES
    FLAG_INCONSISTENCY
    SUGGEST_CONSTRAINT
    SUGGEST_INDEX
    DEPRECATE_ENTITY
    DEPRECATE_RELATIONSHIP
    MERGE_ENTITIES

class Severity(Enum):
    CRITICAL      # Immediate action required
    HIGH          # Important, review soon
    MEDIUM        # Interesting, review when convenient
    LOW           # Nice-to-have suggestion

class Evidence:
    example_id: str              # Neo4j node ID
    example_type: str            # NODE, RELATIONSHIP, PATTERN
    properties: Dict[str, Any]   # Node/rel properties
    context: str                 # Why this is evidence
    frequency: int               # Occurrence count

class ImpactAnalysis:
    affected_entities_count: int
    affected_relationships_count: int
    breaking_change: bool
    migration_complexity: str    # LOW, MEDIUM, HIGH
    estimated_effort_hours: float
    benefits: List[str]
    risks: List[str]

class OntologyChangeProposal:
    proposal_id: str             # Unique ID (OSS_YYYYMMDD_HHMMSS_UUID)
    change_type: ChangeType
    severity: Severity
    title: str
    description: str
    evidence: List[Evidence]
    pattern_query: str           # Cypher query that found it
    occurrence_count: int
    confidence: float            # 0.0-1.0
    confidence_factors: Dict[str, float]
    impact_analysis: ImpactAnalysis
    validation_checks: List[str]
    tags: List[str]

class AnalysisResult:
    cycle_id: str
    started_at: datetime
    completed_at: datetime
    patterns_detected: int
    inconsistencies_detected: int
    proposals_generated: int
    proposals_submitted: int
    errors: List[str]
    warnings: List[str]
    proposals: List[OntologyChangeProposal]
```

---

## Pattern Detection System

The Pattern Detector identifies frequently occurring patterns in the knowledge graph that suggest new entity or relationship types should be created.

### Entity Type Pattern Detection

**How It Works:**

1. Query Neo4j for all Entity nodes with entity_type values
2. Count occurrences of each entity_type
3. Filter for types with >= MIN_PATTERN_OCCURRENCES (default: 10)
4. Generate proposal for each significant type

**Cypher Query:**
```cypher
MATCH (n:Entity)
WHERE n.entity_type IS NOT NULL
  AND n.entity_type <> 'UNKNOWN'
  AND n.entity_type <> 'ARTICLE'
WITH n.entity_type AS type,
     count(*) AS count,
     collect(id(n)) AS node_ids
WHERE count >= $min_occurrences
RETURN type, count, node_ids[0..5] AS sample_ids
ORDER BY count DESC
LIMIT 20
```

**Proposal Generation:**
- Title: "Frequent entity type pattern: {TYPE_NAME}"
- Change Type: NEW_ENTITY_TYPE
- Severity: HIGH (if count > 50) or MEDIUM
- Confidence: min(0.5 + (count/100)*0.4, 0.95)

**Example Output:**
```json
{
  "proposal_id": "OSS_20251124_143022_abc12345",
  "change_type": "NEW_ENTITY_TYPE",
  "severity": "HIGH",
  "title": "Frequent entity type pattern: CyberAttackGroup",
  "occurrence_count": 47,
  "confidence": 0.92,
  "evidence": [
    {
      "example_id": "12345",
      "example_type": "NODE",
      "context": "Example node with type 'CyberAttackGroup'",
      "frequency": 47
    }
  ]
}
```

### Relationship Type Pattern Detection

**How It Works:**

1. Query for RELATED_TO relationships between Entity nodes
2. Group by (source_type, target_type) pairs
3. Count occurrences of each pair
4. Filter for pairs with >= 5 occurrences
5. Generate proposal for each significant pair

**Cypher Query:**
```cypher
MATCH (a:Entity)-[r:RELATED_TO]->(b:Entity)
WHERE a.entity_type IS NOT NULL
  AND b.entity_type IS NOT NULL
  AND a.entity_type <> 'UNKNOWN'
  AND b.entity_type <> 'UNKNOWN'
  AND a.entity_type <> 'ARTICLE'
  AND b.entity_type <> 'ARTICLE'
WITH a.entity_type AS source_type,
     b.entity_type AS target_type,
     count(*) AS count
WHERE count >= 5
RETURN source_type, target_type, count
ORDER BY count DESC
LIMIT 10
```

**Proposal Generation:**
- Title: "Frequent relationship pattern: {SOURCE} → {TARGET}"
- Change Type: NEW_RELATIONSHIP_TYPE
- Severity: MEDIUM
- Confidence: min(0.5 + (count/50)*0.3, 0.90)

**Example Output:**
```json
{
  "proposal_id": "OSS_20251124_143022_def67890",
  "change_type": "NEW_RELATIONSHIP_TYPE",
  "severity": "MEDIUM",
  "title": "Frequent relationship pattern: CyberAttackGroup → Country",
  "occurrence_count": 31,
  "confidence": 0.88
}
```

---

## Inconsistency Detection System

The Inconsistency Detector proactively identifies data quality issues that violate ontology rules or standards.

### ISO Code Violations

**Problem:** Country entities with non-standard ISO 3166-1 alpha-2 codes

**Detection Criteria:**
- entity_type = 'COUNTRY' or 'Country' label
- entity_id length != 2 OR contains lowercase characters OR is NULL

**Cypher Query:**
```cypher
MATCH (c)
WHERE (c.entity_type = 'COUNTRY' OR 'Country' IN labels(c))
  AND (
    size(c.entity_id) <> 2 OR
    c.entity_id =~ '.*[^A-Z].*' OR
    c.entity_id IS NULL
  )
RETURN c.entity_id, c.name, labels(c), id(c)
LIMIT 50
```

**Proposal Details:**
- Change Type: FLAG_INCONSISTENCY
- Severity: CRITICAL (confidence: 1.0)
- Examples: "UKR" (should be "UA"), "Ukraine" (null entity_id)

### Duplicate Entity Detection

**Problem:** Multiple Entity nodes with the same entity_id

**Detection Criteria:**
- entity_id is not NULL
- Multiple nodes share the same entity_id value

**Cypher Query:**
```cypher
MATCH (n)
WHERE n.entity_id IS NOT NULL
WITH n.entity_id AS id, collect(n) AS nodes
WHERE size(nodes) > 1
RETURN id, size(nodes) AS duplicate_count,
       [node IN nodes | id(node)][0..5] AS sample_node_ids
LIMIT 20
```

**Proposal Details:**
- Change Type: FLAG_INCONSISTENCY
- Severity: HIGH (confidence: 1.0)
- Impact: Merge or deduplicate nodes

### Missing Required Properties

**Problem:** Entity nodes missing mandatory properties

**Detection Criteria:**
- entity_id IS NULL OR entity_type IS NULL OR name IS NULL
- NOT 'Article' label (articles aren't entities)
- NOT 'Symbolic' label (intelligence findings)
- name quality checks (not generic, not UUID, reasonable length)

**Cypher Query:**
```cypher
MATCH (e:Entity)
WHERE (e.entity_id IS NULL OR e.entity_type IS NULL OR e.name IS NULL)
  AND NOT 'Article' IN labels(e)
  AND NOT 'Symbolic' IN labels(e)
  AND e.name IS NOT NULL
  AND NOT e.name STARTS WITH 'Article '
  AND size(e.name) > 2
  AND size(e.name) < 200
RETURN id(e), labels(e), e.entity_id, e.entity_type, e.name
LIMIT 50
```

**Proposal Details:**
- Change Type: FLAG_INCONSISTENCY
- Severity: HIGH (confidence: 1.0)
- Required properties: entity_id, entity_type, name

**Quality Filters Applied:**
- Excludes articles and symbolic nodes
- Skips generic terms (president, senate, house, etc.)
- Skips UUIDs and very long names
- Skips demonyms and generic titles

### Unknown Entity Type Detection

**Problem:** Entity nodes with entity_type='UNKNOWN' (massive data quality issue)

**Detection Criteria:**
- entity_type = 'UNKNOWN' exactly

**Cypher Query:**
```cypher
MATCH (e:Entity)
WHERE e.entity_type = 'UNKNOWN'
RETURN count(*) AS unknown_count,
       collect(id(e))[0..10] AS sample_ids
```

**Proposal Details:**
- Change Type: FLAG_INCONSISTENCY
- Severity: CRITICAL (confidence: 1.0)
- Indicates NLP/NER pipeline failure
- Affects 82.8% of entities in test environment
- Estimated effort: 40+ hours to fix

**Root Cause Indicators:**
- NER model not returning entity types
- Entity extraction filtering out type information
- Mapping errors between extraction and storage

### Article Entity Detection

**Problem:** Article UUIDs incorrectly stored as Entity nodes

**Detection Criteria:**
- entity_type = 'ARTICLE' exactly
- name starts with 'Article '

**Cypher Query:**
```cypher
MATCH (e:Entity)
WHERE e.entity_type = 'ARTICLE'
   OR e.name STARTS WITH 'Article '
RETURN count(*) AS article_count,
       collect(id(e))[0..10] AS sample_ids,
       collect(e.name)[0..5] AS sample_names
```

**Proposal Details:**
- Change Type: FLAG_INCONSISTENCY
- Severity: HIGH (confidence: 1.0)
- These are metadata artifacts, not semantic entities
- Recommended action: Delete from Entity graph

---

## Proposal Generation & Submission

### Proposal Generation Process

Each analyzer creates proposals through a multi-step process:

1. **Execute Query:** Run Cypher query against Neo4j
2. **Process Results:** Transform query results into evidence
3. **Build Proposal:** Create OntologyChangeProposal with:
   - Unique ID (OSS_YYYYMMDD_HHMMSS_UUID)
   - Change type and severity
   - Title and detailed description
   - Concrete evidence examples
   - Pattern query for reproducibility
   - Confidence score and factors
   - Impact analysis (affected count, effort, risks)
   - Tags for categorization
4. **Return:** Return proposal objects for filtering and submission

### Confidence Scoring

Confidence is calculated based on multiple factors:

**Pattern Detection Confidence:**
```python
# Entity Type Patterns
frequency_factor = min(count / 100, 1.0)
consistency_factor = 0.8  # Assumed consistency
confidence = min(0.5 + (count/100)*0.4, 0.95)

# Relationship Patterns
confidence = min(0.5 + (count/50)*0.3, 0.90)
```

**Inconsistency Detection Confidence:**
```python
# ISO Code Violations: confidence = 1.0 (always a violation)
# Duplicates: confidence = 1.0 (data integrity issue)
# Missing Properties: confidence = 1.0 (missing required data)
# Unknown Types: confidence = 1.0 (pipeline failure)
# Article Entities: confidence = 1.0 (metadata artifact)
```

### Proposal Submission

After confidence filtering (>= CONFIDENCE_THRESHOLD), proposals are submitted:

```python
async def submit_proposal_to_api(proposal: OntologyChangeProposal) -> bool:
    """Submit proposal to Ontology Proposals API"""
    try:
        url = f"{PROPOSALS_API_URL}/api/v1/ontology/proposals"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=proposal.model_dump(mode="json"),
                timeout=10.0
            )
            if response.status_code == 201:
                logger.info(f"Submitted proposal {proposal.proposal_id} successfully")
                return True
            else:
                logger.error(f"Failed to submit proposal: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Error submitting proposal: {e}")
        return False
```

**Submission Flow:**
1. POST proposal JSON to `/api/v1/ontology/proposals`
2. Check for 201 Created response
3. Log success/failure with proposal ID
4. Continue with next proposal even if one fails (fault tolerance)

---

## Scheduled Analysis

OSS uses **APScheduler** to run analysis cycles automatically at configured intervals.

### Scheduler Implementation

**Startup (in lifespan):**
```python
scheduler = AsyncIOScheduler()
scheduler.add_job(
    scheduled_analysis_job,
    'interval',
    seconds=settings.ANALYSIS_INTERVAL_SECONDS,
    id='oss_analysis',
    replace_existing=True
)
scheduler.start()
```

**Job Function:**
```python
async def scheduled_analysis_job():
    """Background job that runs OSS analysis periodically"""
    try:
        logger.info("Running scheduled OSS analysis cycle")
        result = await analysis.run_analysis_cycle(neo4j_connection)
        logger.info(f"Scheduled analysis completed: "
                   f"{result.proposals_generated} proposals generated, "
                   f"{result.proposals_submitted} proposals submitted")
    except Exception as e:
        logger.error(f"Scheduled analysis failed: {e}", exc_info=True)
```

### Configuration

**Via Environment Variables:**
```bash
# Set interval in docker-compose.yml
environment:
  - ANALYSIS_INTERVAL_SECONDS=3600  # 1 hour (production)
  - ANALYSIS_INTERVAL_SECONDS=1800  # 30 minutes (standard testing)
  - ANALYSIS_INTERVAL_SECONDS=300   # 5 minutes (development/quick testing)
```

**Restart Service:**
```bash
docker compose restart oss-service
```

### Monitoring Scheduled Runs

```bash
# Watch logs for scheduled runs
docker logs -f oss-service 2>&1 | grep "scheduled"

# Expected output:
# 2025-11-24 08:21:34 - app.main - INFO - Running scheduled OSS analysis cycle
# 2025-11-24 08:21:45 - app.main - INFO - Scheduled analysis completed: 6 proposals...
```

### Manual Triggering

Scheduled analysis and manual triggering are independent:

```bash
# Manual trigger (doesn't affect scheduler)
curl -X POST http://localhost:8110/api/v1/analysis/run

# Both run automatically:
# - Scheduler runs at configured interval
# - Manual trigger on-demand via API
```

---

## API Reference

### Health Check

#### `GET /health`

Service health check for monitoring and load balancers.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "OSS Service",
  "version": "1.0.0",
  "timestamp": "2025-11-24T14:30:22Z",
  "neo4j": "connected",
  "proposals_api": "http://ontology-proposals-service:8109"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "service": "OSS Service",
  "version": "1.0.0",
  "timestamp": "2025-11-24T14:30:22Z",
  "neo4j": "disconnected",
  "proposals_api": "http://ontology-proposals-service:8109"
}
```

### Root Endpoint

#### `GET /`

Service information and documentation links.

**Response (200 OK):**
```json
{
  "service": "OSS Service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "description": "Ontology Suggestion System - Learns from knowledge graph to suggest improvements"
}
```

### Trigger Analysis

#### `POST /api/v1/analysis/run`

Trigger a manual analysis cycle. Returns immediately with analysis result.

**Request:**
```bash
curl -X POST http://localhost:8110/api/v1/analysis/run
```

**Response (200 OK):**
```json
{
  "cycle_id": "cycle_20251124_143022_abc12345",
  "started_at": "2025-11-24T14:30:22Z",
  "completed_at": "2025-11-24T14:30:45Z",
  "patterns_detected": 5,
  "inconsistencies_detected": 3,
  "proposals_generated": 6,
  "proposals_submitted": 6,
  "errors": [],
  "warnings": [],
  "proposals": [
    {
      "proposal_id": "OSS_20251124_143022_abc12345",
      "change_type": "NEW_ENTITY_TYPE",
      "severity": "HIGH",
      "title": "Frequent entity type pattern: CyberAttackGroup",
      "occurrence_count": 47,
      "confidence": 0.92,
      ...
    }
  ]
}
```

### Get Status

#### `GET /api/v1/analysis/status`

Get service status and configuration.

**Request:**
```bash
curl http://localhost:8110/api/v1/analysis/status
```

**Response (200 OK):**
```json
{
  "service": "OSS Service",
  "version": "1.0.0",
  "status": "operational",
  "neo4j_connected": true,
  "proposals_api": "http://ontology-proposals-service:8109",
  "analysis_interval_seconds": 3600,
  "min_pattern_occurrences": 10,
  "confidence_threshold": 0.7
}
```

---

## Data Models

### OntologyChangeProposal

Complete structure of an ontology change proposal.

```python
{
  # Identification
  "proposal_id": "OSS_20251124_143022_abc12345",
  "change_type": "NEW_ENTITY_TYPE" | "NEW_RELATIONSHIP_TYPE" | "FLAG_INCONSISTENCY" | ...,
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",

  # Content
  "title": "Short, descriptive title",
  "description": "Detailed explanation with context...",
  "definition": "Optional schema definition",

  # Evidence
  "evidence": [
    {
      "example_id": "12345",
      "example_type": "NODE" | "RELATIONSHIP" | "PATTERN",
      "properties": { "entity_id": "...", "name": "..." },
      "context": "Why this is evidence",
      "frequency": 47
    }
  ],
  "pattern_query": "Cypher query that found this",
  "occurrence_count": 47,

  # Confidence & Validation
  "confidence": 0.92,
  "confidence_factors": {
    "frequency": 0.9,
    "consistency": 0.95,
    "data_quality": 1.0
  },
  "validation_checks": [
    "No conflicting entity types found",
    "Properties are consistent"
  ],

  # Impact
  "impact_analysis": {
    "affected_entities_count": 47,
    "affected_relationships_count": 0,
    "breaking_change": false,
    "migration_complexity": "MEDIUM",
    "estimated_effort_hours": 4.0,
    "benefits": [
      "Better data organization",
      "Improved query performance"
    ],
    "risks": [
      "Need to migrate 47 existing nodes"
    ]
  },

  # Metadata
  "oss_version": "1.0.0",
  "related_proposals": ["OSS_20251124_143022_xyz"],
  "tags": ["pattern-detection", "entity-type", "cyberattackgroup"]
}
```

### AnalysisResult

Result of a complete analysis cycle.

```python
{
  "cycle_id": "cycle_20251124_143022_abc12345",
  "started_at": "2025-11-24T14:30:22Z",
  "completed_at": "2025-11-24T14:30:45Z",
  "patterns_detected": 5,
  "inconsistencies_detected": 3,
  "proposals_generated": 6,
  "proposals_submitted": 6,
  "errors": [],
  "warnings": [],
  "proposals": [...]
}
```

---

## Neo4j Integration

### Connection Management

**Initialization:**
```python
class Neo4jConnection:
    def __init__(self):
        self._driver: Optional[Driver] = None

    def connect(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
```

**Query Execution:**
```python
def execute_read(self, query: str, parameters: Optional[Dict] = None):
    driver = self.connect()
    with driver.session(database=settings.NEO4J_DATABASE) as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]
```

### Connection Settings

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| NEO4J_URI | str | bolt://neo4j:7687 | Protocol + host:port |
| NEO4J_USER | str | neo4j | Authentication user |
| NEO4J_PASSWORD | str | news_graph_2024 | Authentication password |
| NEO4J_DATABASE | str | neo4j | Database name |

### Connection Pooling

The Neo4j Python driver automatically manages:
- Connection pool (default: 50 connections)
- Idle timeout (default: 30 seconds)
- Connection acquisition timeout
- Automatic reconnection on failure

---

## Configuration

### Environment Variables

All settings are loaded from environment variables with fallback defaults:

```bash
# Application
APP_NAME=OSS Service                                  # Service name
APP_VERSION=1.0.0                                     # Version
DEBUG=true                                            # Enable debug mode
ENVIRONMENT=development                               # development|production

# Server
HOST=0.0.0.0                                          # Bind address
PORT=8110                                             # HTTP port

# Neo4j
NEO4J_URI=bolt://neo4j:7687                          # Connection URI
NEO4J_USER=neo4j                                      # Username
NEO4J_PASSWORD=news_graph_2024                        # Password
NEO4J_DATABASE=neo4j                                  # Database name

# Ontology Proposals API
PROPOSALS_API_URL=http://ontology-proposals-service:8109

# Analysis Configuration
ANALYSIS_INTERVAL_SECONDS=3600                        # Scheduled interval
MIN_PATTERN_OCCURRENCES=10                            # Pattern threshold
CONFIDENCE_THRESHOLD=0.7                              # Confidence filter

# Logging
LOG_LEVEL=INFO                                        # DEBUG|INFO|WARNING|ERROR
LOG_FORMAT=text                                       # text or json
```

### Docker Compose Configuration

```yaml
oss-service:
  build:
    context: ./services/oss-service
    dockerfile: Dockerfile.dev
  ports:
    - "8110:8110"
  environment:
    - APP_NAME=OSS Service
    - DEBUG=true
    - ENVIRONMENT=development
    - NEO4J_URI=bolt://neo4j:7687
    - NEO4J_USER=neo4j
    - NEO4J_PASSWORD=news_graph_2024
    - PROPOSALS_API_URL=http://ontology-proposals-service:8109
    - ANALYSIS_INTERVAL_SECONDS=3600
    - MIN_PATTERN_OCCURRENCES=10
    - CONFIDENCE_THRESHOLD=0.7
    - LOG_LEVEL=INFO
  depends_on:
    - neo4j
    - ontology-proposals-service
  networks:
    - network
  volumes:
    - ./services/oss-service/app:/app/app:ro
```

---

## Deployment

### Production Deployment

**Requirements:**
- Python 3.11+
- Neo4j 4.4+ (read access only)
- Ontology Proposals Service running
- Uvicorn or similar ASGI server
- Optional: Gunicorn with multiple workers

**Deployment Steps:**

1. **Build Docker Image:**
   ```bash
   docker build -f services/oss-service/Dockerfile.prod \
                -t oss-service:1.0.0 \
                services/oss-service/
   ```

2. **Configure Environment:**
   ```bash
   # .env.prod
   ENVIRONMENT=production
   DEBUG=false
   LOG_FORMAT=json
   LOG_LEVEL=WARNING
   # ... other settings
   ```

3. **Run with Gunicorn:**
   ```bash
   gunicorn app.main:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8110 \
     --access-logfile - \
     --error-logfile -
   ```

4. **Or Use Docker:**
   ```bash
   docker run -d \
     --name oss-service \
     -p 8110:8110 \
     --env-file .env.prod \
     --network network \
     oss-service:1.0.0
   ```

### Health Checks

**Kubernetes Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8110
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 8110
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## Monitoring & Observability

### Key Metrics

- **Analysis Cycle Duration:** Time to complete analysis (target: < 60s)
- **Patterns Detected:** Number of patterns per cycle
- **Inconsistencies Found:** Data quality issues per cycle
- **Proposals Generated:** Proposals after confidence filtering
- **Proposals Submitted:** Successfully submitted to API
- **Submission Success Rate:** % of proposals successfully submitted
- **Neo4j Query Performance:** Time per Cypher query

### Logging

**Log Levels:**
- DEBUG: Detailed execution flow, query results
- INFO: Analysis cycle progress, proposals submitted
- WARNING: Neo4j connection issues, submission failures
- ERROR: Critical failures, exceptions

**Log Format (JSON):**
```json
{
  "timestamp": "2025-11-24T14:30:22Z",
  "logger": "app.api.analysis",
  "level": "INFO",
  "message": "Submitted proposal OSS_20251124_143022_abc12345 successfully"
}
```

### Monitoring Commands

```bash
# View recent logs
docker logs oss-service | tail -50

# Watch live logs
docker logs -f oss-service

# Filter for analysis cycles
docker logs oss-service 2>&1 | grep "analysis"

# Filter for errors
docker logs oss-service 2>&1 | grep "ERROR"

# Filter for proposals submitted
docker logs oss-service 2>&1 | grep "Submitted proposal"

# Check scheduler status
docker logs oss-service 2>&1 | grep "scheduler"
```

---

## Performance Characteristics

### Analysis Cycle Performance

**Benchmarks (typical):**

| Phase | Duration | Queries | Notes |
|-------|----------|---------|-------|
| Entity Pattern Detection | 1-5s | 1 Cypher | Graph size dependent |
| Relationship Pattern Detection | 1-5s | 1 Cypher | Scans all relationships |
| ISO Code Violations | <1s | 1 Cypher | Country subset |
| Duplicate Detection | 2-10s | 1 Cypher | Full graph scan |
| Missing Properties | 5-15s | 1 Cypher | Entity nodes only |
| Unknown Types | <1s | 1 Cypher | entity_type filter |
| Article Entities | <1s | 1 Cypher | entity_type filter |
| Proposal Submission | 6-8s | 6+ HTTP | Rate limited by API |
| **Total Cycle** | **20-50s** | **~8 queries** | Parallel submission |

### Query Performance Optimization

**Current Optimizations:**
- LIMIT clauses prevent full table scans
- Indexed properties (entity_type, entity_id, labels)
- WHERE filters applied early
- Sample collection (first 5-10 for evidence)

**Future Opportunities:**
- Parallel query execution
- Query result caching (if graph is static)
- Batch proposal submission
- Async Cypher execution

### Resource Usage

**Memory:**
- Base: ~50MB (process overhead)
- Per-connection: ~5MB
- Analysis cycle: ~100MB (query result buffering)

**CPU:**
- Idle: <1%
- During analysis: 10-20%
- Most time in Neo4j, not processing

### Neo4j API Rate Limits

**Considerations:**
- Driver connection pooling: 50 connections default
- Query timeout: Configurable, recommend 30s
- HTTP submission timeout: 10s per proposal

---

## Troubleshooting

### Neo4j Connection Failed

**Symptoms:**
- Health check returns degraded
- All analysis cycles fail

**Diagnosis:**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Test direct connection
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 "RETURN 1"

# Check OSS config
docker exec oss-service env | grep NEO4J

# Check logs
docker logs oss-service 2>&1 | grep "Neo4j"
```

**Solutions:**
1. Verify Neo4j service is running: `docker compose up -d neo4j`
2. Verify credentials are correct
3. Check network connectivity: `docker network inspect network`
4. Restart OSS service: `docker compose restart oss-service`

### Proposals Not Submitting

**Symptoms:**
- Proposals generated = 6, proposals_submitted = 0
- Logs show "Failed to submit proposal"

**Diagnosis:**
```bash
# Check Proposals API is running
curl http://localhost:8109/health

# Check from OSS container
docker exec oss-service curl http://ontology-proposals-service:8109/health

# Check logs for submission errors
docker logs oss-service 2>&1 | grep "submit"

# Verify API endpoint
curl -v http://ontology-proposals-service:8109/api/v1/ontology/proposals
```

**Solutions:**
1. Start Proposals Service: `docker compose up -d ontology-proposals-service`
2. Check network: `docker network connect network oss-service`
3. Verify API URL: Check PROPOSALS_API_URL in status endpoint
4. Increase HTTP timeout: Modify httpx timeout in code

### No Proposals Generated

**Symptoms:**
- Analysis completes, but patterns_detected = 0

**Diagnosis:**
```bash
# Check if Neo4j has data
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (n) RETURN count(n)"

# Check Entity nodes specifically
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (n:Entity) RETURN count(n)"

# Check entity_type distribution
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (e:Entity) RETURN e.entity_type, count(*) \
   ORDER BY count(*) DESC LIMIT 10"
```

**Solutions:**
1. Load sample data into Neo4j: See feed-service docs
2. Lower MIN_PATTERN_OCCURRENCES: `MIN_PATTERN_OCCURRENCES=5`
3. Verify queries execute manually
4. Check query logs: `LOG_LEVEL=DEBUG`

### Scheduler Not Running

**Symptoms:**
- Manual trigger works: `POST /api/v1/analysis/run`
- Automatic analysis doesn't happen

**Diagnosis:**
```bash
# Check scheduler logs
docker logs oss-service 2>&1 | grep "scheduler"

# Expected at startup:
# "Starting background scheduler with interval: 3600s"
# "Background scheduler started"

# Check if scheduled runs are happening
docker logs oss-service 2>&1 | grep "scheduled" | tail -5

# Verify APScheduler is installed
docker exec oss-service pip list | grep -i apscheduler
```

**Solutions:**
1. Verify APScheduler is installed: `pip install apscheduler==3.10.4`
2. Check service logs for startup errors
3. Verify ANALYSIS_INTERVAL_SECONDS is set
4. Restart service: `docker compose restart oss-service`

### Scheduled Analysis Not Running

**Symptoms:**
- Scheduler started but no scheduled runs in logs

**Diagnosis:**
```bash
# Check last scheduled run
docker logs oss-service 2>&1 | grep "scheduled" | tail -1

# Check interval setting
curl http://localhost:8110/api/v1/analysis/status | \
  grep analysis_interval

# Manual trigger to verify functionality
curl -X POST http://localhost:8110/api/v1/analysis/run
```

**Solutions:**
1. Check service uptime: Has it been running longer than interval?
2. Change interval to test: `ANALYSIS_INTERVAL_SECONDS=60` (1 minute)
3. Force service restart: `docker compose up -d --force-recreate oss-service`
4. Check logs for exceptions: `LOG_LEVEL=DEBUG`

### Change Scheduler Interval

```bash
# Stop service
docker compose stop oss-service

# Edit docker-compose.yml
# Add/update under oss-service environment:
#   - ANALYSIS_INTERVAL_SECONDS=300  # 5 minutes for testing

# Restart
docker compose up -d --force-recreate oss-service

# Verify
curl http://localhost:8110/api/v1/analysis/status | \
  grep analysis_interval_seconds
# Expected: "analysis_interval_seconds": 300
```

---

## Code Examples

### Manual Analysis Trigger

```bash
# Trigger analysis
curl -X POST http://localhost:8110/api/v1/analysis/run \
  -H "Content-Type: application/json" | jq

# Parse response
curl -s http://localhost:8110/api/v1/analysis/run | jq '.proposals_generated'
# Expected: 5-10
```

### Check Service Status

```bash
# Get configuration
curl http://localhost:8110/api/v1/analysis/status | jq

# Check Neo4j connectivity
curl http://localhost:8110/api/v1/analysis/status | jq '.neo4j_connected'
# Expected: true
```

### Watch Scheduled Runs

```bash
# Real-time monitoring
docker logs -f oss-service 2>&1 | grep -E "scheduled|proposal"

# Wait for analysis to run and count output
# Sample output:
# 2025-11-24 14:21:34 - INFO - Running scheduled OSS analysis cycle
# 2025-11-24 14:21:45 - INFO - Detected 5 entity patterns
# 2025-11-24 14:21:46 - INFO - Detected 3 inconsistencies
# 2025-11-24 14:21:50 - INFO - Submitted 8 proposals
```

### Query Entity Types

```bash
# Find all entity types in graph
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (e:Entity) \
   WHERE e.entity_type IS NOT NULL \
   RETURN DISTINCT e.entity_type, count(*) \
   ORDER BY count(*) DESC"

# Find high-frequency types (candidates for proposals)
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (e:Entity) \
   WHERE e.entity_type IS NOT NULL AND e.entity_type <> 'UNKNOWN' \
   WITH e.entity_type AS type, count(*) AS cnt \
   WHERE cnt >= 10 \
   RETURN type, cnt ORDER BY cnt DESC"
```

### Verify Data Quality

```bash
# Check for duplicates
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (n) \
   WHERE n.entity_id IS NOT NULL \
   WITH n.entity_id AS id, count(*) AS cnt \
   WHERE cnt > 1 \
   RETURN id, cnt ORDER BY cnt DESC LIMIT 10"

# Check for missing properties
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (e:Entity) \
   WHERE e.entity_id IS NULL OR e.entity_type IS NULL OR e.name IS NULL \
   RETURN count(*) AS missing_properties"

# Check for unknown types
docker exec neo4j cypher-shell -u neo4j -p news_graph_2024 \
  "MATCH (e:Entity) \
   WHERE e.entity_type = 'UNKNOWN' \
   RETURN count(*) AS unknown_count"
```

---

## Future Enhancements

### Short-term (1-2 months)

1. **Approval Rate Tracking**
   - Track which proposals are approved vs rejected
   - Calculate approval rates by change type
   - Monitor proposal quality over time

2. **Confidence Calibration**
   - Adjust confidence factors based on approval history
   - Learn from human feedback
   - Improve future proposal quality

3. **Advanced Validation**
   - Validate content-analysis-v2 output
   - Cross-reference with external sources
   - Detect conflicting proposals

### Medium-term (3-6 months)

1. **Machine Learning Integration**
   - Train classifier on approved/rejected proposals
   - Predict approval likelihood
   - Auto-recommend high-confidence changes

2. **Trend Analysis**
   - Weekly/monthly reports on data quality
   - Track evolution of entity types over time
   - Identify systemic issues (e.g., NLP failures)

3. **Auto-approval**
   - Auto-approve very high confidence proposals (confidence > 0.95)
   - Reduce human review overhead
   - Implement safeguards for critical changes

### Long-term (6-12 months)

1. **Formal Ontology Integration**
   - Integrate with OWL/RDF formal ontology repository
   - Automatic schema generation
   - Reasoning over proposed changes

2. **Advanced Notifications**
   - Slack/Email alerts for critical proposals
   - Daily/weekly digests
   - Escalation for stale proposals

3. **Analytics Dashboard**
   - Visualization of data quality metrics
   - Proposal pipeline analytics
   - Impact tracking of implemented changes

---

## Related Services

- **Ontology Proposals Service** (8109): Receives and implements proposals
- **Knowledge Graph Service** (8111): Stores and exposes Neo4j graphs
- **Content Analysis Service** (v3): Entity extraction pipeline
- **NLP Extraction Service** (8107): Named entity recognition

---

## Support & Documentation

- **API Documentation:** `http://localhost:8110/docs` (Swagger UI)
- **Service README:** `/home/cytrex/news-microservices/services/oss-service/README.md`
- **Architecture Docs:** `/home/cytrex/userdocs/system-ontology/07_OSS_SPECIFICATION.md`
- **Ontology Proposals:** `/home/cytrex/userdocs/doku-update241125/docs/ontology-proposals.md`

---

**Service Status:** ✅ Production Ready

**Last Updated:** 2025-11-24
**Next Review:** 2025-12-01
