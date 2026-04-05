# Centralized Database Schema

**Version:** 1.0.0
**Purpose:** Single source of truth for all database models across microservices

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                      │
│                      news_mcp (shared)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Users   │  │  Feeds   │  │ Articles │  │ Analysis │   │
│  │  (Auth)  │  │  (RSS)   │  │ (Items)  │  │ (AI)     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Schedule │  │  Events  │  │  Logs    │                  │
│  │ (Jobs)   │  │ (RabbitMQ│  │ (Audit)  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         ▲           ▲           ▲           ▲
         │           │           │           │
    ┌────┴───┐  ┌────┴───┐  ┌────┴───┐  ┌────┴───┐
    │ Auth   │  │ Feed   │  │Content │  │Scheduler│
    │Service │  │Service │  │Analysis│  │ Service │
    └────────┘  └────────┘  └────────┘  └─────────┘
```

## Directory Structure

```
database/
├── models/
│   ├── __init__.py          # Central exports (import from here!)
│   ├── base.py              # Base classes and mixins
│   ├── user.py              # User, Role, APIKey, AuthAuditLog
│   ├── feed.py              # Feed, FeedItem, FetchLog, FeedHealth
│   ├── analysis.py          # AnalysisResult, Sentiment, Entities
│   ├── schedule.py          # FeedScheduleState, AnalysisJobQueue
│   └── event.py             # Event tracking for RabbitMQ
├── utils/
│   └── datetime.py          # UTC datetime helpers
├── migrations/
│   └── (Alembic migrations will go here)
└── README.md                # This file
```

## Core Entities

### 1. Users & Authentication (`user.py`)

**Tables:**
- `users` - Core user accounts
- `roles` - RBAC roles
- `user_roles` - User-role assignments
- `api_keys` - API key management
- `auth_audit_log` - Authentication events

**Key Features:**
- UUID primary keys
- Password hashing (bcrypt)
- Failed login tracking
- Account locking
- Audit trail

**Example:**
```python
from database.models import User, Role

user = User(
    email="user@example.com",
    username="johndoe",
    password_hash=hash_password("secret"),
    is_active=True
)
```

### 2. RSS Feeds & Articles (`feed.py`)

**Tables:**
- `feeds` - RSS feed sources (e.g., derstandard.at)
- `feed_items` - Individual articles (append-only)
- `fetch_log` - Fetch operation history
- `feed_health` - Health metrics and uptime
- `feed_categories` - Feed organization
- `feed_schedules` - Cron-based schedules

**Key Features:**
- Deduplication via `content_hash` (SHA-256)
- ETag and Last-Modified caching
- Health scoring (0-100)
- Scraping metadata
- Auto-analysis triggers

**Example:**
```python
from database.models import Feed, FeedItem

feed = Feed(
    url="https://www.derstandard.at/rss",
    name="Der Standard",
    fetch_interval=60,  # minutes
    enable_categorization=True
)

article = FeedItem(
    feed_id=feed.id,
    title="Breaking News",
    link="https://example.com/article",
    content_hash=compute_hash(content),
    published_at=utc_now()
)
```

### 3. Content Analysis (`analysis.py`)

**Tables:**
- `analysis_results` - Main analysis records
- `category_classification` - 6 fixed categories
- `sentiment_analysis` - General sentiment
- `finance_sentiment` - Financial market sentiment
- `geopolitical_sentiment` - Geopolitical analysis
- `extracted_entities` - Named entities (NER)
- `topic_classifications` - Topic tagging
- `summaries` - Article summaries (short/medium/long)
- `extracted_facts` - Fact extraction
- `event_analyses` - OSINT intelligence extraction

**Key Features:**
- Multi-model support (OpenAI, Anthropic, Ollama)
- Cost tracking (tokens, dollars)
- Response caching (SHA-256 keys)
- Performance metrics
- Retry logic

**6 Fixed Categories:**
1. Geopolitics Security
2. Politics Society
3. Economy Markets
4. Climate Environment Health
5. Panorama
6. Technology Science

**Example:**
```python
from database.models import AnalysisResult, CategoryClassification

analysis = AnalysisResult(
    article_id=article.id,
    analysis_type="CATEGORY",
    model_used="gpt-4",
    model_provider="OPENAI",
    status="COMPLETED"
)

category = CategoryClassification(
    analysis_id=analysis.id,
    category="Economy Markets",
    confidence=0.92,
    reasoning="Article discusses stock market trends..."
)
```

### 4. Scheduling & Jobs (`schedule.py`)

**Tables:**
- `feed_schedule_state` - Last fetch timestamps
- `analysis_job_queue` - Pending analysis jobs

**Key Features:**
- Priority-based job queue (1-10)
- Retry logic (max 3 retries)
- Duplicate prevention
- Job status tracking

**Example:**
```python
from database.models import AnalysisJobQueue

job = AnalysisJobQueue(
    feed_id=feed.id,
    article_id=article.id,
    job_type="categorization",
    priority=8,
    status="pending"
)
```

### 5. Event Tracking (`event.py`)

**Tables:**
- `events` - RabbitMQ message log

**Key Features:**
- Message routing information
- Correlation IDs for tracing
- Producer/consumer tracking
- Retry counts
- Error tracking

**Example:**
```python
from database.models import Event

event = Event(
    event_type="article.created",
    event_name="New Article Published",
    payload={"article_id": str(article.id)},
    exchange="news.events",
    routing_key="article.created",
    producer_service="feed-service",
    published_at=utc_now()
)
```

## Schema Relationships

```
User ────────┐
             │
             ├─── UserRole ───── Role
             │
             ├─── APIKey
             │
             └─── AuthAuditLog

Feed ────────┬─── FeedItem ───── AnalysisResult ───┬─── CategoryClassification
             │                                      ├─── SentimentAnalysis
             ├─── FetchLog                          ├─── FinanceSentiment
             │                                      ├─── GeopoliticalSentiment
             ├─── FeedHealth                        ├─── ExtractedEntity
             │                                      ├─── TopicClassification
             ├─── FeedCategory                      ├─── Summary
             │                                      ├─── ExtractedFact
             └─── FeedSchedule                      └─── EventAnalysis

FeedScheduleState (tracks Feed fetches)

AnalysisJobQueue (references Feed + FeedItem)

Event (logs all microservice events)
```

## UTC Datetime Handling

**CRITICAL:** All timestamps MUST be timezone-aware UTC.

### Utility Functions

```python
from database.utils.datetime import utc_now, to_utc, ensure_utc

# Get current UTC time
now = utc_now()  # datetime with tzinfo=timezone.utc

# Convert any datetime to UTC
utc_time = to_utc(some_datetime)

# Handle optional datetimes
safe_time = ensure_utc(optional_datetime)  # Returns None if None
```

### Database Storage

All datetime columns are stored as:
- **Type:** `DateTime(timezone=True)` (PostgreSQL `TIMESTAMPTZ`)
- **Default:** `utc_now()` function
- **Format:** ISO 8601 with timezone (e.g., `2025-10-15T12:00:00+00:00`)

**Never use:**
- `datetime.now()` (naive, no timezone)
- `datetime.utcnow()` (naive, deprecated in Python 3.12)

**Always use:**
- `utc_now()` from `database.utils.datetime`

## Import Guide

### For Services

**Always import from `database.models`:**

```python
# ✅ Correct
from database.models import Base, User, Feed, FeedItem, AnalysisResult
from database.models import utc_now

# ❌ Wrong
from database.models.user import User  # Don't import directly
from app.models.auth import User  # Old scattered models
```

### For Alembic Migrations

```python
from database.models import Base, metadata

target_metadata = metadata
```

## Migration Strategy

### Phase 1: Create Central Schema ✅ DONE
- [x] Create `database/` directory structure
- [x] Define all models with proper relationships
- [x] Add UTC datetime utilities
- [x] Document schema relationships

### Phase 2: Update Services (TODO)
- [ ] Update each service's `requirements.txt` to import from `database/`
- [ ] Replace scattered models with central imports
- [ ] Update Alembic `env.py` to use central metadata
- [ ] Run schema validation

### Phase 3: Database Creation (TODO)
- [ ] Create Alembic initial migration
- [ ] Review generated SQL
- [ ] Apply migration to PostgreSQL
- [ ] Verify all tables created

### Phase 4: Service Integration (TODO)
- [ ] Update auth-service to use central User models
- [ ] Update feed-service to use central Feed models
- [ ] Update content-analysis-service to use central Analysis models
- [ ] Update scheduler-service to use central Schedule models
- [ ] Test end-to-end flows

## Design Decisions

### ADR-001: UUID Primary Keys

**Decision:** Use UUID v4 for all primary keys instead of auto-increment integers.

**Rationale:**
- Better distribution in distributed systems
- No auto-increment bottlenecks in high-throughput scenarios
- Merge-friendly (no ID conflicts between databases)
- Secure (non-sequential, harder to guess)

**Trade-off:** Slightly larger index size (16 bytes vs 4 bytes)

### ADR-002: Timezone-Aware UTC

**Decision:** All timestamps must be timezone-aware UTC.

**Rationale:**
- Prevents timezone conversion bugs
- Ensures consistent sorting across timezones
- PostgreSQL `TIMESTAMPTZ` stores in UTC automatically
- Python 3.12 deprecates naive datetimes

**Implementation:** Custom `utc_now()` helper function

### ADR-003: Append-Only Articles

**Decision:** `feed_items` table is append-only (no updates).

**Rationale:**
- RSS articles don't change after publication
- Simplifies caching and deduplication
- No need for `updated_at` column
- Faster inserts (no update locks)

**Exception:** Scraping metadata (`scraped_at`, `scrape_status`) updated separately

### ADR-004: Centralized Models

**Decision:** Single `database/models/` for all services.

**Rationale:**
- Prevents schema drift between services
- Ensures referential integrity
- Single source of truth for relationships
- Shared metadata for Alembic migrations

**Trade-off:** Services must coordinate schema changes

### ADR-005: JSON for Flexible Data

**Decision:** Use `JSONB` for analysis results instead of separate tables.

**Rationale:**
- Analysis output structure varies by model
- JSONB supports indexing (GIN indexes)
- Easier to add new analysis types
- Reduces table proliferation

**Example:** `sentiment_analysis.emotion_scores` stores `{"joy": 0.8, "fear": 0.2}`

## Performance Considerations

### Indexes

**Primary indexes on:**
- All foreign keys
- Frequently filtered columns (`status`, `is_active`)
- Timestamp columns (`created_at`, `published_at`)
- Unique constraints (`email`, `content_hash`)

**Composite indexes for common queries:**
- `(user_id, action)` in `auth_audit_log`
- `(article_id, analysis_type)` in `analysis_results`
- `(feed_id, started_at)` in `fetch_log`

### GIN Indexes for JSONB

```sql
CREATE INDEX idx_event_analyses_actors
ON event_analyses USING gin (actors);
```

Enables fast queries like:
```python
# Find events where Russia is an actor
events = session.query(EventAnalysis).filter(
    EventAnalysis.actors.contains({"alleged_attacker": "Russia"})
).all()
```

## Security

### Sensitive Data

**Never store in plain text:**
- Passwords → Use `password_hash` (bcrypt)
- API keys → Use `key_hash` (SHA-256)

**Audit logging:**
- All authentication events → `auth_audit_log`
- Failed login attempts → `User.failed_login_attempts`

### SQL Injection Prevention

**Always use:**
- SQLAlchemy ORM (automatic parameterization)
- `.filter(Model.column == value)` (not string formatting)

**Never use:**
- Raw SQL with string interpolation
- `text(f"SELECT * FROM users WHERE id = {user_id}")`

## Testing

### Unit Tests

```python
import pytest
from database.models import User
from database.utils.datetime import utc_now

def test_user_creation():
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        is_active=True
    )

    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.created_at is not None  # Auto-set by TimestampMixin
