"""
Metric 1: Sensor Precision (UQ Accuracy)

Measures how accurately the UQ module identifies which analyses are uncertain.

Success Criteria:
- UQ score accuracy > 0.80
- Factor recall > 0.70
- Factor precision > 0.80
"""

from typing import List, Dict, Tuple


def calculate_sensor_precision(
    predicted_uq_score: float,
    expected_uq_range: Tuple[float, float],
    predicted_uncertainty_factors: List[str],
    expected_uncertainty_factors: List[str],
    should_trigger_verification: bool,
    did_trigger_verification: bool
) -> Dict[str, float]:
    """
    Calculate how accurately UQ detected uncertainty.

    Args:
        predicted_uq_score: Actual UQ confidence score from system
        expected_uq_range: (min, max) expected UQ confidence range
        predicted_uncertainty_factors: Uncertainty factors detected by system
        expected_uncertainty_factors: Expected uncertainty factors from ground truth
        should_trigger_verification: Whether verification should be triggered (ground truth)
        did_trigger_verification: Whether verification was actually triggered

    Returns:
        {
            "uq_score_accuracy": float,      # 1.0 if in range, else distance penalty
            "factor_recall": float,          # % of expected factors detected
            "factor_precision": float,       # % of detected factors that were expected
            "factor_f1": float,              # Harmonisches Mittel
            "verification_flag_correct": bool  # Did trigger match expectation?
        }
    """
    # ========================================================================
    # 1. UQ Score Accuracy
    # ========================================================================
    min_uq, max_uq = expected_uq_range

    if min_uq <= predicted_uq_score <= max_uq:
        # Perfect: within expected range
        uq_score_accuracy = 1.0
    else:
        # Penalty based on distance from range
        if predicted_uq_score < min_uq:
            distance = min_uq - predicted_uq_score
        else:
            distance = predicted_uq_score - max_uq

        # Linear penalty: 1.0 distance = 0.0 accuracy
        uq_score_accuracy = max(0.0, 1.0 - distance)

    # ========================================================================
    # 2. Factor Recall (Coverage)
    # ========================================================================
    # How many of the expected factors were detected?

    expected_set = set(normalize_factors(expected_uncertainty_factors))
    predicted_set = set(normalize_factors(predicted_uncertainty_factors))

    if len(expected_set) > 0:
        matches = expected_set.intersection(predicted_set)
        factor_recall = len(matches) / len(expected_set)
    else:
        # No factors expected
        factor_recall = 1.0 if len(predicted_set) == 0 else 0.0

    # ========================================================================
    # 3. Factor Precision (Accuracy)
    # ========================================================================
    # How many of the detected factors were actually expected?

    if len(predicted_set) > 0:
        matches = predicted_set.intersection(expected_set)
        factor_precision = len(matches) / len(predicted_set)
    else:
        # No factors detected
        factor_precision = 1.0 if len(expected_set) == 0 else 0.0

    # ========================================================================
    # 4. Factor F1 Score
    # ========================================================================
    if (factor_precision + factor_recall) > 0:
        factor_f1 = 2 * (factor_precision * factor_recall) / (factor_precision + factor_recall)
    else:
        factor_f1 = 0.0

    # ========================================================================
    # 5. Verification Flag Correctness
    # ========================================================================
    verification_flag_correct = (should_trigger_verification == did_trigger_verification)

    return {
        "uq_score_accuracy": uq_score_accuracy,
        "factor_recall": factor_recall,
        "factor_precision": factor_precision,
        "factor_f1": factor_f1,
        "verification_flag_correct": verification_flag_correct
    }


def normalize_factors(factors: List[str]) -> List[str]:
    """
    Normalize uncertainty factors for comparison.

    - Lowercase
    - Strip whitespace
    - Remove punctuation
    """
    import string

    normalized = []
    for factor in factors:
        # Lowercase and strip
        norm = factor.lower().strip()

        # Remove trailing punctuation
        norm = norm.rstrip(string.punctuation)

        normalized.append(norm)

    return normalized


def calculate_aggregate_sensor_precision(results: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate sensor precision metrics across multiple test cases.

    Args:
        results: List of sensor precision results from calculate_sensor_precision()

    Returns:
        Aggregated metrics with mean and std
    """
    if not results:
        return {}

    import statistics

    metrics = {
        "uq_score_accuracy": [],
        "factor_recall": [],
        "factor_precision": [],
        "factor_f1": [],
        "verification_flag_correct": []
    }

    for result in results:
        for key in metrics.keys():
            metrics[key].append(result[key])

    # Calculate mean and std
    aggregated = {}
    for key, values in metrics.items():
        if key == "verification_flag_correct":
            # Boolean: calculate accuracy rate
            aggregated[f"{key}_rate"] = sum(values) / len(values)
        else:
            aggregated[f"{key}_mean"] = statistics.mean(values)
            if len(values) > 1:
                aggregated[f"{key}_std"] = statistics.stdev(values)
            else:
                aggregated[f"{key}_std"] = 0.0

    return aggregated


def evaluate_sensor_precision(aggregated: Dict[str, float]) -> Dict[str, bool]:
    """
    Evaluate if sensor precision meets success criteria.

    Success Criteria:
    - UQ score accuracy > 0.80
    - Factor recall > 0.70
    - Factor precision > 0.80

    Args:
        aggregated: Output from calculate_aggregate_sensor_precision()

    Returns:
        {
            "uq_score_accuracy_pass": bool,
            "factor_recall_pass": bool,
            "factor_precision_pass": bool,
            "overall_pass": bool
        }
    """
    results = {
        "uq_score_accuracy_pass": aggregated.get("uq_score_accuracy_mean", 0.0) > 0.80,
        "factor_recall_pass": aggregated.get("factor_recall_mean", 0.0) > 0.70,
        "factor_precision_pass": aggregated.get("factor_precision_mean", 0.0) > 0.80
    }

    results["overall_pass"] = all(results.values())

    return results
