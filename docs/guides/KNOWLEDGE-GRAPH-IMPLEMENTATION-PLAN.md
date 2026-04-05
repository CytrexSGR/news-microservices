# Knowledge Graph Implementation Plan
## Explizite Beziehungsextraktion für Content Analysis Service

**Erstellt:** 2025-10-23
**Status:** In Progress
**Ziel:** Erweiterung des content-analysis-service um strukturierte Entitätsbeziehungen

---

## 📊 Übersicht

Wir erweitern den bestehenden `AnalysisType.ENTITIES` um explizite Beziehungsextraktion im Format `[Subjekt, Beziehung, Objekt]` mit Konfidenz-Scores und Evidence-Tracking.

### Beispiel-Transformation

**Input-Text:**
```
The Competition Appeal Tribunal in London ruled that Apple abused its monopoly in the UK App Store
```

**Aktuell:** Entitäten: `Competition Appeal Tribunal (ORG)`, `Apple (ORG)`, `London (LOC)`

**Neu:** Beziehungs-Triplets:
```json
[
  ["Competition Appeal Tribunal", "ruled_against", "Apple"],
  ["Apple", "abused_monopoly_in", "UK App Store"],
  ["Competition Appeal Tribunal", "located_in", "London"]
]
```

---

## 🎯 Implementierungs-Phasen

### Phase 1: Prompt & Schema Engineering
- **Dauer:** 2-3 Stunden
- **Risiko:** Low
- **Rollback:** Einfach (nur Prompt-Änderungen)

### Phase 2: Pydantic Models & Validation
- **Dauer:** 3-4 Stunden
- **Risiko:** Low
- **Rollback:** Einfach (Code-Änderungen)

### Phase 3: Database Schema Extension
- **Dauer:** 1-2 Stunden
- **Risiko:** Medium (DB-Migration)
- **Rollback:** Migration zurückrollen

### Phase 4: Integration & Testing
- **Dauer:** 4-5 Stunden
- **Risiko:** Medium
- **Rollback:** Feature-Flag

---

## ✅ Phase 1: Prompt & Schema Engineering

### Task 1.1: Prompt-Erweiterung für ENTITIES
**Datei:** `/home/cytrex/news-microservices/services/content-analysis-service/app/llm/prompts.py`
**Zeilen:** 107-137 (AnalysisType.ENTITIES)

**Änderungen:**

1. **System Prompt erweitern** (Zeile 108-110):
```python
"system": """You are an expert in named entity recognition and relationship extraction.
Extract all relevant entities (people, organizations, locations, dates, events, products).
**CRITICAL**: Extract explicit relationships between entities as structured triplets [Subject, Relationship, Object].

Relationship Extraction Rules:
1. Only extract relationships explicitly mentioned or strongly implied in the text
2. Provide a confidence score (0.0-1.0) for each relationship
3. Include a short text snippet (max 200 chars) as evidence
4. Normalize entity names to their canonical forms
5. Focus on factual, verifiable relationships

Confidence Score Guidelines:
- 0.9-1.0: Explicitly stated ("X works for Y", "A ruled against B")
- 0.7-0.9: Strongly implied by context (job title, court case)
- 0.5-0.7: Reasonable inference from multiple mentions
- 0.3-0.5: Weak inference, possible relationship
- Below 0.3: Do not extract (too speculative)

Supported relationship types:
- works_for: Employment, official position
- located_in: Geographic location
- owns: Ownership, possession
- related_to: General association
- member_of: Membership in organization
- partner_of: Partnership, collaboration
- ruled_against: Legal/judicial decision
- abused_monopoly_in: Antitrust violation
- announced: Official announcement/declaration
""",
```