```

### Integration Tests

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Feed, FeedItem

engine = create_engine("postgresql://news_user:news_pass@localhost:5433/news_test")
SessionLocal = sessionmaker(bind=engine)

def test_feed_item_relationship():
    session = SessionLocal()

    # Create feed
    feed = Feed(url="https://example.com/rss", name="Test Feed")
    session.add(feed)
    session.commit()

    # Create article
    article = FeedItem(
        feed_id=feed.id,
        title="Test Article",
        link="https://example.com/article",
        content_hash="abc123"
    )
    session.add(article)
    session.commit()

    # Test relationship
    assert article.feed.id == feed.id
    assert feed.items[0].id == article.id

    session.close()
```

## Troubleshooting

### Common Issues

**Issue:** `ImportError: No module named 'database'`

**Fix:** Add project root to PYTHONPATH:
```bash
export PYTHONPATH=/home/cytrex/news-microservices:$PYTHONPATH
```

Or use relative imports in services:
```python
import sys
sys.path.append('/home/cytrex/news-microservices')
from database.models import User
```

---

**Issue:** `AttributeError: 'str' object has no attribute 'tzinfo'`

**Fix:** You're storing datetime as string instead of using proper datetime column:
```python
# ❌ Wrong
user.created_at = "2025-10-15 12:00:00"

# ✅ Right
from database.utils.datetime import utc_now
user.created_at = utc_now()
```

---

**Issue:** Alembic can't find models

**Fix:** Update `alembic/env.py`:
```python
from database.models import Base
target_metadata = Base.metadata
```

## Support

**Questions or issues?**
1. Check this README
2. Review model docstrings in `database/models/`
3. Check datetime utilities in `database/utils/datetime.py`
4. Consult PostgreSQL logs: `docker logs news-postgres`

**Need to modify schema?**
1. Update model in `database/models/`
2. Create Alembic migration
3. Review generated SQL
4. Test in development environment
5. Apply to production

---

**Last Updated:** 2025-10-15
**Maintained By:** Database Architecture Team
**Version:** 1.0.0
