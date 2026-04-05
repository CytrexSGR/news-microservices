# Feature Documentation Index

**Quick Reference:** [CLAUDE.md](../../CLAUDE.md) | [ARCHITECTURE.md](../../ARCHITECTURE.md)

---

## 📖 About This Directory

This directory contains **feature specifications and documentation** for major platform features.

For architectural decisions, see [../decisions/](../decisions/).
For implementation guides, see [../guides/](../guides/).

---

## 🎯 Current Features

### Trading & Predictions

- **[trading-dashboard.md](trading-dashboard.md)** ⭐ **NEW - 2025-11-29**
  - Real-time trading dashboard
  - Position management
  - Portfolio analytics
  - WebSocket integration

### Content Analysis

- **Content Analysis V3 Pipeline**
  - Multi-LLM analysis (OpenAI/Anthropic/Ollama)
  - Sentiment, entity, topic extraction
  - See: [ADR-020](../decisions/ADR-020-pipeline-v2-architecture.md)

- **Sequential Tier2 Execution**
  - Bias-first execution order
  - Inter-agent learning
  - +15-30% accuracy improvement
  - See: [ADR-029](../decisions/ADR-029-sequential-tier2-implementation.md)

### Knowledge Graph

- **Entity Canonicalization**
  - 5-stage deduplication pipeline
  - Fuzzy/semantic matching
  - Wikidata enrichment
  - See: [../services/entity-canonicalization-service/](../../services/entity-canonicalization-service/)

- **Knowledge Graph Visualization**
  - Neo4j-backed entity relationships
  - Interactive graph explorer
  - Analytics APIs

### Search & Discovery

- **Full-Text Search**
  - Real-time indexing
  - Saved search queries
  - Advanced filtering
  - See: [search-service](../../services/search-service/)

### Intelligence & Synthesis

- **DIA (Dynamic Intelligence Augmentation)**
  - Two-stage LLM planning
  - AI-powered content verification
  - See: [llm-orchestrator](../../services/llm-orchestrator/)

- **Intelligence Synthesizer**
  - Automated intelligence synthesis
  - Metrics tracking
  - See: [ADR-016](../decisions/ADR-016-intelligence-synthesizer.md)

### Feed Management

- **Feed Quality Scoring**
  - Automated quality assessment
  - Source credibility tracking
  - See: [ADR-007](../decisions/ADR-007-feed-quality-scoring.md)

- **Feed Pages Consolidation**
  - Unified feed management UI
  - 5 tabs consolidated into 1 interface
  - See: [ADR-040](../decisions/ADR-040-feed-pages-consolidation.md)

---

## 🚀 Upcoming Features

See [../future-features/](../future-features/) for planned features and roadmap.

---

## 📚 Related Documentation

- **Architecture Decisions:** [../decisions/](../decisions/) - ADRs for features
- **Service Documentation:** [../services/](../services/) - Service-specific features
- **API Documentation:** [../api/](../api/) - Feature API contracts
- **Frontend Documentation:** [../../CLAUDE.frontend.md](../../CLAUDE.frontend.md) - UI features

---

## 🔍 Feature Status

### Production (✅)
- Content Analysis V3
- Knowledge Graph
- Full-Text Search
- Feed Management
- Trading Dashboard

### Beta (🔄)
- Entity Canonicalization
- Intelligence Synthesizer

### Planned (⏳)
- Automated Feed Assessment
- Enhanced OSINT Monitoring
- Multi-tenant Support

---

**Last Updated:** 2025-12-07
**Total Features:** [Count features in directory]
**Maintainer:** Product Team
