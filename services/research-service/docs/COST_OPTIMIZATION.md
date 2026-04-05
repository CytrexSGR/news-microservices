# Cost Optimization Guide

## Overview

The Research Service implements a sophisticated 3-tier cost optimization system that automatically balances research quality with API costs. The system intelligently selects the best tier based on query complexity, budget constraints, and cache availability.

## Cost Tiers

### Tier 1: Quick (Most Cost-Effective)

- **Model**: `sonar`
- **Cost Multiplier**: 1.0x
- **Cache Priority**: 90% (strongly prefers cache)
- **Max Tokens**: 2,000
- **Temperature**: 0.3 (focused)
- **Recency Filter**: Last 24 hours
- **Best For**:
  - Simple fact-checking
  - Quick lookups
  - Straightforward questions
  - Frequently asked queries

**Example Query**: "What is the capital of France?"

### Tier 2: Standard (Balanced)

- **Model**: `sonar`
- **Cost Multiplier**: 1.5x
- **Cache Priority**: 60% (balanced cache usage)
- **Max Tokens**: 4,000
- **Temperature**: 0.5 (balanced)
- **Recency Filter**: Last 7 days
- **Best For**:
  - General research
  - Article analysis
  - Typical queries
  - Moderate complexity topics

**Example Query**: "Analyze the main arguments in this article about climate change"

### Tier 3: Deep (Premium Quality)

- **Model**: `sonar-pro`
- **Cost Multiplier**: 3.0x
- **Cache Priority**: 30% (prefers fresh results)
- **Max Tokens**: 8,000
- **Temperature**: 0.7 (creative)
- **Recency Filter**: Last 30 days
- **Best For**:
  - Complex analysis
  - Comprehensive reports
  - Multi-topic research
  - Expert-level insights

**Example Query**: "Provide a comprehensive analysis of AI ethics including regulatory frameworks, expert opinions, emerging trends, and comparative approaches across different regions"

## Automatic Optimization Features

### 1. Query Complexity Analysis

The system automatically estimates query complexity based on:

- Query length (longer = more complex)
- Number of questions (multiple questions = higher complexity)
- Technical keywords (analysis, synthesis, comprehensive, etc.)
- Conditional clauses (if/when/unless)

**Complexity Score**: 0.0 (simple) to 1.0 (very complex)

### 2. Budget-Aware Tier Selection

The optimizer monitors your budget usage and automatically:

- Downgrade tiers when approaching budget limits
- Warn at 80% of daily/monthly budget
- Block requests that exceed budget
- Recommend cost-saving strategies

### 3. Intelligent Cache Usage

Cache decisions consider:

- Tier cache priority (Quick tier strongly prefers cache)
- Cache age/freshness
- Budget pressure (tight budget = more cache usage)
- Query complexity

### 4. Cost Prediction

Before executing any query, the system:

- Estimates token usage
- Calculates predicted cost
- Checks budget availability
- Suggests optimal tier

## Usage Examples

### Example 1: Automatic Optimization (Recommended)

```python
from app.services.research import research_service

# System automatically selects optimal tier
task = await research_service.create_research_task(
    db=db,
    user_id=user_id,
    query="What are the latest developments in quantum computing?",
    optimize_cost=True  # Default: enabled
)

# Cost optimizer will:
# 1. Analyze query complexity (~0.4)
# 2. Check cache (if available)
# 3. Check budget status
# 4. Select "standard" tier
# 5. Execute with optimal settings
```

### Example 2: Explicit Tier Selection

```python
# Force specific tier (optimizer still checks budget)
task = await research_service.create_research_task(
    db=db,
    user_id=user_id,
    query="Simple question?",
    depth="quick",  # Explicit tier selection
    optimize_cost=True
)

# Optimizer may still downgrade if:
# - Budget is tight
# - Cache is available
# - Query is very simple
```

### Example 3: Disable Optimization

```python
# Disable cost optimization completely
task = await research_service.create_research_task(
    db=db,
    user_id=user_id,
    query="Query",
    depth="deep",
    optimize_cost=False  # Disable optimization
)

# System will:
# - Use specified tier exactly
# - Still check budget limits (if enabled)
# - Skip complexity analysis
```

### Example 4: Cost Prediction

