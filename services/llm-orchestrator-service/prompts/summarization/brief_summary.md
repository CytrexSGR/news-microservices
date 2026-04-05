# Brief Summary Template

## Use Case
Generate concise 2-3 sentence summary of article (50-100 words). Ideal for preview cards and notifications.

## Model Recommendations
- **Primary**: gpt-4o-mini (fast, cost-effective)
- **Alternative**: gpt-3.5-turbo (budget)

## Token Budget
- **Input**: ~1,000 tokens (article)
- **Output**: ~100 tokens (summary)
- **Total Cost**: $0.00016 (gpt-4o-mini)

## System Prompt

```
Summarize article in 2-3 sentences (50-100 words).
Focus on: who, what, when, where, why.
Output: plain text (no markdown, no formatting).
Be factual. No speculation or opinion.
```

## User Prompt Template

```
Article: "{article_title}"
Published: {article_published_at}

{article_content}

Task: 2-3 sentence summary (50-100 words).
```

## Variables
- `article_title`: Article headline
- `article_published_at`: Publication timestamp
- `article_content`: Full or truncated content (max 2000 chars)

## Example

**Input:**
```
Article: "Tesla Reports Record Q3 Earnings"
Content: "Tesla Inc. announced today record-breaking financial results for Q3 2024, reporting net profits of $4.2 billion..."
```

**Output:**
```
Tesla Inc. reported Q3 2024 net profits of $4.2 billion, exceeding analyst expectations. The earnings beat marks the company's strongest quarterly performance this year. Revenue increased 15% year-over-year driven by strong vehicle deliveries.
```

## Best Practices
- Truncate content to 2000 chars
- max_tokens=100 to control length
- Cache summaries for 24 hours

## Performance Metrics
- **Latency**: 0.6-1.0s (gpt-4o-mini)
- **Cost**: $0.00016 per request

## Version History
- **v1.0.0** (2024-11-24): Initial version
