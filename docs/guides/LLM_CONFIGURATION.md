# LLM Configuration Guide

**Document Status**: Current
**Last Updated**: 2025-10-22
**Service**: content-analysis-service

## Overview

The content-analysis-service supports multiple LLM providers with flexible per-analysis-type configuration. This guide covers configuration, costs, and best practices.

## Supported Providers

### 1. OpenAI (Default)

**Status**: ✅ Production Ready
**Current Model**: gpt-4.1-nano
**Use Case**: All analysis types (default)

**Configuration**:
```bash
# .env
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4.1-nano
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4000
```

**Available Models**:
| Model | Speed | Cost ($/1M output) | Quality | Recommended Use |
|-------|-------|-------------------|---------|-----------------|
| gpt-4.1-nano | Fastest | $0.40 | Excellent | **Default** - All analyses |
| gpt-4.1-mini | Very Fast | $0.60 | Excellent | Alternative option |
| gpt-4o-mini | Fast | $0.60 | Excellent | Legacy (replaced) |
| gpt-4o | Slow | $10.00 | Best | Complex reasoning only |

**Why gpt-4.1-nano?**
- 58% faster than gpt-4o-mini
- 35% cheaper than gpt-4o-mini
- Identical quality
- Better consistency at temperature=0.0

### 2. Google Gemini

**Status**: ✅ Prepared (not activated)
**Current Model**: None
**Use Case**: Future - Custom Gemini Flash model

**Configuration** (prepared):
```bash
# .env (currently commented out)
# GEMINI_API_KEY=your-api-key-here
# GEMINI_MODEL=gemini-1.5-flash
# GEMINI_MAX_TOKENS=8000
# GEMINI_TEMPERATURE=0.1
```

**Available Models**:
| Model | Speed | Cost ($/1M output) | Quality | Use Case |
|-------|-------|-------------------|---------|----------|
| gemini-1.5-flash | Very Fast | $0.30 | Very Good | Fast analyses |
| gemini-1.5-pro | Medium | $5.00 | Excellent | Complex reasoning |
| gemini-flash-custom | Custom | $0.20 | Custom | Your fine-tuned model |

**Activation**:
1. Get API key: https://makersuite.google.com/app/apikey
2. Uncomment lines in `.env`
3. Set provider: `DEFAULT_LLM_PROVIDER=gemini`
4. Restart: `docker compose stop content-analysis-service && docker compose up -d content-analysis-service`

### 3. Anthropic Claude

**Status**: ✅ Available (not recommended for cost reasons)
**Current Model**: claude-3-5-sonnet-20241022
**Use Case**: Not used (too expensive)

**Configuration**:
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4000
```

**Available Models**:
| Model | Speed | Cost ($/1M output) | Quality | Notes |
|-------|-------|-------------------|---------|-------|
| claude-3-haiku | Fast | $1.25 | Good | 3x more expensive than gpt-4.1-nano |
| claude-3-5-sonnet | Medium | $15.00 | Excellent | 37x more expensive! |
| claude-3-opus | Slow | $75.00 | Best | 187x more expensive! |

**Not Recommended**: All Claude models are significantly more expensive than OpenAI for equivalent quality.

### 4. Ollama (Local)

**Status**: ⚠️ Available (not production-ready)
**Current Model**: llama3.2
**Use Case**: Development/testing only

**Configuration**:
```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**Notes**:
- **Free**: No API costs
- **Slow**: Much slower than cloud models
- **Quality**: Lower quality than gpt-4.1-nano
- **Use Case**: Local development without API costs only

## Provider Selection

### Default Provider

**File**: `.env`
```bash
# Sets default for all analysis types
DEFAULT_LLM_PROVIDER=openai
```

### Per-Analysis-Type Override

You can use different providers for specific analysis types:

**File**: `.env`
```bash
# All use OpenAI gpt-4.1-nano by default
SENTIMENT_MODEL_PROVIDER=openai
ENTITIES_MODEL_PROVIDER=openai
SUMMARY_MODEL_PROVIDER=openai
FACTS_MODEL_PROVIDER=openai
TOPICS_MODEL_PROVIDER=openai
KEYWORDS_MODEL_PROVIDER=openai

# Example: Use Gemini for summaries (when activated)
# SUMMARY_MODEL_PROVIDER=gemini
```

