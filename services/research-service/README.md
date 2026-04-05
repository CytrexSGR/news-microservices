# Research Service

AI-powered research service using Perplexity AI for deep research on news articles.

## 🚀 Current Status (Phase 1 Complete)

**Service is operational and ready for use!**

✅ **Phase 1 Implemented** (Synchronous Mode):
- Database schema with structured output support (JSON fields, validation status)
- Alembic migrations configured and applied
- Comprehensive health checks (DB/Redis/Celery/Perplexity API)
- API endpoints fully functional
- Template system operational
- **3 Specialized Functions mit strukturierten Outputs:**
  - Feed Source Assessment (sonar, Pydantic-validiert)
  - Fact Check (sonar-reasoning-pro, Evidenz-basiert)
  - Trend Analysis (sonar-pro, Geographic + Narrative)
- Perplexity AI integration with JSON extraction & schema validation
- Cost tracking and caching ready
- 10/10 Tests passed ✅

⏳ **Phase 2 Pending** (Async Mode):
- Celery worker activation
- Background task processing
- Event publishing to RabbitMQ

## Features

- **Perplexity AI Integration**: Deep research using multiple AI models (sonar, sonar-pro, sonar-reasoning-pro)
- **Specialized Research Functions**: 3 spezialisierte Funktionen mit strukturierter JSON-Ausgabe
  - `feed_source_assessment`: Automatische News-Quellen-Bewertung
  - `fact_check`: Evidenz-basierte Faktenprüfung
  - `trend_analysis`: News-Coverage-Trend-Analyse
- **Structured Output**: Pydantic-basierte Schema-Validierung für alle Funktionen
- **Template System**: Create and reuse research templates with variable substitution
- **Cost Optimization**: Intelligent model selection, caching, and cost tracking
- **Rate Limiting**: Respect API limits (10 requests/minute)
- **Legacy Field Support**: Compatibility with old Integer-based feed/article IDs
- **UUID Support**: Modern UUID-based cross-service references
- **Result Caching**: 7-day Redis cache for research results
- **Cost Tracking**: Per-query, daily, and monthly cost monitoring
- **Migration Ready**: Alembic migrations for schema evolution

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Cache**: Redis (7-day TTL)
- **Queue**: Celery + Redis
- **AI**: Perplexity AI
- **Auth**: JWT tokens

## API Endpoints

### Research
- `POST /api/v1/research` - Create research task
- `GET /api/v1/research/{id}` - Get research result
- `POST /api/v1/research/batch` - Batch research requests
- `GET /api/v1/research/feed/{feed_id}` - Get research for feed
- `GET /api/v1/research/history` - Get research history
- `GET /api/v1/research/stats` - Get usage statistics

### Templates
- `POST /api/v1/templates` - Create template
- `GET /api/v1/templates` - List templates
- `GET /api/v1/templates/functions` - List specialised research functions
- `GET /api/v1/templates/{id}` - Get template
- `PUT /api/v1/templates/{id}` - Update template
- `DELETE /api/v1/templates/{id}` - Delete template
- `POST /api/v1/templates/{id}/preview` - Preview template with variables
- `POST /api/v1/templates/{id}/apply` - Apply template and create research task

## Database Schema

### research_tasks
- Tracks all research queries and results
- Stores tokens used and cost per query
- **Cross-service references**:
  - `feed_id` (UUID) - References Feed Service
  - `article_id` (UUID) - References Feed Items
  - `legacy_feed_id` (Integer) - Migration support for old system
  - `legacy_article_id` (Integer) - Migration support for old system
- Indexed on all reference fields for performance

### research_templates
- Reusable query templates
- Variable substitution support
- Usage analytics
- Public/private template sharing

### research_runs
- Scheduled/automated research executions
- Links to templates
- Aggregates results from multiple tasks
- Supports recurring patterns (daily/weekly/monthly)

### research_cache
- 7-day cache of research results
- Reduces API costs by ~75%
- Hit count tracking
- Automatic expiration

### cost_tracking
- Per-user cost tracking
- Daily/monthly aggregation
- Model-specific breakdown
- Links to tasks and runs for audit trail

## Configuration

Key environment variables:

```bash
# Perplexity AI
PERPLEXITY_API_KEY=your-api-key
PERPLEXITY_DEFAULT_MODEL=sonar  # sonar, sonar-pro, sonar-reasoning-pro

# Cost Limits
MAX_COST_PER_REQUEST=1.0
MAX_DAILY_COST=50.0
MAX_MONTHLY_COST=1000.0

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=10

# Cache
REDIS_CACHE_TTL=604800  # 7 days
CACHE_ENABLED=true
```

## Specialised Research Functions

