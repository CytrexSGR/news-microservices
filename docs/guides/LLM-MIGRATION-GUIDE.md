# LLM Model Migration Guide

**Document Status**: Current
**Last Updated**: 2025-10-22
**Service**: content-analysis-service

## Overview

This guide documents the migration from OpenAI's gpt-4o-mini to gpt-4.1-nano and the preparation for multi-provider LLM support (including Google Gemini).

## Migration Summary

**Date**: 2025-10-22
**From**: gpt-4o-mini
**To**: gpt-4.1-nano (default)
**Prepared**: Google Gemini API integration

### Performance Improvements

Based on comprehensive testing (see `/home/cytrex/userdocs/openai-models-quality-analysis.md`):

| Metric | gpt-4o-mini | gpt-4.1-nano | Improvement |
|--------|-------------|--------------|-------------|
| **Speed** | 1.97s avg | 1.16s avg | **58% faster** |
| **Cost** | $0.60/1M output | $0.40/1M output | **35% cheaper** |
| **Quality** | Excellent | Identical | No degradation |

### Why gpt-4.1-nano?

1. **Faster**: 58% reduction in average response time (1.97s → 1.16s)
2. **Cheaper**: 35% cost reduction on output tokens ($0.60 → $0.40 per 1M tokens)
3. **Same Quality**: Identical accuracy in sentiment analysis, entity extraction, and summarization
4. **Better Consistency**: More deterministic outputs at temperature=0.0

## Implementation Changes

### 1. Cost Configuration

**File**: `services/content-analysis-service/app/core/config.py`

```python
@property
def model_costs(self) -> Dict[str, Dict[str, float]]:
    """Get model costs per 1M tokens (USD)."""
    return {
        # OpenAI Models
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},

        # OpenAI GPT-4.1 Models (new, faster and cheaper)
        "gpt-4.1-mini": {"input": 0.15, "output": 0.60},
        "gpt-4.1-nano": {"input": 0.10, "output": 0.40},  # 35% cheaper

        # ... other models
    }
```

**File**: `services/content-analysis-service/app/llm/openai_provider.py`

```python
MODEL_COSTS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    # ... other models
}
```

### 2. Environment Configuration

**File**: `services/content-analysis-service/.env`

**Changed**:
```bash
# Before
OPENAI_MODEL=gpt-4o-mini

# After
OPENAI_MODEL=gpt-4.1-nano
```

### 3. Google Gemini Preparation

**Added to requirements.txt**:
```python
# Google Gemini (optional, prepared for future use)
google-generativeai==0.8.3
```

**Prepared in .env** (commented out, ready for activation):
```bash
# Google Gemini Configuration (FUTURE - For custom Gemini Flash model)
# GEMINI_API_KEY=your-gemini-api-key-here
# GEMINI_MODEL=gemini-flash-custom
# GEMINI_MAX_TOKENS=8000
# GEMINI_TEMPERATURE=0.1
```

## Architecture: Multi-Provider Support

The content-analysis-service already has complete multi-provider architecture:

### Provider Registry

**File**: `services/content-analysis-service/app/llm/factory.py`

```python
_providers: Dict[str, type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
    "gemini": GeminiProvider,  # ✅ Already registered!
}
```

### Per-Analysis-Type Provider Selection

You can use different providers for different analysis types:

**File**: `services/content-analysis-service/.env`

```bash
# Model Selection Strategy - ALL USE GPT-4.1-nano by default
DEFAULT_LLM_PROVIDER=openai
SENTIMENT_MODEL_PROVIDER=openai
ENTITIES_MODEL_PROVIDER=openai
SUMMARY_MODEL_PROVIDER=openai
FACTS_MODEL_PROVIDER=openai
TOPICS_MODEL_PROVIDER=openai
KEYWORDS_MODEL_PROVIDER=openai

# Example: Use Gemini for specific analysis (future)
# SUMMARY_MODEL_PROVIDER=gemini
# GEMINI_MODEL=gemini-1.5-flash
```

## Deployment Steps

### 1. Stop Service
```bash
docker compose stop content-analysis-service
```

### 2. Update Configuration
Edit `services/content-analysis-service/.env`:
```bash
OPENAI_MODEL=gpt-4.1-nano
```

### 3. Rebuild Docker Image (if dependencies changed)
```bash
docker compose build content-analysis-service
```

### 4. Start Service
```bash
docker compose up -d content-analysis-service
```

**Important**: Use `stop` + `up`, NOT `restart`!
→ `restart` does NOT reload .env files
→ `stop` + `up` ensures clean environment reload

### 5. Verify Deployment

**Health Check**:
```bash
curl http://localhost:8102/api/v1/health | jq '.'
```

Expected:
```json
{
  "status": "healthy",
  "checks": {
    "llm_providers": {
      "openai": "configured",
      "gemini": "not configured"
    }
  }
}
```

**Configuration Check**:
```bash
docker exec news-content-analysis-service python -c "from app.core.config import settings; print('Model:', settings.OPENAI_MODEL, 'Provider:', settings.DEFAULT_LLM_PROVIDER)"
```

Expected:
```
Model: gpt-4.1-nano Provider: openai
```