2. **User Prompt erweitern** (Zeile 112-137):
```python
"user": """Extract entities and their relationships from the following content:

{content}

Return a JSON response with:
{{
    "entities": [
        {{
            "text": "entity name",
            "type": "PERSON|ORGANIZATION|LOCATION|DATE|EVENT|PRODUCT",
            "confidence": 0.0-1.0,
            "mention_count": integer,
            "normalized_text": "canonical form"
        }}
    ],
    "relationships": [
        {{
            "entity1": "exact entity1 text (must match entities list)",
            "entity2": "exact entity2 text (must match entities list)",
            "relationship_type": "works_for|located_in|owns|related_to|member_of|partner_of|ruled_against|abused_monopoly_in|announced",
            "confidence": 0.0-1.0,
            "evidence": "supporting text snippet (max 200 chars)",
            "context": "surrounding sentence for context"
        }}
    ]
}}

**IMPORTANT**:
- Every relationship must reference entities from the entities list
- Use normalized_text for entity references if available
- Confidence scores must reflect how explicitly the relationship is stated
- Evidence must be a direct quote from the content
- Minimum confidence threshold: 0.5
"""
```

**Testing nach Task 1.1:**
```bash
# Test mit Sample-Content
curl -X POST http://localhost:8102/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The Competition Appeal Tribunal in London ruled that Apple abused its monopoly in the UK App Store",
    "analysis_type": "entities"
  }'
```

**Erfolgskriterium:** Response enthält `relationships` Array mit Confidence-Scores

---

### Task 1.2: Neue Relationship-Typen zu Enum hinzufügen
**Datei:** `/home/cytrex/news-microservices/database/models/analysis.py`
**Zeilen:** 103-112 (RelationshipType Enum)

**Änderungen:**
```python
class RelationshipType(PyEnum):
    """Types of entity relationships."""
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    OWNS = "owns"
    RELATED_TO = "related_to"
    MEMBER_OF = "member_of"
    PARTNER_OF = "partner_of"
    # NEW: Extended types for Knowledge Graph
    RULED_AGAINST = "ruled_against"
    ABUSED_MONOPOLY_IN = "abused_monopoly_in"
    ANNOUNCED = "announced"
    NOT_APPLICABLE = "not_applicable"
```

**Database Migration erforderlich:**
```sql
-- Will be handled in Phase 3
```

---

## ✅ Phase 2: Pydantic Models & Validation

### Task 2.1: Erstelle Relationship Extraction Schema
**Neue Datei:** `/home/cytrex/news-microservices/services/content-analysis-service/app/schemas/relationship_extraction.py`

**Vollständiger Inhalt:**
```python
"""
Pydantic schemas for relationship extraction validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from enum import Enum


class RelationshipTypeSchema(str, Enum):
    """Extended relationship types for knowledge graph."""
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    OWNS = "owns"
    RELATED_TO = "related_to"
    MEMBER_OF = "member_of"
    PARTNER_OF = "partner_of"
    RULED_AGAINST = "ruled_against"
    ABUSED_MONOPOLY_IN = "abused_monopoly_in"
    ANNOUNCED = "announced"
    NOT_APPLICABLE = "not_applicable"


class EntitySchema(BaseModel):
    """Entity extraction schema with validation."""
    text: str = Field(..., min_length=1, max_length=500)
    type: Literal["PERSON", "ORGANIZATION", "LOCATION", "DATE", "EVENT", "PRODUCT"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    mention_count: int = Field(default=1, ge=1)
    normalized_text: str = Field(default="", max_length=500)

    @field_validator('normalized_text', mode='before')
    @classmethod
    def default_normalized(cls, v, info):
        """Use original text if normalized not provided."""
        if not v:
            return info.data.get('text', '')
        return v


class RelationshipTriplet(BaseModel):
    """Structured relationship triplet with confidence scoring."""
    entity1: str = Field(..., min_length=1, description="Subject entity")
    entity2: str = Field(..., min_length=1, description="Object entity")
    relationship_type: RelationshipTypeSchema
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: str = Field(..., max_length=200, description="Supporting text")
    context: str | None = Field(default=None, max_length=500)

    def to_triplet_tuple(self) -> tuple[str, str, str]:
        """Convert to simple triplet tuple."""
        return (self.entity1, self.relationship_type.value, self.entity2)


class EntityExtractionResponse(BaseModel):
    """Complete entity extraction response with relationships."""
    entities: List[EntitySchema] = Field(default_factory=list)
    relationships: List[RelationshipTriplet] = Field(default_factory=list)

    @field_validator('relationships')
    @classmethod
    def validate_entity_references(cls, relationships, info):
        """Ensure all relationship entities exist in entities list."""
        if 'entities' not in info.data:
            return relationships

        # Build set of valid entity references
        entity_texts = {e.text for e in info.data['entities']}
        entity_normalized = {e.normalized_text for e in info.data['entities']}
        valid_entities = entity_texts | entity_normalized

        # Validate each relationship
        for rel in relationships:
            if rel.entity1 not in valid_entities:
                raise ValueError(f"entity1 '{rel.entity1}' not in entities list")
            if rel.entity2 not in valid_entities:
                raise ValueError(f"entity2 '{rel.entity2}' not in entities list")

        return relationships

    def get_high_confidence_relationships(self, threshold: float = 0.7) -> List[RelationshipTriplet]:
        """Filter relationships by confidence threshold."""
        return [r for r in self.relationships if r.confidence >= threshold]

    def to_triplet_list(self) -> List[tuple[str, str, str]]:
        """Convert all relationships to triplet tuples."""
        return [r.to_triplet_tuple() for r in self.relationships]
```

