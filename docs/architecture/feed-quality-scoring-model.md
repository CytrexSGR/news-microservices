# Feed Quality Scoring Model

**Version:** 1.0
**Date:** 2025-11-06
**Status:** Design Document

## Overview

This document defines the comprehensive Feed Quality Scoring Model that aggregates article-level quality metrics from content-analysis-v2 with feed-level operational metrics to provide a holistic quality assessment for RSS/Atom feeds.

## Objectives

1. **Aggregate Article Quality**: Combine individual article quality scores into feed-level metrics
2. **Multi-Dimensional Analysis**: Assess feeds across credibility, objectivity, relevance, and operational dimensions
3. **Actionable Insights**: Provide clear recommendations for feed management
4. **Trend Detection**: Identify improving/declining feed quality over time
5. **Unified Scoring**: Single 0-100 quality score with Admiralty Code rating

## Data Sources

### 1. Content-Analysis-V2 (Article Level)

From `content_analysis_v2.article_quality_scores` table:

```sql
-- Available per article:
- credibility_score (0-100)      -- Source reliability + bias + facts
- objectivity_score (0-100)      -- Subjectivity + political bias
- verification_score (0-100)     -- Evidence + sources + confidence
- relevance_score (0-100)        -- Priority + impact + intelligence value
- completeness_score (0-100)     -- Agent coverage + depth
- consistency_score (0-100)      -- Cross-agent consistency
- overall_quality_score (0-100)  -- Weighted average
- quality_category               -- premium, high_quality, moderate, low, very_low
- confidence                     -- high, medium, low
- red_flags (JSONB)             -- Quality warnings
- data_completeness (0-100)     -- Percentage of expected data
```

### 2. Feed Service (Feed Level)

From `feeds` and related tables:

```sql
-- Operational metrics:
- health_score (0-100)           -- Fetch success rate
- quality_score (0-100)          -- Existing calculated score
- consecutive_failures (int)     -- Reliability indicator
- total_items (int)              -- Volume
- items_last_24h (int)           -- Activity
- fetch_interval (minutes)       -- Update frequency

-- Assessment data:
- credibility_tier               -- tier_1, tier_2, tier_3
- reputation_score (0-100)       -- From research service
- political_bias                 -- From research service
- editorial_standards (JSONB)    -- fact_checking_level, etc.
- trust_ratings (JSONB)          -- media_bias_fact_check, etc.
```

### 3. Feed Items (Article Metadata)

From `feed_items` table:

```sql
- published_at                   -- Freshness calculation
- content_hash                   -- Uniqueness tracking
- scrape_status                  -- success, paywall, error
- scrape_word_count              -- Content richness
```

## Scoring Components

### Component 1: Article Quality (50% weight)

Aggregates article-level quality scores from content-analysis-v2 over last 30 days.

**Metrics:**

```python
# Average article quality scores (last 30 days)
avg_credibility = AVG(article_quality_scores.credibility_score)      # 25%
avg_objectivity = AVG(article_quality_scores.objectivity_score)      # 15%
avg_verification = AVG(article_quality_scores.verification_score)    # 20%
avg_relevance = AVG(article_quality_scores.relevance_score)          # 15%
avg_completeness = AVG(article_quality_scores.completeness_score)    # 15%
avg_consistency = AVG(article_quality_scores.consistency_score)      # 10%

article_quality_score = (
    avg_credibility * 0.25 +
    avg_objectivity * 0.15 +
    avg_verification * 0.20 +
    avg_relevance * 0.15 +
    avg_completeness * 0.15 +
    avg_consistency * 0.10
)
```

**Fallback:** If <10 analyzed articles available, reduce weight to 30% and increase operational weight.

**Quality Category Distribution:**

```python
# Percentage of articles by quality category (last 30 days)
premium_pct = COUNT(quality_category='premium') / total_analyzed
high_quality_pct = COUNT(quality_category='high_quality') / total_analyzed
moderate_pct = COUNT(quality_category='moderate_quality') / total_analyzed
low_quality_pct = COUNT(quality_category='low_quality') / total_analyzed
very_low_pct = COUNT(quality_category='very_low_quality') / total_analyzed

# Bonus/penalty based on distribution
distribution_bonus = (
    premium_pct * 10 +
    high_quality_pct * 5 +
    moderate_pct * 0 +
    low_quality_pct * -5 +
    very_low_pct * -10
)
```

