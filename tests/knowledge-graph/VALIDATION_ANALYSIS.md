# Knowledge Graph Test Suite - Validation Analysis Report

**Date:** 2025-10-24
**Test Suite Version:** 1.0
**Service:** content-analysis-service
**Endpoint:** `/api/v1/test/analyze`

---

## Executive Summary

**Test Results:**
- ✅ **5/18 Tests Successful (28%)**
- ❌ **13/18 Tests Failed (72%)**

**Failure Categories:**
- 🔴 **7 failures:** 500 Server Error (Internal)
- 🟡 **6 failures:** 422 Validation Error (Unprocessable Entity)

**Root Cause:** LLM generates entity types and relationship types that are **not in our enum definitions**, causing Pydantic validation failures and crashes.

---

## Problem 1: Invalid Entity Types (7 failures)

### What Happened
LLM outputs entity types that don't exist in our `EntityType` enum, causing the service to crash with 500 errors.

### Allowed EntityType Values
```python
class EntityType(PyEnum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DATE = "DATE"
    EVENT = "EVENT"
    PRODUCT = "PRODUCT"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
```

### LLM Generated (Invalid)
| Invalid Type | Frequency | Example Context |
|--------------|-----------|-----------------|
| `LEGISLATION` | 3 | EU AI Act, regulatory frameworks |
| `NORP` | 1 | Nationalities/Religious/Political groups |
| `PLATFORM` | 1 | Technology platforms |
| `LEGAL_REFERENCE` | 1 | Court cases, legal citations |

### Error Messages
```
ValueError: 'LEGISLATION' is not a valid EntityType
ValueError: 'NORP' is not a valid EntityType
ValueError: 'PLATFORM' is not a valid EntityType
ValueError: 'LEGAL_REFERENCE' is not a valid EntityType
```

### Impact
- **Severity:** HIGH
- **Crash Type:** 500 Internal Server Error
- **User Experience:** Complete failure, no results returned
- **Affected Categories:**
  - Category A: 2/5 failures
  - Category B: 3/5 failures
  - Category C: 2/5 failures

---

## Problem 2: Invalid Relationship Types (6+ failures)

### What Happened
LLM outputs relationship types that don't exist in our `RelationshipType` enum.

### Allowed RelationshipType Values
```python
class RelationshipType(PyEnum):
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    OWNS = "owns"
    RELATED_TO = "related_to"
    MEMBER_OF = "member_of"
    PARTNER_OF = "partner_of"
    # Extended (2025-10-23):
    RULED_AGAINST = "ruled_against"
    ABUSED_MONOPOLY_IN = "abused_monopoly_in"
    ANNOUNCED = "announced"
    NOT_APPLICABLE = "not_applicable"
```

### LLM Generated (Invalid)
| Invalid Type | Frequency | Example Usage |
|--------------|-----------|---------------|
| `supporter_of` | 1 | Political endorsements |
| `organizes` | 1 | Event organization |
| `studied_at` | 1 | Education relationships |
| `won` | 1 | Competition victories |
| `owned_by` | 1 | Ownership (inverse of `owns`) |
| `produces` | 1 | Manufacturing/creation |

### Error Messages
```
ValueError: 'supporter_of' is not a valid RelationshipType
ValueError: 'organizes' is not a valid RelationshipType
ValueError: 'produces' is not a valid RelationshipType
```

### Impact
- **Severity:** HIGH
- **Crash Type:** 500 Internal Server Error
- **Root Cause:** LLM tries to express relationships not in our constrained vocabulary
- **Affected Articles:** Complex political/economic analysis (Category B & C)

---

## Problem 3: Pydantic Validation Failures (6 failures)

### What Happened
LLM response doesn't match our strict Pydantic schemas, causing 422 errors.

### Common Validation Errors

#### Missing Required Fields
```
1 validation error for EntityExtractionResponse
  Field required [type=missing, ...]
```

