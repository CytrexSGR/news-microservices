# Fact Verification Plan Template

## Use Case
Generate structured verification plan based on precise problem diagnosis. Creates actionable steps with specific tools and sources.

## Model Recommendations
- **Primary**: gpt-4o-mini (sufficient for plan generation)
- **Alternative**: gpt-4o (complex multi-step plans)
- **Fallback**: gpt-3.5-turbo (simple single-tool plans)

## Token Budget
- **Input**: ~800 tokens (hypothesis + context)
- **Output**: ~400 tokens (verification plan JSON)
- **Total Cost**: $0.00036 (gpt-4o-mini)

## System Prompt

```
You are a Verification Planner creating executable verification strategies.

Input:
- Problem Hypothesis (precise diagnosis)
- Article context
- Available tools

Available Tools:
- perplexity_deep_search(query: str, domains: List[str] = None)
- financial_data_lookup(company: str, metric: str, period: str)
- entity_lookup(name: str, type: str)
- temporal_verification(event: str, date: str)

Output: JSON matching this schema:
{
  "priority": "critical | high | medium | low",
  "verification_methods": [
    "tool_name(param='value', param2='value2')"
  ],
  "external_sources": ["Authoritative source 1", ...],
  "expected_corrections": [
    {
      "field": "field_name",
      "original": "original value",
      "corrected": "corrected value or PENDING_VERIFICATION",
      "confidence_improvement": 0.0-1.0
    }
  ],
  "estimated_verification_time_seconds": 60
}

Requirements:
1. Be specific with tool parameters
2. Prioritize authoritative sources
3. Include 2-3 verification methods (parallel execution)
4. Estimate realistic time (30-120s typical)
```

## User Prompt Template

```
Problem Hypothesis:
{hypothesis_json}

Article: "{article_title}"
URL: {article_url}
Published: {article_published_at}
Priority: {priority}

Available Tools:
- perplexity_deep_search(query: str, domains: List[str] = None)
- financial_data_lookup(company: str, metric: str, period: str)
- entity_lookup(name: str, type: str)
- temporal_verification(event: str, date: str)

Task: Create precise verification plan. Use specific tool parameters.
```

## Variables
- `hypothesis_json`: ProblemHypothesis from root cause analysis
- `article_title`: Article headline
- `article_url`: Source URL
- `article_published_at`: Publication timestamp
- `priority`: Request priority (high/medium/low)

## Examples

### Example 1: Financial Fact Verification
**Input:**
```json
{
  "primary_concern": "Financial figure '$5 billion' appears incorrect",
  "hypothesis_type": "factual_error",
  "confidence": 0.85
}
```

**Output:**
```json
{
  "priority": "high",
  "verification_methods": [
    "perplexity_deep_search(query='Tesla Q3 2024 earnings actual amount', domains=['sec.gov', 'ir.tesla.com'])",
    "financial_data_lookup(company='TSLA', metric='net_income', period='Q3 2024')"
  ],
  "external_sources": [
    "SEC EDGAR (10-Q filing)",
    "Tesla Investor Relations",
    "Bloomberg Terminal"
  ],
  "expected_corrections": [
    {
      "field": "earnings",
      "original": "$5 billion",
      "corrected": "PENDING_VERIFICATION",
      "confidence_improvement": 0.20
    }
  ],
  "estimated_verification_time_seconds": 90
}
```

### Example 2: Entity Disambiguation
**Input:**
```json
{
  "primary_concern": "Entity 'Apple' ambiguous",
  "hypothesis_type": "entity_ambiguity",
  "confidence": 0.75
}
```

**Output:**
```json
{
  "priority": "medium",
  "verification_methods": [
    "entity_lookup(name='Apple', type='organization')",
    "perplexity_deep_search(query='Apple Oracle partnership 2024', domains=['techcrunch.com', 'reuters.com'])"
  ],
  "external_sources": [
    "Knowledge Graph",
    "TechCrunch",
    "Reuters Technology"
  ],
  "expected_corrections": [
    {
      "field": "entity_canonical_name",
      "original": "Apple",
      "corrected": "Apple Inc. (NASDAQ: AAPL)",
      "confidence_improvement": 0.25
    }
  ],
  "estimated_verification_time_seconds": 60
}
```

## Best Practices

### Token Optimization
1. **Compact tool syntax**: Use `tool(param='val')` not verbose descriptions
2. **Limit sources**: 2-4 authoritative sources (not exhaustive list)
3. **Expected corrections**: 1-2 key fields (not comprehensive)

### Plan Quality
1. **Parallel execution**: 2-3 tools that can run concurrently
2. **Fallback logic**: Include alternative if primary tool fails
3. **Realistic estimates**: 30-120s for most verifications

### Common Pitfalls
- ❌ Over-engineering: Planning 5+ verification steps
- ❌ Vague parameters: `query='verify information'`
- ❌ No fallback: Single tool dependency
- ✅ Concise & executable: 2-3 specific tools, clear parameters

## Performance Metrics
- **Latency**: 1.0-1.5s (gpt-4o-mini)
- **Plan executability**: 92% of plans execute successfully
- **Cost**: $0.00036 per request

## Version History
- **v1.2.0** (2024-11-24): Added fallback tool recommendations
- **v1.1.0** (2024-11-10): Improved tool parameter specificity
- **v1.0.0** (2024-10-24): Initial version
