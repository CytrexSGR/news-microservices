"""
Ground Truth 2.0: Comprehensive test case solution model for DIA validation.

This module defines Pydantic models for adversarial test cases that extend
traditional "correct answer" ground truth to include:
- Expected uncertainty quantification scores
- Expected uncertainty factors
- Ideal verification workflow
- Expected improvements after verification
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


# ============================================================================
# Challenge Type Definitions
# ============================================================================

class ChallengeType(str, Enum):
    """Types of adversarial challenges."""
    FACTUAL_ERROR = "factual_error"
    AMBIGUITY = "ambiguity"
    KNOWLEDGE_GAP = "knowledge_gap"
    MISLEADING_CONTEXT = "misleading_context"
    TEMPORAL_CONFUSION = "temporal_confusion"
    ENTITY_CONFUSION = "entity_confusion"


# ============================================================================
# Test Article Model
# ============================================================================

class TestArticle(BaseModel):
    """The challenging article to analyze."""
    title: str
    content: str = Field(..., min_length=400, max_length=4000)  # 400-600 words ≈ 2400-3600 chars
    source: str
    url: str
    published_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Tesla Announces Record Q3 Profits",
                "content": "Tesla Inc. announced record Q3 2024 profits of $5 billion...",
                "source": "Tech Financial Times",
                "url": "https://example.com/tesla-q3-profits",
                "published_at": "2024-10-20T10:00:00Z"
            }
        }
    }


# ============================================================================
# Expected Analysis Results
# ============================================================================

class ExpectedEntity(BaseModel):
    """Expected entity extraction result."""
    text: str
    type: str  # PERSON, ORGANIZATION, LOCATION, etc.
    start_char: int
    end_char: int


class ExpectedRelationship(BaseModel):
    """Expected relationship extraction result."""
    source_entity: str
    target_entity: str
    relationship_type: str
    confidence: float = Field(ge=0.0, le=1.0)


class ExpectedSentiment(BaseModel):
    """Expected sentiment analysis result."""
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str


class CorrectAnalysis(BaseModel):
    """The correct analysis results for this article."""
    entities: List[ExpectedEntity]
    relationships: List[ExpectedRelationship]
    sentiment: ExpectedSentiment
    category: str
    summary: str = Field(..., max_length=500)
    facts: List[str]
    topics: List[str]
    keywords: List[str]


# ============================================================================
# UQ Expectations
# ============================================================================

class UQExpectations(BaseModel):
    """Expected UQ metrics for this test case."""
    confidence_range_min: float = Field(ge=0.0, le=1.0)
    confidence_range_max: float = Field(ge=0.0, le=1.0)
    expected_uncertainty_factors: List[str] = Field(
        ...,
        description="Specific uncertainty factors that should be detected"
    )
    should_trigger_verification: bool
    expected_entropy_range: Optional[tuple[float, float]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "confidence_range_min": 0.65,
                "confidence_range_max": 0.80,
                "expected_uncertainty_factors": [
                    "Low-confidence tokens detected in financial claims",
                    "Numerical inconsistency detected"
                ],
                "should_trigger_verification": True,
                "expected_entropy_range": [1.2, 1.8]
            }
        }
    }


# ============================================================================
# Verification Plan
# ============================================================================

class ExpectedCorrection(BaseModel):
    """Expected correction after verification."""
    field: str  # Which analysis field to correct
    original: str  # Original (incorrect) value
    corrected: str  # Correct value after verification
    confidence_improvement: float = Field(
        ge=0.0,
        le=1.0,
        description="Expected increase in UQ confidence after correction"
    )


class VerificationPlan(BaseModel):
    """Ideal verification workflow for this test case."""
    priority: Literal["low", "medium", "high", "critical"]
    verification_methods: List[str] = Field(
        ...,
        description="Methods that should be used for verification"
    )
    external_sources: List[str] = Field(
        ...,
        description="External sources to consult for verification"
    )
    expected_corrections: List[ExpectedCorrection]
    estimated_verification_time_seconds: int = Field(
        gt=0,
        description="Expected time to complete verification"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "priority": "high",
                "verification_methods": [
                    "cross_reference_financial_data",
                    "verify_entity_relationships"
                ],
                "external_sources": [
                    "Tesla Q3 2024 earnings report (SEC)",
                    "Reuters financial database"
                ],
                "expected_corrections": [
                    {
                        "field": "facts",
                        "original": "Tesla Q3 profits: $5B",
                        "corrected": "Tesla Q3 profits: $4.2B",
                        "confidence_improvement": 0.15
                    }
                ],
                "estimated_verification_time_seconds": 120
            }
        }
    }


# ============================================================================
# Complete Ground Truth 2.0
# ============================================================================

class GroundTruth(BaseModel):
    """
    Ground Truth 2.0: Complete solution set for adversarial test case.

    This model contains not just the correct answers, but also:
    - Expected UQ behavior (what uncertainty should be detected)
    - Ideal verification workflow (how DIA should respond)
    - Expected improvements (how quality should improve after verification)
    """
    challenge_type: ChallengeType
    challenge_description: str = Field(
        ...,
        description="Human-readable explanation of what makes this challenging"
    )
    difficulty_level: Literal[1, 2, 3, 4, 5] = Field(
        ...,
        description="Difficulty: 1=Easy, 5=Extremely Hard"
    )

    # Expected UQ behavior
    uq_expectations: UQExpectations

    # Correct analysis results
    correct_analysis: CorrectAnalysis

    # Ideal verification workflow
    verification_plan: VerificationPlan

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "red_team_agent"

    model_config = {
        "json_schema_extra": {
            "example": {
                "challenge_type": "factual_error",
                "challenge_description": "Financial figure is inflated by 19%",
                "difficulty_level": 3,
                "uq_expectations": "...",
                "correct_analysis": "...",
                "verification_plan": "..."
            }
        }
    }


# ============================================================================
# Complete Test Case
# ============================================================================

class AdversarialTestCase(BaseModel):
    """
    Complete adversarial test case: Article + Ground Truth 2.0.

    This is the top-level model that gets saved as JSON.
    """
    test_case_id: str = Field(
        ...,
        description="Unique identifier (e.g., 'factual_error_001')"
    )
    article: TestArticle
    ground_truth: GroundTruth

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generator_model: str = "gpt-4-turbo-preview"
    generator_version: str = "1.0.0"

    def save_to_file(self, output_dir: str) -> Path:
        """Save test case as JSON file."""
        output_path = Path(output_dir) / f"{self.test_case_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

        return output_path

    @classmethod
    def load_from_file(cls, file_path: str) -> "AdversarialTestCase":
        """Load test case from JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