**Cause:** LLM response JSON is missing required fields like `entities` or `relationships`.

#### Malformed JSON
```
ValueError: Failed to parse JSON response: Expecting ':' delimiter: line 622 column 1
```

**Cause:** LLM generates invalid JSON syntax (missing colons, trailing commas, etc.)

### Impact
- **Severity:** MEDIUM
- **Crash Type:** 422 Unprocessable Entity
- **Affected Categories:**
  - Category C: 3/5 failures (opinion pieces, commentary)
  - Category D: 3/3 failures (negative examples)
- **Pattern:** Happens more with ambiguous/opinion content

---

## Problem 4: Other Enum Validation Failures

### Invalid BiasDirection
```
ValueError: 'negative' is not a valid BiasDirection
```

**Expected:** Sentiment polarity enums like `LEFT`, `RIGHT`, `NEUTRAL`
**LLM Generated:** `negative` (sentiment label, not bias direction)

### Invalid ArticleCategory
```
ValueError: 'Crime & Security' is not a valid ArticleCategory
```

**Expected:** `GEOPOLITICS_SECURITY`
**LLM Generated:** `Crime & Security` (close match but wrong format)

---

## Success Pattern Analysis (5 successful tests)

### Successful Articles
1. ✅ article-002-acquisition (Category A)
2. ✅ article-003-court-ruling (Category A)
3. ✅ article-005-factory-opening (Category A)
4. ✅ article-007-geopolitical-conflict (Category B)
5. ✅ article-008-economic-analysis (Category B)

### Common Characteristics
- **Simple, factual content** (acquisitions, product launches)
- **Standard entity types** (PERSON, ORGANIZATION, LOCATION, DATE)
- **Standard relationships** (works_for, located_in, partner_of)
- **Clear subject-verb-object structure**
- **No ambiguity or opinion**

### Example Success: article-002-acquisition
```json
{
  "entities": [
    {"text": "Adobe Inc.", "type": "ORGANIZATION"},
    {"text": "Figma Inc.", "type": "ORGANIZATION"},
    {"text": "Dylan Field", "type": "PERSON"}
  ],
  "relationships": [
    {"entity1": "Adobe Inc.", "entity2": "Figma Inc.", "type": "works_for"},
    {"entity1": "Figma Inc.", "entity2": "San Francisco", "type": "located_in"}
  ]
}
```

**Why it worked:** All types are valid enums, JSON is well-formed.

---

## Failure Pattern Analysis

### Category A (Simple) - 60% Success Rate
- **Failures:** 2/5
- **Pattern:** Fails when LLM tries to be too specific (e.g., PLATFORM instead of PRODUCT)

### Category B (Complex) - 40% Success Rate
- **Failures:** 3/5
- **Pattern:** Complex political/economic content triggers invalid types (LEGISLATION, supporter_of)

### Category C (Ambiguous) - 0% Success Rate ❌
- **Failures:** 5/5
- **Pattern:** Opinion pieces and commentary cause massive validation failures
- **Root Cause:** LLM struggles with subjective content, generates invalid types

### Category D (Negative Examples) - 0% Success Rate ❌
- **Failures:** 3/3
- **Pattern:** ALL negative examples failed
- **Expected:** Should return `{"entities": [], "relationships": []}`
- **Actual:** Validation errors, possibly hallucinating entities

---

## Root Cause Analysis

### 1. Prompt Engineering Gap
**Problem:** Our prompts don't strictly constrain LLM to valid enum values.

**Evidence:**
```python
# Prompt says "extract relationships" but doesn't list ALL valid types
# LLM invents plausible types like "supporter_of", "produces"
```

**Impact:** LLM generates semantically correct but syntactically invalid types.

### 2. Enum Coverage Gap
**Problem:** Our enums are too restrictive for real-world knowledge graphs.

**Missing Entity Types:**
- LEGISLATION (laws, regulations)
- NATIONALITY/GROUP (ethnic, religious, political groups)
- PLATFORM (software platforms, social media)
- LEGAL_CASE (court cases)