The service ships with structured research functions that return validated JSON
payloads. The registry can be inspected via:

```
GET /api/v1/templates/functions
```

### Specialized Research Functions

Der Service bietet 3 spezialisierte Funktionen mit strukturierter JSON-Ausgabe:

#### 1. Feed Source Assessment
Automatisierte Glaubwürdigkeitsbewertung für News-Quellen:
- **Funktion**: `feed_source_assessment`
- **Model**: sonar (standard depth)
- **Use Case**: Automatische Feed-Qualitätsbewertung bei Neuregistrierung

**Output Schema**:
- `credibility_tier`: tier_1|tier_2|tier_3
- `reputation_score`: 0-100
- `editorial_standards`: fact_checking_level, corrections_policy, source_attribution
- `trust_ratings`: Media Bias/Fact Check, AllSides, NewsGuard
- `political_bias`: left|center_left|center|center_right|right|unknown
- `recommendation`: skip_waiting_period, initial_quality_boost, bot_detection_threshold

**Beispiel-Response**:
```json
{
  "structured_data": {
    "credibility_tier": "tier_1",
    "reputation_score": 90,
    "founded_year": 1851,
    "organization_type": "news_agency",
    "editorial_standards": {
      "fact_checking_level": "high",
      "corrections_policy": "transparent",
      "source_attribution": "good"
    },
    "trust_ratings": {
      "media_bias_fact_check": "Least Biased",
      "allsides_rating": "Center",
      "newsguard_score": 93
    },
    "political_bias": "center",
    "recommendation": {
      "skip_waiting_period": true,
      "initial_quality_boost": 15,
      "bot_detection_threshold": "normal"
    },
    "summary": "Reuters is a tier-1 international news agency..."
  },
  "validation_status": "valid",
  "tokens_used": 584,
  "cost": 0.002920
}
```

#### 2. Fact Check
Faktenprüfung von Behauptungen mit Evidenz-basierter Bewertung:
- **Funktion**: `fact_check`
- **Model**: sonar-reasoning-pro (deep analysis)
- **Use Case**: Automatische Faktenprüfung für Artikel-Claims

**Output Schema**:
- `verdict`: true|mostly_true|mixed|mostly_false|false|unverifiable
- `confidence`: 0-100
- `claim_rating`: accurate|misleading|false|unverified
- `supporting_evidence`: Array mit Quellen, Reliability-Rating, Zusammenfassung
- `contradicting_evidence`: Array mit Gegenbeweisen
- `context`: Wichtiger Kontext zur Einordnung
- `fact_checker_assessments`: Snopes, FactCheck.org, PolitiFact Ratings
- `summary`: Klare Zusammenfassung des Ergebnisses

**Beispiel-Response**:
```json
{
  "structured_data": {
    "verdict": "false",
    "confidence": 95,
    "claim_rating": "false",
    "supporting_evidence": [],
    "contradicting_evidence": [
      {
        "source": "NASA",
        "reliability": "high",
        "summary": "Multiple moon landings documented with evidence"
      },
      {
        "source": "Independent scientists",
        "reliability": "high",
        "summary": "Physical evidence confirms lunar missions"
      }
    ],
    "context": "Moon landing conspiracy theories debunked by scientific community",
    "fact_checker_assessments": {
      "snopes": "False",
      "factcheck_org": "False"
    },
    "summary": "Claim is false according to authoritative scientific sources"
  },
  "validation_status": "valid"
}
```

#### 3. Trend Analysis
Analyse von Trends in der News-Berichterstattung:
- **Funktion**: `trend_analysis`
- **Model**: sonar-pro (deep analysis)
- **Use Case**: Trend-Erkennung für Topics, Agenda-Setting-Analyse

**Output Schema**:
- `topic`: Analysiertes Thema
- `timeframe`: Analysezeitraum
- `overall_trend`: rising|stable|declining|mixed
- `coverage_intensity`: high|medium|low
- `identified_trends`: Array mit Trend-Items (Stärke, Volume, Key Sources)
- `key_drivers`: Haupttreiber der Berichterstattung
- `geographic_distribution`: Regionale Verteilung der Coverage
- `timeline_highlights`: Wichtige Events im Zeitverlauf
- `notable_sources`: Wichtigste Medien zum Thema
- `emerging_narratives`: Neue Story-Winkel
- `summary`: Executive Summary

