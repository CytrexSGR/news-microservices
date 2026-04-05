# Deep Research Template

## Use Case
Comprehensive research synthesis across multiple sources. Used for high-value investigations.

## Model Recommendations
- **Primary**: gpt-4o (highest quality reasoning)
- **Fallback**: gpt-4o-mini (acceptable for straightforward topics)

## Token Budget
- **Input**: ~3,000 tokens (multi-document context)
- **Output**: ~1,000 tokens (comprehensive analysis)
- **Total Cost**: $0.013 (gpt-4o) or $0.00165 (gpt-4o-mini)

## System Prompt

```
You are a research analyst synthesizing information from multiple sources.

Task: Create comprehensive analysis including:
1. Key findings (3-5 points)
2. Supporting evidence with citations
3. Contradictions or inconsistencies
4. Confidence assessment
5. Knowledge gaps

Output JSON:
{
  "key_findings": [{"finding": str, "sources": List[str], "confidence": float}],
  "contradictions": [{"claim_a": str, "claim_b": str, "sources": List[str]}],
  "confidence_overall": float,
  "knowledge_gaps": [str],
  "recommendations": [str]
}

Be thorough but concise. Cite sources for all claims.
```

## User Prompt Template

```
Research Topic: "{research_question}"

Sources:
{source_1}

{source_2}

{source_3}

Task: Synthesize findings, identify contradictions, assess confidence.
```

## Variables
- `research_question`: Primary research question
- `source_1`, `source_2`, `source_3`: Source documents (truncated to 1000 chars each)

## Example Output

```json
{
  "key_findings": [
    {
      "finding": "Tesla Q3 2024 revenue was $25.18B, up 7.8% YoY",
      "sources": ["SEC 10-Q Filing", "Tesla IR"],
      "confidence": 0.95
    },
    {
      "finding": "Automotive gross margin declined to 16.3% from 17.9%",
      "sources": ["10-Q Filing", "Bloomberg Analysis"],
      "confidence": 0.92
    }
  ],
  "contradictions": [
    {
      "claim_a": "Net income: $2.17B (SEC filing)",
      "claim_b": "Net income: $2.3B (Bloomberg article)",
      "sources": ["SEC 10-Q", "Bloomberg 2024-10-24"]
    }
  ],
  "confidence_overall": 0.88,
  "knowledge_gaps": [
    "Detailed breakdown of operating expenses",
    "Full-year 2024 guidance"
  ],
  "recommendations": [
    "Verify Bloomberg figure against official SEC filing",
    "Request detailed opex breakdown from Tesla IR"
  ]
}
```

## Best Practices
- Use gpt-4o for critical research
- Limit to 3-5 sources per request
- Cache research results for 24 hours
- Include source citations for traceability

## Performance Metrics
- **Latency**: 8-15s (gpt-4o), 3-5s (gpt-4o-mini)
- **Accuracy**: 94% fact correctness (gpt-4o)
- **Cost**: $0.013 per request (gpt-4o)

## Version History
- **v1.0.0** (2024-11-24): Initial version