```python
from app.services.research import research_service

# Predict cost before execution
prediction = research_service.predict_query_cost(
    query="Your query here",
    depth="standard"
)

print(f"Query complexity: {prediction['query_complexity']}")
print(f"Predicted cost: ${prediction['predicted_cost']:.4f}")
print(f"Cached cost: ${prediction['cached_cost']:.4f}")
print(f"Potential savings: ${prediction['potential_savings']:.4f}")
```

### Example 5: Usage Analytics

```python
# Get detailed cost optimization analytics
analytics = await research_service.get_cost_optimization_analytics(
    db=db,
    user_id=user_id,
    days=30
)

print(f"Total tasks: {analytics['total_tasks']}")
print(f"Cache hit rate: {analytics['cache_hit_rate']}%")
print(f"Estimated savings: ${analytics['estimated_savings']:.2f}")
print(f"Recommendations:")
for rec in analytics['recommendations']:
    print(f"  - {rec}")
```

### Example 6: Tier Comparison

```python
# Compare all tiers for user decision-making
comparison = research_service.get_tier_comparison()

for tier_name, tier_info in comparison.items():
    print(f"\n{tier_info['name']} Tier:")
    print(f"  Model: {tier_info['model']}")
    print(f"  Cost multiplier: {tier_info['relative_cost']}x")
    print(f"  Max tokens: {tier_info['max_tokens']}")
    print(f"  Best for: {tier_info['best_for']}")
```

## API Integration

### Research Endpoint with Optimization

```bash
POST /api/v1/research/tasks

{
  "query": "Analyze recent AI developments",
  "depth": "standard",  # Optional: quick, standard, deep
  "optimize_cost": true  # Optional: default true
}
```

**Response**:

```json
{
  "id": 123,
  "status": "completed",
  "query": "Analyze recent AI developments",
  "model_name": "sonar",
  "depth": "standard",
  "result": {
    "content": "...",
    "citations": [...],
    "sources": [...]
  },
  "tokens_used": 2500,
  "cost": 0.0125,
  "optimization_applied": true,
  "original_tier": "deep",
  "optimized_tier": "standard",
  "cache_used": false,
  "created_at": "2025-10-11T10:30:00Z",
  "completed_at": "2025-10-11T10:30:15Z"
}
```

### Cost Prediction Endpoint

```bash
POST /api/v1/research/predict-cost

{
  "query": "Your query here",
  "depth": "standard"
}
```

**Response**:

```json
{
  "query_length": 245,
  "query_complexity": 0.42,
  "tier": "standard",
  "model": "sonar",
  "predicted_cost": 0.0180,
  "cached_cost": 0.0000,
  "potential_savings": 0.0180,
  "max_tokens": 4000,
  "description": "Balanced cost and quality for typical research"
}
```

### Analytics Endpoint

```bash
GET /api/v1/research/analytics/cost-optimization?days=30
```

**Response**:

```json
{
  "period_days": 30,
  "total_tasks": 150,
  "cached_tasks": 45,
  "cache_hit_rate": 30.0,
  "estimated_savings": 2.35,
  "tier_breakdown": {
    "quick": {
      "count": 50,
      "total_cost": 0.25,
      "avg_cost": 0.005,
      "percentage": 33.33
    },
    "standard": {
      "count": 80,
      "total_cost": 1.20,
      "avg_cost": 0.015,
      "percentage": 53.33
    },
    "deep": {
      "count": 20,
      "total_cost": 1.00,
      "avg_cost": 0.050,
      "percentage": 13.33
    }
  },
  "recommendations": [
    "Excellent cache usage! You're saving significantly on API costs.",
    "Consider using Quick tier for simple queries to optimize costs."
  ]
}
```

## Configuration

### Environment Variables

```bash
# Enable cost tracking
ENABLE_COST_TRACKING=true

# Enable cost optimization
ENABLE_COST_OPTIMIZATION=true

# Budget limits
MAX_DAILY_COST=50.0
MAX_MONTHLY_COST=1000.0
MAX_COST_PER_REQUEST=1.0

# Budget alerts
COST_ALERT_THRESHOLD=0.8  # Alert at 80% of limit

# Default tier
DEFAULT_COST_TIER=standard

# Auto-downgrade on budget limit
AUTO_DOWNGRADE_ON_BUDGET_LIMIT=true

# Cache preference (0.0-1.0, higher = more cache usage)
CACHE_PREFERENCE_THRESHOLD=0.6
```

### Model Pricing

