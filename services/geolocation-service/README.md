# Geolocation Service

Geographic visualization service for news articles. Displays an interactive world map with country-level article aggregation, real-time updates via WebSocket, and multiple visualization modes.

## Port: 8115

## Features

- **Country-level article aggregation**: Articles mapped to ISO 3166-1 alpha-2 country codes
- **GeoJSON map data**: Natural Earth country boundaries with PostGIS
- **Real-time WebSocket updates**: Live article notifications via RabbitMQ events
- **Multiple visualization modes**: Country coloring + markers, heatmap overlay
- **Region filtering**: Filter by continent (Europe, Asia, Africa, Americas, Oceania)
- **Time range filtering**: Today, 7d, 30d, custom date ranges
- **Category filtering**: Conflict, Diplomacy, Economy events

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    geolocation-service (8115)                    │
├─────────────────────────────────────────────────────────────────┤
│  API Layer                                                       │
│  ├── locations.py     GET /api/v1/geo/countries, /{code}        │
│  ├── map.py           GET /api/v1/geo/map/countries, /markers   │
│  ├── filters.py       GET /api/v1/geo/filters/regions           │
│  └── websocket.py     WS /ws/geo-live                           │
├─────────────────────────────────────────────────────────────────┤
│  Services                                                        │
│  ├── location_resolver.py   Location → ISO code resolution      │
│  ├── article_locator.py     Article-country mapping             │
│  ├── stats_aggregator.py    Country statistics cache            │
│  └── realtime_broadcaster.py WebSocket broadcasting             │
├─────────────────────────────────────────────────────────────────┤
│  Workers                                                         │
│  └── geo_consumer.py        RabbitMQ: analysis.v3.completed     │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Countries & Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/geo/countries` | GET | List all countries with stats |
| `/api/v1/geo/countries/{iso_code}` | GET | Country details with recent articles |
| `/api/v1/geo/countries/{iso_code}/articles` | GET | Paginated articles for country |

### Map Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/geo/map/countries` | GET | GeoJSON FeatureCollection with stats |
| `/api/v1/geo/map/markers` | GET | Article markers for map display |
| `/api/v1/geo/map/heatmap` | GET | Heatmap intensity data |

### Filters

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/geo/filters/regions` | GET | Available regions with country codes |
| `/api/v1/geo/filters/categories` | GET | Event categories with counts |

### WebSocket

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws/geo-live` | WebSocket | Real-time article updates |
| `/api/v1/geo/ws/stats` | GET | WebSocket connection statistics |

## WebSocket Protocol

```typescript
// Client → Server
{ "action": "subscribe", "filters": { "regions": ["europe"], "categories": ["conflict"] } }
{ "action": "unsubscribe" }
{ "action": "ping" }

// Server → Client
{ "type": "connected", "client_id": "geo_user_123", "timestamp": "..." }
{ "type": "heartbeat", "timestamp": "..." }  // Every 30 seconds
{ "type": "article_new", "data": { iso_code, article_id, title, lat, lon, category } }
{ "type": "stats_update", "data": { iso_code, article_count_24h, change: +5 } }
```

## Database Schema (PostGIS)

```sql
-- Countries with boundaries (Natural Earth)
CREATE TABLE countries (
    iso_code VARCHAR(2) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_de VARCHAR(100),
    region VARCHAR(50),        -- Europe, Asia, Africa, Americas, Oceania
    subregion VARCHAR(50),
    centroid GEOMETRY(POINT, 4326),
    boundary GEOMETRY(MULTIPOLYGON, 4326)
);

-- Article-to-country mapping
CREATE TABLE article_locations (
    id UUID PRIMARY KEY,
    article_id UUID NOT NULL,
    country_code VARCHAR(2) REFERENCES countries(iso_code),
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(20)  -- 'entity_extraction', 'manual'
);

-- Cached country statistics
CREATE TABLE country_stats (
    country_code VARCHAR(2) PRIMARY KEY,
    article_count_24h INTEGER DEFAULT 0,
    article_count_7d INTEGER DEFAULT 0,
    article_count_30d INTEGER DEFAULT 0,
    last_article_at TIMESTAMP
);
```

## Event Integration

### Consumed Events

```yaml
Exchange: news.events (topic)
Queue: geo.article.process
Routing Key: analysis.v3.completed

Flow:
  1. Extract LOCATION entities from tier1.entities
  2. Resolve location names to ISO codes
  3. Store article-location mapping
  4. Update country_stats
  5. Broadcast to WebSocket subscribers
```

### Published Events

```yaml
Routing Key: geo.article.located
Payload:
  article_id: "uuid"
  iso_code: "UA"
  country_name: "Ukraine"
  confidence: 0.95
```

## Dependencies

| Service | Purpose |
|---------|---------|
| PostgreSQL + PostGIS | Country boundaries, article mappings |
| Redis | Caching, WebSocket connection state |
| RabbitMQ | Event consumption (analysis.v3.completed) |
| entity-canonicalization-service | Location → ISO code resolution |

## Environment Variables

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=news_user
POSTGRES_PASSWORD=...
POSTGRES_DB=news_mcp

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_secret_2024

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# External Services
ENTITY_CANONICALIZATION_URL=http://entity-canonicalization-service:8112
```

## Data Import

Initial country data from Natural Earth:

```bash
# Download Natural Earth GeoJSON
./scripts/download_data.sh

# Import countries to PostGIS
python scripts/import_countries.py

# Enrich with German names
python scripts/enrich_german_names.py

# Initialize statistics
psql -f scripts/init_country_stats.sql
```

## Frontend Integration

The Geo Map feature is available at `/geo-map` in the frontend:

- `frontend/src/features/geo-map/` - Feature directory
- `frontend/src/pages/GeoMapPage.tsx` - Page component
- Uses Leaflet + react-leaflet for map rendering

## Docker Services

```yaml
# API Service
geolocation-service:
  port: 8115
  healthcheck: /health

# Event Consumer
geolocation-service-consumer:
  command: python -m app.workers.geo_consumer
```

## Related Documentation

- [Design Document](../../docs/plans/2025-01-12-geo-news-map-design.md)
- [Implementation Plan](../../docs/plans/2025-01-12-geo-news-map-implementation.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System overview
