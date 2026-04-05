# Research Service - Specialized Research Functions

## Overview

The Research Service now includes 12+ specialized research functions that leverage Perplexity AI for deep, authoritative research capabilities. Each function is designed for specific research tasks with optimized prompts and cost-aware model selection.

## Architecture

### Base Class: `ResearchFunction`

All research functions inherit from the `ResearchFunction` base class which provides:
- Consistent execution pattern
- Automatic caching support
- Cost tracking integration
- Error handling
- Perplexity AI client integration

### Key Features

✅ **12 Specialized Functions** - Each optimized for specific research tasks
✅ **Smart Model Selection** - Automatically selects appropriate model (sonar, sonar-pro, sonar-reasoning-pro)
✅ **Cost Optimization** - Cost-aware execution with budget tracking
✅ **Caching** - Redis-backed caching to reduce API calls
✅ **Structured Outputs** - JSON-formatted results for easy parsing
✅ **Citation Support** - All results include authoritative sources

## Available Research Functions

### 1. Deep Article Analysis
**Function:** `deep_article_analysis`
**Model:** sonar-pro
**Depth:** deep

Performs comprehensive analysis of article content including:
- Main arguments and claims
- Evidence quality assessment
- Logical structure analysis
- Bias detection
- Context and background
- Implications and consequences
- Credibility assessment
- Key takeaways

**Usage:**
```python
function = get_research_function("deep_article_analysis")
result = await function.execute(
    db=db,
    user_id=user_id,
    article_title="Article Title",
    article_content="Full article text...",
    article_url="https://example.com/article"
)
```

### 2. Fact Checking
**Function:** `fact_checking`
**Model:** sonar-reasoning-pro
**Depth:** deep

Verifies multiple claims with authoritative sources:
- Verification status (true/false/partial/unverifiable)
- Confidence levels
- Supporting evidence with citations
- Contradicting evidence
- Expert consensus
- Source reliability assessment
- Important nuances

**Usage:**
```python
function = get_research_function("fact_checking")
result = await function.execute(
    db=db,
    user_id=user_id,
    claims=[
        "Claim 1 to verify",
        "Claim 2 to verify",
        "Claim 3 to verify"
    ],
    context="Additional context if needed"
)
```

### 3. Source Verification
**Function:** `source_verification`
**Model:** sonar-pro
**Depth:** standard

Assesses credibility of information sources:
- Authority and expertise
- Reputation and track record
- Bias indicators
- Transparency measures
- Fact-checking history
- Editorial standards
- Funding and ownership
- Overall credibility score (0-100)
- Usage recommendations

**Usage:**
```python
function = get_research_function("source_verification")
result = await function.execute(
    db=db,
    user_id=user_id,
    sources=[
        "Source 1 name or URL",
        "Source 2 name or URL",
        "Source 3 name or URL"
    ],
    domain="Optional domain/topic context"
)
```

### 4. Topic Extraction
**Function:** `topic_extraction`
**Model:** sonar
**Depth:** standard

Extracts and analyzes topics and themes:
- Primary topics (main subjects)
- Secondary topics (supporting themes)
- Related concepts and keywords
- Topic relationships
- Topic hierarchy
- Emerging themes
- Relevance scores
- Domain classification
- Semantic clusters

**Usage:**
```python
function = get_research_function("topic_extraction")
result = await function.execute(
    db=db,
    user_id=user_id,
    content="Text content to analyze...",
    max_topics=10
)
```

### 5. Related Content Discovery
**Function:** `related_content_discovery`
**Model:** sonar-pro
**Depth:** deep

Discovers related content and articles:
- Recent articles on topic
- Academic studies and papers
- Expert opinions
- Statistical data and reports
- Case studies
- Debates and controversies
- Alternative perspectives
- Key figures and organizations
- Recommended reading

**Usage:**
```python
function = get_research_function("related_content_discovery")
result = await function.execute(
    db=db,
    user_id=user_id,
    topic="Main topic",
    keywords=["keyword1", "keyword2", "keyword3"],
    timeframe="month"  # day, week, month
)
```

### 6. Timeline Generation
**Function:** `timeline_generation`
**Model:** sonar-pro
**Depth:** deep

Creates chronological timelines:
- Key events in order
- Dates and timeframes
- Event descriptions
- Cause-and-effect relationships
- Turning points
- Parallel developments
- Leading figures
- Impact and consequences
- Related sub-events

**Usage:**
```python
function = get_research_function("timeline_generation")
result = await function.execute(
    db=db,
    user_id=user_id,
    topic="Topic to create timeline for",
    start_date="2020-01-01",  # Optional
    end_date="2024-12-31"      # Optional
)
```

### 7. Expert Identification
**Function:** `expert_identification`
**Model:** sonar-pro
**Depth:** standard

Identifies experts and thought leaders:
- Name and credentials
- Institutional affiliation
- Areas of expertise
- Notable publications
- Citations and impact
- Social media presence
- Recent contributions
- Perspective and approach
- Credibility indicators
- Contact information

**Usage:**
```python
function = get_research_function("expert_identification")
result = await function.execute(
    db=db,
    user_id=user_id,
    field="Field of expertise",
    sub_topics=["topic1", "topic2"]  # Optional
)
```

### 8. Statistical Analysis
**Function:** `statistical_analysis`
**Model:** sonar-reasoning-pro
**Depth:** deep

Analyzes statistical data and trends:
- Current statistics
- Historical trends
- Growth rates
- Statistical significance
- Correlations
- Outliers and anomalies
- Comparative analysis
- Projections
- Data sources
- Visualizable summaries