```python
PERPLEXITY_MODELS = {
    "sonar": {
        "cost_per_1k_tokens": 0.005,  # $0.005 per 1K tokens
        "max_tokens": 4000
    },
    "sonar-pro": {
        "cost_per_1k_tokens": 0.015,  # $0.015 per 1K tokens
        "max_tokens": 8000
    },
    "sonar-reasoning-pro": {
        "cost_per_1k_tokens": 0.025,  # $0.025 per 1K tokens
        "max_tokens": 16000
    }
}
```

## Cost Optimization Best Practices

### 1. Use Cache Effectively

- Enable caching for repeated queries
- Set appropriate TTL (default: 7 days)
- Review cache hit rate regularly
- Target: >30% cache hit rate

### 2. Choose the Right Tier

- **Quick**: Simple questions, fact-checking
- **Standard**: General research, article analysis
- **Deep**: Complex analysis, comprehensive reports

### 3. Monitor Budget

- Set realistic daily/monthly limits
- Review analytics weekly
- Adjust limits based on usage patterns
- Enable budget alerts

### 4. Optimize Queries

- Be specific and concise
- Avoid redundant questions
- Use templates for common queries
- Batch related questions when possible

### 5. Review Analytics

```python
# Weekly review
analytics = await research_service.get_cost_optimization_analytics(
    db=db,
    user_id=user_id,
    days=7
)

# Check metrics
print(f"Cache hit rate: {analytics['cache_hit_rate']}%")
print(f"Total cost: ${sum(t['total_cost'] for t in analytics['tier_breakdown'].values()):.2f}")

# Review recommendations
for rec in analytics['recommendations']:
    print(f"- {rec}")
```

## Cost Savings Examples

### Example 1: Cache Usage

**Without Cache**:
- 100 queries/day
- Average: $0.015 per query
- Daily cost: $1.50
- Monthly cost: $45.00

**With 40% Cache Hit Rate**:
- 60 API calls/day
- 40 cached (free)
- Daily cost: $0.90
- Monthly cost: $27.00
- **Savings**: $18.00/month (40%)

### Example 2: Smart Tier Selection

**All Deep Tier**:
- 50 queries/day
- Average: $0.045 per query
- Daily cost: $2.25
- Monthly cost: $67.50

**Optimized Mix (20% Quick, 60% Standard, 20% Deep)**:
- Quick: 10 × $0.005 = $0.05
- Standard: 30 × $0.015 = $0.45
- Deep: 10 × $0.045 = $0.45
- Daily cost: $0.95
- Monthly cost: $28.50
- **Savings**: $39.00/month (58%)

### Example 3: Combined Optimization

**Without Optimization**:
- 100 queries/day
- All deep tier
- No cache
- Monthly cost: $135.00

**With Full Optimization**:
- 100 queries/day
- 40% cache hits (free)
- 60 API calls with smart tier selection
- Monthly cost: $22.80
- **Savings**: $112.20/month (83%)

## Monitoring and Alerts

### Budget Alerts

The system automatically sends alerts when:

- Daily budget reaches 80% (warning)
- Daily budget reaches 100% (blocked)
- Monthly budget reaches 80% (warning)
- Monthly budget reaches 100% (blocked)

### Cost Tracking

View real-time cost tracking:

```bash
GET /api/v1/research/usage-stats?days=30
```

Monitor key metrics:

- Total requests
- Total cost
- Average cost per request
- Cost by model
- Cost by tier
- Cache hit rate

## Troubleshooting

### Issue: Budget Exceeded

**Symptoms**: Requests blocked with "budget exceeded" error

**Solutions**:
1. Review usage analytics to identify high-cost patterns
2. Increase cache usage (adjust TTL, reuse queries)
3. Use lower tiers for simple queries
4. Increase budget limits if justified
5. Enable automatic tier downgrade

### Issue: Low Cache Hit Rate

**Symptoms**: Cache hit rate below 20%

**Solutions**:
1. Review query patterns for duplication
2. Use research templates for common queries
3. Standardize query formatting
4. Increase cache TTL
5. Enable cache recommendations

### Issue: Unexpected Costs

**Symptoms**: Costs higher than predicted

**Solutions**:
1. Review tier distribution in analytics
2. Check for runaway queries (very long)
3. Verify model pricing configuration
4. Review complex query patterns
5. Enable cost prediction before execution

## Support

For questions or issues with cost optimization:

1. Review this documentation
2. Check usage analytics for insights
3. Review cost optimization recommendations
4. Contact support with specific query patterns
5. Share analytics data for optimization advice

---

**Last Updated**: 2025-10-11
**Version**: 1.0.0
