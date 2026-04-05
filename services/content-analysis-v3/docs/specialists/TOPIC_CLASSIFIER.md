# TOPIC_CLASSIFIER Specialist

## Overview

The TOPIC_CLASSIFIER specialist provides detailed topic classification with hierarchical parent categories, building on Tier1's broad keyword classification.

**File:** `/app/pipeline/tier2/specialists/topic_classifier.py`

## Purpose

Enhance Tier1's broad topic keywords (FINANCE, TECHNOLOGY, etc.) with specific, granular topics organized into parent categories for better article categorization and searchability.

## Architecture

### Extends BaseSpecialist

```python
class TopicClassifierSpecialist(BaseSpecialist):
    def __init__(self):
        super().__init__(specialist_type=SpecialistType.TOPIC_CLASSIFIER)
```

### Two-Stage Processing

1. **Quick Check** (~100 tokens, < 2 seconds)
   - Determines if article has classifiable topics
   - Uses Tier1 topics as reference
   - Returns YES/NO with reasoning

2. **Deep Dive** (~1500 tokens, 3-5 seconds)
   - Extracts 2-5 detailed topics
   - Assigns parent categories
   - Provides confidence scores

## Token Budget

- **Total:** ~1700 tokens per article
- **Quick Check:** 100 tokens
- **Deep Dive:** 1500 tokens
- **Cost:** ~$0.00003 per article (Gemini 2.0 Flash Exp)

## Input

### From Tier1Results
```python
topics: [
    Topic(keyword="FINANCE", confidence=0.95, parent_category="Economic"),
    Topic(keyword="TECHNOLOGY", confidence=0.85, parent_category="Innovation")
]
```

### Article Data
- `title`: Article title
- `content`: Full article content (truncated to 3000 chars)

## Output

### SpecialistFindings Structure

```python
SpecialistFindings(
    specialist_type=SpecialistType.TOPIC_CLASSIFIER,
    topic_classification=TopicClassification(
        topics=[
            {
                "topic": "Bitcoin Price Analysis",
                "parent_topic": "Economics and Finance",
                "confidence": 0.95
            },
            {
                "topic": "Federal Reserve Policy",
                "parent_topic": "Economics and Finance",
                "confidence": 0.85
            }
        ]
    ),
    tokens_used=1200,
    cost_usd=0.00004,
    model="gemini-2.0-flash-exp"
)
```

## Examples

### Example 1: Financial Article

**Input (Tier1):**
```json
{
  "topics": [
    {"keyword": "FINANCE", "confidence": 0.95}
  ]
}
```

**Output:**
```json
{
  "topics": [
    {
      "topic": "Bitcoin Price Analysis",
      "parent_topic": "Economics and Finance",
      "confidence": 0.95
    },
    {
      "topic": "Federal Reserve Monetary Policy",
      "parent_topic": "Economics and Finance",
      "confidence": 0.90
    },
    {
      "topic": "Cryptocurrency Market Trends",
      "parent_topic": "Technology and Innovation",
      "confidence": 0.85
    }
  ]
}
```

### Example 2: Technology Article

**Input (Tier1):**
```json
{
  "topics": [
    {"keyword": "TECHNOLOGY", "confidence": 0.90},
    {"keyword": "SECURITY", "confidence": 0.75}
  ]
}
```

**Output:**
```json
{
  "topics": [
    {
      "topic": "AI Ethics and Regulation",
      "parent_topic": "Technology and Innovation",
      "confidence": 0.92
    },
    {
      "topic": "Data Privacy Legislation",
      "parent_topic": "Legal and Regulatory",
      "confidence": 0.88
    },
    {
      "topic": "Cybersecurity Infrastructure",
      "parent_topic": "Technology and Innovation",
      "confidence": 0.80
    }
  ]
}
```

## Parent Topic Categories

The specialist uses these standard parent categories:

- **Economics and Finance**
  - Bitcoin, stocks, monetary policy, market analysis

- **Geopolitics and Defense**
  - NATO, military strategy, diplomatic relations

- **Technology and Innovation**
  - AI, blockchain, renewable energy, cybersecurity

- **Social and Cultural Issues**
  - Demographics, education, public health

- **Environmental and Climate**
  - Climate change, sustainability, conservation

- **Legal and Regulatory**
  - Legislation, compliance, government policy

- **Healthcare and Biosciences**
  - Medical research, pharmaceuticals, public health

- **Energy and Resources**
  - Oil, gas, renewable energy, commodities

## Error Handling

