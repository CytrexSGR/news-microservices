# Content-Analysis-V3 Changelog

All notable changes to the Content-Analysis-V3 service will be documented in this file.

## [1.1.1] - 2026-01-05

### Fixed

#### 🔴 DATABASE COLUMN FIX - Pipeline Version Storage Failure

**Problem Identified:**
- Batch reprocessing of today's articles (339) completed successfully
- Consumer logs showed analysis execution working
- BUT: Zero results were being saved to database
- Root cause: `pipeline_version` column was VARCHAR(10), but `'3.0-backfill'` is 12 characters

**Error:**
```
ERROR: value too long for type character varying(10)
```

**Solution Implemented:**
```sql
ALTER TABLE article_analysis ALTER COLUMN pipeline_version TYPE VARCHAR(50);
```

**Results:**
- ✅ Database inserts now succeed
- ✅ Analysis results properly stored
- ✅ Verified by checking `article_analysis` count increase

**Impact:**
- Silent data loss for batch reprocessing prevented
- No data lost (reprocessed after fix)

**References:**
- README.md - Known Issues & Resolutions section

---

## [1.1.0] - 2025-11-21

### Changed

#### 🔴 TIER0 TRIAGE HARDENING - Stricter Filtering for Cost Optimization

**Problem Identified:**
- Keep rate was 77.7% (only 22% discarded)
- Average priority of kept articles: 4.6/10 (too low)
- 777 articles with priority 4 being kept (45.2% of all articles)
- User examples showed routine news being kept that should be discarded:
  - "Climate conference COP30 goes to overtime" (Priority 4, HUMANITARIAN)
  - "Senator fears for safety after Trump tweet" (Priority 4, POLITICS)
  - "Colombian drug boat strike kills 5" (Priority 4, SECURITY)

**Solution Implemented:**
- **Raised minimum keep threshold from ≥4 to ≥5**
- Rewrote `TIER0_PROMPT_TEMPLATE` with explicit override rules
- Added critical rule at top: "🔴 MINIMUM KEEP THRESHOLD = SCORE 5+ ONLY 🔴"
- Reclassified Score 3-4 from "MODERATE - Keep" to "LOW RELEVANCE - DISCARD"
- Added specific examples matching user's feedback (COP30, Senator fears, regional conflicts)
- Increased target discard rate from 40-50% to 60-70%

**Results (20 articles after deployment):**
- ✅ Keep rate: 40.0% (down from 77.7%) - **48% reduction**
- ✅ Average priority (kept): 6.3/10 (up from 4.6) - **37% improvement**
- ✅ Zero violations: No articles with priority ≤4 were kept
- ✅ All kept articles (priority 6): Important G20 politics, nation-state security

**Cost Impact:**
- Estimated savings: ~600 fewer articles per day processed through Tier1/Tier2
- Tier1 savings: ~$12/day (600 × $0.02)
- Tier2 savings: ~$60/day (600 × $0.10)
- **Total estimated savings: ~$72/day = $2,160/month**

**Technical Details:**
- Modified file: `app/pipeline/tier0/triage.py` (lines 224-353)
- Deployment: 2025-11-21 22:41:45 CET
- Verification: 100% compliance with new threshold (0 violations in 20 test articles)
- Monitoring: Database query confirmed no priority ≤4 articles kept after restart time

**Monitoring Commands:**
```sql
-- Check current triage distribution
SELECT
    (triage_results->>'priority_score')::int as priority,
    (triage_results->>'keep')::boolean as keep,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
FROM public.article_analysis
WHERE created_at > NOW() - INTERVAL '24 hours'
AND triage_results IS NOT NULL
GROUP BY priority, keep
ORDER BY priority DESC, keep DESC;

-- Verify threshold compliance (should return 0 rows after deployment)
SELECT COUNT(*) as violations
FROM public.article_analysis
WHERE created_at > '2025-11-21 22:41:45'
AND triage_results IS NOT NULL
AND (
    ((triage_results->>'priority_score')::int <= 4 AND (triage_results->>'keep')::boolean = true)
    OR
    ((triage_results->>'priority_score')::int >= 5 AND (triage_results->>'keep')::boolean = false)
);
```

**References:**
- POSTMORTEMS.md Incident #20: Content-Analysis-V2 Service Shutdown
- User feedback: "triage agenten einen touch härter werden lassen"

---

## [1.0.0] - 2025-11-20

### Added
- Initial release of Content-Analysis-V3 service
- 4-tier progressive analysis pipeline (Tier0-Tier3)
- 96.7% cost reduction vs V2 (Gemini 2.0 Flash)
- 6 Tier2 specialists with 2-stage prompting
- RabbitMQ event-driven architecture
- FastAPI REST API with health checks
- 3 parallel worker consumers (30 concurrent analyses)
- Comprehensive test suite (19/19 tests passing)

### Changed
- Storage architecture: Event-driven writes to `public.article_analysis` (unified table)
- No direct database writes from V3 service
- BiasScorer optimization: 65% token reduction (2025-11-20)

### Fixed
- Schema validation with field validators (POSTMORTEMS Incident #18)
- Triage bypass prevention (objective scoring criteria)
- Cost metadata completeness for all articles

---

**Version:** 1.1.2
**Last Updated:** 2026-01-05
**Maintainer:** Andreas (andreas@test.com)
