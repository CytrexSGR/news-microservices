# Documentation Index

**Prinzip:** "Undokumentierte Arbeit = nicht gemachte Arbeit"

Siehe **CLAUDE.md** für vollständige Dokumentationsstrategie und Templates.

---

## 📚 Dokumentationsstruktur

```
docs/
├── README.md                    # Diese Datei (Index)
├── CHANGELOG.md                 # Version history and changes
├── services/                    # Service-spezifische Dokumentation
│   ├── auth-service.md
│   ├── feed-service.md
│   ├── content-analysis-service.md
│   └── ...                      # Ein .md pro Service
│
├── api/                         # API-Kontrakt-Dokumentation
│   ├── auth-api.md              # Endpoints, Request/Response
│   ├── feed-api.md
│   └── ...                      # Ein .md pro Service-API
│
├── features/                    # Feature-specific documentation
│   ├── feed-quality-score.md   # NEW: Quality scoring system
│   └── ...                      # Complex features get dedicated docs
│
├── decisions/                   # Architecture Decision Records (ADR)
│   ├── ADR-001-mandatory-documentation.md
│   ├── ADR-007-feed-quality-scoring.md  # NEW: Scoring methodology
│   └── ADR-XXX-<titel>.md       # Nummeriert, chronologisch
│
├── deployment/                  # Deployment & Infrastructure
│   ├── docker-setup.md
│   ├── database-migrations.md
│   └── ...
│
└── incidents/                   # Bug-Fixes & Lessons Learned
    └── YYYY-MM-DD-<issue>.md    # Datiert

frontend/
└── docs/                        # Frontend-spezifische Dokumentation
    ├── auth-flow.md
    ├── feed-management.md
    └── ...                      # Ein .md pro Feature/Flow
```

---

## 📋 Wann dokumentieren?

| Trigger | Template | Location |
|---------|----------|----------|
| Neuer Service | [Service-Template](../CLAUDE.md#service-template) | `docs/services/<name>.md` |
| API-Änderung | [API-Template](../CLAUDE.md#api-template) | `docs/api/<service>-api.md` |
| Architektur-Entscheidung | [ADR-Template](../CLAUDE.md#adr-template) | `docs/decisions/ADR-XXX-<titel>.md` |
| Frontend-Feature | [Frontend-Template](../CLAUDE.md#frontend-template) | `frontend/docs/<feature>.md` |
| Deployment-Änderung | Update CLAUDE.md | `docs/guides/deployment/<topic>.md` |
| Kritischer Bug-Fix | [Incident-Template](../CLAUDE.md#incident-template) | `docs/incidents/YYYY-MM-DD-<issue>.md` |

**Regel:** Code-Commit ohne Dokumentations-Update → PR rejected.

---

## ✅ Pre-Commit Checklist

Vor jedem Commit:

- [ ] **Service/Feature added?** → `docs/services/<name>.md` exists?
- [ ] **API changed?** → `docs/api/<service>-api.md` updated?
- [ ] **Architecture decision?** → `docs/decisions/ADR-*.md` created?
- [ ] **Frontend changed?** → `frontend/docs/<feature>.md` updated?
- [ ] **Deployment changed?** → `CLAUDE.md` + `docs/guides/deployment/` updated?

**Wenn EINE Antwort "Nein" → Dokumentation UNVOLLSTÄNDIG.**

---

## 🎯 Ziel

**Minimum viable documentation:**
- Was macht es? (1 Satz)
- Wie benutze ich es? (Commands/Code)
- Was kann schiefgehen? (Häufige Probleme)

**Nicht mehr, nicht weniger.** Templates in CLAUDE.md halten Docs fokussiert.

---

**Last updated:** 2025-01-22

## Current Structure

docs/
├── README.md                    # This file
├── POSTMORTEMS.md              # Lessons learned from failures
├── architecture/               # System architecture documentation
├── guides/                     # How-to guides and protocols
├── services/                   # Service-specific docs (per service)
│   ├── n8n-service.md          # 🆕 Workflow automation (2025-10-28)
│   ├── auth-service.md
│   ├── feed-service.md
│   └── ...                     # One .md per service
├── api/                        # API documentation (per service)
├── n8n/                        # 🆕 n8n workflow guides (2025-10-28)
│   └── workflow-guide-*.md     # Step-by-step workflow creation
├── templates/                  # Documentation templates
├── decisions/                  # Architecture Decision Records
├── notification-service/       # Reference implementation (fully documented)
└── archive/                    # Historical documents

## Quick Navigation

- **Architecture**: [System Overview](architecture/ARCHITECTURE_DIAGRAM.md), [Database](architecture/DATABASE_ARCHITECTURE.md), [Events](architecture/EVENT_DRIVEN_ARCHITECTURE.md)
- **Features**: [Feed Quality Score System](features/feed-quality-score.md), [Admiralty Code System](features/admiralty-code-system.md)
- **Guides**: [Deployment](guides/DEPLOYMENT_GUIDE.md), [Development](guides/DEVELOPMENT_WORKFLOW.md), [Migrations](guides/migration-protocol.md)
- **Automation**: [n8n Workflow Service](services/n8n-service.md) 🆕 **2025-10-28** - Event-driven automation & orchestration
- **Templates**: [Service](templates/service-template.md), [API](templates/api-template.md), [Architecture](templates/architecture-template.md)
- **Decisions (ADR)**: [ADR-011: Analysis Idempotency](decisions/ADR-011-analysis-idempotency.md) 🆕 **2025-01-22**, [ADR-008: Admiralty Code Rating](decisions/ADR-008-admiralty-code-rating-system.md), [All ADRs](decisions/)
- **Incidents**: [2025-01-22: Duplicate Analysis Fix](incidents/2025-01-22-duplicate-analysis-fix.md) 🆕 **(1026 duplicates removed)**, [All Incidents](incidents/)
- **Changes**: [CHANGELOG](CHANGELOG.md) - Latest: v1.2.0 Idempotency & Event-Carried State Transfer

