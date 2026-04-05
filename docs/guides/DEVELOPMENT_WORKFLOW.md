# Development Workflow Guide

## Critical Learnings from Test 3 (End-to-End Feed Lifecycle)

This guide documents important patterns discovered during testing that all developers should follow.

---

## 🚨 Critical: Making Code Changes in Docker Environment

### The Problem
Code changes in services don't take effect with just `docker compose restart`. Docker Compose builds **images** (snapshots of code), not just volume mounts.

### The Solution
**Always rebuild the image after code changes:**

```bash
# Step 1: Make your code changes
vim services/content-analysis-service/app/api/analysis.py

# Step 2: Rebuild the specific service image
docker compose build content-analysis-service

# Step 3: Restart with new image
docker compose up -d content-analysis-service

# Step 4: Verify changes took effect
docker compose exec content-analysis-service cat /app/app/api/analysis.py | grep "your_change"
```

### Quick Reference
```bash
# ❌ WRONG - Changes won't appear
docker compose restart content-analysis-service

# ✅ CORRECT - Rebuild + restart
docker compose build content-analysis-service && docker compose up -d content-analysis-service
```

---

## 🔧 SQLAlchemy Enum Handling

### Critical Understanding
SQLAlchemy's `Enum()` column type uses **Python enum member NAMES**, not values, when creating PostgreSQL enums.

### Example

```python
# Python Enum Definition
class ModelProvider(str, PyEnum):
    OPENAI = "openai"      # Member name: OPENAI, Value: "openai"
    ANTHROPIC = "anthropic"

# SQLAlchemy Column
model_provider = Column(Enum(ModelProvider), nullable=False)

# What gets created in PostgreSQL
CREATE TYPE modelprovider AS ENUM ('OPENAI', 'ANTHROPIC');  -- Uses MEMBER NAMES!

# Your code tries to insert
model_provider = "openai"  # ❌ ERROR: "openai" is not in enum

# Must insert member name instead
model_provider = "OPENAI"  # ✅ CORRECT
```

### Best Practice: Match Names and Values

```python
# ✅ RECOMMENDED: Member names match values
class ModelProvider(str, PyEnum):
    """LLM model providers."""
    OPENAI = "OPENAI"          # Name matches value
    ANTHROPIC = "ANTHROPIC"
    OLLAMA = "OLLAMA"
    HUGGINGFACE = "HUGGINGFACE"
```

This eliminates confusion between what SQLAlchemy creates and what your code uses.

---

## 🔗 Microservices ID Type Management

### Issue Discovered
- **Feed Service**: Uses `id: integer` (19, 20, 21...)
- **Content Analysis**: Expects `article_id: uuid` (550e8400-e29b-41d4-a716-446655440000)

### Current Workaround
Make `article_id` **optional** and store Feed IDs in metadata:

```python
# API Schema
class AnalysisRequest(BaseModel):
    content: str
    article_id: Optional[UUID] = None  # Optional!
    metadata: Optional[Dict] = None

# Database Schema
article_id = Column(UUID(as_uuid=True), nullable=True)  # Nullable!

# Usage - Store Feed ID in metadata
payload = {
    "content": article_content,
    "metadata": {
        "feed_article_id": 19,  # Feed Service integer ID
        "feed_id": 1,
        "title": "Article Title"
    }
}
```

### Long-term Solutions (Pick One)

**Option A: Standardize on UUIDs** (Recommended)
```sql
-- Migrate Feed Service
ALTER TABLE feed_items ADD COLUMN uuid UUID DEFAULT gen_random_uuid();
ALTER TABLE feed_items DROP CONSTRAINT feed_items_pkey;
ALTER TABLE feed_items ADD PRIMARY KEY (uuid);
```

**Option B: Accept Both Types**
```python
class AnalysisRequest(BaseModel):
    content: str
    article_id: Optional[Union[UUID, int]] = None  # Accept either!
```

**Option C: ID Mapping Service**
- Create a lightweight service that maps Feed integer IDs ↔ Analysis UUIDs
- All cross-service references go through mapper

---

## 🧪 Testing Best Practices

### End-to-End Test Pattern