**Testing nach Task 2.1:**
```python
# Unit test in tests/test_schemas.py
from app.schemas.relationship_extraction import EntityExtractionResponse

def test_relationship_validation():
    data = {
        "entities": [
            {"text": "Apple", "type": "ORGANIZATION", "confidence": 0.9}
        ],
        "relationships": [
            {
                "entity1": "Apple",
                "entity2": "UK",  # Not in entities - should fail
                "relationship_type": "located_in",
                "confidence": 0.8,
                "evidence": "..."
            }
        ]
    }

    try:
        response = EntityExtractionResponse(**data)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not in entities list" in str(e)
```

---

### Task 2.2: Erstelle Relationship Validator
**Neue Datei:** `/home/cytrex/news-microservices/services/content-analysis-service/app/services/relationship_validator.py`

**Vollständiger Inhalt:**
```python
"""
Relationship quality validation and filtering.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of relationship validation."""
    is_valid: bool
    confidence_adjusted: float
    reason: str | None = None


class RelationshipValidator:
    """Validates extracted relationships for quality."""

    def __init__(self, min_confidence: float = 0.5):
        """
        Initialize validator.

        Args:
            min_confidence: Minimum confidence threshold (0.0-1.0)
        """
        self.min_confidence = min_confidence
        self.validation_stats = {
            'total': 0,
            'passed': 0,
            'failed_confidence': 0,
            'failed_evidence': 0,
            'failed_entity': 0,
            'failed_self_ref': 0
        }

    def validate_triplet(
        self,
        entity1: str,
        relationship: str,
        entity2: str,
        confidence: float,
        evidence: str
    ) -> ValidationResult:
        """
        Validate a single relationship triplet.

        Validation rules:
        1. Confidence above threshold
        2. Evidence is non-empty and substantial
        3. Entity names are valid (not empty, not too long)
        4. No self-relationships
        """
        self.validation_stats['total'] += 1

        # Rule 1: Confidence threshold
        if confidence < self.min_confidence:
            self.validation_stats['failed_confidence'] += 1
            return ValidationResult(
                is_valid=False,
                confidence_adjusted=confidence,
                reason=f"Confidence {confidence:.2f} below threshold {self.min_confidence}"
            )

        # Rule 2: Evidence required
        if not evidence or len(evidence.strip()) < 10:
            self.validation_stats['failed_evidence'] += 1
            adjusted = confidence * 0.8  # Penalty for missing evidence
            return ValidationResult(
                is_valid=adjusted >= self.min_confidence,
                confidence_adjusted=adjusted,
                reason="Missing or insufficient evidence"
            )

        # Rule 3: Entity validation
        if not entity1 or not entity2:
            self.validation_stats['failed_entity'] += 1
            return ValidationResult(
                is_valid=False,
                confidence_adjusted=0.0,
                reason="Empty entity name"
            )

        if len(entity1) > 500 or len(entity2) > 500:
            self.validation_stats['failed_entity'] += 1
            return ValidationResult(
                is_valid=False,
                confidence_adjusted=0.0,
                reason="Entity name too long"
            )

        # Rule 4: No self-relationships
        if entity1.lower().strip() == entity2.lower().strip():
            self.validation_stats['failed_self_ref'] += 1
            return ValidationResult(
                is_valid=False,
                confidence_adjusted=0.0,
                reason="Self-relationship detected"
            )

        # All checks passed
        self.validation_stats['passed'] += 1
        return ValidationResult(
            is_valid=True,
            confidence_adjusted=confidence,
            reason=None
        )

    def filter_relationships(
        self,
        relationships: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter relationships into valid and invalid groups.

        Returns:
            (valid_relationships, invalid_relationships)
        """
        valid = []
        invalid = []

        for rel in relationships:
            result = self.validate_triplet(
                entity1=rel.get('entity1', ''),
                relationship=rel.get('relationship_type', ''),
                entity2=rel.get('entity2', ''),
                confidence=rel.get('confidence', 0.0),
                evidence=rel.get('evidence', '')
            )

            if result.is_valid:
                # Adjust confidence if needed
                if result.confidence_adjusted != rel.get('confidence', 0.0):
                    rel['confidence'] = result.confidence_adjusted
                    rel['confidence_adjusted'] = True
                valid.append(rel)
            else:
                logger.debug(f"Filtered relationship: {result.reason}")
                invalid.append({**rel, 'rejection_reason': result.reason})

        return valid, invalid

    def calculate_metrics(
        self,
        valid: List[Dict[str, Any]],
        invalid: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate quality metrics for relationships."""
        total = len(valid) + len(invalid)
        if total == 0:
            return {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'acceptance_rate': 0.0,
                'avg_confidence': 0.0,
                'high_confidence_count': 0
            }

        avg_confidence = sum(r['confidence'] for r in valid) / len(valid) if valid else 0.0

        return {
            'total': total,
            'valid': len(valid),
            'invalid': len(invalid),
            'acceptance_rate': len(valid) / total,
            'avg_confidence': avg_confidence,
            'high_confidence_count': len([r for r in valid if r['confidence'] >= 0.8]),
            'validation_stats': self.validation_stats
        }

    def reset_stats(self):
        """Reset validation statistics."""
        self.validation_stats = {
            'total': 0,
            'passed': 0,
            'failed_confidence': 0,
            'failed_evidence': 0,
            'failed_entity': 0,
            'failed_self_ref': 0
        }
```

