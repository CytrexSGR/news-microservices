# Operations Documentation

**Quick Reference:** [ARCHITECTURE.md](../../ARCHITECTURE.md) | [POSTMORTEMS.md](../../POSTMORTEMS.md)

---

## 📖 About This Directory

This directory contains **operational runbooks, SLI/SLO definitions, and troubleshooting guides** for production services.

For incident reports, see [../incidents/](../incidents/).
For architecture overview, see [ARCHITECTURE.md](../../ARCHITECTURE.md).

---

## 🎯 Available Documentation

### FMP & Knowledge Graph Operations

- **[fmp-kg-runbook.md](fmp-kg-runbook.md)**
  - FMP (Financial Markets Platform) operational procedures
  - Knowledge Graph integration runbook
  - Step-by-step operational tasks
  - Common maintenance procedures

- **[fmp-kg-sli-slo.md](fmp-kg-sli-slo.md)**
  - Service Level Indicators (SLIs)
  - Service Level Objectives (SLOs)
  - Performance targets
  - Monitoring metrics

- **[fmp-kg-troubleshooting.md](fmp-kg-troubleshooting.md)**
  - Common issues and solutions
  - Debugging procedures
  - Performance troubleshooting
  - Integration issues

---

## 📊 Service Coverage

### Services with Operational Documentation
- ✅ FMP Service (fmp-kg-runbook.md, fmp-kg-sli-slo.md, fmp-kg-troubleshooting.md)
- ✅ Knowledge Graph Service (integrated with FMP docs)

### Services Needing Documentation
- ⏳ auth-service
- ⏳ feed-service
- ⏳ content-analysis-v3
- ⏳ search-service
- ⏳ analytics-service
- ⏳ Other core services (8+ services)

---

## 🚨 Operational Procedures

### Daily Operations

1. **Health Checks**
   ```bash
   # Check all services
   ./scripts/health_check.sh

   # Individual service health
   curl http://localhost:<port>/health
   ```

2. **Log Monitoring**
   ```bash
   # View service logs
   docker compose logs -f <service-name>

   # Check for errors
   docker compose logs <service-name> | grep ERROR
   ```

3. **Metrics Review**
   - Grafana: http://localhost:3001 (if configured)
   - Prometheus: http://localhost:9090 (if configured)
   - RabbitMQ: http://localhost:15672

### Weekly Operations

1. **Performance Review**
   - Check SLI/SLO compliance
   - Review response times
   - Analyze resource usage

2. **Capacity Planning**
   - Monitor disk usage
   - Review memory trends
   - Check database growth

3. **Security Checks**
   - Review access logs
   - Check for failed auth attempts
   - Verify SSL certificates

---

## 📝 Runbook Template

```markdown
# Service Runbook: [Service Name]

## Service Overview
- **Port:** 8XXX
- **Purpose:** Brief description
- **Dependencies:** Database, RabbitMQ, etc.

## Common Operations

### Start/Stop Service
Instructions for starting and stopping

### Restart Service
When and how to restart safely

### Deploy Updates
Deployment procedure

### Backup Data
How to backup service data

## Health Checks

### Service Health
How to verify service is healthy

### Dependency Health
How to check dependencies

### Performance Metrics
Key metrics to monitor

## Troubleshooting

### Common Issue 1
Symptoms, causes, solutions

### Common Issue 2
Symptoms, causes, solutions

## Emergency Procedures

### Service Outage
Steps to restore service

### Data Corruption
Recovery procedures

### Security Incident
Incident response steps

## Contacts
- **Primary Owner:** Name/Team
- **Escalation:** Contact info
- **On-Call:** Rotation schedule
```

---

## 🎯 SLI/SLO Framework

### Service Level Indicators (SLIs)

**Availability SLIs:**
- Uptime percentage
- Success rate (non-error responses)
- Health check pass rate

**Performance SLIs:**
- Request latency (p50, p95, p99)
- Throughput (requests/sec)
- Queue processing time

**Quality SLIs:**
- Error rate
- Data accuracy
- Completeness

### Service Level Objectives (SLOs)

**Example SLOs:**
- Availability: 99.9% uptime
- Latency: p95 < 200ms
- Error Rate: < 0.1%
- Queue Processing: < 5 minutes

**See:** [fmp-kg-sli-slo.md](fmp-kg-sli-slo.md) for detailed example

---

## 🔍 Troubleshooting Framework

### 1. Identify Issue
- Check service health endpoint
- Review recent logs
- Check monitoring dashboards

### 2. Gather Context
- When did issue start?
- What changed recently?
- Is it affecting all users or specific subset?

### 3. Isolate Root Cause
- Check service dependencies
- Review configuration
- Analyze error patterns

### 4. Implement Fix
- Apply solution
- Verify fix in staging
- Deploy to production

### 5. Verify Resolution
- Monitor for 30+ minutes
- Check SLI metrics
- Confirm no recurrence

### 6. Document
- Create incident report (see [../incidents/](../incidents/))
- Update troubleshooting guide
- Update runbook if needed

---

## 📚 Related Documentation

- **Incidents:** [../incidents/](../incidents/) - Incident reports and post-mortems
- **Post-Mortems:** [POSTMORTEMS.md](../../POSTMORTEMS.md) - Lessons learned
- **Architecture:** [ARCHITECTURE.md](../../ARCHITECTURE.md) - System design
- **Service Docs:** [../services/](../services/) - Service-specific documentation
- **Monitoring Guide:** [../guides/monitoring-guide.md](../guides/) (if exists)

---

## 🎯 Next Steps

### Immediate
- ✅ FMP service operations documented
- ⏳ Create runbooks for auth-service
- ⏳ Create runbooks for feed-service
- ⏳ Define SLIs/SLOs for all core services

### Future
- ⏳ Automated runbook execution
- ⏳ Self-healing procedures
- ⏳ Chaos engineering tests
- ⏳ Disaster recovery procedures

---

**Last Updated:** 2025-12-07
**Services with Runbooks:** 2 (FMP, Knowledge Graph)
**Target:** 12+ services
**Maintainer:** Operations Team
