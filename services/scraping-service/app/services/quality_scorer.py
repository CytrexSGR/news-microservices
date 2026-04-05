"""
Content Quality Scorer

Evaluates scraped content quality based on multiple criteria:
- Word count and content length
- Metadata completeness
- Text-to-HTML ratio
- Readability indicators
- Structural elements presence
"""
import re
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Quality assessment result"""
    overall_score: float  # 0.0 - 1.0
    word_count_score: float
    metadata_score: float
    structure_score: float
    readability_score: float
    details: Dict[str, Any]


class ContentQualityScorer:
    """
    Evaluates content quality based on multiple factors.

    Scoring weights:
    - Word count: 25%
    - Metadata completeness: 25%
    - Content structure: 25%
    - Readability: 25%
    """

    # Minimum thresholds for good quality
    MIN_WORD_COUNT = 100
    IDEAL_WORD_COUNT = 500
    MAX_WORD_COUNT = 10000

    # Expected metadata fields
    EXPECTED_METADATA = [
        "title",
        "author",
        "publish_date",
        "description",
        "image"
    ]

    # Structural elements that indicate quality
    STRUCTURAL_ELEMENTS = [
        "h1", "h2", "h3",  # Headers
        "p",               # Paragraphs
        "article",         # Article container
        "blockquote",      # Quotes
        "ul", "ol",        # Lists
        "figure", "img"    # Media
    ]

    def __init__(self):
        self._weights = {
            "word_count": 0.25,
            "metadata": 0.25,
            "structure": 0.25,
            "readability": 0.25
        }

    def score_content(
        self,
        content: str,
        html: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Score content quality.

        Args:
            content: Extracted text content
            html: Original HTML (optional, for structure analysis)
            metadata: Extracted metadata (optional)

        Returns:
            QualityScore with detailed breakdown
        """
        # Calculate individual scores
        word_count_score = self._score_word_count(content)
        metadata_score = self._score_metadata(metadata)
        structure_score = self._score_structure(html) if html else 0.5
        readability_score = self._score_readability(content)

        # Calculate weighted overall score
        overall_score = (
            word_count_score * self._weights["word_count"] +
            metadata_score * self._weights["metadata"] +
            structure_score * self._weights["structure"] +
            readability_score * self._weights["readability"]
        )

        details = {
            "word_count": len(content.split()) if content else 0,
            "metadata_fields_present": self._count_metadata_fields(metadata),
            "metadata_fields_expected": len(self.EXPECTED_METADATA),
            "structural_elements_found": self._count_structural_elements(html) if html else 0,
            "avg_sentence_length": self._avg_sentence_length(content),
            "paragraph_count": self._count_paragraphs(content)
        }

        return QualityScore(
            overall_score=round(overall_score, 3),
            word_count_score=round(word_count_score, 3),
            metadata_score=round(metadata_score, 3),
            structure_score=round(structure_score, 3),
            readability_score=round(readability_score, 3),
            details=details
        )

    def _score_word_count(self, content: str) -> float:
        """Score based on word count (0-1)"""
        if not content:
            return 0.0

        word_count = len(content.split())

        if word_count < self.MIN_WORD_COUNT:
            # Below minimum - linear scale from 0
            return word_count / self.MIN_WORD_COUNT * 0.5

        elif word_count <= self.IDEAL_WORD_COUNT:
            # Between min and ideal - scale from 0.5 to 1.0
            return 0.5 + (word_count - self.MIN_WORD_COUNT) / (self.IDEAL_WORD_COUNT - self.MIN_WORD_COUNT) * 0.5

        elif word_count <= self.MAX_WORD_COUNT:
            # Above ideal but not too long - perfect score
            return 1.0

        else:
            # Too long - slight penalty
            return 0.9

    def _score_metadata(self, metadata: Optional[Dict[str, Any]]) -> float:
        """Score based on metadata completeness (0-1)"""
        if not metadata:
            return 0.0

        present = self._count_metadata_fields(metadata)
        total = len(self.EXPECTED_METADATA)

        return present / total

    def _count_metadata_fields(self, metadata: Optional[Dict[str, Any]]) -> int:
        """Count present metadata fields"""
        if not metadata:
            return 0

        count = 0
        for field in self.EXPECTED_METADATA:
            # Check various field name variants
            variants = [
                field,
                f"extracted_{field}",
                field.replace("_", ""),
                f"article_{field}"
            ]
            for variant in variants:
                if variant in metadata and metadata[variant]:
                    count += 1
                    break

        return count

    def _score_structure(self, html: Optional[str]) -> float:
        """Score based on HTML structure (0-1)"""
        if not html:
            return 0.5  # Neutral if no HTML available

        try:
            soup = BeautifulSoup(html, "html.parser")
            found_elements = self._count_structural_elements(html)

            # Score based on variety of structural elements
            # More element types = better structured content
            total_types = len(self.STRUCTURAL_ELEMENTS)

            return min(1.0, found_elements / (total_types * 0.5))

        except Exception as e:
            logger.debug(f"Structure scoring error: {e}")
            return 0.5

    def _count_structural_elements(self, html: Optional[str]) -> int:
        """Count distinct structural element types present"""
        if not html:
            return 0

        try:
            soup = BeautifulSoup(html, "html.parser")
            count = 0

            for element in self.STRUCTURAL_ELEMENTS:
                if soup.find(element):
                    count += 1

            return count
        except Exception:
            return 0

    def _score_readability(self, content: str) -> float:
        """Score based on readability indicators (0-1)"""
        if not content or len(content.split()) < 10:
            return 0.0

        # Calculate based on multiple factors
        scores = []

        # 1. Average sentence length (ideal: 15-25 words)
        avg_sentence = self._avg_sentence_length(content)
        if 15 <= avg_sentence <= 25:
            scores.append(1.0)
        elif 10 <= avg_sentence < 15 or 25 < avg_sentence <= 35:
            scores.append(0.7)
        elif avg_sentence < 10:
            scores.append(0.5)  # Too short, likely fragmented
        else:
            scores.append(0.4)  # Very long sentences

        # 2. Paragraph count (ideal: multiple paragraphs)
        paragraph_count = self._count_paragraphs(content)
        if paragraph_count >= 3:
            scores.append(1.0)
        elif paragraph_count >= 1:
            scores.append(0.6)
        else:
            scores.append(0.3)

        # 3. Text diversity (unique words ratio)
        words = content.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.5:
                scores.append(1.0)
            elif unique_ratio > 0.3:
                scores.append(0.7)
            else:
                scores.append(0.4)

        return sum(scores) / len(scores) if scores else 0.5

    def _avg_sentence_length(self, content: str) -> float:
        """Calculate average sentence length in words"""
        if not content:
            return 0.0

        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        total_words = sum(len(s.split()) for s in sentences)
        return total_words / len(sentences)

    def _count_paragraphs(self, content: str) -> int:
        """Count paragraphs in content"""
        if not content:
            return 0

        # Split by double newlines or single newlines with content
        paragraphs = re.split(r'\n\n+|\n(?=[A-Z])', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip() and len(p.split()) > 3]

        return len(paragraphs)

    def get_quality_category(self, score: float) -> str:
        """
        Get quality category from score.

        Returns: "excellent", "good", "fair", "poor"
        """
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"


# Singleton instance
_quality_scorer: Optional[ContentQualityScorer] = None


def get_quality_scorer() -> ContentQualityScorer:
    """Get singleton quality scorer"""
    global _quality_scorer
    if _quality_scorer is None:
        _quality_scorer = ContentQualityScorer()
    return _quality_scorer
