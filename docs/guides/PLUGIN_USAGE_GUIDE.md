# Claude Code Plugins - Usage Guide

**Created:** 2025-10-31
**Purpose:** Quick reference for when and how to use installed plugins
**Location:** `/home/cytrex/news-microservices/docs/guides/PLUGIN_USAGE_GUIDE.md`

---

## 🎯 Installed Plugins Overview

**Total Plugins:** 16
**Installation Date:** 2025-10-31
**Categories:** Performance, Security, Documentation, Testing, Development

---

## 📋 Quick Reference - When to Use Which Plugin

### Performance & Operations (Phase 4 Priority)

#### 1. **observability-monitoring** ⭐⭐⭐ CRITICAL
**Use When:**
- Validating cache hit rates (Task 403 - 24h monitoring)
- Monitoring memory leaks (Task 401 - entity-canonicalization validation)
- Tracking service health metrics
- Setting up distributed tracing

**How to Activate:**
```bash
# In Claude Code session
/observability-monitoring setup metrics collection
/observability-monitoring analyze service performance
```

**Current Use Cases:**
- Task 403: Cache strategy validation (hit rate tracking)
- Task 401: Memory leak monitoring (845 MiB stability check)
- RabbitMQ queue monitoring

---

#### 2. **application-performance** ⭐⭐⭐ HIGH PRIORITY
**Use When:**
- Optimizing Research Service (Task 404 - target: 1243ms → <50ms)
- Profiling frontend bundle (Task 406 - 45% unused code)
- Identifying bottlenecks in any service
- Performance regression testing

**How to Activate:**
```bash
/application-performance profile research-service
/application-performance analyze frontend bundle
/application-performance benchmark api-endpoint
```

**Current Use Cases:**
- Task 404: Research Service optimization (NEXT)
- Task 406: Frontend bundle size reduction

---

#### 3. **distributed-debugging** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- Debugging RabbitMQ message flow (Task 405)
- Tracing requests across 17 microservices
- Investigating timeout issues
- Analyzing service-to-service communication

**How to Activate:**
```bash
/distributed-debugging trace request-flow
/distributed-debugging analyze rabbitmq topology
```

**Current Use Cases:**
- Task 405: RabbitMQ optimization (workers 5/5 online)
- Inter-service communication debugging

---

#### 4. **database-cloud-optimization** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- Validating Task 402 database optimizations
- Analyzing query performance
- Optimizing connection pools
- Cost analysis for cloud resources

**How to Activate:**
```bash
/database-cloud-optimization analyze query performance
/database-cloud-optimization review connection pools
```

**Current Use Cases:**
- Task 402 validation: Batch insert (-90%), stats queries (-80%)
- Connection pool optimization (+100% efficiency)

---

### Documentation (Phase 5 & Ongoing)

#### 5. **code-documentation** ⭐⭐⭐ HIGH PRIORITY
**Use When:**
- Writing docstrings for Python services
- Generating API documentation
- Explaining complex code sections
- Creating technical documentation

**How to Activate:**
```bash
/code-documentation generate docstrings
/code-documentation explain complex-function
/code-documentation create api-docs
```

**When to Use:**
- After completing any Phase 4 optimization (document changes)
- Before Phase 5 (test documentation)
- When adding new features

---

#### 6. **documentation-generation** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- Creating OpenAPI specs
- Generating Mermaid diagrams
- Building architecture documentation
- Creating user guides

**How to Activate:**
```bash
/documentation-generation create openapi-spec
/documentation-generation generate architecture-diagram
```

**When to Use:**
- Phase 5: API documentation
- Architecture Decision Records (ADRs)
- System diagrams for documentation

---

### Code Quality & Review

#### 7. **code-review-ai** ⭐⭐⭐ HIGH PRIORITY
**Use When:**
- Before committing Phase 4 optimizations
- Reviewing refactored code
- Architectural review of new services
- Pre-deployment validation

**How to Activate:**
```bash
/code-review-ai review changes
/code-review-ai architectural-analysis
/code-review-ai security-check
```

**When to Use:**
- Before deploying Task 404 changes
- After completing any major refactoring
- Pre-production validation

---

#### 8. **comprehensive-review** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- Multi-perspective code analysis
- Architecture validation
- Security + performance + quality combined review

**How to Activate:**
```bash
/comprehensive-review full-analysis
```

**When to Use:**
- End of Phase 4 (comprehensive review)
- Before Phase 5 starts
- Major milestone reviews

---

#### 9. **code-refactoring** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- Technical debt reduction
- Code cleanup operations
- Pattern standardization

**How to Activate:**
```bash
/code-refactoring analyze tech-debt
/code-refactoring cleanup dead-code
```

**When to Use:**
- Phase 3 type work
- Ongoing code maintenance

---

### Testing

#### 10. **unit-testing** ⭐⭐⭐ HIGH PRIORITY
**Use When:**
- Writing tests for Phase 4 optimizations
- Creating test suites (Phase 5)
- Test coverage analysis
- Test automation

**How to Activate:**
```bash
/unit-testing generate tests
/unit-testing coverage-analysis
```

**When to Use:**
- Task 404: Test Research Service optimizations
- Phase 5: 80%+ code coverage requirement
- After any code changes

---

