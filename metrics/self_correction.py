"""
Metric 4: Self-Correction Capability (Analysis Improvement)

Measures how much DIA improves analysis quality after verification.

Success Criteria:
- Accuracy improvement > 0.15
- Confidence improvement > 0.10
- Error correction rate > 0.80
- Regression rate < 0.05
- Net quality gain > 0.20
"""

from typing import List, Dict, Set


def calculate_self_correction_capability(
    original_analysis: Dict,
    corrected_analysis: Dict,
    ground_truth: Dict,
    original_uq_score: float,
    corrected_uq_score: float
) -> Dict[str, float]:
    """
    Measure improvement in analysis quality after DIA verification.

    Args:
        original_analysis: Analysis results before verification
        corrected_analysis: Analysis results after verification
        ground_truth: Ground truth from test case
        original_uq_score: UQ confidence before verification
        corrected_uq_score: UQ confidence after verification

    Returns:
        {
            "accuracy_improvement": float,      # Increase in correctness
            "confidence_improvement": float,    # Increase in UQ score
            "error_correction_rate": float,     # % of errors fixed
            "regression_rate": float,           # % of correct data corrupted
            "net_quality_gain": float           # Overall improvement
        }
    """
    # ========================================================================
    # 1. Accuracy Improvement (Facts)
    # ========================================================================
    accuracy_improvement = calculate_accuracy_improvement(
        original_analysis.get("facts", []),
        corrected_analysis.get("facts", []),
        ground_truth.get("facts", [])
    )

    # ========================================================================
    # 2. Confidence Improvement
    # ========================================================================
    confidence_improvement = corrected_uq_score - original_uq_score

    # ========================================================================
    # 3. Error Correction Rate
    # ========================================================================
    error_correction_rate = calculate_error_correction_rate(
        original_analysis.get("facts", []),
        corrected_analysis.get("facts", []),
        ground_truth.get("facts", [])
    )

    # ========================================================================
    # 4. Regression Rate
    # ========================================================================
    regression_rate = calculate_regression_rate(
        original_analysis.get("facts", []),
        corrected_analysis.get("facts", []),
        ground_truth.get("facts", [])
    )

    # ========================================================================
    # 5. Net Quality Gain
    # ========================================================================
    net_quality_gain = accuracy_improvement - regression_rate

    return {
        "accuracy_improvement": accuracy_improvement,
        "confidence_improvement": confidence_improvement,
        "error_correction_rate": error_correction_rate,
        "regression_rate": regression_rate,
        "net_quality_gain": net_quality_gain
    }


def calculate_accuracy_improvement(
    original_facts: List[str],
    corrected_facts: List[str],
    ground_truth_facts: List[str]
) -> float:
    """
    Calculate improvement in factual accuracy.

    Args:
        original_facts: Facts from original analysis
        corrected_facts: Facts from corrected analysis
        ground_truth_facts: Correct facts

    Returns:
        Accuracy improvement delta
    """
    if not ground_truth_facts:
        return 0.0

    # Normalize facts
    correct_set = normalize_facts(ground_truth_facts)
    original_set = normalize_facts(original_facts)
    corrected_set = normalize_facts(corrected_facts)

    # Calculate accuracy scores
    original_accuracy = calculate_fact_accuracy(original_set, correct_set)
    corrected_accuracy = calculate_fact_accuracy(corrected_set, correct_set)

    return corrected_accuracy - original_accuracy


def calculate_fact_accuracy(facts: Set[str], ground_truth: Set[str]) -> float:
    """
    Calculate accuracy of facts against ground truth.

    Uses fuzzy matching for semantic equivalence.

    Args:
        facts: Set of normalized facts
        ground_truth: Set of correct facts

    Returns:
        Accuracy score [0.0, 1.0]
    """
    if not ground_truth:
        return 1.0 if not facts else 0.0

    if not facts:
        return 0.0

    # Count matches using fuzzy comparison
    matches = 0

    for gt_fact in ground_truth:
        if has_match(gt_fact, facts):
            matches += 1

    return matches / len(ground_truth)


def has_match(target: str, candidates: Set[str], threshold: float = 0.7) -> bool:
    """
    Check if target has a semantic match in candidates.

    Uses keyword overlap similarity.

    Args:
        target: Target fact
        candidates: Candidate facts
        threshold: Match threshold

    Returns:
        True if match found
    """
    target_words = set(target.split())

    for candidate in candidates:
        candidate_words = set(candidate.split())

        if target_words and candidate_words:
            overlap = len(target_words.intersection(candidate_words))
            similarity = overlap / len(target_words)

            if similarity >= threshold:
                return True

    return False


