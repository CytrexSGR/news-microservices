# news-intelligence-common

Shared library for News Intelligence features in the news-microservices platform.

## Installation

```bash
# From project root
pip install -e libs/news-intelligence-common

# With dev dependencies
pip install -e "libs/news-intelligence-common[dev]"
```

## Components

### SimHasher

Near-duplicate detection using SimHash fingerprinting.

```python
from news_intelligence_common import SimHasher

hasher = SimHasher()

# Compute fingerprint
fp = SimHasher.compute_fingerprint("Breaking news article text")

# Check for duplicates
if hasher.is_duplicate(fp1, fp2):
    print("Duplicate detected!")
elif hasher.is_near_duplicate(fp1, fp2):
    print("Near-duplicate detected!")
```

### TimeDecayScorer

Time-weighted relevance scoring with exponential decay.

```python
from datetime import datetime, timedelta, timezone
from news_intelligence_common import TimeDecayScorer

scorer = TimeDecayScorer(decay_rate=0.05)

# Calculate score
now = datetime.now(timezone.utc)
published = now - timedelta(hours=12)
score = scorer.calculate_score(1.0, published, now)
print(f"Relevance: {score:.2f}")  # ~0.55

# Rank articles
articles = [...]
ranked = scorer.rank_articles(articles)
```

### EventEnvelope

Standardized event messaging for RabbitMQ.

```python
from news_intelligence_common import EventEnvelope

envelope = EventEnvelope(
    event_type="article.created",
    payload={"article_id": "123", "title": "Test Article"},
)

# Serialize for publishing
message = envelope.to_dict()
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=news_intelligence_common --cov-report=term-missing

# Type checking
mypy src/news_intelligence_common/
```

## License

MIT