**Testing nach Task 2.2:**
```python
# Unit test in tests/test_relationship_validator.py
from app.services.relationship_validator import RelationshipValidator

def test_validator_confidence_threshold():
    validator = RelationshipValidator(min_confidence=0.7)

    result = validator.validate_triplet(
        entity1="Apple",
        relationship="located_in",
        entity2="California",
        confidence=0.5,  # Below threshold
        evidence="Apple is headquartered in California"
    )

    assert not result.is_valid
    assert "below threshold" in result.reason
```

---

## ✅ Phase 3: Database Schema Extension

### Task 3.1: Add JSONB fields to AnalysisResult
**Datei:** `/home/cytrex/news-microservices/database/models/analysis.py`
**Zeilen:** 196 (nach raw_response)

**Änderungen:**
```python
class AnalysisResult(Base, TimestampMixin):
    # ... existing fields ...

    # Raw response storage
    raw_response = Column(JSONB)

    # NEW: Structured relationship triplets for quick access
    extracted_relationships = Column(
        JSONB,
        comment="Structured relationship triplets [entity1, relation, entity2]"
    )
    relationship_metadata = Column(
        JSONB,
        comment="Confidence scores, evidence, and validation metrics for relationships"
    )
```

---

### Task 3.2: Create Database Migration
**Neue Datei:** `/home/cytrex/news-microservices/database/migrations/add_relationship_fields.sql`

