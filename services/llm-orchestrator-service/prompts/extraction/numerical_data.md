# Numerical Data Extraction Template

## Use Case
Extract numerical claims, financial figures, statistics from article.

## Model Recommendations
- **Primary**: gpt-4o-mini
- **Alternative**: gpt-4o (complex financial documents)

## Token Budget
- **Input**: ~1,200 tokens
- **Output**: ~300 tokens
- **Total Cost**: $0.00024 (gpt-4o-mini)

## System Prompt
```
Extract numerical data. Output JSON:
{
  "financial_figures": [{"metric": str, "value": str, "unit": str, "period": str}],
  "statistics": [{"claim": str, "value": float, "unit": str}],
  "percentages": [{"claim": str, "value": float, "context": str}],
  "dates": [{"date": str, "event": str}]
}
```

## User Prompt Template
```
Article: "{article_title}"
{article_content}

Extract: financial figures, statistics, percentages, dates.
```

## Example Output
```json
{
  "financial_figures": [
    {"metric": "net_income", "value": "$4.2B", "unit": "USD", "period": "Q3 2024"},
    {"metric": "revenue", "value": "$25.18B", "unit": "USD", "period": "Q3 2024"}
  ],
  "statistics": [
    {"claim": "vehicle deliveries", "value": 462890, "unit": "units"}
  ],
  "percentages": [
    {"claim": "revenue growth YoY", "value": 7.8, "context": "Q3 2024"}
  ],
  "dates": [
    {"date": "2024-10-23", "event": "earnings announcement"}
  ]
}
```

## Performance Metrics
- **Latency**: 0.9-1.3s (gpt-4o-mini)
- **Cost**: $0.00024 per request

## Version History
- **v1.0.0** (2024-11-24): Initial version
