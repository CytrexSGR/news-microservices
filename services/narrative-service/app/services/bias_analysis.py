"""
Bias Analysis Service - Detect political/ideological bias in text
Uses linguistic markers, sentiment, and framing to estimate bias
"""
import re
from typing import Dict, Any, List, Optional
from collections import Counter


class BiasAnalysisService:
    """
    Analyze text for political/ideological bias

    Bias spectrum: -1 (left) to +1 (right)
    - left: Strong progressive/liberal bias
    - center-left: Moderate progressive bias
    - center: Neutral/balanced
    - center-right: Moderate conservative bias
    - right: Strong conservative bias
    """

    # Language indicators for bias detection
    LEFT_INDICATORS = [
        r"\b(progressive|liberal|equality|justice|rights|reform|change)\b",
        r"\b(inequality|discrimination|oppression|systemic)\b",
        r"\b(climate|environment|renewable|sustainable)\b",
        r"\b(healthcare|education|welfare|safety net)\b",
    ]

    RIGHT_INDICATORS = [
        r"\b(conservative|traditional|freedom|liberty|free market)\b",
        r"\b(law and order|border|security|national)\b",
        r"\b(tax|regulation|government overreach|bureaucracy)\b",
        r"\b(family values|faith|patriot|constitution)\b",
    ]

    # Emotional/loaded language
    EMOTIONAL_POSITIVE = [
        r"\b(amazing|incredible|fantastic|wonderful|excellent|brilliant)\b",
        r"\b(hero|triumph|success|victory|achievement)\b",
    ]

    EMOTIONAL_NEGATIVE = [
        r"\b(terrible|horrible|awful|disaster|catastrophe|crisis)\b",
        r"\b(threat|danger|attack|destroy|devastate)\b",
    ]

    def __init__(self):
        pass

    def analyze_bias(self, text: str, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze text for political/ideological bias

        Returns:
            Dictionary with bias_score, bias_label, sentiment, language_indicators, perspective
        """
        # Count left/right indicators
        left_count = self._count_patterns(text, self.LEFT_INDICATORS)
        right_count = self._count_patterns(text, self.RIGHT_INDICATORS)

        # Calculate bias score (-1 to +1)
        total = left_count + right_count
        if total == 0:
            bias_score = 0.0
        else:
            bias_score = (right_count - left_count) / total

        # Determine bias label
        bias_label = self._get_bias_label(bias_score)

        # Analyze sentiment
        sentiment = self._analyze_sentiment(text)

        # Extract language indicators
        language_indicators = {
            "left_markers": left_count,
            "right_markers": right_count,
            "emotional_positive": self._count_patterns(text, self.EMOTIONAL_POSITIVE),
            "emotional_negative": self._count_patterns(text, self.EMOTIONAL_NEGATIVE),
        }

        # Determine perspective
        perspective = self._determine_perspective(text)

        return {
            "bias_score": round(bias_score, 3),
            "bias_label": bias_label,
            "sentiment": round(sentiment, 3),
            "language_indicators": language_indicators,
            "perspective": perspective,
            "source": source,
        }

    def _count_patterns(self, text: str, patterns: List[str]) -> int:
        """Count occurrences of regex patterns in text"""
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count

    def _get_bias_label(self, bias_score: float) -> str:
        """Convert bias score to label"""
        if bias_score <= -0.5:
            return "left"
        elif bias_score <= -0.15:
            return "center-left"
        elif bias_score >= 0.5:
            return "right"
        elif bias_score >= 0.15:
            return "center-right"
        else:
            return "center"

    def _analyze_sentiment(self, text: str) -> float:
        """
        Simple sentiment analysis based on positive/negative language

        Returns: -1 (negative) to +1 (positive)
        """
        positive_count = self._count_patterns(text, self.EMOTIONAL_POSITIVE)
        negative_count = self._count_patterns(text, self.EMOTIONAL_NEGATIVE)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        return (positive_count - negative_count) / total

    def _determine_perspective(self, text: str) -> str:
        """
        Determine if text is pro, con, or neutral on a topic

        Returns: "pro", "con", or "neutral"
        """
        # Look for support/opposition language
        support_patterns = [
            r"\b(support|favor|endorse|advocate|promote|defend)\b",
            r"\b(important|necessary|essential|vital|critical)\b",
        ]

        oppose_patterns = [
            r"\b(oppose|against|reject|criticize|condemn)\b",
            r"\b(problem|issue|concern|worry|danger)\b",
        ]

        support_count = self._count_patterns(text, support_patterns)
        oppose_count = self._count_patterns(text, oppose_patterns)

        if support_count > oppose_count * 1.5:
            return "pro"
        elif oppose_count > support_count * 1.5:
            return "con"
        else:
            return "neutral"

    def compare_sources(self, texts_with_sources: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Compare bias across multiple sources

        Args:
            texts_with_sources: List of {"text": "...", "source": "..."}

        Returns:
            Comparison analysis
        """
        source_analyses = {}

        for item in texts_with_sources:
            text = item["text"]
            source = item["source"]

            analysis = self.analyze_bias(text, source)
            source_analyses[source] = analysis

        # Calculate spectrum distribution
        spectrum = {
            "left": 0,
            "center-left": 0,
            "center": 0,
            "center-right": 0,
            "right": 0,
        }

        for analysis in source_analyses.values():
            spectrum[analysis["bias_label"]] += 1

        return {
            "source_count": len(texts_with_sources),
            "source_analyses": source_analyses,
            "spectrum_distribution": spectrum,
            "avg_bias_score": sum(a["bias_score"] for a in source_analyses.values()) / len(source_analyses) if source_analyses else 0,
            "avg_sentiment": sum(a["sentiment"] for a in source_analyses.values()) / len(source_analyses) if source_analyses else 0,
        }


# Global service instance
bias_analysis_service = BiasAnalysisService()