**Vollständiger Inhalt:**
```sql
-- Migration: Add relationship extraction fields to analysis_results
-- Created: 2025-10-23
-- Service: content-analysis-service

-- Add new enum values for RelationshipType
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'RULED_AGAINST';
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'ABUSED_MONOPOLY_IN';
ALTER TYPE relationshiptype ADD VALUE IF NOT EXISTS 'ANNOUNCED';

-- Add JSONB columns for relationship storage
ALTER TABLE analysis_results
ADD COLUMN IF NOT EXISTS extracted_relationships JSONB;

ALTER TABLE analysis_results
ADD COLUMN IF NOT EXISTS relationship_metadata JSONB;

-- Add comments for documentation
COMMENT ON COLUMN analysis_results.extracted_relationships IS
'Structured relationship triplets in format [[entity1, relation, entity2], ...]';

COMMENT ON COLUMN analysis_results.relationship_metadata IS
'Confidence scores, evidence, validation metrics, and quality indicators for relationships';

-- Create index for relationship queries
CREATE INDEX IF NOT EXISTS idx_analysis_has_relationships
ON analysis_results ((extracted_relationships IS NOT NULL))
WHERE analysis_type = 'entities';

-- Create GIN index for JSONB containment queries
CREATE INDEX IF NOT EXISTS idx_analysis_relationships_gin
ON analysis_results USING gin (extracted_relationships)
WHERE analysis_type = 'entities';

-- Optional: Add index on entity_relationships for confidence-based filtering
CREATE INDEX IF NOT EXISTS idx_entity_relationship_confidence
ON entity_relationships(confidence)
WHERE confidence >= 0.7;
```

**Rollback Script:**
```sql
-- Rollback: Remove relationship extraction fields
-- File: /home/cytrex/news-microservices/database/migrations/rollback_relationship_fields.sql

DROP INDEX IF EXISTS idx_analysis_has_relationships;
DROP INDEX IF EXISTS idx_analysis_relationships_gin;
DROP INDEX IF EXISTS idx_entity_relationship_confidence;

ALTER TABLE analysis_results DROP COLUMN IF EXISTS extracted_relationships;
ALTER TABLE analysis_results DROP COLUMN IF EXISTS relationship_metadata;

-- Note: Cannot remove enum values without recreating the type
-- Manual intervention required if enum values need to be removed
```

---

### Task 3.3: Execute Migration
**Commands:**
```bash
# Backup database first
docker exec news-postgres pg_dump -U news_user -d news_mcp \
  -t analysis_results --schema-only \
  > /tmp/backup_analysis_results_schema_$(date +%Y%m%d).sql

# Execute migration
docker exec -i news-postgres psql -U news_user -d news_mcp < \
  /home/cytrex/news-microservices/database/migrations/add_relationship_fields.sql

# Verify migration
docker exec news-postgres psql -U news_user -d news_mcp -c \
  "\d+ analysis_results" | grep relationship
```

**Erfolgskriterium:**
```
extracted_relationships    | jsonb       |           |          |         |
relationship_metadata      | jsonb       |           |          |         |
```

---

## ✅ Phase 4: Integration & Testing

### Task 4.1: Integriere Validation in LLM Provider
**Datei:** `/home/cytrex/news-microservices/services/content-analysis-service/app/llm/openai_provider.py`
**Zeilen:** 90-93 (nach JSON parsing)

**Änderungen:**
```python
# Extract content
raw_content = response.choices[0].message.content
content = self._parse_json_response(raw_content)

# NEW: Validate entity extraction responses with Pydantic
if request.analysis_type == AnalysisType.ENTITIES:
    from app.schemas.relationship_extraction import EntityExtractionResponse
    try:
        validated = EntityExtractionResponse(**content)
        content = validated.model_dump()  # Back to dict for database
        logger.info(
            f"Entity validation: {len(validated.entities)} entities, "
            f"{len(validated.relationships)} relationships"
        )
    except ValueError as e:
        logger.warning(
            f"Entity validation failed: {e}, using raw response. "
            "This may indicate LLM output quality issues."
        )
        # Continue with raw response, log for monitoring
```