**API Test**:
```bash
# Get an article ID
ARTICLE_ID=$(docker exec postgres psql -U news_user -d news_mcp -t -c "SELECT id FROM feed_items WHERE content IS NOT NULL LIMIT 1;" | xargs)

# Test sentiment analysis
curl -X POST http://localhost:8102/api/v1/internal/analyze/standard-sentiment \
  -H "X-Service-Key: ZQnaPRqcelc3IJ-xKXtqrnYxGXLBCOBhDzQhNsaBxZg" \
  -H "Content-Type: application/json" \
  -d "{\"article_id\": \"$ARTICLE_ID\"}" | jq '.'
```

Expected:
```json
{
  "status": "success",
  "analysis_type": "standard_sentiment",
  "overall_sentiment": "neutral",
  "confidence": 0.75
}
```

**Log Verification**:
```bash
docker compose logs content-analysis-service --tail 20 | grep -E "(gpt-4|sentiment|analysis)"
```

Should show:
- Sentiment analysis executed
- OpenAI API call successful
- No errors

## Rollback Procedure

If issues occur, rollback is simple:

```bash
# 1. Stop service
docker compose stop content-analysis-service

# 2. Revert .env change
# Change OPENAI_MODEL=gpt-4.1-nano back to gpt-4o-mini

# 3. Restart
docker compose up -d content-analysis-service

# 4. Verify
curl http://localhost:8102/api/v1/health
```

## Activating Google Gemini (Future)

When ready to use Gemini:

### 1. Get API Key
Visit: https://makersuite.google.com/app/apikey

### 2. Configure Environment
Edit `.env`:
```bash
# Uncomment and add your API key
GEMINI_API_KEY=your-actual-api-key-here
GEMINI_MODEL=gemini-1.5-flash
```

### 3. Select Gemini for Specific Analyses
```bash
# Example: Use Gemini for summaries
SUMMARY_MODEL_PROVIDER=gemini

# Or use Gemini as default for everything
DEFAULT_LLM_PROVIDER=gemini
```

### 4. Restart Service
```bash
docker compose stop content-analysis-service
docker compose up -d content-analysis-service
```

### 5. Verify Gemini Status
```bash
curl http://localhost:8102/api/v1/health | jq '.checks.llm_providers.gemini'
```

Should return: `"configured"`

## Cost Monitoring

### Check Daily Costs
```bash
curl -s http://localhost:8102/api/v1/internal/status/operations \
  -H "X-Service-Key: ZQnaPRqcelc3IJ-xKXtqrnYxGXLBCOBhDzQhNsaBxZg" \
  | jq '.cost_tracking'
```

### Expected Savings

With same analysis volume:
- **Before** (gpt-4o-mini): ~$100/month
- **After** (gpt-4.1-nano): ~$65/month
- **Savings**: $35/month (35% reduction)

## Troubleshooting

### Issue: Service won't start after update

**Solution**:
```bash
# Check logs
docker compose logs content-analysis-service --tail 50

# Common causes:
# 1. Typo in .env file → Fix typo
# 2. Old image cached → Rebuild: docker compose build content-analysis-service
# 3. Port conflict → Check: lsof -ti:8102 | xargs kill -9
```

### Issue: "Model not found" error

**Solution**:
```bash
# Verify model name in .env
grep OPENAI_MODEL services/content-analysis-service/.env

# Should be exactly: OPENAI_MODEL=gpt-4.1-nano
# NOT: gpt-4-1-nano, gpt-41-nano, etc.
```

### Issue: Gemini shows "not configured" but API key is set

**Solution**:
```bash
# 1. Verify API key in .env (no quotes, no spaces)
grep GEMINI_API_KEY services/content-analysis-service/.env

# 2. Ensure line is uncommented (no # at start)

# 3. Restart with stop+up (not restart!)
docker compose stop content-analysis-service
docker compose up -d content-analysis-service
```

## Testing Recommendations

### Smoke Tests
After migration, run these tests:

1. **Health Check**: `curl http://localhost:8102/api/v1/health`
2. **Config Check**: Verify model name in logs
3. **API Test**: Run sentiment analysis on test article
4. **Cost Tracking**: Check cost calculations are correct

### Consistency Tests
For production deployments, run consistency test:

```bash
cd /home/cytrex/userdocs
python test_consistency.py
```

This runs the same analysis 5x and checks:
- Label consistency (should be 100% at temperature=0.0)
- Score variance (should be < 0.05)

## References

- **Quality Analysis**: `/home/cytrex/userdocs/openai-models-quality-analysis.md`
- **Service Documentation**: `/home/cytrex/news-microservices/docs/services/content-analysis-service.md`
- **API Documentation**: `/home/cytrex/news-microservices/docs/api/content-analysis-api.md`
- **LLM Configuration**: `/home/cytrex/news-microservices/docs/guides/LLM_CONFIGURATION.md`

## Support

For questions or issues:
1. Check service logs: `docker compose logs content-analysis-service`
2. Verify configuration: `docker exec news-content-analysis-service env | grep -E "(OPENAI|GEMINI)"`
3. Consult documentation in `/home/cytrex/news-microservices/docs/`

---

**Migration Status**: ✅ Complete (Phase 1 & 2)
**Production Ready**: Yes
**Rollback Risk**: Low (simple .env change)
