# Architecture Documentation

Core system architecture documents and technical references.

## Core System Architecture

- **ARCHITECTURE_DIAGRAM.md** - Complete system topology and service interaction
- **DATABASE_ARCHITECTURE.md** - Data ownership and schema design
- **EVENT_DRIVEN_ARCHITECTURE.md** - RabbitMQ event flows and consumers
- **FRONTEND_ARCHITECTURE.md** - Frontend structure and state management
- **API_CATALOG.md** - Complete API endpoint catalog across all services

## Service Integration Designs

### FMP-Knowledge-Graph Integration (Financial Markets)

**Status:** ✅ Design Complete, Ready for Implementation
**Phase:** Phase 1 - Market Sync Foundation

Integration design documents for syncing financial market data from FMP Service to Knowledge-Graph Service (Neo4j).

**Documentation:**
- **[FMP-KG-INTEGRATION-SUMMARY.md](FMP-KG-INTEGRATION-SUMMARY.md)** - Executive summary, quick start (read this first)
- **[fmp-kg-integration-design.md](fmp-kg-integration-design.md)** - Detailed architecture design (30 KB)
- **[fmp-kg-integration-implementation-guide.md](fmp-kg-integration-implementation-guide.md)** - Step-by-step implementation

**Supporting Files:**
- Neo4j Schema: `/services/knowledge-graph-service/migrations/neo4j/001_market_schema.cypher`
- OpenAPI Spec: `/docs/api/kg-markets-api-spec.yaml`

**Scope:** 40 financial assets (stocks, forex, commodities, crypto) as Neo4j graph nodes

## Analysis & Planning

- **ARCHITECTURAL_TECHNICAL_DEBT.md** - Known technical debt and remediation plans
- **ARCHITECTURE_REFACTORING_PLAN.md** - Ongoing refactoring initiatives
- **ARCHITECTURE_CONFLICT_ANALYSIS_2025-10-17.md** - Service boundary conflict analysis

## Domain Models

- **analysis-tables-schema.md** - Article analysis data schema
- **feed-quality-scoring-model.md** - RSS feed quality scoring algorithm
- **EVENT_ARCHITECTURE.md** - Event-driven architecture patterns

## Related

- See [../guides/](../guides/) for implementation guides
- See [../services/](../services/) for service-specific architecture
- See [../api/](../api/) for API specifications