**Use Cases for Mixed Providers**:
1. **Cost Optimization**: Use cheaper provider for simple tasks
2. **Speed Optimization**: Use faster provider for real-time analyses
3. **Quality Optimization**: Use best provider for critical analyses
4. **A/B Testing**: Compare providers side-by-side

## Cost Management

### Current Costs (gpt-4.1-nano)

**Per Analysis**:
- Sentiment: ~500 tokens = $0.0002
- Entities: ~1000 tokens = $0.0004
- Summary: ~800 tokens = $0.0003
- Topics: ~600 tokens = $0.00024
- Facts: ~700 tokens = $0.00028

**Total per article** (all 8 analyses): ~$0.0025

**Monthly Estimate** (10,000 articles/month):
- gpt-4.1-nano: ~$25/month
- gpt-4o-mini (old): ~$40/month
- **Savings**: $15/month (37.5%)

### Cost Limits

**File**: `.env`
```bash
# Cost Management
ENABLE_COST_TRACKING=true
MAX_COST_PER_REQUEST=1.0      # Max $1 per article
MAX_DAILY_COST=100.0          # Max $100 per day
```

**Monitoring**:
```bash
# Check daily costs
curl -s http://localhost:8102/api/v1/internal/status/operations \
  -H "X-Service-Key: ZQnaPRqcelc3IJ-xKXtqrnYxGXLBCOBhDzQhNsaBxZg" \
  | jq '.cost_tracking'
```

## Cache Configuration

Caching reduces costs by avoiding duplicate API calls:

**File**: `.env`
```bash
# Cache TTL Settings (in seconds)
CACHE_ENABLED=true
CACHE_SENTIMENT_TTL=2592000    # 30 days
CACHE_ENTITIES_TTL=1209600     # 14 days
CACHE_TOPICS_TTL=1209600       # 14 days
CACHE_SUMMARIES_TTL=604800     # 7 days
CACHE_FACTS_TTL=604800         # 7 days
```

**Cache Hit Rate Impact**:
- 50% hit rate = 50% cost savings
- 80% hit rate = 80% cost savings
- 90% hit rate = 90% cost savings

**Monitor Cache Performance**:
```bash
curl -s http://localhost:8102/api/v1/internal/status/operations \
  -H "X-Service-Key: ZQnaPRqcelc3IJ-xKXtqrnYxGXLBCOBhDzQhNsaBxZg" \
  | jq '.cache_stats'
```

## Rate Limiting

Protect against runaway costs:

**File**: `.env`
```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
```

**Per Provider Limits**:
- **OpenAI**: 10,000 requests/min (API tier dependent)
- **Gemini**: 1,500 requests/min (free tier), 360,000/min (paid)
- **Anthropic**: 5 requests/sec (tier dependent)
- **Ollama**: No limit (local)

## Best Practices

### 1. Temperature Settings

**For Deterministic Outputs** (preferred):
```bash
OPENAI_TEMPERATURE=0.0
```
- Same input = same output
- Best for production consistency
- Lower variance

**For Creative Outputs**:
```bash
OPENAI_TEMPERATURE=0.7
```
- More variety in responses
- Use only if creative diversity needed

### 2. Token Management

**Max Tokens Settings**:
```bash
OPENAI_MAX_TOKENS=4000  # Default
```

**Optimization**:
- Set lower for simple tasks (500-1000)
- Set higher for complex reasoning (4000-8000)
- Monitor actual usage: most responses use < 1000 tokens

### 3. Provider Failover

Currently not implemented, but architecture supports it:

**Future Implementation**:
```python
# Pseudo-code
try:
    result = await openai_provider.analyze(request)
except OpenAIError:
    logger.warning("OpenAI failed, falling back to Gemini")
    result = await gemini_provider.analyze(request)
```

### 4. Multi-Model Testing

**A/B Testing Pattern**:
```bash
# Production: gpt-4.1-nano for all
DEFAULT_LLM_PROVIDER=openai

# Test: Gemini for 10% of summaries
# Implement in code with random selection
```

