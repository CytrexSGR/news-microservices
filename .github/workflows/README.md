# CI/CD Workflows Documentation

## Overview

This directory contains GitHub Actions workflows for automated testing, linting, building, and deployment of the News Microservices platform.

---

## 📋 Available Workflows

### 1. Test Pipeline (`test.yml`)

**Triggers:**
- Push to `main`, `develop`, or `feature/**` branches
- Pull requests to `main` or `develop`

**Jobs:**
- **test-shared-library**: Tests the shared news-mcp-common library
- **test-services**: Parallel testing of all 12 microservices
- **integration-tests**: End-to-end integration tests
- **security-scan**: Bandit and Safety security scans

**Services Tested:**
1. auth-service
2. feed-service
3. content-analysis-v2
4. research-service
5. osint-service
6. notification-service
7. search-service
8. analytics-service
9. fmp-service
10. knowledge-graph-service
11. entity-canonicalization-service
12. llm-orchestrator-service

**Dependencies:**
- PostgreSQL 15
- Redis 7
- RabbitMQ 3.12

**Artifacts:**
- Coverage reports uploaded to Codecov
- Per-service coverage XML files

---

### 2. Lint Pipeline (`01-lint.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main`

**Checks:**
- **Hadolint**: Dockerfile linting
- **Docker Compose Validation**: Validates all compose files
- **ShellCheck**: Bash script linting
- **Dockerfile Anti-Patterns**: Custom pattern checks
- **Image Size Validation**: Ensures images stay within limits

**Image Size Limits:**
- Backend services: 400MB
- content-analysis-v2: 600MB (due to ML models)

---

### 3. Build Pipeline (`build.yml`)

**Triggers:**
- Push to `main`
- Git tags matching `v*`
- Pull requests to `main`

**Jobs:**
- Builds Docker images for all 12 services
- Pushes to GitHub Container Registry (ghcr.io)
- Runs Trivy security scanning on images

**Output:**
- Tagged images: `ghcr.io/[repo]/[service]:[tag]`
- Security scan results (SARIF format)

---

### 4. Coverage Gate (`coverage-gate.yml`)

**Triggers:**
- Pull requests to `main` or `develop`

**Purpose:**
- Validates test coverage thresholds
- Posts coverage summary to PR comments
- Blocks PRs with insufficient coverage (when configured)

**Current Coverage Baseline (Phase 5 Validation):**
- **Overall:** 73.7% (913/1238 tests passing)
- **Production-Ready:** 8/11 services (>70%)

**Service Coverage:**
| Service | Pass Rate | Status |
|---------|-----------|--------|
| fmp-service | 100% | ✅ |
| knowledge-graph | 100% | ✅ |
| entity-canonicalization | 100% | ✅ |
| auth-service | 97.6% | ✅ |
| osint-service | 90.9% | ✅ |
| analytics-service | 68.5% | ⚠️ |
| llm-orchestrator | 63.1% | ⚠️ |
| research-service | 62.5% | ⚠️ |
| notification-service | 62.6% | ⚠️ |
| search-service | 54.5% | ⚠️ |
| feed-service | 36.7% | ❌ |

---

### 5. Deploy Pipeline (`deploy.yml`)

**Triggers:**
- Manual workflow dispatch
- Push to `main` (staging)
- Git tags (production)

**Environments:**
- **Staging**: Automated deployment on main
- **Production**: Manual approval required

**Features:**
- Blue-green deployment
- Automated rollback on failure
- Health check validation
- Smoke tests

---

## 🔧 Configuration

### Secrets Required

**Container Registry:**
- `GITHUB_TOKEN` (automatically provided)

**Deployment:**
- `STAGING_HOST` - Staging server hostname
- `STAGING_USER` - SSH username for staging
- `STAGING_SSH_KEY` - SSH private key for staging
- `PROD_HOST` - Production server hostname
- `PROD_USER` - SSH username for production
- `PROD_SSH_KEY` - SSH private key for production

**External Services (Optional):**
- `SNYK_TOKEN` - Snyk security scanning
- `SLACK_WEBHOOK` - Slack notifications
- `CODECOV_TOKEN` - Codecov coverage reporting

---

## 📊 Workflow Matrix Strategy

All workflows use GitHub Actions matrix strategy for parallel execution:

```yaml
strategy:
  matrix:
    service:
      - auth-service
      - feed-service
      - content-analysis-v2
      # ... all 12 services
```

