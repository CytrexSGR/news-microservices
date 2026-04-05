# Knowledge Graph Validation - Fix Recommendations

**Priority:** CRITICAL → HIGH → MEDIUM
**Estimated Total Implementation Time:** 4-6 hours

---

## 🔴 CRITICAL FIX 1: Graceful Enum Fallback (1-2 hours)

### Objective
Stop 500 errors by gracefully handling invalid LLM-generated types.

### Implementation Steps

#### Step 1: Create Fallback Parser Functions

**File:** `services/content-analysis-service/app/utils/enum_parsers.py` (NEW)

```python
"""
Robust enum parsing with graceful fallback for LLM responses.
"""
import logging
from database.models import EntityType, RelationshipType

logger = logging.getLogger(__name__)


def parse_entity_type(llm_type: str) -> EntityType:
    """
    Parse LLM entity type with fallback to NOT_APPLICABLE.

    Args:
        llm_type: Raw entity type string from LLM

    Returns:
        Valid EntityType enum value

    Example:
        >>> parse_entity_type("PERSON")
        EntityType.PERSON
        >>> parse_entity_type("LEGISLATION")  # Invalid
        EntityType.NOT_APPLICABLE  # Fallback
    """
    # Try exact match first
    try:
        return EntityType(llm_type.upper())
    except ValueError:
        pass

    # Try case-insensitive match
    try:
        return EntityType[llm_type.upper()]
    except KeyError:
        pass

    # Fallback with warning
    logger.warning(
        f"Invalid EntityType '{llm_type}' not in enum. "
        f"Falling back to NOT_APPLICABLE. "
        f"Valid types: {[e.value for e in EntityType]}"
    )
    return EntityType.NOT_APPLICABLE


def parse_relationship_type(llm_type: str) -> RelationshipType:
    """
    Parse LLM relationship type with fallback to RELATED_TO.

    Args:
        llm_type: Raw relationship type string from LLM

    Returns:
        Valid RelationshipType enum value

    Example:
        >>> parse_relationship_type("works_for")
        RelationshipType.WORKS_FOR
        >>> parse_relationship_type("supporter_of")  # Invalid
        RelationshipType.RELATED_TO  # Fallback
    """
    # Normalize to lowercase
    llm_type_normalized = llm_type.lower().replace(" ", "_")

    # Try exact match
    try:
        return RelationshipType(llm_type_normalized)
    except ValueError:
        pass

    # Try uppercase enum name match
    try:
        return RelationshipType[llm_type.upper().replace(" ", "_")]
    except KeyError:
        pass

    # Fallback with warning
    logger.warning(
        f"Invalid RelationshipType '{llm_type}' not in enum. "
        f"Falling back to RELATED_TO. "
        f"Valid types: {[e.value for e in RelationshipType]}"
    )
    return RelationshipType.RELATED_TO
```

#### Step 2: Integrate into Analysis Service

**File:** `services/content-analysis-service/app/services/analysis_service.py`

**Find:** Entity extraction response processing (around line 250)

**Replace:**
```python
# OLD (crashes on invalid type):
entity = ExtractedEntity(
    text=ent["text"],
    type=EntityType(ent["type"]),  # ❌ Crashes here
    ...
)

# NEW (graceful fallback):
from app.utils.enum_parsers import parse_entity_type, parse_relationship_type

entity = ExtractedEntity(
    text=ent["text"],
    type=parse_entity_type(ent["type"]),  # ✅ Never crashes
    ...
)
```

**For Relationships:**
```python
# OLD:
relationship = EntityRelationship(
    entity1=rel["entity1"],
    entity2=rel["entity2"],
    type=RelationshipType(rel["type"]),  # ❌ Crashes
    ...
)

# NEW:
relationship = EntityRelationship(
    entity1=rel["entity1"],
    entity2=rel["entity2"],
    type=parse_relationship_type(rel["type"]),  # ✅ Never crashes
    ...
)
```

#### Step 3: Update Pydantic Schemas

**File:** `services/content-analysis-service/app/schemas/relationship_extraction.py`