### Component 2: Source Credibility (20% weight)

Combines research service assessment with article-level credibility trends.

**Metrics:**

```python
# Base: Research service assessment (if available)
if feed.reputation_score:
    base_credibility = feed.reputation_score
else:
    base_credibility = 50  # Neutral

# Tier adjustment
tier_bonus = {
    'tier_1': +15,  # Top-tier sources
    'tier_2': 0,    # Solid sources
    'tier_3': -10   # Questionable sources
}
credibility_adjustment = tier_bonus.get(feed.credibility_tier, 0)

# Article-level credibility trend (last 7 vs 30 days)
recent_credibility = AVG(credibility_score WHERE published_at >= NOW() - 7 days)
historical_credibility = AVG(credibility_score WHERE published_at >= NOW() - 30 days)
trend_adjustment = (recent_credibility - historical_credibility)  # -100 to +100

# Editorial standards bonus
editorial_bonus = 0
if editorial_standards.get('fact_checking_level') == 'rigorous':
    editorial_bonus += 5
if editorial_standards.get('corrections_policy') == 'transparent':
    editorial_bonus += 3

source_credibility_score = CLAMP(
    base_credibility + credibility_adjustment + (trend_adjustment * 0.1) + editorial_bonus,
    0, 100
)
```

### Component 3: Operational Reliability (20% weight)

Existing feed-level metrics for fetch reliability and uptime.

**Metrics:**

```python
# From existing FeedQualityScorer
reliability_score = (
    health.success_rate * 0.4 +
    health.uptime_24h * 0.2 +
    health.uptime_7d * 0.2 +
    health.uptime_30d * 0.2
) * 100

# Penalty for consecutive failures
if feed.consecutive_failures > 0:
    penalty = MIN(feed.consecutive_failures * 5, 30)
    reliability_score = MAX(0, reliability_score - penalty)

operational_score = reliability_score
```

### Component 4: Content Freshness & Consistency (10% weight)

How recent and regular are article publications.

**Metrics:**

```python
# Freshness (from existing FeedQualityScorer)
freshness_score = calculate_freshness_score(feed_id)  # 0-100

# Publishing consistency (from existing FeedQualityScorer)
consistency_score = calculate_consistency_score(feed_id)  # 0-100

freshness_consistency_score = (
    freshness_score * 0.6 +
    consistency_score * 0.4
)
```

## Overall Feed Quality Score

```python
# Component weights (configurable)
WEIGHTS = {
    'article_quality': 0.50,      # 50% - Most important
    'source_credibility': 0.20,   # 20% - Trustworthiness
    'operational': 0.20,          # 20% - Reliability
    'freshness_consistency': 0.10  # 10% - Timeliness
}

# Calculate overall score
overall_feed_quality = (
    article_quality_score * WEIGHTS['article_quality'] +
    source_credibility_score * WEIGHTS['source_credibility'] +
    operational_score * WEIGHTS['operational'] +
    freshness_consistency_score * WEIGHTS['freshness_consistency']
)

# Apply distribution bonus (capped at ±5 points)
overall_feed_quality = CLAMP(
    overall_feed_quality + CLAMP(distribution_bonus, -5, 5),
    0, 100
)
```

## Admiralty Code Mapping

Maps overall_feed_quality (0-100) to Admiralty Code (A-F):

| Code | Label | Min Score | Description |
|------|-------|-----------|-------------|
| A | Completely Reliable | 90 | Premium source, excellent quality, highly credible |
| B | Usually Reliable | 75 | Good source, consistent quality, trustworthy |
| C | Fairly Reliable | 60 | Acceptable source, moderate quality |
| D | Not Usually Reliable | 40 | Questionable source, low quality |
| E | Unreliable | 20 | Poor source, very low quality |
| F | Cannot Be Judged | 0 | Insufficient data or never assessed |

## Quality Recommendations

### Tier 1: Excellent Feeds (Score 90-100, Code A)

**Recommendations:**
- "Excellent source. Prioritize in article distribution"
- "Consider for premium content features"
- "Suitable for high-visibility use cases"

**Actions:**
- Increase fetch frequency if articles are time-sensitive
- Enable all analysis features
- Feature in curated lists

### Tier 2: Good Feeds (Score 75-89, Code B)