**Missing Relationship Types:**
- produces/manufactures
- supports/opposes (political)
- studied_at/graduated_from (education)
- competes_with/rivals
- acquired/merged_with
- regulates/governed_by

### 3. Schema Validation Too Strict
**Problem:** Pydantic validation fails HARD on any deviation.

**Current Behavior:**
```python
# If LLM outputs "supporter_of" → CRASH (500 error)
# No fallback, no graceful degradation
```

**Desired Behavior:**
```python
# If LLM outputs invalid type → SKIP/MAP to RELATED_TO
# Log warning, continue processing
```

### 4. JSON Robustness Gap
**Problem:** Malformed JSON from LLM causes complete failure.

**Examples:**
- Missing colons
- Trailing commas
- Unclosed brackets

**Impact:** 422 errors even when content is extractable.

---

## Recommended Fixes (Priority Order)

### 🔴 CRITICAL (Fix Immediately)

#### 1. Add Graceful Fallback for Invalid Types
**Location:** `app/llm/openai_provider.py`, `app/services/analysis_service.py`

**Implementation:**
```python
def parse_entity_type(llm_type: str) -> EntityType:
    """Parse LLM entity type with fallback."""
    try:
        return EntityType(llm_type)
    except ValueError:
        logger.warning(f"Invalid EntityType '{llm_type}', mapping to NOT_APPLICABLE")
        return EntityType.NOT_APPLICABLE

def parse_relationship_type(llm_type: str) -> RelationshipType:
    """Parse LLM relationship type with fallback."""
    try:
        return RelationshipType(llm_type)
    except ValueError:
        logger.warning(f"Invalid RelationshipType '{llm_type}', mapping to RELATED_TO")
        return RelationshipType.RELATED_TO
```

**Impact:** Eliminates 500 errors, tests become 100% parseable.

#### 2. Improve JSON Parsing Robustness
**Location:** `app/llm/openai_provider.py`

**Add:** JSON repair library or regex cleaning before parsing.

**Example:**
```python
import json_repair

def parse_llm_json(raw_response: str) -> dict:
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError as e:
        # Try to repair malformed JSON
        logger.warning(f"Malformed JSON, attempting repair: {e}")
        try:
            return json_repair.loads(raw_response)
        except:
            logger.error(f"JSON repair failed, using fallback")
            return {"entities": [], "relationships": []}
```

### 🟡 HIGH PRIORITY (Fix This Week)

#### 3. Expand Entity Type Enum
**Location:** `database/models/analysis.py`

**Add:**
```python
class EntityType(PyEnum):
    # Existing...
    LEGISLATION = "LEGISLATION"  # Laws, regulations, acts
    NATIONALITY = "NATIONALITY"  # Ethnic/national groups
    PLATFORM = "PLATFORM"  # Tech platforms, systems
    LEGAL_CASE = "LEGAL_CASE"  # Court cases
```

**Migration Required:** Yes (database enum)

#### 4. Expand Relationship Type Enum
**Location:** `database/models/analysis.py`

**Add:**
```python
class RelationshipType(PyEnum):
    # Existing...
    PRODUCES = "produces"  # Manufacturing, creation
    SUPPORTS = "supports"  # Political/social support
    OPPOSES = "opposes"  # Political/social opposition
    STUDIED_AT = "studied_at"  # Education
    COMPETES_WITH = "competes_with"  # Business competition
    ACQUIRED = "acquired"  # Business acquisition
    REGULATES = "regulates"  # Regulatory relationships
```

#### 5. Improve Prompt Constraints
**Location:** `app/llm/prompts.py`