**Add validator:**
```python
from app.utils.enum_parsers import parse_entity_type, parse_relationship_type

class RelationshipTriplet(BaseModel):
    entity1: str
    entity2: str
    type: RelationshipType
    confidence: float

    @field_validator('type', mode='before')
    @classmethod
    def parse_type(cls, value):
        """Parse relationship type with graceful fallback."""
        if isinstance(value, str):
            return parse_relationship_type(value)
        return value
```

#### Step 4: Test

```bash
# Run test suite - should have 0% crash rate
cd /home/cytrex/news-microservices/tests/knowledge-graph
python3 scripts/run_test_suite.py

# Expected: 18/18 tests parse (even with fallback types)
# grep "success.*true" test-results/**/*-result.json | wc -l
```

**Expected Improvement:**
- Before: 5/18 success (28%)
- After: 18/18 parse successfully (100%)
- Quality: Some relationships mapped to RELATED_TO (acceptable)

---

## 🔴 CRITICAL FIX 2: JSON Parsing Robustness (30 minutes)

### Objective
Handle malformed JSON from LLM gracefully.

### Implementation

**File:** `services/content-analysis-service/app/llm/openai_provider.py`

**Install:** Add to `requirements.txt`:
```
json-repair==0.7.1
```

**Update parse method:**
```python
import json_repair

async def analyze(self, request: LLMRequest) -> LLMResponse:
    # ... existing code ...

    try:
        # Try standard JSON parsing first
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.warning(f"Malformed JSON from LLM: {e}")
        logger.debug(f"Raw response: {response_text[:500]}...")

        # Attempt JSON repair
        try:
            result = json_repair.loads(response_text)
            logger.info("✓ JSON repair successful")
        except Exception as repair_error:
            logger.error(f"JSON repair failed: {repair_error}")
            # Return empty fallback
            return LLMResponse(
                content={"entities": [], "relationships": []},
                metadata={"parsing_failed": True}
            )

    return LLMResponse(content=result, ...)
```

**Expected Improvement:**
- Before: 6/18 422 validation errors
- After: ~2/18 (most malformed JSON fixed)

---

## 🟡 HIGH PRIORITY FIX: Expand Enums (2-3 hours)

### Objective
Support more entity and relationship types from real-world content.

### Step 1: Database Migration

**File:** `database/migrations/expand_knowledge_graph_enums.sql`

```sql
-- Expand EntityType enum
ALTER TYPE entitytype ADD VALUE IF NOT EXISTS 'LEGISLATION';
ALTER TYPE entitytype ADD VALUE IF NOT EXISTS 'NATIONALITY';
ALTER TYPE entitytype ADD VALUE IF NOT EXISTS 'PLATFORM';
ALTER TYPE entitytype ADD VALUE IF NOT EXISTS 'LEGAL_CASE';

-- Expand RelationshipType enum
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'PRODUCES';
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'SUPPORTS';
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'OPPOSES';
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'STUDIED_AT';
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'COMPETES_WITH';
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'ACQUIRED';
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'REGULATES';

-- Verify
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'entitytype'::regtype ORDER BY enumlabel;
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'relationshiptype'::regtype ORDER BY enumlabel;
```

**Run migration:**
```bash
docker exec -i news-postgres psql -U news_user -d news_mcp < database/migrations/expand_knowledge_graph_enums.sql
```

### Step 2: Update Python Enums

**File:** `database/models/analysis.py`

