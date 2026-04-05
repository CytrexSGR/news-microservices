# Root Cause Analysis Template

## Use Case
Identify precise root cause of uncertainty in content analysis. Transforms vague uncertainty factors into actionable problem hypotheses.

## Model Recommendations
- **Primary**: gpt-4o-mini (balanced speed/accuracy)
- **Alternative**: gpt-4o (complex cases with multiple uncertainty factors)
- **Fallback**: gpt-3.5-turbo (budget constraint)

## Token Budget
- **Input**: ~1,200 tokens (truncated article + context)
- **Output**: ~300 tokens (hypothesis JSON)
- **Total Cost**: $0.00024 (gpt-4o-mini @ $0.15/1M input, $0.60/1M output)

## System Prompt

```
You are a Root Cause Analysis specialist for uncertainty diagnosis.

Task: Identify the PRECISE reason for content uncertainty.

Input:
- Article content (truncated to 2000 chars)
- Vague uncertainty factors (e.g., "Low confidence in claim accuracy")
- Current analysis (potentially incorrect)

Output: JSON matching this schema:
{
  "primary_concern": "Specific, actionable problem statement",
  "affected_content": "Exact excerpt from article",
  "hypothesis_type": "factual_error | entity_ambiguity | temporal_inconsistency | missing_context | contradictory_claims | source_reliability_issue",
  "confidence": 0.0-1.0,
  "reasoning": "Your analytical reasoning (max 200 chars)",
  "verification_approach": "High-level strategy (max 100 chars)"
}

Requirements:
1. Quote specific problematic text
2. Explain WHY it's problematic (not just THAT it is)
3. Prioritize MOST critical issue
4. Be concise (reasoning < 200 chars)
```

## User Prompt Template

```
Article: "{article_title}"
URL: {article_url}
Published: {article_published_at}

Content (truncated):
{article_content_truncated}

UQ Score: {uq_confidence_score} (lower = more uncertain)
Uncertainty Factors:
{uncertainty_factors_list}

Current Analysis:
- Summary: {analysis_summary}
- Entities: {entity_count}
- Category: {category}

Task: Identify precise root cause.
```

## Variables
- `article_title`: Article headline
- `article_url`: Source URL
- `article_published_at`: Publication timestamp
- `article_content_truncated`: First 2000 chars of content
- `uq_confidence_score`: Uncertainty score (0.0-1.0)
- `uncertainty_factors_list`: Bulleted list of factors
- `analysis_summary`: Current analysis (may be wrong)
- `entity_count`: Number of extracted entities
- `category`: Article category

## Examples

### Example 1: Factual Error
**Input:**
```
Article: "Tesla Reports Record Q3 Earnings"
Content: "Tesla Inc. announced Q3 2024 net profits of $5 billion..."
UQ Score: 0.45
Factors: ["Low confidence in claim accuracy", "Numerical claim lacks verification"]
```

**Output:**
```json
{
  "primary_concern": "Financial figure '$5 billion' appears incorrect",
  "affected_content": "Q3 2024 net profits of $5 billion",
  "hypothesis_type": "factual_error",
  "confidence": 0.85,
  "reasoning": "Industry reports show Tesla Q3 typically $4-4.5B range. Specific claim needs fact-checking.",
  "verification_approach": "Cross-reference SEC filings and Tesla IR"
}
```

### Example 2: Entity Ambiguity
**Input:**
```
Article: "Apple Announces New Partnership"
Content: "Apple has announced a strategic partnership with Oracle..."
UQ Score: 0.52
Factors: ["Entity identification unclear"]
```

**Output:**
```json
{
  "primary_concern": "Entity 'Apple' ambiguous - tech company or Apple Records",
  "affected_content": "Apple has announced a strategic partnership",
  "hypothesis_type": "entity_ambiguity",
  "confidence": 0.75,
  "reasoning": "Context mentions 'Oracle' suggesting tech, but article lacks clear disambiguation.",
  "verification_approach": "Verify entity type via knowledge graph lookup"
}
```

## Best Practices

### Token Optimization
1. **Truncate input**: Max 2000 chars for article content
2. **Constrain output**: Max 300 tokens via `max_tokens=300`
3. **Use JSON mode**: Enforces structured output (no verbose prose)

### Accuracy Improvements
1. **Low temperature**: 0.2-0.3 for consistent JSON structure
2. **Quote specifics**: Always include exact problematic text
3. **Prioritize**: Focus on MOST critical issue (don't analyze everything)

### Common Pitfalls
- ❌ Vague reasoning: "Information may be inaccurate"
- ❌ Multiple issues: Analyzing 3+ problems at once
- ❌ Missing context: Not quoting exact problematic text
- ✅ Specific diagnosis: "Financial figure '$5B' exceeds typical range by 20%"

## Performance Metrics
- **Latency**: 1.2-1.8s (gpt-4o-mini)
- **Accuracy**: 87% hypothesis type correctness
- **Cost**: $0.00024 per request

## Version History
- **v1.2.0** (2024-11-24): Reduced token usage by 30% via truncation
- **v1.1.0** (2024-11-15): Improved reasoning conciseness
- **v1.0.0** (2024-10-24): Initial version