#### 11. **performance-testing-review** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- Load testing optimized services
- Performance regression detection
- Benchmark validation

**How to Activate:**
```bash
/performance-testing-review benchmark service
/performance-testing-review regression-check
```

**When to Use:**
- After Task 404 deployment
- Validating Phase 4 improvements
- CI/CD integration (Phase 5)

---

### Development

#### 12. **python-development** ⭐⭐⭐ HIGH PRIORITY
**Use When:**
- FastAPI development
- Async programming patterns
- Python best practices
- Type hints and validation

**How to Activate:**
```bash
/python-development optimize fastapi
/python-development async-patterns
```

**When to Use:**
- All backend service work
- Phase 4 optimizations
- New feature development

---

### Security

#### 13. **backend-api-security** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- API security hardening
- Authentication/authorization review
- Security vulnerability assessment

**How to Activate:**
```bash
/backend-api-security audit api
/backend-api-security check authentication
```

**When to Use:**
- Before production deployment
- Security audits
- After auth changes

---

#### 14. **security-scanning** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- SAST analysis
- Dependency vulnerability scanning
- OWASP Top 10 checks

**How to Activate:**
```bash
/security-scanning sast-analysis
/security-scanning dependency-check
```

**When to Use:**
- Before deployment
- Regular security audits
- Dependency updates

---

### Infrastructure (Phase 5)

#### 15. **error-diagnostics** ⭐⭐ MEDIUM PRIORITY
**Use When:**
- Root cause analysis
- Error tracing
- Production debugging

**How to Activate:**
```bash
/error-diagnostics trace error
/error-diagnostics root-cause-analysis
```

**When to Use:**
- Production incidents
- Complex bug investigation

---

#### 16. **cicd-automation** ⭐⭐⭐ HIGH PRIORITY (Phase 5)
**Use When:**
- Creating CI/CD pipelines
- GitHub Actions workflows
- Quality gates setup

**How to Activate:**
```bash
/cicd-automation create pipeline
/cicd-automation setup quality-gates
```

**When to Use:**
- Phase 5: CI/CD pipeline (< 5 min requirement)
- Automation workflows

---

## 🎯 Priority Matrix for Current Work

### Phase 4 - Performance Optimization (NOW)

**Daily Use:**
1. **observability-monitoring** - Cache & memory monitoring
2. **application-performance** - Task 404 & 406 optimization
3. **python-development** - Backend optimization work

**Before Deployment:**
4. **code-review-ai** - Pre-deployment validation
5. **unit-testing** - Test coverage

**As Needed:**
6. **distributed-debugging** - RabbitMQ issues
7. **database-cloud-optimization** - Query validation

---

### Phase 5 - Testing & CI/CD (LATER)

**Primary:**
1. **cicd-automation** - Pipeline creation
2. **unit-testing** - 80%+ coverage
3. **performance-testing-review** - Load testing

**Secondary:**
4. **code-documentation** - API docs
5. **documentation-generation** - OpenAPI specs
6. **security-scanning** - Pre-production checks

---

## 📝 Integration with Current Workflow

### Before Starting a Task
```bash
# Example: Task 404 - Research Service Optimization
/application-performance profile research-service
/observability-monitoring setup metrics
```

### During Development
```bash
/python-development async-patterns  # For implementation
/code-review-ai review changes      # For validation
```

### Before Committing
```bash
/unit-testing generate tests
/code-review-ai security-check
/security-scanning dependency-check
```

### After Deployment
```bash
/observability-monitoring analyze metrics
/performance-testing-review benchmark service
```

---

## 🚨 Important Notes

### Plugin Usage Policy
**From CLAUDE.md:**
> Skills & Specialized Agents: Proactive Usage - No Permission Required
> When a task matches a specialized skill, use it directly without asking

**This applies to plugins!** Use them proactively when they fit the task.

### Integration with Existing Tools
- Plugins **complement** existing bash/curl/pytest workflows
- Use plugins for **systematic analysis**, manual tools for **quick checks**
- Plugins provide **structured output** suitable for documentation

### Performance Consideration
- Plugins may add processing time
- Use for **analysis and planning**, not simple file reads
- Combine plugin insights with direct tool usage

---

## 📊 Tracking Plugin Usage

### Create Plugin Usage Log
```bash
# Add to SESSION_LOG.md when using plugins
## Plugin Usage
- **Plugin:** observability-monitoring
- **Task:** Task 403 cache validation
- **Outcome:** Identified hit rate < 40%, needs tuning
```

### Measure Impact
Track improvements from plugin usage:
- Code quality scores
- Performance metrics before/after
- Time saved in analysis

---

## 🔗 Related Documents

- **Main Guidelines:** `/home/cytrex/CLAUDE.md`
- **Backend Guide:** `/home/cytrex/CLAUDE.backend.md`
- **Phase 4 Plan:** `/home/cytrex/userdocs/refactoring2510/implementation/phase-4-performance/PHASE_4_PLAN.md`
- **Session Log:** `/home/cytrex/userdocs/refactoring2510/SESSION_LOG.md`

---

## 🎓 Learning Resources

Each plugin has built-in help:
```bash
/plugin-name --help
/plugin-name examples
```

---

**Last Updated:** 2025-10-31
**Next Review:** After Task 404 completion
**Maintained By:** Development team (guided by CLAUDE.md)
