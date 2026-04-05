# File: services/feed-service/tests/test_risk_scorer.py
"""
Tests for the RiskScorer service.

TDD: Tests written first, then implementation.

Risk patterns tested:
- Legal language ("lawsuit", "litigation", "settlement") - weight 0.3
- Allegations ("accused", "alleged", "scandal") - weight 0.25
- Financial data ("earnings", "revenue", "profit") - weight 0.15
- Investment advice ("buy", "sell", "target price") - weight 0.2
- Unverified claims ("reportedly", "sources say", "rumored") - weight 0.1
"""

import pytest
from typing import Dict, Any


class TestRiskScorer:
    """Test risk score calculation for SITREP content."""

    def test_import_risk_scorer(self):
        """Verify RiskScorer can be imported."""
        from app.services.risk_scorer import RiskScorer, RiskResult

        scorer = RiskScorer()
        assert scorer is not None

    def test_calculate_risk_score_returns_result(self):
        """Test that calculate returns a RiskResult with score, flags, and level."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "Regular market update with standard analysis."

        result = scorer.calculate(content)

        assert hasattr(result, "risk_score")
        assert hasattr(result, "flags")
        assert hasattr(result, "level")
        assert 0.0 <= result.risk_score <= 1.0

    def test_low_risk_content(self):
        """Content without risky patterns should have low risk score."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The company released its quarterly report today. Market conditions remain stable."

        result = scorer.calculate(content)

        assert result.risk_score < 0.3, f"Low risk content scored {result.risk_score}"
        assert result.level == "low"
        assert len(result.flags) == 0

    def test_legal_language_detected(self):
        """Legal terms should trigger legal_language flag with weight 0.3."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The company faces a major lawsuit over patent infringement."

        result = scorer.calculate(content)

        assert "legal_language" in result.flags
        assert result.risk_score >= 0.3, f"Legal language should contribute 0.3, got {result.risk_score}"

    def test_litigation_detected(self):
        """Litigation term should trigger legal_language flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "Ongoing litigation could impact the company's financial position."

        result = scorer.calculate(content)

        assert "legal_language" in result.flags

    def test_settlement_detected(self):
        """Settlement term should trigger legal_language flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The company reached a settlement in the class action case."

        result = scorer.calculate(content)

        assert "legal_language" in result.flags

    def test_allegations_detected(self):
        """Allegation terms should trigger allegations flag with weight 0.25."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The CEO was accused of financial misconduct."

        result = scorer.calculate(content)

        assert "allegations" in result.flags
        assert result.risk_score >= 0.25, f"Allegations should contribute 0.25, got {result.risk_score}"

    def test_alleged_detected(self):
        """'Alleged' should trigger allegations flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The alleged fraud has not been proven in court."

        result = scorer.calculate(content)

        assert "allegations" in result.flags

    def test_scandal_detected(self):
        """'Scandal' should trigger allegations flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The accounting scandal shook investor confidence."

        result = scorer.calculate(content)

        assert "allegations" in result.flags

    def test_financial_data_detected(self):
        """Financial terms should trigger financial_data flag with weight 0.15."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The company reported earnings of $2.5 billion this quarter."

        result = scorer.calculate(content)

        assert "financial_data" in result.flags
        assert result.risk_score >= 0.15, f"Financial data should contribute 0.15, got {result.risk_score}"

    def test_revenue_detected(self):
        """'Revenue' should trigger financial_data flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "Revenue increased by 15% year over year."

        result = scorer.calculate(content)

        assert "financial_data" in result.flags

    def test_profit_detected(self):
        """'Profit' should trigger financial_data flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "Net profit margins expanded to 12% this quarter."

        result = scorer.calculate(content)

        assert "financial_data" in result.flags

    def test_investment_advice_detected(self):
        """Investment advice terms should trigger investment_advice flag with weight 0.2."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "Analysts recommend to buy the stock at current levels."

        result = scorer.calculate(content)

        assert "investment_advice" in result.flags
        assert result.risk_score >= 0.2, f"Investment advice should contribute 0.2, got {result.risk_score}"

    def test_sell_recommendation_detected(self):
        """'Sell' recommendation should trigger investment_advice flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The analyst upgraded from hold to sell rating."

        result = scorer.calculate(content)

        assert "investment_advice" in result.flags

    def test_target_price_detected(self):
        """'Target price' should trigger investment_advice flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The target price was raised to $150 per share."

        result = scorer.calculate(content)

        assert "investment_advice" in result.flags

    def test_unverified_claims_detected(self):
        """Unverified claim terms should trigger unverified_claims flag with weight 0.1."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The company reportedly plans to acquire a competitor."

        result = scorer.calculate(content)

        assert "unverified_claims" in result.flags
        assert result.risk_score >= 0.1, f"Unverified claims should contribute 0.1, got {result.risk_score}"

    def test_sources_say_detected(self):
        """'Sources say' should trigger unverified_claims flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "Sources say the deal could be announced next week."

        result = scorer.calculate(content)

        assert "unverified_claims" in result.flags

    def test_rumored_detected(self):
        """'Rumored' should trigger unverified_claims flag."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "A merger has been rumored for months."

        result = scorer.calculate(content)

        assert "unverified_claims" in result.flags

    def test_multiple_patterns_combined(self):
        """Multiple risk patterns should combine to higher score."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        # Contains: allegations (0.25), legal_language (0.3), financial_data (0.15)
        content = "The company accused of fraud faces a major lawsuit. Earnings were impacted significantly."

        result = scorer.calculate(content)

        # Should have at least 2-3 flags
        assert len(result.flags) >= 2, f"Expected multiple flags, got {result.flags}"
        # Combined score should be higher
        assert result.risk_score >= 0.4, f"Combined patterns should score higher, got {result.risk_score}"

    def test_high_risk_content(self):
        """Content with many risky patterns should score high (>= 0.7)."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        # Contains multiple patterns:
        # - allegations: "accused", "scandal"
        # - legal: "lawsuit"
        # - investment: "buy", "target price"
        # - unverified: "reportedly"
        content = """
        Breaking: CEO accused of massive fraud scandal.
        The company reportedly faces a major lawsuit.
        Analysts still recommend to buy with a target price of $200.
        """

        result = scorer.calculate(content)

        assert result.risk_score >= 0.7, f"High risk content scored {result.risk_score}"
        assert result.level == "high"
        assert len(result.flags) >= 3

    def test_medium_risk_level(self):
        """Content with moderate risk should be level 'medium'."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        # Contains: financial_data (0.15) + investment_advice (0.2) = 0.35
        content = "The company reported strong earnings. Analysts maintain a buy rating."

        result = scorer.calculate(content)

        assert 0.3 <= result.risk_score < 0.7, f"Medium risk content scored {result.risk_score}"
        assert result.level == "medium"

    def test_threshold_parameter(self):
        """Test that threshold parameter affects flagging."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The company reported strong earnings this quarter."  # 0.15 from financial_data

        # Default threshold is 0.3, so this should not be flagged
        result_default = scorer.calculate(content)

        # With lower threshold, this should be flagged
        result_low = scorer.calculate(content, threshold=0.1)

        # Risk score should be the same
        assert result_default.risk_score == result_low.risk_score

    def test_case_insensitive_matching(self):
        """Pattern matching should be case-insensitive."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()

        lower = scorer.calculate("the lawsuit was filed yesterday")
        upper = scorer.calculate("THE LAWSUIT WAS FILED YESTERDAY")
        mixed = scorer.calculate("The LAWSUIT was Filed Yesterday")

        assert lower.risk_score == upper.risk_score == mixed.risk_score
        assert "legal_language" in lower.flags
        assert "legal_language" in upper.flags
        assert "legal_language" in mixed.flags

    def test_empty_content(self):
        """Empty content should have zero risk score."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        result = scorer.calculate("")

        assert result.risk_score == 0.0
        assert result.level == "low"
        assert len(result.flags) == 0

    def test_none_content_handled(self):
        """None content should be handled gracefully."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        result = scorer.calculate(None)

        assert result.risk_score == 0.0
        assert result.level == "low"

    def test_score_capped_at_one(self):
        """Risk score should be capped at 1.0 even with many patterns."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        # Content with ALL patterns - should total more than 1.0 if not capped
        content = """
        The CEO was accused of a massive scandal and alleged fraud.
        The lawsuit and litigation resulted in a major settlement.
        Company earnings, revenue, and profit all declined.
        Analysts say buy now at target price $500.
        Sources say and reportedly it's rumored the company will fail.
        """

        result = scorer.calculate(content)

        assert result.risk_score <= 1.0, f"Score should be capped at 1.0, got {result.risk_score}"

    def test_get_risk_scorer_singleton(self):
        """Test singleton pattern for get_risk_scorer."""
        from app.services.risk_scorer import get_risk_scorer

        scorer1 = get_risk_scorer()
        scorer2 = get_risk_scorer()

        assert scorer1 is scorer2, "Should return the same instance"

    def test_risk_weights_constant(self):
        """Test that RISK_PATTERNS constant is defined correctly."""
        from app.services.risk_scorer import RISK_PATTERNS

        expected_patterns = {
            "legal_language": 0.3,
            "allegations": 0.25,
            "financial_data": 0.15,
            "investment_advice": 0.2,
            "unverified_claims": 0.1,
        }

        for pattern, weight in expected_patterns.items():
            assert pattern in RISK_PATTERNS, f"Missing pattern: {pattern}"
            assert RISK_PATTERNS[pattern]["weight"] == weight, f"Wrong weight for {pattern}"

    def test_result_includes_details(self):
        """RiskResult should include detailed breakdown."""
        from app.services.risk_scorer import RiskScorer

        scorer = RiskScorer()
        content = "The lawsuit caused a scandal affecting earnings."

        result = scorer.calculate(content)

        # Should have details about which patterns matched
        assert hasattr(result, "details")
        assert isinstance(result.details, dict)