**Gleiche Änderung in:**
- `app/llm/anthropic_provider.py` (ähnliche Position)
- `app/llm/gemini_provider.py` (ähnliche Position)

---

### Task 4.2: Integriere Validator in Message Handler
**Datei:** `/home/cytrex/news-microservices/services/content-analysis-service/app/services/message_handler.py`

**Finde die Stelle wo Entity-Extraktion stattfindet** (ca. Zeile 200-300, nach LLM-Call):

**Änderungen:**
```python
# After LLM response for entities
if analysis_type == AnalysisType.ENTITIES:
    entities_data = llm_response.content

    # NEW: Validate and filter relationships
    from app.services.relationship_validator import RelationshipValidator

    relationships = entities_data.get('relationships', [])

    if relationships:
        # Validate relationships
        validator = RelationshipValidator(min_confidence=0.5)
        valid_rels, invalid_rels = validator.filter_relationships(relationships)
        metrics = validator.calculate_metrics(valid_rels, invalid_rels)

        logger.info(
            f"📊 Relationship validation for article {item_id}: "
            f"{metrics['valid']}/{metrics['total']} valid "
            f"(acceptance rate: {metrics['acceptance_rate']:.1%}, "
            f"avg confidence: {metrics['avg_confidence']:.2f})"
        )

        # Store filtered relationships
        entities_data['relationships'] = valid_rels
        entities_data['relationship_metadata'] = {
            'metrics': metrics,
            'invalid_count': len(invalid_rels),
            'validation_timestamp': datetime.utcnow().isoformat()
        }

        # Extract triplet list for quick access
        triplets = [
            [r['entity1'], r['relationship_type'], r['entity2']]
            for r in valid_rels
        ]
        entities_data['triplet_list'] = triplets

        # Update Prometheus metrics
        from app.core.metrics import (
            relationship_extraction_total,
            relationship_confidence_distribution
        )
        relationship_extraction_total.labels(status='valid').inc(len(valid_rels))
        relationship_extraction_total.labels(status='invalid').inc(len(invalid_rels))

        for rel in valid_rels:
            relationship_confidence_distribution.observe(rel['confidence'])
```

---

### Task 4.3: Store Relationships in Database
**Datei:** `/home/cytrex/news-microservices/services/content-analysis-service/app/services/message_handler.py`
**Zeilen:** Beim Speichern der AnalysisResult

**Änderungen:**
```python
# When creating AnalysisResult record
analysis_result = AnalysisResult(
    article_id=item_id,
    analysis_type=analysis_type,
    model_used=model_name,
    model_provider=ModelProvider.OPENAI,
    status=AnalysisStatus.COMPLETED,
    total_cost=llm_response.cost,
    total_tokens=llm_response.total_tokens,
    input_tokens=llm_response.input_tokens,
    output_tokens=llm_response.output_tokens,
    processing_time_ms=llm_response.latency_ms,
    raw_response=llm_response.content,
    # NEW: Store relationship data
    extracted_relationships=entities_data.get('triplet_list'),
    relationship_metadata=entities_data.get('relationship_metadata'),
    started_at=start_time,
    completed_at=datetime.utcnow()
)
```

---

### Task 4.4: Add Prometheus Metrics
**Datei:** `/home/cytrex/news-microservices/services/content-analysis-service/app/core/metrics.py`

**Füge hinzu (am Ende der Datei):**
```python
# Relationship extraction metrics
relationship_extraction_total = Counter(
    'relationship_extraction_total',
    'Total relationships extracted',
    ['status']  # valid, invalid
)

relationship_confidence_distribution = Histogram(
    'relationship_confidence',
    'Distribution of relationship confidence scores',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

relationship_validation_failures = Counter(
    'relationship_validation_failures_total',
    'Relationship validation failures by reason',
    ['reason']  # confidence, evidence, entity, self_ref
)
```