### Quick Check Failure
```python
# Conservative fallback: assume relevant if Tier1 has topics
return QuickCheckResult(
    is_relevant=len(tier1_results.topics) > 0,
    confidence=0.5,
    reasoning=f"Error during quick check: {str(e)}",
    tokens_used=0
)
```

### Deep Dive Failure
```python
# Return empty findings with metadata
return SpecialistFindings(
    specialist_type=SpecialistType.TOPIC_CLASSIFIER,
    topic_classification=TopicClassification(topics=[]),
    tokens_used=0,
    cost_usd=0.0,
    model=self.provider.model
)
```

### JSON Parse Error
```python
# Return empty topics but preserve metadata
return SpecialistFindings(
    specialist_type=SpecialistType.TOPIC_CLASSIFIER,
    topic_classification=TopicClassification(topics=[]),
    tokens_used=metadata.tokens_used,
    cost_usd=metadata.cost_usd,
    model=metadata.model
)
```

## Integration

### Import and Use

```python
from app.pipeline.tier2.specialists import TopicClassifierSpecialist

# Initialize
specialist = TopicClassifierSpecialist()

# Quick check only
result = await specialist.quick_check(
    article_id=article_id,
    title=title,
    content=content,
    tier1_results=tier1_results
)

# Full analysis (quick_check + deep_dive)
findings = await specialist.analyze(
    article_id=article_id,
    title=title,
    content=content,
    tier1_results=tier1_results,
    max_tokens=1700
)
```

### In Tier2 Pipeline

```python
from app.pipeline.tier2.orchestrator import Tier2Orchestrator

# Orchestrator automatically manages specialists
orchestrator = Tier2Orchestrator(db_pool=db_pool)

tier2_results = await orchestrator.execute(
    article_id=article_id,
    title=title,
    content=content,
    tier1_results=tier1_results
)

# Access topic classification
if "TOPIC_CLASSIFIER" in tier2_results.specialists:
    topics = tier2_results.specialists["TOPIC_CLASSIFIER"].topic_classification.topics
```

## Performance

### Benchmarks

- **Quick Check:** 100 tokens, 0.5-1.5 seconds
- **Deep Dive:** 1200-1500 tokens, 3-5 seconds
- **Total:** 1300-1600 tokens, 3.5-6.5 seconds

### Cost Analysis

At Gemini 2.0 Flash Exp pricing ($0.00003 per 1000 tokens):
- **Per article:** $0.00003 - $0.00005
- **Per 1000 articles:** $0.03 - $0.05
- **Per 100K articles:** $3 - $5

## Testing

Comprehensive test suite in `tests/test_topic_classifier.py`:

```bash
# Run all tests
pytest tests/test_topic_classifier.py -v

# Run specific test
pytest tests/test_topic_classifier.py::test_deep_dive_analysis -v
```

### Test Coverage

- ✅ Specialist initialization
- ✅ Quick check with topics
- ✅ Quick check without topics
- ✅ Deep dive analysis
- ✅ Full analyze workflow
- ✅ Token tracking
- ✅ Budget enforcement

## Logging

All operations are logged with structured context:

```python
logger.info(f"[{article_id}] TOPIC_CLASSIFIER: Quick check starting")
logger.info(f"[{article_id}] TOPIC_CLASSIFIER: Quick check complete - relevant={is_relevant}, confidence={confidence:.2f}")
logger.info(f"[{article_id}] TOPIC_CLASSIFIER: Deep dive starting (max_tokens={max_tokens})")
logger.info(f"[{article_id}] TOPIC_CLASSIFIER: Deep dive complete - topics={len(topics)}, tokens={tokens_used}")
logger.error(f"[{article_id}] TOPIC_CLASSIFIER: JSON parse failed: {e}")
```

## Future Enhancements

1. **Multi-language Support**
   - Detect article language
   - Use language-specific topic hierarchies

2. **Custom Taxonomies**
   - Support user-defined topic hierarchies
   - Industry-specific categorizations

3. **Topic Trends**
   - Track topic frequency over time
   - Detect emerging topics

4. **Confidence Calibration**
   - Track accuracy of confidence scores
   - Auto-adjust thresholds

## Related Documentation

- [Tier2 Base Specialist](../tier2/BASE_SPECIALIST.md)
- [Specialist Models](../tier2/MODELS.md)
- [Provider Factory](../providers/FACTORY.md)
- [Data Model Design](/home/cytrex/userdocs/content-analysis-v3/design/data-model.md)

## Change Log

### 2025-11-19: Initial Implementation
- ✅ Created TopicClassifierSpecialist class
- ✅ Implemented quick_check stage
- ✅ Implemented deep_dive stage
- ✅ Added comprehensive test suite
- ✅ Documentation complete
