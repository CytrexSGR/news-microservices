# Analyzer Extension Guide

> How to create new analyzers for the OSS (Ontology Suggestion System) Service

## Overview

The OSS Service uses analyzers to detect patterns and issues in the Neo4j knowledge graph. Each analyzer focuses on a specific type of analysis and generates `OntologyChangeProposal` objects.

## Analyzer Architecture

```
app/
├── analyzers/
│   ├── __init__.py
│   ├── base.py              # Optional: Base analyzer class
│   ├── pattern_detector.py  # Detects new entity/relationship patterns
│   └── inconsistency_detector.py  # Detects data quality issues
```

## Creating a New Analyzer

### Step 1: Create the Analyzer Class

```python
# app/analyzers/my_analyzer.py

"""
My Custom Analyzer for OSS.
Detects <describe what it detects>.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.database import Neo4jConnection
from app.config import settings
from app.models.proposal import (
    OntologyChangeProposal,
    ChangeType,
    Severity,
    Evidence,
    ImpactAnalysis
)

logger = logging.getLogger(__name__)


class MyAnalyzer:
    """Detects <specific pattern or issue> in Neo4j."""

    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize analyzer with Neo4j connection.

        Args:
            neo4j: Neo4j database connection
        """
        self.neo4j = neo4j

    async def detect_my_pattern(self) -> List[OntologyChangeProposal]:
        """
        Detect <specific pattern>.

        Returns:
            List of proposals for <action>
        """
        proposals = []

        try:
            # 1. Execute Neo4j query
            query = """
            MATCH (n:Entity)
            WHERE <your conditions>
            RETURN n.property AS property, count(*) AS count
            LIMIT 50
            """

            results = self.neo4j.execute_read(query)

            # 2. Process results and create proposals
            for record in results:
                proposal = self._create_proposal(record)
                if proposal:
                    proposals.append(proposal)

            logger.info(f"Detected {len(proposals)} patterns")

        except Exception as e:
            logger.error(f"Detection failed: {e}", exc_info=True)

        return proposals

    def _create_proposal(
        self,
        record: Dict[str, Any]
    ) -> Optional[OntologyChangeProposal]:
        """
        Create a proposal from detection result.

        Args:
            record: Query result record

        Returns:
            OntologyChangeProposal or None
        """
        try:
            # Generate unique proposal ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            proposal_id = f"OSS_{timestamp}_{short_uuid}"

            # Calculate confidence (0.0 - 1.0)
            confidence = self._calculate_confidence(record)

            # Create proposal
            return OntologyChangeProposal(
                proposal_id=proposal_id,
                change_type=ChangeType.FLAG_INCONSISTENCY,  # or other type
                severity=Severity.MEDIUM,
                title="Descriptive title",
                description="Detailed description of the issue",
                evidence=[
                    Evidence(
                        example_id=str(record.get("node_id")),
                        example_type="NODE",
                        context="Why this is evidence"
                    )
                ],
                occurrence_count=record.get("count", 1),
                confidence=confidence,
                impact_analysis=ImpactAnalysis(
                    affected_entities_count=record.get("count", 0),
                    breaking_change=False,
                    migration_complexity="LOW",
                    benefits=["Benefit 1", "Benefit 2"],
                    risks=["Risk 1"]
                ),
                tags=["my-analyzer", "category"]
            )

        except Exception as e:
            logger.error(f"Failed to create proposal: {e}")
            return None

    def _calculate_confidence(self, record: Dict[str, Any]) -> float:
        """
        Calculate confidence score for detection.

        Args:
            record: Detection result

        Returns:
            Confidence score (0.0 - 1.0)
        """
        # Example: Base confidence + boost from frequency
        count = record.get("count", 1)
        confidence = min(0.5 + (count / 100) * 0.4, 0.95)
        return confidence
```

### Step 2: Register the Analyzer

Add your analyzer to the analysis cycle in `app/api/analysis.py`:

```python
from app.analyzers.my_analyzer import MyAnalyzer

async def run_analysis_cycle(neo4j: Neo4jConnection) -> AnalysisResult:
    # ... existing code ...

    # Initialize your analyzer
    my_analyzer = MyAnalyzer(neo4j)

    # Run detection
    my_patterns = await my_analyzer.detect_my_pattern()

    # Add to all_proposals
    all_proposals = (
        entity_patterns +
        relationship_patterns +
        # ... other patterns ...
        my_patterns  # Add here
    )
```

