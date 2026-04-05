# Knowledge Graph Test Suite

Comprehensive testing framework for validating relationship extraction in the content-analysis-service.

## 📁 Directory Structure

```
tests/knowledge-graph/
├── README.md                    # This file
├── test-data/
│   ├── articles/               # Test input articles
│   │   ├── category-a/        # Simple, factual (5 articles)
│   │   ├── category-b/        # Complex, dense (5 articles)
│   │   ├── category-c/        # Ambiguous, opinion (5 articles)
│   │   └── category-d/        # Negative examples (3 articles)
│   └── ground-truth/          # Expected results (18 files)
├── test-results/              # Generated test results
│   ├── category-a/
│   ├── category-b/
│   ├── category-c/
│   ├── category-d/
│   ├── execution_stats.json
│   ├── summary_report.json
│   └── test_report.html
└── scripts/
    ├── run_test_suite.py       # Execute all tests
    ├── calculate_metrics.py    # Compute precision/recall/F1
    ├── generate_report.py      # Create HTML report
    └── validate_monitoring.py  # Verify Prometheus metrics
```

## 🎯 Test Categories

### Category A: Simple & Factual
- **Articles:** 5
- **Description:** Straightforward news articles with clear, explicit relationships
- **Expected Performance:** Precision >90%, Recall >85%, FP <1 per article
- **Examples:** CEO appointments, product launches, corporate acquisitions

### Category B: Complex & Dense
- **Articles:** 5
- **Description:** Multi-actor scenarios with nested relationships and entity normalization challenges
- **Expected Performance:** Precision >75%, Recall >60%, FP <3 per article
- **Examples:** M&A analyses, geopolitical conflicts, economic policy discussions

### Category C: Ambiguous & Opinion-Based
- **Articles:** 5
- **Description:** Speculative content with indirect speech, conditional language, and subjective interpretations
- **Expected Performance:** Precision >60%, Recall >50%, FP <6 per article
- **Examples:** Opinion pieces, interviews, market predictions, political commentary

### Category D: Negative Examples
- **Articles:** 3
- **Description:** Content with NO extractable relationships (pure lists, weather reports, technical specs)
- **Expected Performance:** 0 relationships extracted, FP <2 per article
- **Purpose:** Tests false positive rate and system's ability to distinguish non-relational content

## 🚀 Quick Start

### Prerequisites

```bash
# 1. Ensure content-analysis-service is running
docker compose up -d content-analysis

# 2. Verify service is accessible
curl http://localhost:8102/api/v1/health

# 3. Get authentication token (if required)
export AUTH_TOKEN="your-jwt-token-here"
```

### Environment Variables

```bash
# Required
export CONTENT_ANALYSIS_API_URL="http://localhost:8102/api/v1"
export AUTH_TOKEN="your-jwt-token"

# Optional
export CONTENT_ANALYSIS_METRICS_URL="http://localhost:8102/metrics"
```

### Run Complete Test Suite

```bash
cd /home/cytrex/news-microservices/tests/knowledge-graph

# Option 1: Run all steps sequentially
python3 scripts/run_test_suite.py
python3 scripts/calculate_metrics.py
python3 scripts/generate_report.py
python3 scripts/validate_monitoring.py

# Option 2: Use master script (executes all 4 steps)
./scripts/run_all_tests.sh
```

### View Results

```bash
# 1. View console summary
cat test-results/summary_report.json | jq '.overall'

# 2. Open HTML report in browser
firefox test-results/test_report.html
# or
google-chrome test-results/test_report.html
```

## 📊 Scripts Documentation

### 1. run_test_suite.py

**Purpose:** Execute all test articles through content-analysis-service

**Input:**
- Articles from `test-data/articles/`
- Environment variables: `CONTENT_ANALYSIS_API_URL`, `AUTH_TOKEN`

**Output:**
- `test-results/<category>/<article-id>-result.json` for each article
- `test-results/execution_stats.json` with execution statistics

**Usage:**
```bash
export CONTENT_ANALYSIS_API_URL="http://localhost:8102/api/v1"
export AUTH_TOKEN="your-token"
python3 scripts/run_test_suite.py
```

