# API Documentation Index

**Quick Reference:** [CLAUDE.md](../../CLAUDE.md) | [Backend Guide](../../CLAUDE.backend.md)

---

## 📖 About This Directory

This directory contains **API contracts and specifications** for all microservices.

Each service exposes Swagger/OpenAPI documentation at `http://localhost:<port>/docs`.

---

## 🎯 Service API Documentation

### Trading & Prediction

- **indicators-api** (8116): [indicators-api.md](indicators-api.md) ⭐ NEW
  - Technical indicators (RSI, MACD, EMA, ADX, ATR, Bollinger Bands, etc.)
  - Multi-timeframe support (15m, 1h, 4h, 1d)
  - Fair Value Gaps, Liquidity Sweeps, Volume Profile
  - Implementation Guide: [indicators-implementation-guide.md](indicators-implementation-guide.md)
  - Swagger: http://localhost:8116/docs

### Core Services

- **auth-service** (8100): [auth-service-api.md](auth-service-api.md)
  - JWT authentication, RBAC, API keys
  - Swagger: http://localhost:8100/docs

- **feed-service** (8101): [feed-service-api.md](feed-service-api.md)
  - Feed management, ingestion, configuration
  - Swagger: http://localhost:8101/docs

- **content-analysis-v3** (8114)
  - Multi-LLM analysis pipeline
  - Swagger: http://localhost:8114/docs

### Intelligence & Analysis

- **llm-orchestrator** (8109)
  - DIA (Dynamic Intelligence Augmentation)
  - Swagger: http://localhost:8109/docs

- **knowledge-graph-service** (8111)
  - Entity relationships, Neo4j queries
  - Swagger: http://localhost:8111/docs

- **entity-canonicalization** (8112)
  - Entity deduplication API
  - Swagger: http://localhost:8112/docs

### Search & Analytics

- **search-service** (8106): [search-service-api.md](search-service-api.md)
  - Full-text search, saved queries
  - Swagger: http://localhost:8106/docs

- **analytics-service** (8107)
  - Metrics, trends, analytics
  - Swagger: http://localhost:8107/docs

### Supporting Services

- **research-service** (8103)
  - Perplexity AI integration
  - Swagger: http://localhost:8103/docs

- **notification-service** (8105)
  - Email/webhook delivery
  - Swagger: http://localhost:8105/docs

- **osint-service** (8104)
  - Investigation templates
  - Swagger: http://localhost:8104/docs

---

## 🔍 API Testing

### Quick Test Commands

```bash
# Health check all services
./scripts/health_check.sh

# Test specific endpoint
curl http://localhost:8100/api/v1/auth/health

# Authenticated request (JWT)
TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8101/api/v1/feeds
```

### Postman Collection

Import Swagger/OpenAPI specs into Postman:
```
http://localhost:<port>/openapi.json
```

---

## 📚 Related Documentation

- **Service Documentation:** [../services/](../services/) - Service-specific guides
- **Architecture:** [../../ARCHITECTURE.md](../../ARCHITECTURE.md) - System design
- **Backend Guide:** [../../CLAUDE.backend.md](../../CLAUDE.backend.md) - Backend development

---

**Last Updated:** 2025-12-07
**Maintainer:** API Team