**Usage:**
```python
function = get_research_function("statistical_analysis")
result = await function.execute(
    db=db,
    user_id=user_id,
    topic="Topic to analyze",
    metrics=["metric1", "metric2"]  # Optional
)
```

### 9. Trend Detection
**Function:** `trend_detection`
**Model:** sonar-pro
**Depth:** deep

Detects emerging trends:
- Emerging patterns
- Trend strength
- Early indicators
- Adoption curves
- Geographic distribution
- Demographic patterns
- Driving forces
- Potential disruptions
- Future predictions
- Investment metrics

**Usage:**
```python
function = get_research_function("trend_detection")
result = await function.execute(
    db=db,
    user_id=user_id,
    domain="Domain to analyze",
    timeframe="6 months"  # Time period
)
```

### 10. Claim Verification
**Function:** `claim_verification`
**Model:** sonar-reasoning-pro
**Depth:** deep

Verifies specific claims:
- Truthfulness assessment
- Confidence level
- Supporting evidence
- Contradicting evidence
- Expert opinions
- Original sources
- Similar claims
- Common misconceptions
- Important context
- Verification methodology

**Usage:**
```python
function = get_research_function("claim_verification")
result = await function.execute(
    db=db,
    user_id=user_id,
    claim="Specific claim to verify",
    context="Optional context"
)
```

### 11. Comparative Analysis
**Function:** `comparative_analysis`
**Model:** sonar-pro
**Depth:** deep

Compares multiple topics or approaches:
- Key similarities
- Important differences
- Strengths and weaknesses
- Use cases
- Performance metrics
- Cost-benefit analysis
- Expert preferences
- Historical evolution
- Future outlook
- Recommendation matrix

**Usage:**
```python
function = get_research_function("comparative_analysis")
result = await function.execute(
    db=db,
    user_id=user_id,
    items=["Item 1", "Item 2", "Item 3"],
    comparison_aspects=["aspect1", "aspect2"]  # Optional
)
```

### 12. Impact Assessment
**Function:** `impact_assessment`
**Model:** sonar-reasoning-pro
**Depth:** deep

Assesses impact and consequences:
- Immediate effects
- Short-term consequences
- Long-term implications
- Direct impacts
- Ripple effects
- Economic impacts
- Social effects
- Environmental considerations
- Policy implications
- Mitigation strategies

**Usage:**
```python
function = get_research_function("impact_assessment")
result = await function.execute(
    db=db,
    user_id=user_id,
    event_or_decision="Event or decision to assess",
    stakeholders=["stakeholder1", "stakeholder2"]  # Optional
)
```

## Helper Functions

### List Available Functions
```python
from app.services.research import list_research_functions

functions = list_research_functions()
# Returns list of all functions with metadata:
# [
#   {
#     "name": "deep_article_analysis",
#     "description": "...",
#     "model": "sonar-pro",
#     "depth": "deep"
#   },
#   ...
# ]
```

### Get Specific Function
```python
from app.services.research import get_research_function

function = get_research_function("fact_checking")
if function:
    result = await function.execute(db=db, user_id=user_id, ...)
```

## Model Selection Strategy

### sonar (Cost-effective)
- Used for: Topic extraction
- Cost: $0.005 per 1k tokens
- Best for: Simple extraction tasks

### sonar-pro (Balanced)
- Used for: Source verification, expert identification, comparative analysis, trend detection, related content, timeline generation
- Cost: $0.015 per 1k tokens
- Best for: Complex analysis requiring good reasoning

### sonar-reasoning-pro (Premium)
- Used for: Fact checking, claim verification, statistical analysis, impact assessment, deep article analysis
- Cost: $0.025 per 1k tokens
- Best for: Critical analysis requiring highest accuracy

## Cost Optimization

All functions integrate with the cost optimizer:
- **Automatic caching** - Reuses results when appropriate
- **Budget tracking** - Monitors daily/monthly costs
- **Tier adjustment** - Downgrades model if budget constrained
- **Query estimation** - Predicts cost before execution

## Response Format

All functions return structured results:
```python
{
    "function": "function_name",
    "task_id": 123,
    "status": "completed",
    "result": {
        "content": "Structured analysis...",
        "citations": [...],
        "sources": [...]
    },
    "cost": 0.05,
    "tokens_used": 1000
}
```

## Error Handling

Functions handle errors gracefully:
- API failures trigger retries (up to 3 attempts)
- Rate limiting automatically backs off
- Budget exceeded returns clear error message
- Invalid inputs are validated before API calls

## Integration with ResearchService

Functions integrate seamlessly with the existing `ResearchService`:
- Use same caching mechanism
- Share cost tracking
- Follow same security patterns
- Work with existing database models

## Testing

Test each function:
```python
# Example test
async def test_fact_checking():
    function = get_research_function("fact_checking")
    result = await function.execute(
        db=test_db,
        user_id=1,
        claims=["The Earth is round"],
        context="Scientific fact"
    )
    
    assert result["status"] == "completed"
    assert "result" in result
    assert result["cost"] > 0
```

## Performance Metrics

Expected performance:
- **Deep analysis**: 10-30 seconds, $0.10-0.50 per request
- **Standard analysis**: 5-15 seconds, $0.05-0.20 per request
- **Quick queries**: 2-8 seconds, $0.01-0.10 per request
- **Cached results**: <1 second, $0.00

## Future Enhancements

Potential additions:
- Multi-language support
- Image analysis integration
- Real-time trend monitoring
- Automated fact-checking pipelines
- Cross-referencing between functions
- Batch processing support
- Custom model fine-tuning

---

**Last Updated:** 2025-10-11
**Service Version:** 0.1.0
**Total Functions:** 12
**Status:** ✅ Production Ready