---

### Task 4.5: Create Integration Tests
**Neue Datei:** `/home/cytrex/news-microservices/services/content-analysis-service/tests/test_relationship_extraction_integration.py`

**Vollständiger Inhalt:**
```python
"""
Integration tests for relationship extraction.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.message_handler import process_analysis_message
from database.models import AnalysisType


@pytest.mark.asyncio
async def test_relationship_extraction_full_flow():
    """Test complete flow from message to database."""

    # Mock message
    message = {
        "item_id": "test-article-123",
        "content": "The Competition Appeal Tribunal in London ruled that Apple abused its monopoly.",
        "analysis_config": {
            "enable_entities": True
        }
    }

    # Mock LLM response
    mock_llm_response = {
        "entities": [
            {
                "text": "Competition Appeal Tribunal",
                "type": "ORGANIZATION",
                "confidence": 0.95,
                "mention_count": 1
            },
            {
                "text": "London",
                "type": "LOCATION",
                "confidence": 0.9,
                "mention_count": 1
            },
            {
                "text": "Apple",
                "type": "ORGANIZATION",
                "confidence": 0.95,
                "mention_count": 1
            }
        ],
        "relationships": [
            {
                "entity1": "Competition Appeal Tribunal",
                "entity2": "Apple",
                "relationship_type": "ruled_against",
                "confidence": 0.95,
                "evidence": "The Competition Appeal Tribunal ruled that Apple abused its monopoly"
            },
            {
                "entity1": "Competition Appeal Tribunal",
                "entity2": "London",
                "relationship_type": "located_in",
                "confidence": 0.8,
                "evidence": "The Competition Appeal Tribunal in London"
            }
        ]
    }

    with patch('app.services.message_handler.llm_service.analyze') as mock_analyze:
        mock_analyze.return_value = Mock(
            content=mock_llm_response,
            cost=0.001,
            total_tokens=500,
            latency_ms=1500
        )

        # Process message
        result = await process_analysis_message(message)

        # Assertions
        assert result is not None
        assert 'extracted_relationships' in result
        assert len(result['extracted_relationships']) == 2
        assert result['relationship_metadata']['metrics']['valid'] == 2
        assert result['relationship_metadata']['metrics']['acceptance_rate'] == 1.0


@pytest.mark.asyncio
async def test_relationship_validation_filters_low_confidence():
    """Test that low confidence relationships are filtered."""

    relationships = [
        {
            "entity1": "Apple",
            "entity2": "California",
            "relationship_type": "located_in",
            "confidence": 0.3,  # Below threshold
            "evidence": "Maybe in California"
        }
    ]

    from app.services.relationship_validator import RelationshipValidator

    validator = RelationshipValidator(min_confidence=0.5)
    valid, invalid = validator.filter_relationships(relationships)

    assert len(valid) == 0
    assert len(invalid) == 1
    assert "below threshold" in invalid[0]['rejection_reason']


@pytest.mark.asyncio
async def test_pydantic_validation_catches_invalid_entity_references():
    """Test that Pydantic catches entity reference mismatches."""

    from app.schemas.relationship_extraction import EntityExtractionResponse

    data = {
        "entities": [
            {"text": "Apple", "type": "ORGANIZATION", "confidence": 0.9}
        ],
        "relationships": [
            {
                "entity1": "Apple",
                "entity2": "Google",  # Not in entities list!
                "relationship_type": "partner_of",
                "confidence": 0.8,
                "evidence": "Apple and Google partnered"
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        EntityExtractionResponse(**data)

    assert "not in entities list" in str(exc_info.value)
```

---

## 🧪 Testing Strategy

### Unit Tests
```bash
# Test schemas
cd /home/cytrex/news-microservices/services/content-analysis-service
pytest tests/test_schemas.py -v

# Test validator
pytest tests/test_relationship_validator.py -v

# Test integration
pytest tests/test_relationship_extraction_integration.py -v
```

