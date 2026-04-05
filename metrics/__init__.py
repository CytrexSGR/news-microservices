"""
Metrics package for DIA validation.

Contains four core metrics:
1. Sensor Precision (UQ Accuracy)
2. Diagnosis Quality (Uncertainty Factors)
3. Planning Effectiveness (Verification Plans)
4. Self-Correction (Analysis Improvement)
"""

from .sensor_precision import (
    calculate_sensor_precision,
    calculate_aggregate_sensor_precision,
    evaluate_sensor_precision
)

from .diagnosis_quality import (
    calculate_diagnosis_quality,
    calculate_aggregate_diagnosis_quality,
    evaluate_diagnosis_quality
)

from .planning_effectiveness import (
    calculate_planning_effectiveness,
    calculate_aggregate_planning_effectiveness,
    evaluate_planning_effectiveness
)

from .self_correction import (
    calculate_self_correction_capability,
    calculate_aggregate_self_correction,
    evaluate_self_correction
)

__all__ = [
    # Sensor Precision
    "calculate_sensor_precision",
    "calculate_aggregate_sensor_precision",
    "evaluate_sensor_precision",
    # Diagnosis Quality
    "calculate_diagnosis_quality",
    "calculate_aggregate_diagnosis_quality",
    "evaluate_diagnosis_quality",
    # Planning Effectiveness
    "calculate_planning_effectiveness",
    "calculate_aggregate_planning_effectiveness",
    "evaluate_planning_effectiveness",
    # Self-Correction
    "calculate_self_correction_capability",
    "calculate_aggregate_self_correction",
    "evaluate_self_correction"
]