**Beispiel-Response**:
```json
{
  "structured_data": {
    "topic": "AI regulation",
    "timeframe": "month",
    "overall_trend": "rising",
    "coverage_intensity": "high",
    "identified_trends": [
      {
        "trend": "EU AI Act implementation discussions",
        "strength": "growing",
        "coverage_volume": "high",
        "key_sources": ["Reuters", "BBC", "Politico"]
      },
      {
        "trend": "US state-level AI regulation initiatives",
        "strength": "emerging",
        "coverage_volume": "medium",
        "key_sources": ["NYT", "Washington Post"]
      }
    ],
    "key_drivers": [
      "EU AI Act finalization",
      "US Congressional hearings",
      "Industry lobbying efforts"
    ],
    "geographic_distribution": [
      {
        "region": "Europe",
        "coverage_level": "high",
        "notable_aspects": "Focus on EU AI Act implementation"
      },
      {
        "region": "North America",
        "coverage_level": "medium",
        "notable_aspects": "State vs federal regulation debate"
      }
    ],
    "timeline_highlights": {
      "2024-10-15": "EU AI Act enters into force",
      "2024-10-20": "US Senate AI working group report"
    },
    "notable_sources": ["Reuters", "BBC", "NYT", "Politico", "Financial Times"],
    "emerging_narratives": [
      "AI safety vs innovation balance",
      "Small business compliance concerns",
      "International regulatory competition"
    ],
    "summary": "AI regulation coverage shows rising trend with high intensity..."
  },
  "validation_status": "valid"
}
```

### Function Usage

Templates können spezialisierte Funktionen via `research_function` referenzieren:

```json
{
  "name": "Reuters Credibility Check",
  "research_function": "feed_source_assessment",
  "function_parameters": {
    "domain": "reuters.com",
    "include_bias_analysis": true
  }
}
```

Klassische Templates ohne Funktionen funktionieren weiterhin normal.

## Development

### Quick Start (Phase 1 - Current)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# .env already exists with development settings
# Update PERPLEXITY_API_KEY if you have one

# 4. Run database migrations
alembic upgrade head

# 5. Start service (sync mode)
uvicorn app.main:app --reload --port 8003
```

**Service will be available at:**
- API: http://localhost:8003
- Docs: http://localhost:8003/docs
- Health: http://localhost:8003/health

### Health Check

```bash
curl http://localhost:8003/health
```

Expected response (Phase 1):
```json
{
  "status": "degraded",
  "service": "research-service",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "no workers",  // Expected - Phase 2
    "perplexity_api": "ok"
  }
}
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current
```

### Phase 2 Setup (Async Mode - Optional)

```bash
# Start Celery Worker
celery -A app.workers.celery_app worker \
  --loglevel=info \
  --queues=research,research_scheduled,maintenance,health

# Optional: Start Celery Beat (for scheduled tasks)
celery -A app.workers.celery_app beat --loglevel=info
```

### Run Tests
```bash
pytest tests/ -v
```

## Docker Deployment

```bash
# Build image
docker build -t research-service:latest .

# Run container
docker run -d \
  --name research-service \
  -p 8003:8003 \
  --env-file .env \
  research-service:latest
```

## Model Selection

### sonar (default)
- Cost: $0.005 / 1K tokens
- Speed: Fast
- Use: General research, news summaries

### sonar-pro
- Cost: $0.015 / 1K tokens
- Speed: Medium
- Use: Detailed analysis, complex queries

### sonar-reasoning-pro
- Cost: $0.025 / 1K tokens
- Speed: Slower
- Use: Deep research, multi-step reasoning

## Cost Optimization

1. **Caching**: Results cached for 7 days
2. **Model Selection**: Choose appropriate model for task
3. **Batch Processing**: Process multiple queries efficiently
4. **Cost Alerts**: Alert at 80% of daily/monthly limit
5. **Rate Limiting**: Prevent excessive API usage

## Integration

### With Feed Service
```python
# Research articles from a feed
POST /api/v1/research
{
  "query": "Analyze recent developments in {{topic}}",
  "feed_id": 123
}
```

### With Content Analysis Service
```python
# Combine analysis with research
GET /api/v1/research/feed/123
# Returns research tasks for analyzed articles
```

## Template Examples

### News Summary Template
```json
{
  "name": "News Summary",
  "query_template": "Summarize the latest news about {{topic}} from the past {{timeframe}}",
  "parameters": {
    "topic": "Technology",
    "timeframe": "24 hours"
  }
}
```

### Deep Dive Template
```json
{
  "name": "Deep Analysis",
  "query_template": "Provide a comprehensive analysis of {{subject}} including historical context, current status, and future implications",
  "parameters": {
    "subject": "AI Regulation"
  },
  "default_model": "sonar-reasoning-pro"
}
```

## Monitoring

- Health check: `GET /health`
- API docs: `http://localhost:8003/docs`
- Celery monitoring: Flower (port 5555)

## License

Part of the News Microservices project.

## Documentation

- [Service Documentation](../../docs/services/research-service.md)
- [API Documentation](../../docs/api/research-service-api.md)