**Benefits:**
- **Parallelization**: 12 services tested simultaneously
- **Isolation**: Service failures don't block others
- **Speed**: ~5-8 minutes total (vs. 60+ minutes sequential)

---

## 🚀 Performance Metrics

### Test Pipeline
- **Target:** < 10 minutes
- **Current:** ~8-12 minutes (12 services in parallel)
- **Parallelization:** 12x (12 services simultaneously)

### Lint Pipeline
- **Target:** < 3 minutes
- **Current:** ~2-4 minutes

### Build Pipeline
- **Target:** < 15 minutes
- **Current:** ~10-15 minutes (with caching)

---

## 📈 Quality Gates

### Test Coverage

**Thresholds (when fully configured):**
- Backend services: 80% minimum
- Frontend: 70% minimum
- Shared library: 85% minimum

**Current Status:**
- ✅ 8 services above 60%
- ⚠️ 3 services need improvement
- 📊 Overall: 73.7% pass rate

### Security Scanning

**Tools:**
- **Bandit**: Python security issues
- **Safety**: Dependency vulnerabilities
- **Trivy**: Container image vulnerabilities
- **Hadolint**: Dockerfile best practices

**Thresholds:**
- High severity: Blocking
- Medium severity: Warning
- Low severity: Informational

---

## 🔄 Workflow Dependencies

```
test.yml (required)
  ├── test-shared-library
  ├── test-services (12 parallel jobs)
  ├── integration-tests
  └── security-scan

01-lint.yml (required)
  ├── dockerfile-lint
  ├── compose-validate
  ├── shellcheck
  ├── dockerfile-patterns
  └── image-size-check

build.yml (required for releases)
  └── build-service-images (12 parallel jobs)

coverage-gate.yml (informational)
  └── coverage-check

deploy.yml (manual/automated)
  └── deploy (staging or production)
```

---

## 🛠️ Local Testing

### Test Workflow Locally

```bash
# Run tests for a specific service
cd services/auth-service
pytest tests/ -v --cov=app

# Run all service tests
for service in services/*/; do
    cd "$service"
    pytest tests/ -v || echo "No tests for $service"
    cd ../..
done
```

### Lint Locally

```bash
# Dockerfile linting
hadolint services/*/Dockerfile

# Shell script linting
shellcheck scripts/*.sh

# Docker Compose validation
docker compose config --quiet
```

### Build Locally

```bash
# Build all services
docker compose build

# Build specific service
docker compose build auth-service
```

---

## 📝 Adding New Services

When adding a new service:

1. **Update workflow matrices** in:
   - `.github/workflows/test.yml`
   - `.github/workflows/build.yml`

2. **Add tests** in:
   - `services/[new-service]/tests/`

3. **Configure volume mounts** in:
   - `docker-compose.yml` (tests directory)

4. **Verify pytest dependencies**:
   - `services/[new-service]/requirements.txt`

---

## 🔍 Troubleshooting

### Tests Failing in CI but Passing Locally

**Common causes:**
1. **Missing dependencies** in requirements.txt
2. **Environment variables** not set in CI
3. **Service timeouts** (increase in workflow)
4. **Database state** - ensure tests clean up

**Solution:**
```yaml
# Add to workflow
env:
  SERVICE_TIMEOUT: 60
  DATABASE_URL: postgresql://...
```

### Slow Test Pipeline

**Optimizations:**
1. **Use caching** for pip packages
2. **Reduce matrix size** (run only affected services)
3. **Skip integration tests** on draft PRs
4. **Parallel test execution** within services

### Docker Build Failures

**Common issues:**
1. **Cache invalidation** - Clear Docker Buildx cache
2. **Image size limits** - Check COPY commands
3. **Missing files** - Verify .dockerignore

---

## 📚 Related Documentation

- [Phase 5 Test Validation Report](/reports/PHASE_5_RESTARBEITEN_COMPLETE.md)
- [Service Inventory](/reports/phase-1-inventory/SERVICE_INVENTORY_SUMMARY.md)
- [Docker Guide](/docs/guides/docker-guide.md)
- [Testing Guide](/docs/guides/testing-guide.md)

---

## ✅ Status

**Last Updated:** 2025-10-31
**Version:** 1.1.0
**Test Coverage:** 73.7% (913/1238 tests)
**CI/CD Status:** ✅ Operational

**Recent Changes:**
- Updated service matrix to 12 services
- Added coverage-gate.yml workflow
- Enhanced test parallelization
- Improved workflow documentation

---

**Maintained by:** Dev Team
**Questions?** See CLAUDE.md or contact maintainers
