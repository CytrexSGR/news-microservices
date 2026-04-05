# News MCP Common Library

Shared library for News MCP microservices providing common functionality for:
- Authentication and authorization
- Database connections and session management
- Event publishing and consuming (RabbitMQ)
- Observability (OpenTelemetry, Prometheus)
- Configuration management
- Resilience patterns (Circuit Breaker, Retry)

**Version:** 0.1.0
**Status:** Production
**Last Updated:** 2025-11-03

## Installation

### ⚠️ CRITICAL: For Services (Required)

**Every service that imports from `news_mcp_common` MUST declare it in `requirements.txt`:**

```txt
# services/your-service/requirements.txt

# Shared MCP Common Library (REQUIRED)
-e ../../shared/news-mcp-common

# Other dependencies...
```

**Why this is critical:**
- Without this entry, the service will crash with `ModuleNotFoundError: no module named 'news_mcp_common'`
- Docker restarts clear Python import cache, exposing missing dependencies
- See [Incident #10 in POSTMORTEMS.md](../../POSTMORTEMS.md#incident-10-feed-service-dependency-failure-after-docker-restart-2025-11-03) for real-world impact (30 min outage)

**Services currently using news-mcp-common:**
- ✅ content-analysis-v2 - Has dependency declared
- ✅ notification-service - Has dependency declared
- ✅ research-service - Has dependency declared
- ✅ feed-service - **Fixed 2025-11-03** (was missing, caused outage)

**Before adding import to new service:**
1. ✅ Add `-e ../../shared/news-mcp-common` to service's requirements.txt
2. ✅ Test with fresh Docker build: `docker compose up -d --build <service>`
3. ✅ Verify health: `docker ps` should show `(healthy)` status
4. ✅ Check logs: `docker logs <service>` should have no ModuleNotFoundError

### For Development

```bash
# Clone the repository
cd /home/cytrex/news-microservices/shared/news-mcp-common

# Install in editable mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Emergency Fix (Running Container)

If you need to install manually in a running container (for immediate fixes):

```bash
# 1. Install the package
docker exec <container-name> pip install -e /app/shared/news-mcp-common

# 2. Verify installation
docker exec <container-name> python3 -c "import news_mcp_common; print('✅ Installed')"

# 3. Restart service
docker restart <container-name>

# 4. ⚠️ IMPORTANT: Add to requirements.txt permanently!
```

## Usage

### Authentication Module

```python
from news_mcp_common.auth import JWTHandler, verify_token, require_roles

jwt_handler = JWTHandler()

# Create token
token = jwt_handler.create_access_token(user_id=1, roles=["admin"])

# Verify token in FastAPI
from fastapi import Depends
from news_mcp_common.auth import get_current_user

@app.get("/protected")
async def protected_route(current_user=Depends(get_current_user)):
    return {"user": current_user}
```

### Database Module

```python
from news_mcp_common.database import get_db_session, BaseModel

# In your FastAPI app
@app.get("/items")
async def get_items(db=Depends(get_db_session)):
    items = await db.execute(select(Item))
    return items.scalars().all()
```

### Events Module

```python
from news_mcp_common.events import EventPublisher, EventConsumer

# Publishing events
publisher = EventPublisher()
await publisher.publish("feed.article.created", {
    "article_id": 123,
    "title": "Breaking News"
})

# Consuming events
consumer = EventConsumer()
await consumer.subscribe("feed.article.*", callback=handle_article_event)
```

### Observability Module

```python
from news_mcp_common.observability import setup_tracing, track_request

# Setup in your main app
setup_tracing("auth-service")

# Track custom metrics
track_request("login", duration=0.123, success=True)
```

### Resilience Module (Circuit Breaker)

```python
from news_mcp_common.resilience import (
    CircuitBreakerState,
    create_circuit_breaker,
)

# Create circuit breaker for external API
perplexity_cb = create_circuit_breaker(
    name="perplexity-api",
    failure_threshold=5,
    timeout_seconds=60
)

# Use in async function
@perplexity_cb
async def call_perplexity_api():
    # Your API call here
    pass
```

### Configuration Module

```python
from news_mcp_common.config import settings

# Access configuration
print(settings.postgres_host)
print(settings.redis_url)
print(settings.jwt_secret)
```

### Ontology Package

**NEW in v0.1.0:** Formal ontology definitions for entity and relationship types.

The ontology package provides canonical type definitions and shared primitives for the news intelligence system's property graph ontology. This implements a three-layer architecture:

1. **Schema Layer**: EntityType and RelationshipType enums
2. **Primitives Layer**: EntityReference, RelationshipHint, ConfidenceMetadata models
3. **Instance Layer**: Actual graph nodes and relationships (in Neo4j)

**Quick Start:**

```python
from news_mcp_common.ontology import (
    EntityType,
    RelationshipType,
    EntityReference,
    RelationshipHint,
    ConfidenceMetadata,
)

# Create entity reference (with validation)
country = EntityReference(
    entity_id="US",  # ISO 3166-1 alpha-2 (validated)
    entity_type=EntityType.COUNTRY,
    name="United States",
    wikidata_id="Q30",
    aliases=["USA", "United States of America"]
)

# Create relationship hint
company = EntityReference(
    entity_id="TSLA",  # Stock ticker (validated)
    entity_type=EntityType.COMPANY,
    name="Tesla Inc."
)

market = EntityReference(
    entity_id="NASDAQ",
    entity_type=EntityType.MARKET,
    name="NASDAQ"
)

relationship = RelationshipHint(
    source=company,
    target=market,
    relationship_type=RelationshipType.IMPACTS_STOCK,
    confidence=0.92,
    evidence="Tesla stock surged 12% on NASDAQ."
)

# Track confidence metadata
metadata = ConfidenceMetadata(
    overall_confidence=0.92,
    supporting_agents=["claude-3.5-sonnet", "gpt-4"],
    evidence_count=3,
    source_count=2,
    is_validated=True,
    validation_method="OSS_cross_check"
)

print(metadata.derive_uncertainty())  # "low"
print(metadata.should_trigger_review())  # False (confidence above threshold)
```

**MVO Phase 1 Entity Types:**
- `COMPANY`: Stock ticker-based entities (e.g., "TSLA", "AAPL")
- `CRITICAL_INFRASTRUCTURE`: Infrastructure entities
- `WEAPON_SYSTEM`: Military systems
- `COUNTRY`: ISO 3166-1 alpha-2 codes (e.g., "US", "RU", "UA")
- `ORGANIZATION`: Non-corporate organizations
- `PERSON`: Individuals
- `LOCATION`: Geographic locations
- `MARKET`: Financial markets (e.g., "NASDAQ", "NYSE")

**MVO Phase 1 Relationship Types:**
- `DISRUPTS_OPERATIONS`: Operational disruption
- `DISRUPTS_SUPPLY_CHAIN`: Supply chain impact
- `IMPACTS_STOCK`: Stock price influence
- `ATTACKS`: Direct attack relationship
- `VIOLATES_IHL`: International humanitarian law violation
- `LOCATED_IN`: Physical location
- `WORKS_FOR`: Employment relationship

**Type-Specific Validation:**

The ontology package enforces type-specific ID formats:

```python
# ✅ Valid COUNTRY entity (ISO 3166-1 alpha-2)
EntityReference(entity_id="US", entity_type=EntityType.COUNTRY, name="United States")

# ❌ Invalid COUNTRY entity (wrong format)
EntityReference(entity_id="USA", entity_type=EntityType.COUNTRY, name="United States")
# ValidationError: COUNTRY entity_id must be ISO 3166-1 alpha-2

# ✅ Valid COMPANY entity (stock ticker)
EntityReference(entity_id="TSLA", entity_type=EntityType.COMPANY, name="Tesla Inc.")

# ❌ Invalid COMPANY entity (too long)
EntityReference(entity_id="ABCDEF", entity_type=EntityType.COMPANY, name="Example Corp")
# ValidationError: stock ticker (1-5 uppercase letters)
```

**Graph Conversion:**

```python
# Convert to Neo4j node properties
entity = EntityReference(
    entity_id="US",
    entity_type=EntityType.COUNTRY,
    name="United States"
)

# Get node properties
node_props = entity.to_graph_node()
# {"entity_id": "US", "entity_type": "COUNTRY", "name": "United States", ...}

# Get node label
label = entity.to_graph_label()  # "Entity:COUNTRY"

# Convert relationship to Cypher parameters
hint = RelationshipHint(source=company, target=market, relationship_type=RelationshipType.IMPACTS_STOCK)
cypher_params = hint.to_cypher_params()
# {"source_id": "TSLA", "relationship_type": "IMPACTS_STOCK", "target_id": "NASDAQ", ...}
```

**References:**
- **Formal Ontology Design**: `/home/cytrex/userdocs/system-ontology/`
- **Implementation Plan**: `/home/cytrex/userdocs/system-ontology/IMPLEMENTATION_PLAN_PHASE1.md`
- **Ontology Strategy Insights**: `/home/cytrex/userdocs/system-ontology/ONTOLOGY_FIRST_STRATEGY_INSIGHTS.md`

## Dependencies

This package includes the following dependencies (see `setup.py` for full list):

**Core:**
- fastapi >= 0.104.0
- pydantic >= 2.8.0, < 3.0.0 (constrained for ontology package compatibility)
- sqlalchemy >= 2.0.0
- asyncpg >= 0.29.0

**Messaging:**
- aio-pika >= 9.3.0
- redis[hiredis] >= 5.0.0

**Observability:**
- opentelemetry-api >= 1.20.0
- opentelemetry-sdk >= 1.20.0
- opentelemetry-exporter-prometheus >= 0.41b0
- opentelemetry-exporter-jaeger >= 1.20.0
- deprecated >= 1.2.0
- prometheus-client >= 0.19.0

**Authentication:**
- python-jose[cryptography] >= 3.3.0
- passlib[bcrypt] >= 1.7.4

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black news_mcp_common/
isort news_mcp_common/

# Type checking
mypy news_mcp_common/
```

## Troubleshooting

### ModuleNotFoundError: no module named 'news_mcp_common'

**Symptom:** Service crashes on startup with import error.

**Solution:**
1. Check if service has `-e ../../shared/news-mcp-common` in requirements.txt
2. If missing, add it and rebuild: `docker compose up -d --build <service>`
3. For emergency fix, install in running container (see Installation section)

**Prevention:**
- Always add to requirements.txt BEFORE importing in code
- Test with fresh Docker build before committing

### Service "unhealthy" after restart

**Symptom:** `docker ps` shows service as "unhealthy" after restart.

**Check logs:**
```bash
docker logs <service-name> --tail 50
```

**Common causes:**
- Missing news-mcp-common dependency
- Missing transitive dependencies (deprecated, opentelemetry-exporter-prometheus)
- Import errors not caught during Docker build

## Related Documentation

- [POSTMORTEMS.md - Incident #10](../../POSTMORTEMS.md#incident-10-feed-service-dependency-failure-after-docker-restart-2025-11-03) - Real-world dependency failure case study
- [CLAUDE.backend.md](../../CLAUDE.backend.md) - Backend development guidelines
- [setup.py](./setup.py) - Complete dependency list

## License

MIT