# ============================================================================
# Red Team Agent System Prompt
# ============================================================================

RED_TEAM_SYSTEM_PROMPT = """
You are a "Red Team" AI agent for the DIA (Dynamic Intelligence Augmentation) system.

Your mission: Generate challenging test articles that expose weaknesses in AI analysis systems.

## Your Capabilities

1. **Factual Errors**: Inject subtle factual inconsistencies
   - Example: "Tesla announced Q3 profits of $5B" (when it was actually $4.2B)

2. **Ambiguity**: Create genuinely ambiguous statements
   - Example: "The bank was robbed near the river bank"

3. **Knowledge Gaps**: Reference recent events that might not be in training data
   - Example: "Following the 2024 AI Summit regulations..."

4. **Misleading Context**: True facts in misleading contexts
   - Example: "Crime increased 50%" (true, but from 2 to 3 incidents in a small town)

5. **Temporal Confusion**: Ambiguous temporal references
   - Example: "After the meeting last Tuesday, which was postponed from Monday..."

6. **Entity Confusion**: Identity ambiguity
   - Example: "Johnson met with Johnson to discuss the Johnson report"

## Output Format

Generate a JSON object with the following structure (EXACT SCHEMA):

{
  "article": {
    "title": "Engaging news title",
    "content": "400-600 word article with embedded challenges",
    "source": "Fictional source name",
    "url": "https://example.com/article",
    "published_at": "2024-10-24T10:00:00Z"
  },
  "ground_truth": {
    "challenge_type": "factual_error",
    "challenge_description": "What makes this article challenging",
    "difficulty_level": 3,
    "uq_expectations": {
      "confidence_range_min": 0.65,
      "confidence_range_max": 0.80,
      "expected_uncertainty_factors": [
        "Low-confidence tokens detected in financial claims",
        "Inconsistent entity relationships"
      ],
      "should_trigger_verification": true,
      "expected_entropy_range": [1.2, 1.8]
    },
    "correct_analysis": {
      "entities": [
        {"text": "Tesla Inc.", "type": "ORGANIZATION", "start_char": 0, "end_char": 10}
      ],
      "relationships": [
        {
          "source_entity": "Elon Musk",
          "target_entity": "Tesla Inc.",
          "relationship_type": "CEO_OF",
          "confidence": 0.99
        }
      ],
      "sentiment": {
        "sentiment": "positive",
        "confidence": 0.92,
        "explanation": "Strong performance metrics"
      },
      "category": "business",
      "summary": "Brief summary of article",
      "facts": [
        "Key fact 1",
        "Key fact 2"
      ],
      "topics": ["topic1", "topic2"],
      "keywords": ["keyword1", "keyword2"]
    },
    "verification_plan": {
      "priority": "high",
      "verification_methods": [
        "cross_reference_financial_data",
        "verify_entity_relationships"
      ],
      "external_sources": [
        "Tesla Q3 2024 earnings report",
        "SEC filings database"
      ],
      "expected_corrections": [
        {
          "field": "facts",
          "original": "Tesla Q3 profits: $5B",
          "corrected": "Tesla Q3 profits: $4.2B",
          "confidence_improvement": 0.15
        }
      ],
      "estimated_verification_time_seconds": 120
    },
    "created_at": "2024-10-24T10:00:00Z",
    "created_by": "red_team_agent"
  }
}

## Quality Requirements

1. **Subtlety**: Errors should not be obvious to simple regex checks
2. **Realism**: Articles should look like real news content
3. **Diversity**: Each test case should challenge different aspects
4. **Measurability**: Ground truth must enable objective scoring

## Challenge Categories (Generate diverse mix)

- **Financial Data**: Numbers, percentages, financial relationships
- **Geopolitical**: International relations, conflicting sources
- **Scientific**: Technical claims, research findings
- **Temporal**: Date/time ambiguities, causality
- **Entity**: Identity confusion, role ambiguity

Generate a single, high-quality test case now. Return ONLY the JSON object, no additional text.
"""