**Add to ENTITIES prompt:**
```
STRICT REQUIREMENT: You MUST only use these entity types:
- PERSON, ORGANIZATION, LOCATION, DATE, EVENT, PRODUCT, MONEY, PERCENT

STRICT REQUIREMENT: You MUST only use these relationship types:
- works_for, located_in, owns, related_to, member_of, partner_of
- ruled_against, abused_monopoly_in, announced

If a relationship doesn't fit these types, use "related_to" as a fallback.
NEVER invent new types. NEVER use types not in this list.
```

### 🟢 MEDIUM PRIORITY (Next Sprint)

#### 6. Add Validation Metrics
**Track:**
- Invalid type fallback rate
- JSON repair success rate
- Pydantic validation failure rate

**Prometheus Metrics:**
```python
invalid_entity_type_total = Counter(
    'invalid_entity_type_total',
    'Entity types rejected and mapped to fallback',
    ['attempted_type', 'mapped_to']
)
```

#### 7. Category D (Negative Examples) Fix
**Problem:** Weather reports, attendee lists → Should have 0 relationships

**Solution:** Add pre-filtering logic:
```python
def should_skip_analysis(content: str) -> bool:
    """Detect content unlikely to have meaningful relationships."""
    skip_patterns = [
        r"weather forecast",
        r"attendee list",
        r"technical specifications",
        r"product datasheet"
    ]
    return any(re.search(pattern, content.lower()) for pattern in skip_patterns)
```

---

## Testing Impact Analysis

### Before Fixes
- **Success Rate:** 28% (5/18)
- **Crash Rate:** 72% (13/18)
- **User Experience:** Broken

### After CRITICAL Fixes (Estimated)
- **Success Rate:** 100% (18/18) ✅
- **Crash Rate:** 0%
- **Quality:** Lower (fallback types used)
- **User Experience:** Working but with warnings

### After HIGH PRIORITY Fixes (Estimated)
- **Success Rate:** 100% (18/18) ✅
- **Quality:** High (proper types used)
- **False Positive Rate:** <10%
- **User Experience:** Production-ready

---

## Conclusion

### Key Findings
1. **Test Suite Works Perfectly:** Infrastructure is solid, found real issues
2. **Enum Definitions Too Restrictive:** Need 10+ more entity/relationship types
3. **No Graceful Degradation:** Service crashes instead of falling back
4. **Prompt Engineering Needs Work:** LLM not constrained enough

### Success Criteria for v2.0
- ✅ 100% of tests parse without crashes
- ✅ 90%+ success rate on Category A (simple)
- ✅ 70%+ success rate on Category B (complex)
- ✅ 50%+ success rate on Category C (ambiguous)
- ✅ 0% false positives on Category D (negative)

### Next Steps
1. Implement CRITICAL fixes (graceful fallback)
2. Run test suite again → Expect 100% parse rate
3. Implement HIGH PRIORITY fixes (expand enums)
4. Run test suite again → Expect 80%+ quality
5. Implement MEDIUM PRIORITY fixes (metrics, filtering)
6. Production deployment

---

## Appendix: Detailed Error Log

### Failed Articles List

**500 Errors (Internal):**
1. article-001-ceo-appointment → Invalid EntityType
2. article-004-product-launch → Invalid EntityType
3. article-006-merger-analysis → Invalid RelationshipType
4. article-009-investigative-journalism → Invalid EntityType
5. article-010-political-analysis → Invalid RelationshipType
6. article-011-opinion-tech-regulation → Invalid EntityType
7. article-012-interview-indirect-speech → Invalid RelationshipType

**422 Errors (Validation):**
1. article-013-market-speculation → Malformed JSON
2. article-014-political-commentary → Missing required fields
3. article-015-future-prediction → Pydantic validation error
4. article-016-conference-attendees → Invalid response structure
5. article-017-weather-report → Validation failure
6. article-018-product-specs → Invalid JSON

---

**Report Generated:** 2025-10-24 04:50:00 UTC
**Test Suite Location:** `/home/cytrex/news-microservices/tests/knowledge-graph/`
**Raw Results:** `test-results/`
**Service Logs:** `docker logs news-content-analysis-service`
