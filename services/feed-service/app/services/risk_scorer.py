# File: services/feed-service/app/services/risk_scorer.py
"""
Risk Scoring Service for SITREP Content.

Analyzes content for risky patterns that may require human review
before publication. Returns a risk score (0.0-1.0) and list of flags
indicating which patterns matched.

Risk Patterns and Weights:
- Legal language ("lawsuit", "litigation", "settlement") - weight 0.3
- Allegations ("accused", "alleged", "scandal") - weight 0.25
- Financial data ("earnings", "revenue", "profit") - weight 0.15
- Investment advice ("buy", "sell", "target price") - weight 0.2
- Unverified claims ("reportedly", "sources say", "rumored") - weight 0.1

Usage:
    from app.services.risk_scorer import get_risk_scorer

    scorer = get_risk_scorer()
    result = scorer.calculate("Content to analyze...")

    print(result.risk_score)  # 0.0 - 1.0
    print(result.flags)       # ["legal_language", "allegations"]
    print(result.level)       # "low" / "medium" / "high"
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# Risk patterns with weights and detection terms
RISK_PATTERNS: Dict[str, Dict[str, Any]] = {
    "legal_language": {
        "weight": 0.3,
        "patterns": [
            r"\blawsuit\b",
            r"\blitigation\b",
            r"\bsettlement\b",
            r"\blitigate\b",
            r"\bsue\b",
            r"\bsuing\b",
            r"\blegal\s+action\b",
            r"\bcourt\s+case\b",
        ],
        "description": "Legal terms that may require verification",
    },
    "allegations": {
        "weight": 0.25,
        "patterns": [
            r"\baccused\b",
            r"\balleged\b",
            r"\ballegation\b",
            r"\bscandal\b",
            r"\bfraud\b",
            r"\bfraudulent\b",
            r"\bwrongdoing\b",
            r"\bimplicated\b",
        ],
        "description": "Accusatory language that may be unverified",
    },
    "financial_data": {
        "weight": 0.15,
        "patterns": [
            r"\bearnings\b",
            r"\brevenue\b",
            r"\bprofit\b",
            r"\bprofits\b",
            r"\beps\b",
            r"\bquarterly\s+results?\b",
            r"\bfinancial\s+results?\b",
            r"\bnet\s+income\b",
            r"\bgross\s+margin\b",
        ],
        "description": "Financial data that should be verified",
    },
    "investment_advice": {
        "weight": 0.2,
        "patterns": [
            r"\bbuy\b",
            r"\bsell\b",
            r"\bhold\b",
            r"\btarget\s+price\b",
            r"\bprice\s+target\b",
            r"\brecommend\b",
            r"\brating\b",
            r"\bupgrade\b",
            r"\bdowngrade\b",
            r"\boverweight\b",
            r"\bunderweight\b",
        ],
        "description": "Investment advice that requires disclaimer",
    },
    "unverified_claims": {
        "weight": 0.1,
        "patterns": [
            r"\breportedly\b",
            r"\bsources?\s+say\b",
            r"\brumor(?:ed|s)?\b",
            r"\bspeculat(?:e|ion|ing)\b",
            r"\bunconfirmed\b",
            r"\ballegedly\b",
            r"\bpurportedly\b",
            r"\bapparently\b",
            r"\bseemingly\b",
        ],
        "description": "Unverified claims that may need confirmation",
    },
}


@dataclass
class RiskResult:
    """Result of risk score calculation."""

    risk_score: float
    flags: List[str] = field(default_factory=list)
    level: str = "low"
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate level based on score if not set."""
        if self.risk_score < 0.3:
            self.level = "low"
        elif self.risk_score < 0.7:
            self.level = "medium"
        else:
            self.level = "high"


class RiskScorer:
    """
    Calculate risk scores for SITREP content.

    Analyzes text content for patterns that indicate higher risk,
    such as legal language, allegations, financial data, investment
    advice, and unverified claims.

    Attributes:
        patterns: Dict of pattern definitions with weights
    """

    def __init__(self, patterns: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize RiskScorer.

        Args:
            patterns: Optional custom patterns dict. Uses RISK_PATTERNS if not provided.
        """
        self.patterns = patterns or RISK_PATTERNS
        # Pre-compile regex patterns for performance
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        for pattern_name, pattern_def in self.patterns.items():
            self._compiled_patterns[pattern_name] = [
                re.compile(p, re.IGNORECASE) for p in pattern_def["patterns"]
            ]

    def _detect_pattern(self, content: str, pattern_name: str) -> Tuple[bool, List[str]]:
        """
        Check if content matches a specific pattern.

        Args:
            content: Text content to analyze
            pattern_name: Name of the pattern to check

        Returns:
            Tuple of (matched: bool, matched_terms: List[str])
        """
        if pattern_name not in self._compiled_patterns:
            return False, []

        matched_terms = []
        for regex in self._compiled_patterns[pattern_name]:
            matches = regex.findall(content)
            if matches:
                matched_terms.extend(matches)

        return bool(matched_terms), matched_terms

    def calculate(
        self,
        content: Optional[str],
        threshold: float = 0.3,
    ) -> RiskResult:
        """
        Calculate risk score for content.

        Args:
            content: Text content to analyze (can be None or empty)
            threshold: Flagging threshold (default 0.3, not currently used
                      for score calculation but reserved for future use)

        Returns:
            RiskResult with risk_score (0.0-1.0), flags list, and level
        """
        # Handle empty/None content
        if not content:
            return RiskResult(
                risk_score=0.0,
                flags=[],
                level="low",
                details={"raw_score": 0.0, "pattern_matches": {}},
            )

        flags: List[str] = []
        weighted_scores: List[float] = []
        pattern_matches: Dict[str, List[str]] = {}

        # Check each pattern
        for pattern_name, pattern_def in self.patterns.items():
            matched, terms = self._detect_pattern(content, pattern_name)
            if matched:
                flags.append(pattern_name)
                weighted_scores.append(pattern_def["weight"])
                pattern_matches[pattern_name] = terms
                logger.debug(
                    f"Pattern '{pattern_name}' matched: {terms[:5]}..."  # Log first 5 terms
                )

        # Calculate final score (sum of weights, capped at 1.0)
        raw_score = sum(weighted_scores)
        final_score = min(1.0, raw_score)

        # Determine risk level
        if final_score < 0.3:
            level = "low"
        elif final_score < 0.7:
            level = "medium"
        else:
            level = "high"

        return RiskResult(
            risk_score=round(final_score, 3),
            flags=flags,
            level=level,
            details={
                "raw_score": round(raw_score, 3),
                "pattern_matches": pattern_matches,
                "threshold": threshold,
            },
        )

    def analyze_batch(
        self,
        contents: List[Dict[str, Any]],
    ) -> Dict[str, RiskResult]:
        """
        Analyze multiple content items.

        Args:
            contents: List of dicts with 'id' and 'content' keys

        Returns:
            Dict mapping content_id -> RiskResult
        """
        results = {}
        for item in contents:
            item_id = str(item.get("id", ""))
            content = item.get("content", "")
            if item_id:
                results[item_id] = self.calculate(content)
        return results


# Singleton instance
_scorer: Optional[RiskScorer] = None


def get_risk_scorer() -> RiskScorer:
    """
    Get singleton RiskScorer instance.

    Returns:
        RiskScorer instance
    """
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer


def reset_risk_scorer() -> None:
    """Reset the singleton (useful for testing)."""
    global _scorer
    _scorer = None