### Manual API Testing
```bash
# Test with real article
curl -X POST http://localhost:8102/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @test_data/apple_ruling.json

# Check database
docker exec -it news-postgres psql -U news_user -d news_mcp -c "
SELECT
    article_id,
    jsonb_array_length(extracted_relationships) as rel_count,
    relationship_metadata->'metrics'->>'acceptance_rate' as acceptance_rate
FROM analysis_results
WHERE analysis_type = 'entities'
  AND extracted_relationships IS NOT NULL
ORDER BY created_at DESC
LIMIT 5;
"
```

### Performance Testing
```bash
# Measure latency impact
time curl -X POST http://localhost:8102/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "content": "$(cat test_data/long_article.txt)",
    "analysis_type": "entities"
  }'
```

---

## 📊 Success Criteria

### Phase 1: Prompt & Schema ✅
- [ ] Prompt erweitert mit Relationship-Regeln
- [ ] RelationshipType Enum erweitert
- [ ] API-Response enthält relationships Array

### Phase 2: Validation ✅
- [ ] Pydantic Schema validiert Entity-Referenzen
- [ ] RelationshipValidator filtert low-confidence
- [ ] Unit Tests pass (100% coverage)

### Phase 3: Database ✅
- [ ] Migration erfolgreich ausgeführt
- [ ] Indizes erstellt
- [ ] Relationships werden gespeichert

### Phase 4: Integration ✅
- [ ] LLM Provider validiert mit Pydantic
- [ ] Message Handler nutzt Validator
- [ ] Prometheus Metrics funktionieren
- [ ] Integration Tests pass

### Quality Metrics (nach 1 Woche Production)
- [ ] **Precision:** ≥75% bei Confidence ≥ 0.7
- [ ] **Acceptance Rate:** ≥60%
- [ ] **Latency Increase:** ≤300ms
- [ ] **Zero DB Errors:** Keine FK-Violations

---

## 🚨 Rollback Plan

### Immediate Rollback (< 1 hour)
```bash
# 1. Disable feature via config
docker exec news-content-analysis sed -i 's/ENABLE_RELATIONSHIP_EXTRACTION=true/ENABLE_RELATIONSHIP_EXTRACTION=false/' /app/.env
docker restart news-content-analysis

# 2. Rollback database
docker exec -i news-postgres psql -U news_user -d news_mcp < \
  /home/cytrex/news-microservices/database/migrations/rollback_relationship_fields.sql

# 3. Revert code
cd /home/cytrex/news-microservices
git revert <commit-hash>
docker compose up -d --build content-analysis-service
```

---

## 📝 Monitoring & Alerts

### Key Metrics to Watch
```promql
# Relationship extraction rate
rate(relationship_extraction_total[5m])

# Acceptance rate (should be >0.6)
relationship_extraction_total{status="valid"} /
  (relationship_extraction_total{status="valid"} + relationship_extraction_total{status="invalid"})

# Average confidence (should be >0.7)
histogram_quantile(0.5, relationship_confidence)

# Validation failures
rate(relationship_validation_failures_total[5m])
```

### Grafana Dashboard
- Create panel: "Relationship Extraction Rate"
- Create panel: "Confidence Distribution"
- Create panel: "Validation Failure Reasons"

---

## 🎯 Next Steps (After Phase 4)

1. **Neo4j Integration:** Export relationships to graph database
2. **Entity Linking:** Wikidata/DBpedia linkage
3. **Relationship Inference:** ML-based relationship prediction
4. **Knowledge Graph API:** Query endpoint for graph traversal
5. **UI Visualization:** D3.js relationship graph in frontend

---

**Status Tracking:**
- [ ] Phase 1: Prompt & Schema (2-3h)
- [ ] Phase 2: Validation (3-4h)
- [ ] Phase 3: Database (1-2h)
- [ ] Phase 4: Integration (4-5h)

**Total Estimated Time:** 10-14 hours
**Start Date:** 2025-10-23
**Target Completion:** 2025-10-25