def calculate_error_correction_rate(
    original_facts: List[str],
    corrected_facts: List[str],
    ground_truth_facts: List[str]
) -> float:
    """
    Calculate rate of error correction.

    Measures how many original errors were fixed.

    Args:
        original_facts: Original facts
        corrected_facts: Corrected facts
        ground_truth_facts: Ground truth

    Returns:
        Error correction rate [0.0, 1.0]
    """
    correct_set = normalize_facts(ground_truth_facts)
    original_set = normalize_facts(original_facts)
    corrected_set = normalize_facts(corrected_facts)

    # Find original errors (facts not in ground truth)
    original_errors = count_errors(original_set, correct_set)

    if original_errors == 0:
        # No errors to correct
        return 1.0

    # Find remaining errors after correction
    corrected_errors = count_errors(corrected_set, correct_set)

    # Calculate how many errors were fixed
    errors_fixed = original_errors - corrected_errors

    return max(0.0, errors_fixed / original_errors)


def count_errors(facts: Set[str], ground_truth: Set[str]) -> int:
    """
    Count number of incorrect facts.

    Args:
        facts: Facts to check
        ground_truth: Correct facts

    Returns:
        Number of incorrect facts
    """
    errors = 0

    for fact in facts:
        if not has_match(fact, ground_truth):
            errors += 1

    return errors


def calculate_regression_rate(
    original_facts: List[str],
    corrected_facts: List[str],
    ground_truth_facts: List[str]
) -> float:
    """
    Calculate regression rate.

    Measures how many originally correct facts were corrupted.

    Args:
        original_facts: Original facts
        corrected_facts: Corrected facts
        ground_truth_facts: Ground truth

    Returns:
        Regression rate [0.0, 1.0]
    """
    correct_set = normalize_facts(ground_truth_facts)
    original_set = normalize_facts(original_facts)
    corrected_set = normalize_facts(corrected_facts)

    # Find originally correct facts
    originally_correct = set()
    for fact in original_set:
        if has_match(fact, correct_set):
            originally_correct.add(fact)

    if not originally_correct:
        # No correct facts to regress
        return 0.0

    # Count how many are still correct after correction
    still_correct = 0
    for fact in originally_correct:
        if has_match(fact, corrected_set):
            still_correct += 1

    regressions = len(originally_correct) - still_correct

    return regressions / len(originally_correct)


def normalize_facts(facts: List[str]) -> Set[str]:
    """
    Normalize facts for comparison.

    - Lowercase
    - Strip whitespace
    - Remove punctuation
    - Deduplicate

    Args:
        facts: List of facts

    Returns:
        Set of normalized facts
    """
    import re

    normalized = set()

    for fact in facts:
        # Lowercase and strip
        norm = fact.lower().strip()

        # Remove extra whitespace
        norm = re.sub(r'\s+', ' ', norm)

        # Remove trailing punctuation
        norm = norm.rstrip('.,;:!?')

        if norm:
            normalized.add(norm)

    return normalized


def calculate_aggregate_self_correction(
    results: List[Dict[str, float]]
) -> Dict[str, float]:
    """
    Aggregate self-correction metrics across test cases.

    Args:
        results: List of self-correction results

    Returns:
        Aggregated metrics
    """
    if not results:
        return {}

    import statistics

    metrics = {
        "accuracy_improvement": [],
        "confidence_improvement": [],
        "error_correction_rate": [],
        "regression_rate": [],
        "net_quality_gain": []
    }

    for result in results:
        for key in metrics.keys():
            metrics[key].append(result[key])

    aggregated = {}
    for key, values in metrics.items():
        aggregated[f"{key}_mean"] = statistics.mean(values)
        if len(values) > 1:
            aggregated[f"{key}_std"] = statistics.stdev(values)
        else:
            aggregated[f"{key}_std"] = 0.0

    return aggregated


def evaluate_self_correction(aggregated: Dict[str, float]) -> Dict[str, bool]:
    """
    Evaluate if self-correction meets success criteria.

    Success Criteria:
    - Accuracy improvement > 0.15
    - Confidence improvement > 0.10
    - Error correction rate > 0.80
    - Regression rate < 0.05
    - Net quality gain > 0.20

    Args:
        aggregated: Output from calculate_aggregate_self_correction()

    Returns:
        Pass/fail for each criterion
    """
    results = {
        "accuracy_improvement_pass": aggregated.get("accuracy_improvement_mean", 0.0) > 0.15,
        "confidence_improvement_pass": aggregated.get("confidence_improvement_mean", 0.0) > 0.10,
        "error_correction_rate_pass": aggregated.get("error_correction_rate_mean", 0.0) > 0.80,
        "regression_rate_pass": aggregated.get("regression_rate_mean", 1.0) < 0.05,
        "net_quality_gain_pass": aggregated.get("net_quality_gain_mean", 0.0) > 0.20
    }

    results["overall_pass"] = all(results.values())

    return results