## Troubleshooting

### Issue: High Costs

**Solutions**:
1. Enable caching: `CACHE_ENABLED=true`
2. Increase cache TTL: `CACHE_SENTIMENT_TTL=2592000`
3. Use cheaper model: `OPENAI_MODEL=gpt-4.1-nano`
4. Lower max tokens: `OPENAI_MAX_TOKENS=1000`
5. Check for duplicate analyses in logs

### Issue: Slow Performance

**Solutions**:
1. Use fastest model: `OPENAI_MODEL=gpt-4.1-nano`
2. Lower temperature: `OPENAI_TEMPERATURE=0.0`
3. Reduce max tokens: `OPENAI_MAX_TOKENS=2000`
4. Enable caching: `CACHE_ENABLED=true`
5. Check rate limits

### Issue: Provider Unavailable

**Check Provider Status**:
```bash
curl http://localhost:8102/api/v1/health | jq '.checks.llm_providers'
```

**Expected**:
```json
{
  "openai": "configured",
  "anthropic": "configured",
  "ollama": "configured",
  "gemini": "not configured"
}
```

**Solutions**:
1. Verify API key: `grep OPENAI_API_KEY .env`
2. Check API key validity at provider website
3. Verify network connectivity: `curl https://api.openai.com`
4. Check service logs: `docker compose logs content-analysis-service`

### Issue: Inconsistent Results

**Causes**:
1. Temperature too high → Lower to 0.0
2. Model changed mid-analysis → Check model configuration
3. Cache disabled → Enable caching for consistency
4. Provider API issues → Check provider status page

**Solutions**:
```bash
# Set temperature to 0.0 for deterministic outputs
OPENAI_TEMPERATURE=0.0

# Enable caching
CACHE_ENABLED=true

# Run consistency test
python /home/cytrex/userdocs/test_consistency.py
```

## Migration History

### 2025-10-22: Migration to gpt-4.1-nano

**From**: gpt-4o-mini
**To**: gpt-4.1-nano
**Reason**: 58% faster, 35% cheaper, identical quality

**Changes**:
- Updated `OPENAI_MODEL=gpt-4.1-nano` in `.env`
- Added cost definitions to `config.py` and `openai_provider.py`
- Rebuilt Docker image
- Verified with smoke tests

**Results**:
- ✅ Service healthy
- ✅ API calls successful
- ✅ Cost tracking accurate
- ✅ Performance improved (1.97s → 1.16s avg)

See: `/home/cytrex/news-microservices/docs/guides/LLM-MIGRATION-GUIDE.md`

## Future Enhancements

### 1. Auto-Provider Selection

Automatically select best provider based on:
- Analysis type complexity
- Cost constraints
- Performance requirements
- Provider availability

### 2. Provider Health Monitoring

Continuous monitoring of:
- API response times
- Error rates
- Cost per request
- Quality metrics

Auto-switch providers if degradation detected.

### 3. Multi-Provider Ensembling

Use multiple providers and ensemble results:
- Improved accuracy
- Reduced bias
- Better error detection
- Higher confidence scores

### 4. Fine-Tuned Models

Train custom models for:
- Domain-specific analysis (news, finance, legal)
- Language-specific models
- Brand voice matching
- Cost reduction (smaller models)

## References

- **Migration Guide**: `docs/guides/LLM-MIGRATION-GUIDE.md`
- **Service Documentation**: `docs/services/content-analysis-service.md`
- **API Documentation**: `docs/api/content-analysis-api.md`
- **Quality Analysis**: `/home/cytrex/userdocs/openai-models-quality-analysis.md`

## Provider Resources

- **OpenAI**: https://platform.openai.com/docs/models
- **Google Gemini**: https://ai.google.dev/docs
- **Anthropic**: https://docs.anthropic.com/claude/docs
- **Ollama**: https://ollama.ai/library

---

**Configuration Status**: ✅ Optimized
**Default Provider**: OpenAI (gpt-4.1-nano)
**Prepared Providers**: Gemini, Anthropic, Ollama
**Production Ready**: Yes
