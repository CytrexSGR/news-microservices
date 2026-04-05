# Sentiment Analysis Template

## Use Case
Analyze article sentiment: positive, negative, neutral. Include confidence and reasoning.

## Model Recommendations
- **Primary**: gpt-4o-mini (fast, accurate)
- **Fallback**: gpt-3.5-turbo

## Token Budget
- **Input**: ~1,000 tokens
- **Output**: ~150 tokens
- **Total Cost**: $0.00018 (gpt-4o-mini)

## System Prompt
```
Analyze sentiment. Output JSON:
{
  "sentiment": "positive | negative | neutral",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation (max 100 chars)",
  "tone": "objective | subjective | biased"
}
```

## User Prompt Template
```
Article: "{article_title}"
{article_content}

Analyze sentiment, tone, bias.
```

## Example Output
```json
{
  "sentiment": "positive",
  "confidence": 0.85,
  "reasoning": "Focuses on record-breaking earnings, strong growth metrics",
  "tone": "objective"
}
```

## Performance Metrics
- **Latency**: 0.7-1.1s (gpt-4o-mini)
- **Cost**: $0.00018 per request

## Version History
- **v1.0.0** (2024-11-24): Initial version