```python
class EntityType(PyEnum):
    """Types of named entities."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DATE = "DATE"
    EVENT = "EVENT"
    PRODUCT = "PRODUCT"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    # NEW (2025-10-24):
    LEGISLATION = "LEGISLATION"  # Laws, acts, regulations
    NATIONALITY = "NATIONALITY"  # Ethnic/national/religious groups
    PLATFORM = "PLATFORM"  # Tech platforms, software systems
    LEGAL_CASE = "LEGAL_CASE"  # Court cases, legal precedents
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RelationshipType(PyEnum):
    """Types of entity relationships."""
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    OWNS = "owns"
    RELATED_TO = "related_to"
    MEMBER_OF = "member_of"
    PARTNER_OF = "partner_of"
    RULED_AGAINST = "ruled_against"
    ABUSED_MONOPOLY_IN = "abused_monopoly_in"
    ANNOUNCED = "announced"
    # NEW (2025-10-24):
    PRODUCES = "produces"  # Manufacturing, creation
    SUPPORTS = "supports"  # Political/organizational support
    OPPOSES = "opposes"  # Political/organizational opposition
    STUDIED_AT = "studied_at"  # Educational affiliation
    COMPETES_WITH = "competes_with"  # Business competition
    ACQUIRED = "acquired"  # Merger/acquisition
    REGULATES = "regulates"  # Regulatory authority
    NOT_APPLICABLE = "not_applicable"
```

### Step 3: Update LLM Prompt

**File:** `services/content-analysis-service/app/llm/prompts.py`

**Add to ENTITIES prompt:**
```python
RELATIONSHIP_EXTRACTION_RULES = """
## Valid Relationship Types

You MUST use ONLY these relationship types:

### Business/Professional
- works_for: Employment relationship (Person → Organization)
- owns: Ownership (Organization/Person → Asset)
- partner_of: Business partnership (Org ↔ Org)
- acquired: Acquisition (Buyer → Target)
- competes_with: Market competition (Org ↔ Org)
- produces: Manufacturing/creation (Org → Product)

### Governance/Legal
- regulates: Regulatory authority (Gov → Entity)
- ruled_against: Legal decision (Court → Entity)
- abused_monopoly_in: Antitrust violation (Org → Market)

### Political/Social
- supports: Political/social endorsement (Entity → Entity)
- opposes: Political/social opposition (Entity → Entity)
- member_of: Organizational membership (Person → Org)

### Geographic
- located_in: Physical location (Entity → Location)

### Education
- studied_at: Educational affiliation (Person → Organization)

### General
- announced: Official announcements (Entity → Event/Product)
- related_to: Generic relationship (fallback)
- not_applicable: No relationships exist

**STRICT RULE:** If unsure, use "related_to". NEVER invent new types.
"""

# Update ENTITIES system prompt to include this
```

**Expected Improvement:**
- Before: 72% failure rate
- After: <20% failure rate (most types now valid)

---

## 🟢 MEDIUM PRIORITY: Add Monitoring (1 hour)

### Objective
Track validation failures and fallback usage for continuous improvement.

### Implementation

**File:** `services/content-analysis-service/app/utils/enum_parsers.py`

**Add metrics:**
```python
from prometheus_client import Counter

invalid_type_fallback = Counter(
    'llm_invalid_type_fallback_total',
    'Invalid types from LLM requiring fallback mapping',
    ['type_category', 'attempted_value', 'fallback_value']
)

def parse_entity_type(llm_type: str) -> EntityType:
    try:
        return EntityType(llm_type.upper())
    except ValueError:
        # Metric
        invalid_type_fallback.labels(
            type_category='entity',
            attempted_value=llm_type,
            fallback_value='NOT_APPLICABLE'
        ).inc()

        logger.warning(f"Invalid EntityType '{llm_type}'")
        return EntityType.NOT_APPLICABLE
```

**Prometheus Queries:**
```promql
# Top invalid entity types
topk(10, sum by (attempted_value) (
  rate(llm_invalid_type_fallback_total{type_category="entity"}[1h])
))

# Fallback rate percentage
sum(rate(llm_invalid_type_fallback_total[5m])) /
sum(rate(entity_extraction_total[5m])) * 100
```

---

## 🟢 MEDIUM PRIORITY: Negative Example Filter (30 minutes)

### Objective
Skip analysis for content unlikely to have knowledge graph relationships.

### Implementation

**File:** `services/content-analysis-service/app/utils/content_filters.py` (NEW)

