# Architecture Refactoring Plan (Service-Aligned Data)

_Revision: 2025-10-18_

The runtime architecture is stable, but Postgres remains a shared dependency (`news_mcp`). The next architectural milestone is to transition each service to its own schema/database without disrupting the event-driven workflows that now exist in production. This document outlines the phased approach.

---

## Phase 0 – Preparation (Complete)

- ✅ Catalogue SQLAlchemy models per service (`services/*/app/models`)
- ✅ Document active tables and ownership (`docs/DATABASE_ARCHITECTURE.md`)
- ✅ Ship Alembic scaffolding with every service
- ✅ Stabilise event flows (Feed → Content Analysis → Search/Notification)

---

## Phase 1 – Schema Extraction (In Progress)

1. **Create service schemas/databases**
   - Provision logical databases `news_auth`, `news_feed`, `news_analysis`, etc. (Postgres).
   - Update service settings to support dual configuration: shared DB (default) vs dedicated DB (feature flag).

2. **Generate baseline migrations**
   - Run Alembic autogenerate against shared schema to produce canonical migration scripts per service.
   - Store migrations under `database/<service>/versions/` for shared visibility.

3. **Update code to target new engines**
   - Introduce repository layer that can abstract session creation (`news_mcp_common.database`).
   - Support read/write splitting via env toggles (`USE_SERVICE_DATABASE=true`).

Deliverable: services can boot against either shared or dedicated databases with the same code path.

---

## Phase 2 – Dual Writing & Backfill

1. **Dual Writes**
   - Implement writes to both shared and service database when the feature flag is enabled.
   - Add idempotency guards to avoid duplicate key errors.

2. **Backfill Historical Data**
   - Use chunked copy jobs (psycopg `COPY`) to migrate existing records from `news_mcp`.
   - Validate row counts and constraints via automated scripts.

3. **Smoke Tests**
   - Replay RabbitMQ events (`scripts/requeue_old_articles.py`) against dual DB setup.
   - Run integration tests that span Auth → Feed → Analysis → Search.

Deliverable: service databases are populated and stay in sync with the shared DB.

---

## Phase 3 – Cutover & Optimisation

1. **Read Switch**
   - Update each service to read exclusively from its dedicated database.
   - Keep writes dual for one release to guarantee consistency.

2. **Decommission Shared Tables**
   - Drop or archive service-owned tables from `news_mcp`.
   - Retain cross-service read-only views if required (e.g., analytics rollups).

3. **Optimise**
   - Tune indexes and vacuum settings per service workload.
   - Update observability dashboards to track database health individually.

Deliverable: each service operates on its own database, shared DB reduced to cross-cutting data only.

---

## Risk Mitigations

- **Change Management**: rollout feature flags service-by-service; coordinate migrations via CI/CD pipelines.
- **Rollback Plan**: keep shared DB writes enabled until confidence high; switching env vars returns to legacy mode.
- **Observability**: expand metrics (connection pools, query latency) during dual write phase.
- **Event Contracts**: ensure events include enough identifiers to reconcile data across databases.

---

## Supporting Assets

- `docs/DATABASE_ARCHITECTURE.md` – current schema ownership & gap analysis
- `docs/EVENT_DRIVEN_ARCHITECTURE.md` – list of event producers/consumers
- `shared/news-mcp-common` – reusable DB + auth utilities (extend with multi-DB support)
- `Makefile` – add targets for cross-service migrations and copy jobs

This plan supersedes older migration notes and reflects the stable codebase present in the repository today.