**Recommendations:**
- "Reliable source. Good for general use"
- "Suitable for most use cases"

**Actions:**
- Standard fetch frequency
- Enable core analysis features
- Include in general feeds

### Tier 3: Acceptable Feeds (Score 60-74, Code C)

**Recommendations:**
- "Acceptable source. Monitor quality trends"
- "Use with context and verification"

**Actions:**
- Monitor for quality degradation
- Consider additional verification steps
- Review article quality distribution

### Tier 4: Questionable Feeds (Score 40-59, Code D)

**Recommendations:**
- "Low-quality source. Use with caution"
- "Consider additional fact-checking"
- "Monitor closely or consider removal"

**Actions:**
- Reduce fetch frequency
- Flag articles for additional review
- Consider pausing if quality continues to decline

### Tier 5: Unreliable Feeds (Score 20-39, Code E)

**Recommendations:**
- "Unreliable source. Not recommended"
- "Consider removing from active feeds"

**Actions:**
- Pause feed or reduce to minimal fetch
- Alert administrators
- Archive or remove

### Tier 6: Unassessed (Score 0-19 or NULL, Code F)

**Recommendations:**
- "Insufficient data to assess quality"
- "Continue collecting data before making decisions"

**Actions:**
- Collect minimum 20 analyzed articles
- Monitor initial quality metrics
- Defer quality-based decisions

## Trend Analysis

Track quality score changes over time to detect improvements or degradation.

**Metrics:**

```python
# Quality score trend (last 7 days vs 30 days)
score_7d = calculate_quality_score(days=7)
score_30d = calculate_quality_score(days=30)
trend = score_7d - score_30d

trend_label = {
    trend > 5: "Improving",
    trend < -5: "Declining",
    else: "Stable"
}

# Article quality trends
credibility_trend = AVG(credibility_score, 7d) - AVG(credibility_score, 30d)
objectivity_trend = AVG(objectivity_score, 7d) - AVG(objectivity_score, 30d)
verification_trend = AVG(verification_score, 7d) - AVG(verification_score, 30d)
```

## Red Flags Detection

Aggregate article-level red flags to feed-level warnings.

**Feed-Level Red Flags:**

```python
# Count articles with red flags (last 30 days)
articles_with_flags = COUNT(article_quality_scores WHERE red_flags IS NOT NULL)
flag_percentage = articles_with_flags / total_analyzed_articles

# Common red flag types
common_flags = {
    'unverified_claims': COUNT(red_flags @> '["unverified_claims"]'),
    'extreme_bias': COUNT(red_flags @> '["extreme_bias"]'),
    'clickbait': COUNT(red_flags @> '["clickbait"]'),
    'low_verification': COUNT(red_flags @> '["low_verification"]'),
    'propaganda_indicators': COUNT(red_flags @> '["propaganda_indicators"]')
}

# Alert if >30% of articles have red flags
if flag_percentage > 0.30:
    recommendation = "High percentage of articles with quality warnings. Review feed credibility."
```

## Data Completeness & Confidence

**Confidence Levels:**

```python
# Article analysis coverage
articles_analyzed = COUNT(article_quality_scores WHERE feed_id = X)
total_articles = COUNT(feed_items WHERE feed_id = X AND published_at >= NOW() - 30 days)
coverage_pct = articles_analyzed / total_articles if total_articles > 0 else 0

# Confidence calculation
if articles_analyzed >= 50 and coverage_pct >= 0.80:
    confidence = "high"
elif articles_analyzed >= 20 and coverage_pct >= 0.50:
    confidence = "medium"
else:
    confidence = "low"

# Data completeness (average from articles)
avg_data_completeness = AVG(article_quality_scores.data_completeness)

# Overall confidence score
confidence_score = (coverage_pct * 0.5 + avg_data_completeness * 0.5) * 100
```

## API Response Format

### `/api/v1/feeds/{feed_id}/quality` Response:

