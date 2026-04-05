#!/usr/bin/env python3
"""
Metrics Calculation Script with Mock DIA Agent

Runs adversarial test cases through a mock DIA system and calculates
the four core validation metrics:
1. Sensor Precision (UQ Accuracy)
2. Diagnosis Quality (Uncertainty Factors)
3. Planning Effectiveness (Verification Plans)
4. Self-Correction (Analysis Improvement)

Usage:
    python scripts/calculate_metrics.py --test-cases-dir tests/adversarial-data
    python scripts/calculate_metrics.py --test-case-id misleading_context_001
    python scripts/calculate_metrics.py --report-path reports/metrics_report.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.adversarial_test_case import (
    AdversarialTestCase,
    ChallengeType,
    TestArticle
)
from metrics import (
    calculate_sensor_precision,
    calculate_aggregate_sensor_precision,
    evaluate_sensor_precision,
    calculate_diagnosis_quality,
    calculate_aggregate_diagnosis_quality,
    evaluate_diagnosis_quality,
    calculate_planning_effectiveness,
    calculate_aggregate_planning_effectiveness,
    evaluate_planning_effectiveness,
    calculate_self_correction_capability,
    calculate_aggregate_self_correction,
    evaluate_self_correction
)


class MockDIAAgent:
    """
    Mock DIA (Diagnosis, Inspection, Analysis) Agent for testing metrics.

    Simulates the behavior of a real DIA system by generating plausible
    analysis results with controlled accuracy levels.
    """

    def __init__(self, accuracy_level: float = 0.7):
        """
        Initialize mock agent.

        Args:
            accuracy_level: How accurate the mock agent should be (0.0-1.0)
                          0.7 = 70% of factors/plans match ground truth
        """
        self.accuracy_level = accuracy_level
        self.analysis_count = 0

    def analyze_article(
        self,
        article: TestArticle,
        ground_truth: Dict
    ) -> Dict:
        """
        Run mock analysis on article.

        Args:
            article: Test article to analyze
            ground_truth: Ground truth from test case

        Returns:
            Mock analysis results with:
            - uq_score: Uncertainty quantification confidence
            - uncertainty_factors: List of identified factors
            - should_verify: Verification flag
            - facts: List of extracted facts
        """
        self.analysis_count += 1

        # =====================================================================
        # 1. Mock UQ Score
        # =====================================================================
        expected_min = ground_truth["uq_expectations"]["confidence_range_min"]
        expected_max = ground_truth["uq_expectations"]["confidence_range_max"]

        # Simulate UQ with some noise
        if random.random() < self.accuracy_level:
            # Within expected range
            uq_score = random.uniform(expected_min, expected_max)
        else:
            # Outside range (error case)
            if random.random() < 0.5:
                uq_score = expected_min - random.uniform(0.05, 0.15)
            else:
                uq_score = expected_max + random.uniform(0.05, 0.15)

        uq_score = max(0.0, min(1.0, uq_score))  # Clamp to [0, 1]

        # =====================================================================
        # 2. Mock Uncertainty Factors
        # =====================================================================
        expected_factors = ground_truth["uq_expectations"]["expected_uncertainty_factors"]

        # Start with some expected factors
        num_correct = int(len(expected_factors) * self.accuracy_level)
        predicted_factors = random.sample(expected_factors, num_correct)

        # Add some irrelevant factors (false positives)
        noise_factors = [
            "Low source credibility",
            "Outdated information",
            "Biased language detected",
            "Statistical claims lack context",
            "Expert opinion missing"
        ]
        num_noise = random.randint(0, 2)
        predicted_factors.extend(random.sample(noise_factors, num_noise))

        random.shuffle(predicted_factors)

        # =====================================================================
        # 3. Mock Verification Flag
        # =====================================================================
        should_verify_expected = ground_truth["uq_expectations"]["should_trigger_verification"]

        # Simulate verification decision (mostly correct)
        if random.random() < self.accuracy_level:
            should_verify = should_verify_expected
        else:
            should_verify = not should_verify_expected

        # =====================================================================
        # 4. Mock Extracted Facts
        # =====================================================================
        # Generate plausible facts from article content
        correct_facts = ground_truth["correct_analysis"]["facts"]

        # Start with some correct facts
        num_correct_facts = int(len(correct_facts) * self.accuracy_level)
        predicted_facts = random.sample(correct_facts, num_correct_facts)

        # Add some incorrect facts (errors)
        error_facts = [
            "The company raised $50 million in funding",
            "The CEO announced plans to expand internationally",
            "Industry experts predict significant market disruption",
            "Government regulations are expected to change next quarter"
        ]
        num_errors = random.randint(1, 2)
        predicted_facts.extend(random.sample(error_facts, num_errors))

        random.shuffle(predicted_facts)

        return {
            "uq_score": uq_score,
            "uncertainty_factors": predicted_factors,
            "should_verify": should_verify,
            "facts": predicted_facts
        }

    def generate_verification_plan(
        self,
        analysis: Dict,
        ground_truth: Dict
    ) -> Dict:
        """
        Generate mock verification plan.

        Args:
            analysis: Analysis results from analyze_article()
            ground_truth: Ground truth from test case

        Returns:
            Mock verification plan with:
            - priority: Verification priority level
            - verification_methods: List of methods
            - external_sources: List of sources
        """
        expected_plan = ground_truth["verification_plan"]

        # =====================================================================
        # 1. Mock Priority
        # =====================================================================
        expected_priority = expected_plan["priority"]
        priority_levels = ["low", "medium", "high", "critical"]

        if random.random() < self.accuracy_level:
            # Correct priority
            priority = expected_priority
        else:
            # Wrong priority (±1 level)
            idx = priority_levels.index(expected_priority)
            if random.random() < 0.5 and idx > 0:
                priority = priority_levels[idx - 1]
            elif idx < len(priority_levels) - 1:
                priority = priority_levels[idx + 1]
            else:
                priority = expected_priority

        # =====================================================================
        # 2. Mock Verification Methods
        # =====================================================================
        expected_methods = expected_plan["verification_methods"]

        # Include some expected methods
        num_correct_methods = int(len(expected_methods) * self.accuracy_level)
        methods = random.sample(expected_methods, num_correct_methods)

        # Add some noise methods
        noise_methods = [
            "Fact-check claims against Wikipedia",
            "Run sentiment analysis",
            "Check for plagiarism",
            "Verify image metadata"
        ]
        num_noise_methods = random.randint(0, 1)
        methods.extend(random.sample(noise_methods, num_noise_methods))

        # =====================================================================
        # 3. Mock External Sources
        # =====================================================================
        expected_sources = expected_plan["external_sources"]

        # Include some expected sources
        num_correct_sources = int(len(expected_sources) * self.accuracy_level)
        sources = random.sample(expected_sources, num_correct_sources)

        # Add some noise sources
        noise_sources = [
            "Wikipedia",
            "Google News Archive",
            "Social media monitoring tools"
        ]
        num_noise_sources = random.randint(0, 1)
        sources.extend(random.sample(noise_sources, num_noise_sources))

        return {
            "priority": priority,
            "verification_methods": methods,
            "external_sources": sources
        }

    def apply_self_correction(
        self,
        original_analysis: Dict,
        verification_plan: Dict,
        ground_truth: Dict
    ) -> Tuple[Dict, float]:
        """
        Simulate self-correction after verification.

        Args:
            original_analysis: Original analysis results
            verification_plan: Verification plan that was executed
            ground_truth: Ground truth from test case

        Returns:
            Tuple of (corrected_analysis, corrected_uq_score)
        """
        correct_facts = ground_truth["correct_analysis"]["facts"]
        original_facts = original_analysis["facts"]

        # =====================================================================
        # Simulate Improvement
        # =====================================================================
        # Start with original facts
        corrected_facts = original_facts.copy()

        # Fix some errors (remove incorrect facts)
        incorrect_facts = [f for f in corrected_facts if f not in correct_facts]
        num_fixes = int(len(incorrect_facts) * 0.6)  # Fix 60% of errors
        facts_to_remove = random.sample(incorrect_facts, num_fixes)
        corrected_facts = [f for f in corrected_facts if f not in facts_to_remove]

        # Add some missing correct facts
        missing_facts = [f for f in correct_facts if f not in corrected_facts]
        num_additions = int(len(missing_facts) * 0.4)  # Add 40% of missing
        facts_to_add = random.sample(missing_facts, num_additions)
        corrected_facts.extend(facts_to_add)

        # Simulate small regression (corrupt 5% of correct facts)
        currently_correct = [f for f in corrected_facts if f in correct_facts]
        if currently_correct:
            num_regressions = max(0, int(len(currently_correct) * 0.05))
            if num_regressions > 0:
                facts_to_corrupt = random.sample(currently_correct, num_regressions)
                corrected_facts = [f for f in corrected_facts if f not in facts_to_corrupt]

        # =====================================================================
        # Improve UQ Score
        # =====================================================================
        original_uq = original_analysis["uq_score"]
        expected_min = ground_truth["uq_expectations"]["confidence_range_min"]
        expected_max = ground_truth["uq_expectations"]["confidence_range_max"]

        # Move closer to expected range
        if original_uq < expected_min:
            corrected_uq = original_uq + random.uniform(0.05, 0.15)
        elif original_uq > expected_max:
            corrected_uq = original_uq - random.uniform(0.05, 0.15)
        else:
            # Already in range, small improvement
            corrected_uq = original_uq + random.uniform(0.02, 0.08)

        corrected_uq = max(0.0, min(1.0, corrected_uq))

        return {
            "facts": corrected_facts
        }, corrected_uq


class MetricsCalculator:
    """
    Calculates and aggregates validation metrics across test cases.
    """

    def __init__(
        self,
        test_cases_dir: Path,
        mock_accuracy: float = 0.7
    ):
        """
        Initialize metrics calculator.

        Args:
            test_cases_dir: Directory containing test case JSON files
            mock_accuracy: Accuracy level for mock DIA agent (0.0-1.0)
        """
        self.test_cases_dir = test_cases_dir
        self.mock_agent = MockDIAAgent(accuracy_level=mock_accuracy)
        self.results = []

    def load_test_cases(
        self,
        test_case_id: Optional[str] = None
    ) -> List[AdversarialTestCase]:
        """
        Load test cases from directory.

        Args:
            test_case_id: Optional specific test case to load

        Returns:
            List of loaded test cases
        """
        test_cases = []

        if test_case_id:
            # Load specific test case
            file_path = self.test_cases_dir / f"{test_case_id}.json"
            if file_path.exists():
                test_case = AdversarialTestCase.load_from_file(str(file_path))
                test_cases.append(test_case)
            else:
                print(f"⚠️  Test case not found: {file_path}")
        else:
            # Load all test cases
            for file_path in self.test_cases_dir.glob("*.json"):
                if file_path.name == "metadata.json":
                    continue
                test_case = AdversarialTestCase.load_from_file(str(file_path))
                test_cases.append(test_case)

        return test_cases

    def run_test_case(self, test_case: AdversarialTestCase) -> Dict:
        """
        Run single test case through mock DIA pipeline.

        Args:
            test_case: Test case to run

        Returns:
            Results dictionary with all metric calculations
        """
        print(f"\n{'='*70}")
        print(f"Test Case: {test_case.test_case_id}")
        print(f"Challenge: {test_case.ground_truth.challenge_type.value}")
        print(f"Difficulty: {test_case.ground_truth.difficulty_level}/5")
        print(f"{'='*70}")

        gt = test_case.ground_truth

        # =====================================================================
        # Step 1: Initial Analysis
        # =====================================================================
        print("\n[1/4] Running initial analysis...")
        original_analysis = self.mock_agent.analyze_article(
            test_case.article,
            gt.model_dump()
        )

        # =====================================================================
        # Step 2: Verification Plan
        # =====================================================================
        print("[2/4] Generating verification plan...")
        verification_plan = self.mock_agent.generate_verification_plan(
            original_analysis,
            gt.model_dump()
        )

        # =====================================================================
        # Step 3: Self-Correction
        # =====================================================================
        print("[3/4] Applying self-correction...")
        corrected_analysis, corrected_uq = self.mock_agent.apply_self_correction(
            original_analysis,
            verification_plan,
            gt.model_dump()
        )

        # =====================================================================
        # Step 4: Calculate Metrics
        # =====================================================================
        print("[4/4] Calculating metrics...")

        # Metric 1: Sensor Precision
        sensor_precision = calculate_sensor_precision(
            predicted_uq_score=original_analysis["uq_score"],
            expected_uq_range=(
                gt.uq_expectations.confidence_range_min,
                gt.uq_expectations.confidence_range_max
            ),
            predicted_uncertainty_factors=original_analysis["uncertainty_factors"],
            expected_uncertainty_factors=gt.uq_expectations.expected_uncertainty_factors,
            should_trigger_verification=gt.uq_expectations.should_trigger_verification,
            did_trigger_verification=original_analysis["should_verify"]
        )

        # Metric 2: Diagnosis Quality
        diagnosis_quality = calculate_diagnosis_quality(
            predicted_factors=original_analysis["uncertainty_factors"],
            expected_factors=gt.uq_expectations.expected_uncertainty_factors,
            challenge_description=gt.challenge_description,
            verification_plan=verification_plan
        )

        # Metric 3: Planning Effectiveness
        planning_effectiveness = calculate_planning_effectiveness(
            predicted_plan=verification_plan,
            expected_plan=gt.verification_plan.model_dump()
        )

        # Metric 4: Self-Correction
        self_correction = calculate_self_correction_capability(
            original_analysis={"facts": original_analysis["facts"]},
            corrected_analysis=corrected_analysis,
            ground_truth={"facts": gt.correct_analysis.facts},
            original_uq_score=original_analysis["uq_score"],
            corrected_uq_score=corrected_uq
        )

        # =====================================================================
        # Print Summary
        # =====================================================================
        print("\n" + "─" * 70)
        print("RESULTS:")
        print("─" * 70)

        print(f"\n📊 Metric 1: Sensor Precision")
        print(f"  UQ Score Accuracy:     {sensor_precision['uq_score_accuracy']:.3f}")
        print(f"  Factor Recall:         {sensor_precision['factor_recall']:.3f}")
        print(f"  Factor Precision:      {sensor_precision['factor_precision']:.3f}")
        print(f"  Factor F1:             {sensor_precision['factor_f1']:.3f}")
        print(f"  Verification Correct:  {sensor_precision['verification_flag_correct']}")

        print(f"\n📊 Metric 2: Diagnosis Quality")
        print(f"  Factor Match Score:    {diagnosis_quality['factor_match_score']:.3f}")
        print(f"  Root Cause Found:      {diagnosis_quality['root_cause_identified']}")
        print(f"  Actionability Score:   {diagnosis_quality['actionability_score']:.3f}")
        print(f"  Coverage Score:        {diagnosis_quality['coverage_score']:.3f}")

        print(f"\n📊 Metric 3: Planning Effectiveness")
        print(f"  Method Coverage:       {planning_effectiveness['method_coverage']:.3f}")
        print(f"  Source Coverage:       {planning_effectiveness['source_coverage']:.3f}")
        print(f"  Priority Accuracy:     {planning_effectiveness['priority_accuracy']:.3f}")
        print(f"  Efficiency Score:      {planning_effectiveness['efficiency_score']:.3f}")
        print(f"  Completeness Score:    {planning_effectiveness['completeness_score']:.3f}")

        print(f"\n📊 Metric 4: Self-Correction")
        print(f"  Accuracy Improvement:  {self_correction['accuracy_improvement']:+.3f}")
        print(f"  Confidence Improve:    {self_correction['confidence_improvement']:+.3f}")
        print(f"  Error Correction Rate: {self_correction['error_correction_rate']:.3f}")
        print(f"  Regression Rate:       {self_correction['regression_rate']:.3f}")
        print(f"  Net Quality Gain:      {self_correction['net_quality_gain']:+.3f}")

        return {
            "test_case_id": test_case.test_case_id,
            "challenge_type": test_case.ground_truth.challenge_type.value,
            "difficulty_level": test_case.ground_truth.difficulty_level,
            "sensor_precision": sensor_precision,
            "diagnosis_quality": diagnosis_quality,
            "planning_effectiveness": planning_effectiveness,
            "self_correction": self_correction
        }

    def run_all_test_cases(
        self,
        test_case_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Run all test cases and collect results.

        Args:
            test_case_id: Optional specific test case to run

        Returns:
            List of result dictionaries
        """
        test_cases = self.load_test_cases(test_case_id)

        if not test_cases:
            print("❌ No test cases found")
            return []

        print(f"\n✓ Loaded {len(test_cases)} test case(s)")
        print(f"✓ Mock DIA Agent accuracy: {self.mock_agent.accuracy_level:.1%}")

        results = []
        for test_case in test_cases:
            result = self.run_test_case(test_case)
            results.append(result)

        self.results = results
        return results

    def calculate_aggregate_metrics(self) -> Dict:
        """
        Aggregate metrics across all test cases.

        Returns:
            Aggregated metrics with pass/fail evaluations
        """
        if not self.results:
            return {}

        # Separate results by metric
        sensor_results = [r["sensor_precision"] for r in self.results]
        diagnosis_results = [r["diagnosis_quality"] for r in self.results]
        planning_results = [r["planning_effectiveness"] for r in self.results]
        correction_results = [r["self_correction"] for r in self.results]

        # Calculate aggregations
        sensor_agg = calculate_aggregate_sensor_precision(sensor_results)
        diagnosis_agg = calculate_aggregate_diagnosis_quality(diagnosis_results)
        planning_agg = calculate_aggregate_planning_effectiveness(planning_results)
        correction_agg = calculate_aggregate_self_correction(correction_results)

        # Evaluate against success criteria
        sensor_eval = evaluate_sensor_precision(sensor_agg)
        diagnosis_eval = evaluate_diagnosis_quality(diagnosis_agg)
        planning_eval = evaluate_planning_effectiveness(planning_agg)
        correction_eval = evaluate_self_correction(correction_agg)

        return {
            "sensor_precision": {
                "aggregated": sensor_agg,
                "evaluation": sensor_eval
            },
            "diagnosis_quality": {
                "aggregated": diagnosis_agg,
                "evaluation": diagnosis_eval
            },
            "planning_effectiveness": {
                "aggregated": planning_agg,
                "evaluation": planning_eval
            },
            "self_correction": {
                "aggregated": correction_agg,
                "evaluation": correction_eval
            }
        }

    def generate_report(self, output_path: Optional[Path] = None) -> Dict:
        """
        Generate comprehensive metrics report.

        Args:
            output_path: Optional path to save JSON report

        Returns:
            Complete report dictionary
        """
        aggregated = self.calculate_aggregate_metrics()

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_cases_count": len(self.results),
            "mock_agent_accuracy": self.mock_agent.accuracy_level,
            "individual_results": self.results,
            "aggregated_metrics": aggregated
        }

        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n✓ Report saved: {output_path}")

        # Print human-readable summary
        self.print_report_summary(report)

        return report

    def print_report_summary(self, report: Dict):
        """Print human-readable report summary."""
        print("\n" + "=" * 70)
        print("AGGREGATED METRICS REPORT")
        print("=" * 70)

        agg = report["aggregated_metrics"]

        # Sensor Precision
        print("\n📊 METRIC 1: SENSOR PRECISION (UQ Accuracy)")
        print("─" * 70)
        sp = agg["sensor_precision"]
        print(f"  UQ Score Accuracy:  {sp['aggregated'].get('uq_score_accuracy_mean', 0):.3f} ± {sp['aggregated'].get('uq_score_accuracy_std', 0):.3f}")
        print(f"  Factor Recall:      {sp['aggregated'].get('factor_recall_mean', 0):.3f} ± {sp['aggregated'].get('factor_recall_std', 0):.3f}")
        print(f"  Factor Precision:   {sp['aggregated'].get('factor_precision_mean', 0):.3f} ± {sp['aggregated'].get('factor_precision_std', 0):.3f}")
        print(f"  Factor F1:          {sp['aggregated'].get('factor_f1_mean', 0):.3f} ± {sp['aggregated'].get('factor_f1_std', 0):.3f}")
        print(f"\n  Evaluation:")
        for key, passed in sp['evaluation'].items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"    {key:30s} {status}")

        # Diagnosis Quality
        print("\n📊 METRIC 2: DIAGNOSIS QUALITY")
        print("─" * 70)
        dq = agg["diagnosis_quality"]
        print(f"  Factor Match Score: {dq['aggregated'].get('factor_match_score_mean', 0):.3f} ± {dq['aggregated'].get('factor_match_score_std', 0):.3f}")
        print(f"  Root Cause Rate:    {dq['aggregated'].get('root_cause_identified_rate', 0):.3f}")
        print(f"  Actionability:      {dq['aggregated'].get('actionability_score_mean', 0):.3f} ± {dq['aggregated'].get('actionability_score_std', 0):.3f}")
        print(f"\n  Evaluation:")
        for key, passed in dq['evaluation'].items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"    {key:30s} {status}")

        # Planning Effectiveness
        print("\n📊 METRIC 3: PLANNING EFFECTIVENESS")
        print("─" * 70)
        pe = agg["planning_effectiveness"]
        print(f"  Method Coverage:    {pe['aggregated'].get('method_coverage_mean', 0):.3f} ± {pe['aggregated'].get('method_coverage_std', 0):.3f}")
        print(f"  Source Coverage:    {pe['aggregated'].get('source_coverage_mean', 0):.3f} ± {pe['aggregated'].get('source_coverage_std', 0):.3f}")
        print(f"  Priority Accuracy:  {pe['aggregated'].get('priority_accuracy_mean', 0):.3f} ± {pe['aggregated'].get('priority_accuracy_std', 0):.3f}")
        print(f"  Completeness:       {pe['aggregated'].get('completeness_score_mean', 0):.3f} ± {pe['aggregated'].get('completeness_score_std', 0):.3f}")
        print(f"\n  Evaluation:")
        for key, passed in pe['evaluation'].items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"    {key:30s} {status}")

        # Self-Correction
        print("\n📊 METRIC 4: SELF-CORRECTION")
        print("─" * 70)
        sc = agg["self_correction"]
        print(f"  Accuracy Improve:   {sc['aggregated'].get('accuracy_improvement_mean', 0):+.3f} ± {sc['aggregated'].get('accuracy_improvement_std', 0):.3f}")
        print(f"  Confidence Improve: {sc['aggregated'].get('confidence_improvement_mean', 0):+.3f} ± {sc['aggregated'].get('confidence_improvement_std', 0):.3f}")
        print(f"  Error Correction:   {sc['aggregated'].get('error_correction_rate_mean', 0):.3f} ± {sc['aggregated'].get('error_correction_rate_std', 0):.3f}")
        print(f"  Regression Rate:    {sc['aggregated'].get('regression_rate_mean', 0):.3f} ± {sc['aggregated'].get('regression_rate_std', 0):.3f}")
        print(f"  Net Quality Gain:   {sc['aggregated'].get('net_quality_gain_mean', 0):+.3f} ± {sc['aggregated'].get('net_quality_gain_std', 0):.3f}")
        print(f"\n  Evaluation:")
        for key, passed in sc['evaluation'].items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"    {key:30s} {status}")

        # Overall
        print("\n" + "=" * 70)
        all_passed = all([
            agg["sensor_precision"]["evaluation"]["overall_pass"],
            agg["diagnosis_quality"]["evaluation"]["overall_pass"],
            agg["planning_effectiveness"]["evaluation"]["overall_pass"],
            agg["self_correction"]["evaluation"]["overall_pass"]
        ])

        if all_passed:
            print("✓ OVERALL: ALL METRICS PASS")
        else:
            print("✗ OVERALL: SOME METRICS FAIL")
        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate DIA validation metrics on adversarial test cases"
    )
    parser.add_argument(
        "--test-cases-dir",
        type=Path,
        default=Path("tests/adversarial-data"),
        help="Directory containing test case JSON files"
    )
    parser.add_argument(
        "--test-case-id",
        type=str,
        help="Run specific test case only (e.g., misleading_context_001)"
    )
    parser.add_argument(
        "--mock-accuracy",
        type=float,
        default=0.7,
        help="Mock DIA agent accuracy level (0.0-1.0, default: 0.7)"
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        help="Path to save JSON report (e.g., reports/metrics_report.json)"
    )

    args = parser.parse_args()

    # Initialize calculator
    calculator = MetricsCalculator(
        test_cases_dir=args.test_cases_dir,
        mock_accuracy=args.mock_accuracy
    )

    # Run test cases
    calculator.run_all_test_cases(test_case_id=args.test_case_id)

    # Generate report
    calculator.generate_report(output_path=args.report_path)


if __name__ == "__main__":
    main()