See `test_e2e_lifecycle.py` for complete example:

```python
def test_workflow():
    # 1. Authentication
    token = authenticate()

    # 2. Get Resource
    feed = get_feed()

    # 3. Fetch Related Data
    article = get_article(feed['id'])

    # 4. Trigger Service Operation
    result = trigger_analysis(article, token)

    # 5. Verify Results
    verify_results(result['id'], token)
```

### Key Testing Patterns

1. **Always handle trailing slashes in URLs**
   ```python
   ANALYSIS_URL = "http://localhost:8002/api/v1/analyze"
   response = requests.post(f"{ANALYSIS_URL}/")  # Note trailing slash!
   ```

2. **Store metadata for cross-service references**
   ```python
   payload = {
       "content": data,
       "metadata": {
           "source_service": "feed-service",
           "source_id": feed_article_id,
           "timestamp": datetime.utcnow().isoformat()
       }
   }
   ```

3. **Check multiple status codes**
   ```python
   if response.status_code in [200, 201]:  # Both success codes
       result = response.json()
   ```

---

## 🛠️ Common Troubleshooting

### Problem: "Enum value not valid"

```
psycopg2.errors.InvalidTextRepresentation: invalid input value for enum: "openai"
```

**Diagnosis:**
```bash
# Check database enum
docker compose exec postgres psql -U newsuser -d feed_db -c "\dT+ modelprovider"

# Check Python enum
docker compose exec content-analysis-service python -c "from app.models.analysis import ModelProvider; print([e.value for e in ModelProvider])"
```

**Fix:** Ensure Python enum values match database enum values (see SQLAlchemy Enum Handling above)

### Problem: Code changes not appearing

```bash
# Check if old code is still running
docker compose exec content-analysis-service cat /app/app/api/analysis.py | grep "your_change"
```

**Fix:** Rebuild image (see Critical: Making Code Changes above)

### Problem: Database constraint violation

```
psycopg2.errors.NotNullViolation: null value in column "article_id"
```

**Fix:** Make column nullable if API contract says optional:
```sql
ALTER TABLE analysis_results ALTER COLUMN article_id DROP NOT NULL;
```

---

## 📊 Service Status Verification

### Check All Services

```bash
# Quick status
docker compose ps

# Detailed health checks
for service in auth-service feed-service content-analysis-service; do
    echo "=== $service ==="
    docker compose ps $service
    docker compose logs $service --tail 5
done
```

### Verify Database Connectivity

```bash
# Test from service container
docker compose exec content-analysis-service python -c "
from app.models.base import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connected:', result.scalar())
"
```

---

## 📝 Documentation Requirements

After making significant changes, update:

1. **TEST_RESULTS.md** - Test outcomes, issues found, fixes applied
2. **API documentation** - If endpoints changed
3. **Database schema docs** - If migrations performed
4. **This file (DEVELOPMENT_WORKFLOW.md)** - If new patterns discovered

---

## ✅ Pre-Commit Checklist

Before committing service changes:

- [ ] Code changes made
- [ ] Docker image rebuilt (`docker compose build <service>`)
- [ ] Service restarted (`docker compose up -d <service>`)
- [ ] Changes verified in running container
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Database migrations applied (if needed)
- [ ] Documentation updated
- [ ] Enum values consistent (if changed)
- [ ] API contracts match implementation

---

## 🎯 Quick Command Reference

```bash
# Development cycle
docker compose build <service>
docker compose up -d <service>
docker compose logs <service> -f

# Database operations
docker compose exec postgres psql -U newsuser -d feed_db
docker compose exec postgres psql -U newsuser -d feed_db -c "\dt"

# Service debugging
docker compose exec <service> python -c "from app.models import *; print('Imports OK')"
docker compose exec <service> env | grep -i config

# Testing
python3 test_e2e_lifecycle.py
python3 test_auth_service.py
python3 test_feed_service.py

# Full restart (last resort)
docker compose down
docker compose up -d
```

---

*Last updated: After Test 3 completion (End-to-End Feed Lifecycle)*
*Key learnings: SQLAlchemy enum behavior, Docker image rebuilding, ID type management*