```json
{
  "feed_id": "uuid",
  "feed_name": "Reuters",
  "quality_score": 87.5,
  "admiralty_code": {
    "code": "B",
    "label": "Usually Reliable",
    "color": "blue"
  },
  "confidence": "high",
  "confidence_score": 92.3,
  "trend": "stable",
  "trend_direction": 0,

  "component_scores": {
    "article_quality": {
      "score": 85.0,
      "weight": 0.50,
      "breakdown": {
        "credibility": 88.0,
        "objectivity": 82.0,
        "verification": 90.0,
        "relevance": 78.0,
        "completeness": 85.0,
        "consistency": 87.0
      }
    },
    "source_credibility": {
      "score": 92.0,
      "weight": 0.20,
      "reputation_score": 95,
      "credibility_tier": "tier_1",
      "trend": "stable"
    },
    "operational": {
      "score": 88.0,
      "weight": 0.20,
      "success_rate": 0.98,
      "uptime_7d": 0.99
    },
    "freshness_consistency": {
      "score": 85.0,
      "weight": 0.10,
      "freshness": 90.0,
      "consistency": 75.0
    }
  },

  "quality_distribution": {
    "premium": 0.25,
    "high_quality": 0.55,
    "moderate_quality": 0.15,
    "low_quality": 0.05,
    "very_low_quality": 0.00
  },

  "red_flags": {
    "total_flagged_articles": 3,
    "flag_percentage": 0.05,
    "common_flags": {
      "unverified_claims": 2,
      "extreme_bias": 1
    }
  },

  "trends": {
    "quality_7d_vs_30d": 2.5,
    "credibility_trend": 1.2,
    "objectivity_trend": -0.5,
    "verification_trend": 3.0
  },

  "data_stats": {
    "articles_analyzed": 127,
    "total_articles": 150,
    "coverage_percentage": 84.7,
    "date_range_days": 30
  },

  "recommendations": [
    "Excellent source. Prioritize in article distribution",
    "Consider enabling real-time analysis for time-sensitive content",
    "Verification scores improving - good trend"
  ],

  "calculated_at": "2025-11-06T10:30:00Z"
}
```

## Implementation Notes

### Performance Considerations

1. **Caching**: Cache quality scores for 5 minutes (expensive calculation)
2. **Batch Calculation**: Calculate quality for all feeds nightly, store in `feeds.quality_score`
3. **Incremental Updates**: Recalculate when new articles are analyzed (>5 new articles)
4. **Database Indexes**: Ensure indexes on:
   - `article_quality_scores(article_id)`
   - `feed_items(feed_id, published_at)`
   - `pipeline_executions(article_id, started_at)`

### Database Schema Changes

**Add to `feeds` table:**

```sql
ALTER TABLE feeds
ADD COLUMN quality_score_v2 INTEGER,  -- New comprehensive score
ADD COLUMN quality_confidence VARCHAR(20),  -- high, medium, low
ADD COLUMN quality_trend VARCHAR(20),  -- improving, stable, declining
ADD COLUMN quality_calculated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN article_quality_stats JSONB;  -- Component breakdown
```

### Configuration

**Default Weights (stored in database, configurable):**

```python
QUALITY_WEIGHTS = {
    'article_quality': 0.50,
    'source_credibility': 0.20,
    'operational': 0.20,
    'freshness_consistency': 0.10
}

ARTICLE_QUALITY_WEIGHTS = {
    'credibility': 0.25,
    'objectivity': 0.15,
    'verification': 0.20,
    'relevance': 0.15,
    'completeness': 0.15,
    'consistency': 0.10
}
```

## Success Metrics

1. **Accuracy**: Quality scores correlate with manual expert assessments (target: >85% agreement)
2. **Coverage**: >80% of feeds have quality scores based on analyzed articles
3. **Actionability**: Administrators act on recommendations (target: 70% action rate for low-quality feeds)
4. **Trend Detection**: Early detection of quality degradation (target: 7-day advance warning)
5. **Performance**: Quality calculation <500ms per feed (with caching)

## Future Enhancements

1. **Machine Learning**: Train ML model to predict feed quality from metadata
2. **User Feedback**: Incorporate user ratings into quality scoring
3. **Comparative Analysis**: Compare feeds within same category
4. **Quality Prediction**: Predict future quality based on trends
5. **Anomaly Detection**: Detect sudden quality drops (potential compromised sources)

## References

- ADR-035: Circuit Breaker Pattern
- Content-Analysis-V2 Pipeline Design
- Admiralty Code Configuration (Task 403)
- Feed Quality Scorer (existing implementation)

---

**Document Status:** Draft - Pending Review
**Next Steps:**
1. Review with stakeholders
2. Implement backend service
3. Create database migration
4. Build frontend dashboard
5. Performance testing with production data
