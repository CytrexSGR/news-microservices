# Topic Classification Template

## Use Case
Classify article into primary and secondary topics. Multi-label classification.

## Model Recommendations
- **Primary**: gpt-4o-mini
- **Fallback**: gpt-3.5-turbo

## Token Budget
- **Input**: ~800 tokens
- **Output**: ~150 tokens
- **Total Cost**: $0.00015 (gpt-4o-mini)

## System Prompt
```
Classify article into topics. Output JSON:
{
  "primary_topic": str,
  "secondary_topics": List[str],
  "confidence": float,
  "keywords": List[str]
}

Topics: business, technology, finance, politics, science, health, sports, entertainment, other
```

## User Prompt Template
```
Article: "{article_title}"
{article_content}

Classify into primary/secondary topics.
```

## Example Output
```json
{
  "primary_topic": "finance",
  "secondary_topics": ["technology", "business"],
  "confidence": 0.92,
  "keywords": ["earnings", "revenue", "Tesla", "automotive"]
}
```

## Performance Metrics
- **Latency**: 0.6-0.9s (gpt-4o-mini)
- **Cost**: $0.00015 per request

## Version History
- **v1.0.0** (2024-11-24): Initial version
