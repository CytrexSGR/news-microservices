"""
Intelligence Router Utilities
Shared functions for risk normalization and level calculation
"""


def normalize_risk_score(raw_score: float) -> float:
    """
    Normalize risk score to 0-100 range

    DB values range: avg ~2700, P95 ~4200, max ~5100 (as of 2026-02)
    We normalize to 0-100 for better UX understanding

    Args:
        raw_score: Raw risk score from database

    Returns:
        Normalized score between 0-100
    """
    MAX_OBSERVED_SCORE = 5500.0
    normalized = min(100.0, (raw_score / MAX_OBSERVED_SCORE) * 100.0)
    return round(normalized, 1)


def get_risk_level(score: float) -> str:
    """Convert risk score to risk level string"""
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    else:
        return "critical"