### Step 3: Add Tests

Create tests in `tests/test_my_analyzer.py`:

```python
import pytest
from unittest.mock import MagicMock
from app.analyzers.my_analyzer import MyAnalyzer
from app.models.proposal import ChangeType


@pytest.fixture
def mock_neo4j():
    neo4j = MagicMock()
    neo4j.execute_read = MagicMock(return_value=[])
    return neo4j


@pytest.fixture
def analyzer(mock_neo4j):
    return MyAnalyzer(mock_neo4j)


class TestMyAnalyzer:

    @pytest.mark.asyncio
    async def test_detect_returns_empty_list_on_no_results(self, analyzer):
        proposals = await analyzer.detect_my_pattern()
        assert proposals == []

    @pytest.mark.asyncio
    async def test_detect_creates_proposals_from_results(self, analyzer, mock_neo4j):
        mock_neo4j.execute_read.return_value = [
            {"node_id": 123, "count": 50}
        ]

        proposals = await analyzer.detect_my_pattern()

        assert len(proposals) == 1
        assert proposals[0].change_type == ChangeType.FLAG_INCONSISTENCY
```

## Available ChangeTypes

| ChangeType | Use Case |
|------------|----------|
| `NEW_ENTITY_TYPE` | Suggest a new entity type based on patterns |
| `NEW_RELATIONSHIP_TYPE` | Suggest a new relationship type |
| `MODIFY_ENTITY_PROPERTIES` | Suggest property changes |
| `FLAG_INCONSISTENCY` | Flag data quality issues |
| `SUGGEST_CONSTRAINT` | Suggest database constraints |
| `MERGE_ENTITIES` | Suggest merging duplicate entities |

## Severity Levels

| Severity | Use Case |
|----------|----------|
| `CRITICAL` | Data quality issues affecting core functionality |
| `HIGH` | Important issues that should be addressed soon |
| `MEDIUM` | Patterns worth investigating |
| `LOW` | Nice-to-have suggestions |

## Best Practices

### 1. Query Optimization

```python
# Good: Use LIMIT and efficient patterns
query = """
MATCH (n:Entity)
WHERE n.entity_type IS NOT NULL
WITH n.entity_type AS type, count(*) AS count
WHERE count >= $min_occurrences
RETURN type, count
ORDER BY count DESC
LIMIT 20
"""

# Bad: Scanning entire graph without limits
query = """
MATCH (n)
RETURN n
"""
```

### 2. Error Handling

Always wrap Neo4j operations in try-except:

```python
try:
    results = self.neo4j.execute_read(query)
except Exception as e:
    logger.error(f"Query failed: {e}", exc_info=True)
    return []  # Return empty list, don't crash
```

### 3. Logging

Use appropriate log levels:

```python
logger.debug(f"Processing {len(results)} results")  # Verbose
logger.info(f"Detected {len(proposals)} patterns")  # Normal
logger.warning(f"Skipped invalid record: {record}") # Potential issue
logger.error(f"Detection failed: {e}")             # Error
```

### 4. Confidence Calculation

Base confidence on evidence quality:

```python
def _calculate_confidence(self, record: Dict[str, Any]) -> float:
    base = 0.5

    # Frequency boost
    count = record.get("count", 1)
    frequency_boost = min(count / 100, 0.3)

    # Quality factors
    has_valid_type = 0.1 if record.get("entity_type") else 0
    has_evidence = 0.1 if record.get("sample_ids") else 0

    return min(base + frequency_boost + has_valid_type + has_evidence, 0.95)
```

### 5. Deduplication Support

Ensure your proposals can be deduplicated by using consistent:
- `title` (include the pattern identifier)
- `tags` (include searchable identifiers)
- `occurrence_count` (for fingerprint generation)

## Integration Checklist

- [ ] Create analyzer class with `__init__(self, neo4j)`
- [ ] Implement async detection method(s)
- [ ] Create proposal with all required fields
- [ ] Add to analysis cycle in `api/analysis.py`
- [ ] Write unit tests
- [ ] Test manually against Neo4j
- [ ] Update this documentation if needed

## Example Analyzers

Study the existing analyzers for patterns:

- `pattern_detector.py` - Entity and relationship pattern detection
- `inconsistency_detector.py` - Data quality issue detection

## Support

If you need help creating an analyzer:

1. Check existing analyzers for patterns
2. Review the `OntologyChangeProposal` model in `app/models/proposal.py`
3. Test queries in Neo4j Browser first