```python
"""Pre-filtering logic for content analysis."""
import re
from typing import Tuple

# Patterns indicating non-relational content
SKIP_PATTERNS = [
    r"weather\s+forecast",
    r"attendee\s+list",
    r"technical\s+specifications",
    r"product\s+datasheet",
    r"stock\s+prices",
    r"sports\s+scores",
    r"ingredient\s+list"
]

def should_skip_relationship_extraction(
    content: str,
    title: str = ""
) -> Tuple[bool, str]:
    """
    Determine if content is unlikely to contain meaningful relationships.

    Returns:
        (should_skip, reason)

    Example:
        >>> should_skip_relationship_extraction("Weekly weather forecast...")
        (True, "weather forecast detected")
    """
    full_text = f"{title} {content}".lower()

    for pattern in SKIP_PATTERNS:
        if re.search(pattern, full_text):
            return True, pattern.replace(r"\s+", " ")

    # Word count heuristic: Very short content unlikely to have relationships
    word_count = len(content.split())
    if word_count < 50:
        return True, f"content too short ({word_count} words)"

    return False, ""
```

**Integrate into test endpoint:**
```python
from app.utils.content_filters import should_skip_relationship_extraction

async def test_analyze_article(request: TestAnalysisRequest, ...):
    # Check if we should skip
    should_skip, reason = should_skip_relationship_extraction(
        request.content,
        request.title or ""
    )

    if should_skip:
        logger.info(f"Skipping relationship extraction: {reason}")
        return TestAnalysisResponse(
            article_id=article_id,
            entities=[],
            relationships=[],
            entity_count=0,
            relationship_count=0,
            processing_time_ms=0,
            cached=False
        )

    # Continue with analysis...
```

**Expected Improvement:**
- Category D (negative examples): 0% → 100% success
- Reduced unnecessary LLM calls
- Cost savings: ~5-10% fewer API calls

---

## Implementation Order

### Week 1: Critical Fixes
1. **Day 1:** Implement graceful enum fallback (Fix 1)
2. **Day 1:** Add JSON parsing robustness (Fix 2)
3. **Day 2:** Test suite validation (expect 100% parse rate)
4. **Day 2:** Deploy to staging

### Week 2: High Priority
1. **Day 3:** Database migration (expand enums)
2. **Day 3:** Update Python enums
3. **Day 4:** Update LLM prompts
4. **Day 4:** Test suite validation (expect 80%+ quality)
5. **Day 5:** Deploy to staging

### Week 3: Medium Priority
1. **Day 6:** Add monitoring metrics
2. **Day 7:** Implement negative example filter
3. **Day 7:** Final test suite run
4. **Day 8:** Production deployment

---

## Success Metrics

### After Critical Fixes (Week 1)
- ✅ 0% crash rate (500 errors eliminated)
- ✅ 100% parse rate
- ⚠️ Some quality degradation (fallback types used)

### After High Priority Fixes (Week 2)
- ✅ 90%+ use valid types (not fallbacks)
- ✅ 80%+ F1 score on Category A
- ✅ 60%+ F1 score on Category B

### After Medium Priority Fixes (Week 3)
- ✅ <5% fallback rate
- ✅ Category D: 0% false positives
- ✅ Production-ready quality

---

## Testing Checklist

After each fix phase:

```bash
# 1. Run test suite
cd /home/cytrex/news-microservices/tests/knowledge-graph
python3 scripts/run_test_suite.py

# 2. Calculate metrics
python3 scripts/calculate_metrics.py

# 3. Generate report
python3 scripts/generate_report.py
firefox test-results/test_report.html

# 4. Check Prometheus metrics
curl http://localhost:8102/metrics | grep invalid_type_fallback
```

**Acceptance Criteria:**
- [ ] 18/18 tests parse without crashes
- [ ] <10% use fallback types (after enum expansion)
- [ ] Category A: >85% F1 score
- [ ] Category D: 0 false positives
- [ ] Test suite runs in <5 minutes

---

## Rollback Plan

If fixes cause issues:

```bash
# 1. Revert code changes
git revert <commit-hash>

# 2. Rollback database migration
psql -U news_user -d news_mcp < database/migrations/rollback_enum_expansion.sql

# 3. Restart service
docker compose restart content-analysis-service

# 4. Verify old tests still work
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Owner:** Knowledge Graph Team
**Priority:** CRITICAL