**Features:**
- Rate limiting (1 request/second)
- Error handling and retry logic
- Progress tracking per category
- Detailed console output

---

### 2. calculate_metrics.py

**Purpose:** Compare test results against ground truth and calculate metrics

**Input:**
- `test-results/<category>/*-result.json`
- `test-data/ground-truth/*-ground-truth.json`

**Output:**
- `test-results/summary_report.json` with:
  - Overall precision, recall, F1
  - Per-category metrics
  - Confusion matrix (TP, FP, FN)
  - Hall of Fame (top 3 articles)
  - Hall of Shame (highest FP articles)

**Usage:**
```bash
python3 scripts/calculate_metrics.py
```

**Metrics Calculation:**
```python
TP = triplets in both extracted and ground_truth
FP = triplets in extracted but not in ground_truth
FN = triplets in ground_truth but not in extracted

Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Triplet Normalization:**
- Lowercase entities
- Normalize relationship types (e.g., "works_for" == "works for")
- Strip whitespace

---

### 3. generate_report.py

**Purpose:** Create visual HTML report from metrics

**Input:**
- `test-results/summary_report.json`

**Output:**
- `test-results/test_report.html`

**Usage:**
```bash
python3 scripts/generate_report.py

# Open in browser
firefox test-results/test_report.html
```

**Report Sections:**
1. **Overall Performance:** Precision, Recall, F1 with visual cards
2. **Performance by Category:** Detailed table with color-coded metrics
3. **Hall of Fame:** Top 3 best-performing articles
4. **Hall of Shame:** Top 3 articles with most false positives
5. **Category Expectations:** Reference table for target metrics

**Features:**
- Clean, modern design
- Color-coded performance indicators
- Responsive layout
- Print-friendly CSS

---

### 4. validate_monitoring.py

**Purpose:** Verify Prometheus metrics match actual test execution

**Input:**
- `test-results/*-result.json`
- Prometheus `/metrics` endpoint

**Output:**
- Console validation report
- Pass/Fail status per metric

**Usage:**
```bash
export CONTENT_ANALYSIS_METRICS_URL="http://localhost:8102/metrics"
python3 scripts/validate_monitoring.py
```

**Validated Metrics:**
1. `relationship_extraction_total{status="valid"}`
2. `relationship_extraction_total{status="invalid"}`
3. `relationship_acceptance_rate`
4. `relationship_confidence_distribution` (histogram)

**Validation Logic:**
- Counts relationships from test results
- Fetches current Prometheus metrics
- Compares with 10% tolerance
- Reports discrepancies

---

## 📈 Interpreting Results

### Success Criteria

| Category | Precision | Recall | F1 | False Positives |
|----------|-----------|--------|----|-----------------|
| A (Simple) | >90% | >85% | >87% | <1/article |
| B (Complex) | >75% | >60% | >67% | <3/article |
| C (Ambiguous) | >60% | >50% | >54% | <6/article |
| D (Negative) | N/A | N/A | N/A | <2/article |

### What to Optimize

**If Precision is Low (many FP):**
- System is hallucinating relationships
- Increase confidence threshold in prompts
- Strengthen validation rules
- Improve evidence quality checks

**If Recall is Low (many FN):**
- System is missing relationships
- Enhance entity extraction
- Improve indirect speech handling
- Add more relationship types to prompts

**If Category D has FP:**
- **CRITICAL:** False positive rate too high
- System extracting from non-relational content
- Add negative examples to training
- Strengthen "no relationship" detection

### Hall of Fame/Shame Analysis

**Hall of Fame (High F1):**
- Study what worked well
- Replicate patterns in prompt engineering
- Use as few-shot examples

**Hall of Shame (High FP):**
- Identify root causes
- Add similar articles to test suite
- Create targeted fixes
- Document failure patterns

---

## 🔧 Troubleshooting

### "401 Unauthorized" during test execution

**Cause:** Missing or invalid AUTH_TOKEN

**Fix:**
```bash
# Get new token from auth-service
curl -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "andreas@test.com", "password": "Aug2012#"}'

export AUTH_TOKEN="<token-from-response>"
```

---

### "Connection refused" to content-analysis-service

**Cause:** Service not running or wrong URL

**Fix:**
```bash
# Check if service is running
docker compose ps content-analysis

# Restart if needed
docker compose restart content-analysis

# Verify correct port
docker compose logs content-analysis | grep "Uvicorn running"
```

---

### "No ground truth found" warnings

**Cause:** Missing ground truth file for article

**Fix:**
```bash
# Check ground truth files exist
ls test-data/ground-truth/

# Each article should have matching ground truth
# article-001-ceo-appointment.json → article-001-ground-truth.json
```

---

### Prometheus validation fails

**Cause:** Metrics endpoint not accessible or metrics stale

**Fix:**
```bash
# Check metrics endpoint
curl http://localhost:8102/metrics | grep relationship_extraction

# Restart service to reset metrics (if needed)
docker compose restart content-analysis
```

---

### Test results differ on re-run

**Cause:** LLM non-determinism or service state changes

**Expected:** Small variance is normal (±5%)

**Fix:**
```bash
# For consistent results, use temperature=0 in LLM config
# Check services/content-analysis/app/llm/providers/*.py
```

---

## 🔄 Continuous Testing

### Add New Test Articles

1. Create article JSON in appropriate category:
```bash
vim test-data/articles/category-a/article-019-new-test.json
```

2. Create matching ground truth:
```bash
vim test-data/ground-truth/article-019-ground-truth.json
```

3. Follow existing format (see template below)

4. Re-run test suite

### Article JSON Template

```json
{
  "article_id": "article-019",
  "category": "A",
  "title": "Clear, Descriptive Title",
  "content": "Article content with extractable relationships...",
  "source": "Source Name",
  "published_at": "2025-01-15",
  "metadata": {
    "word_count": 150,
    "expected_entities": 5,
    "expected_relationships": 3,
    "difficulty": "simple",
    "notes": "What this article tests"
  }
}
```

### Ground Truth Template

```json
{
  "article_id": "article-019",
  "ground_truth_relationships": [
    {
      "triplet": ["Entity1", "relationship_type", "Entity2"],
      "evidence": "Exact text from article",
      "confidence_expectation": "high",
      "mandatory": true,
      "notes": "Why this relationship should be extracted"
    }
  ],
  "expected_metrics": {
    "total_relationships_min": 2,
    "total_relationships_max": 4,
    "avg_confidence_min": 0.85,
    "precision_min": 0.90,
    "false_positives_max": 1
  },
  "notes": "Overall article purpose and testing goals"
}
```

---

## 🎓 Best Practices

### When to Run Tests

1. **Before Commits:** Always run test suite before committing prompt changes
2. **After LLM Updates:** New model versions may change extraction behavior
3. **Weekly:** Track performance trends over time
4. **Before Production:** Full validation before deploying changes

### Test-Driven Development

1. **Add failing test** for new relationship type
2. **Update prompts/code** to handle new case
3. **Run test suite** until test passes
4. **Verify** no regressions in other categories

### Maintaining Ground Truth

- **Review Hall of Shame** monthly and add corrections
- **Update expectations** if system capabilities change
- **Add edge cases** discovered in production
- **Document** why certain relationships are/aren't extractable

---

## 📚 References

- **Implementation Plan:** `/home/cytrex/news-microservices/docs/guides/KNOWLEDGE-GRAPH-IMPLEMENTATION-PLAN.md`
- **Validation Plan:** `/home/cytrex/news-microservices/docs/testing/KNOWLEDGE-GRAPH-VALIDATION-PLAN.md`
- **ADR-011:** Idempotency and Event-Carried State Transfer
- **Service Docs:** `/home/cytrex/news-microservices/docs/services/content-analysis-service.md`

---

## 💡 Tips

- **Start small:** Test individual categories before running full suite
- **Use `jq`:** Parse JSON reports easily: `cat summary_report.json | jq '.overall'`
- **Version control:** Commit test results to track performance over time
- **Automate:** Add test suite to CI/CD pipeline
- **Monitor trends:** Track F1 score changes across commits

---

**Last Updated:** 2025-10-23
**Maintainer:** Knowledge Graph Team
**Test Suite Version:** 1.0.0
