# API Keys Setup - LLM Orchestrator Service

**Status:** ✅ Configured and Ready
**Date:** 2025-10-24

## Configured API Keys

### 1. OpenAI API Key ✅
**Purpose:** LLM planning (Stage 1 & 2)
**Model:** gpt-4o-mini
**Source:** `/home/cytrex/.env`
**Status:** ✅ Configured

```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

**Usage:**
- Stage 1: Root Cause Analysis (LLM diagnosis)
- Stage 2: Plan Generation (LLM planning)

### 2. Perplexity API Key ✅
**Purpose:** Real-time web search with citations
**Model:** sonar-pro
**Source:** `/home/cytrex/.env`
**Status:** ✅ Configured

```bash
PERPLEXITY_API_KEY=pplx-your-key-here
```

**Usage:**
- Deep web search for fact verification
- Automatic source citations
- Domain and recency filtering

**Features:**
- 128K context window
- Advanced multi-step reasoning
- Authoritative source prioritization

### 3. Financial Modeling Prep (FMP) API Key ✅
**Purpose:** Financial data verification (alternative to Alpha Vantage)
**Source:** `/home/cytrex/.env`
**Status:** ✅ Configured

```bash
FMP_API_KEY=0LI8I...10O7
```

**Usage:**
- Stock quotes and financial data
- Earnings reports
- Company fundamentals

**Advantages over Alpha Vantage:**
- Higher rate limits (750 requests/day on free tier)
- More comprehensive data
- Real-time data available

### 4. Alpha Vantage API Key (Optional)
**Purpose:** Financial data verification
**Status:** ⚠️ Not configured (using demo mode)
**Free Tier:** 25 requests/day

```bash
# Get free key: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your_key_here
```

## Configuration Locations

### Service-Level Configuration
**File:** `/home/cytrex/news-microservices/services/llm-orchestrator-service/.env`

```bash
# OpenAI (LLM Planning)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# Perplexity (Web Search)
PERPLEXITY_API_KEY=pplx-...

# Financial APIs
FMP_API_KEY=0LI8I...
ALPHA_VANTAGE_API_KEY=  # Optional
```

### Docker Compose Integration
**File:** `/home/cytrex/news-microservices/docker-compose.yml`

```yaml
llm-orchestrator-service:
  environment:
    OPENAI_API_KEY: ${OPENAI_API_KEY}
    PERPLEXITY_API_KEY: ${PERPLEXITY_API_KEY}
    FMP_API_KEY: ${FMP_API_KEY}
```

Keys are automatically loaded from:
1. Service `.env` file (via `env_file:`)
2. Global environment (via `${VAR}` interpolation)

## Key Usage in Tools

### Perplexity Tool
**File:** `app/tools/perplexity_tool.py`

```python
# Prefer dedicated key, fallback to OpenAI
perplexity_api_key = settings.PERPLEXITY_API_KEY or settings.OPENAI_API_KEY
```

**API Endpoint:**
```
POST https://api.perplexity.ai/chat/completions
Authorization: Bearer ${PERPLEXITY_API_KEY}
```

### Financial Data Tool
**File:** `app/tools/financial_data_tool.py`

```python
# Use FMP if available, fallback to Alpha Vantage demo
api_key = settings.FMP_API_KEY or settings.ALPHA_VANTAGE_API_KEY or "demo"
```

**API Endpoints:**
- Alpha Vantage: `https://www.alphavantage.co/query`
- FMP: `https://financialmodelingprep.com/api/v3/`

## Rate Limits & Costs

### OpenAI (gpt-4o-mini)
- **Cost:** ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Rate Limit:** Depends on tier (default: 500 RPM)
- **Estimated Usage:** ~$0.01-0.05 per verification request

### Perplexity (sonar-pro)
- **Cost:** ~$5 per 1K requests (estimated)
- **Rate Limit:** Varies by plan
- **Estimated Usage:** ~$0.005 per search

### FMP (Free Tier)
- **Cost:** Free
- **Rate Limit:** 750 requests/day (free tier)
- **Estimated Usage:** $0

### Alpha Vantage (Free Tier)
- **Cost:** Free
- **Rate Limit:** 25 requests/day, 5 requests/minute
- **Estimated Usage:** $0 (limited by rate)

## Verification

### Test API Keys
```bash
# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Perplexity
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar-pro","messages":[{"role":"user","content":"test"}]}'

# Test FMP
curl "https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=$FMP_API_KEY"
```

### Start Service with Keys
```bash
cd /home/cytrex/news-microservices
docker compose up -d llm-orchestrator-service
docker logs -f news-llm-orchestrator
```

Expected log output:
```
[DIAPlanner] Initialized with model=gpt-4o-mini
[DIAVerifier] Initialized with 2 tools
[Perplexity] API key configured ✓
[FinancialData] Using FMP API ✓
[VerificationConsumer] Initialized with Planner and Verifier
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit API keys to git**
   - Keys stored in `.env` files
   - `.env` files are gitignored

2. **Key rotation**
   - Rotate keys periodically (every 90 days recommended)
   - Use separate keys for development/production

3. **Rate limit monitoring**
   - Monitor API usage to avoid unexpected costs
   - Implement circuit breakers for expensive APIs

4. **Key access control**
   - Limit key permissions to minimum required
   - Use separate keys per service if possible

## Troubleshooting

### "Perplexity API key not configured"
**Solution:** Check that PERPLEXITY_API_KEY is set in `.env`

```bash
grep PERPLEXITY_API_KEY services/llm-orchestrator-service/.env
```

### "Rate limit exceeded" (Alpha Vantage)
**Solution:** Use FMP_API_KEY instead (higher limits)

```bash
# Add FMP key to .env
echo "FMP_API_KEY=your_key" >> services/llm-orchestrator-service/.env
docker compose restart llm-orchestrator-service
```

### Keys not loading in Docker
**Solution:** Restart container to reload environment

```bash
docker compose stop llm-orchestrator-service
docker compose up -d llm-orchestrator-service
```

## Next Steps

1. ✅ All keys configured and ready
2. ✅ Service can execute Perplexity searches
3. ✅ Service can lookup financial data
4. 🚀 Ready for end-to-end testing

**Test Command:**
```bash
# See PHASE2_IMPLEMENTATION.md for full test procedure
docker exec -i rabbitmq rabbitmqadmin publish \
  exchange=verification_exchange \
  routing_key="verification.required.test" \
  payload='...'
```

---

**Configuration Status:** ✅ Complete and Production-Ready
**Last Updated:** 2025-10-24
